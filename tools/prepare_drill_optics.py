"""只准备钻头光学材质/PNG文本资源，不编译C++或HLSL、不导出网格、不部署游戏。"""
from pathlib import Path
from io import BytesIO
import json,hashlib
import numpy as np
from PIL import Image
from safeio import ROOT,put
from nif_geometry import read_nif
A=ROOT/'package/IrisArsenal/assets'
SOURCE=Path('E:/skyrimspecialedition/mods/soulworker_Iris')
CONTRACT='IRIS_DRILL_OPTICS_V1'
SHADER=r"""// Iris钻头前向材质：沿用POSITION/NORMAL/UV；066仅圆环的自有实例消费custom9裁剪门。
struct MetalInput {float4 position:POSITION;float3 normal:NORMAL;float4 uv:TEXCOORD0;};
struct MetalOutput {float4 position:SV_Position;float4 uv:TEXCOORD0;float3 normal:TEXCOORD1;float3 view:TEXCOORD2;};
MetalOutput iris_drill_metal_vp(MetalInput i,uniform float4x4 worldViewProjMatrix,uniform float4x4 worldMatrix,
                              uniform float4x4 normalMatrix,uniform float3 cameraPosition) {
 MetalOutput o;o.position=mul(worldViewProjMatrix,i.position);o.uv=i.uv;
 o.normal=mul((float3x3)normalMatrix,i.normal);o.view=cameraPosition-mul(worldMatrix,i.position).xyz;return o;
}
// 066：小金属箍保留原金属法线/UV/照明，仅在旋转前将整组三角置于远裁剪面外。
// 使用实例custom9，不能改共享IndexData或材质常量；开门后顶点保持原worldViewProj变换。
MetalOutput iris_drill_ring_metal_vp(MetalInput i,uniform float4x4 worldViewProjMatrix,uniform float4x4 worldMatrix,
                                   uniform float4x4 normalMatrix,uniform float3 cameraPosition,uniform float4 ringState) {
 MetalOutput o=iris_drill_metal_vp(i,worldViewProjMatrix,worldMatrix,normalMatrix,cameraPosition);
 if(ringState.x<0.5)o.position=float4(0,0,2,1);return o;
}
Texture2D sourceTex:register(t0);SamplerState sourceSampler:register(s0);
float3 unitSafe(float3 x) {return x*rsqrt(max(dot(x,x),0.0000001));}
float4 iris_drill_metal_fp(MetalOutput i,uniform float3 emission,uniform float3 specularColour,
                          uniform float glossiness,uniform float specularStrength,uniform float4 uvTransform,
                          uniform float3 sunDirection,uniform float4 sunColour,
                          uniform float3 zenithLight,uniform float3 nadirLight):SV_Target {
 float3 base=sourceTex.Sample(sourceSampler,i.uv.xy*uvTransform.zw+uvTransform.xy).rgb;
 float3 N=unitSafe(i.normal),V=unitSafe(i.view),L=unitSafe(sunDirection),H=unitSafe(V+L);
 // 源几何允许双面显示；背面光照方向翻正，不让一整片旋转叶片成为没有高光的黑剪影。
 if(dot(N,V)<0)N=-N;
 float ndl=saturate(dot(N,L)),nv=saturate(dot(N,V));float fresnel=pow(1-nv,5);
 float3 sky=max(zenithLight,0),ground=max(nadirLight,0),sun=max(sunColour.rgb,0);
 float3 ambient=lerp(ground,sky,saturate(N.y*0.5+0.5));
 float3 reflected=lerp(ground,sky,saturate(reflect(-V,N).y*0.5+0.5));
 // Kenshi没有滚5原ENB环境贴图；用原生天/地环境与太阳作显式近似。发光和镜面值仍来自源材质，
 // 少量环境底光只保留深灰体块；亮点由法线/观察方向产生，随模型真实旋转移动，不靠随机闪烁。
 // 041原002.dds只有40～49的深灰，不能再以0.18作为暗部基底把源色压成墨黑。
 // 保留源像素作为可读底色，附加Kenshi环境与太阳；不改贴图、不染色、不把金属改成自发光。
 float3 diffuse=base*(1.0+ambient*0.45+sun*ndl*0.65);
 float3 specular=specularColour*specularStrength*0.25*sun*pow(saturate(dot(N,H)),max(glossiness,1));
 // 原翼片镜面强度10也要参与广域环境反射，而非只在极窄的太阳高光中生效。
 float3 reflection=reflected*specularColour*max(specularStrength,0)*(0.06+0.18*fresnel);
 // 源实体部件没有NiAlphaProperty：diffuse alpha不是这里的透明度，必须按不透明实体绘制。
 return float4(diffuse+specular+reflection+base*emission,1);
}
// 066：四张源弧光保留原UV/片元着色，只增加和钻头同一时钟的实例裁剪；不自行旋转贴图。
struct OpticInput {float4 position:SV_Position;float4 colour:COLOR;float4 uv:TEXCOORD0;};
OpticInput iris_drill_ring_optic_vp(MetalInput i,uniform float4x4 worldViewProjMatrix,uniform float4 ringState) {
 OpticInput o;o.position=mul(worldViewProjMatrix,i.position);o.colour=float4(1,1,1,1);o.uv=i.uv;
 // 所有顶点同时移到z>w；开门时恢复原投影，不制造可见缩放、渐变或等待阶段。
 if(ringState.x<0.5)o.position=float4(0,0,2,1);return o;
}
float4 iris_drill_optic_fp(OpticInput i,uniform float3 emission,uniform float4 uvTransform,
                          uniform float alphaScale,uniform float alphaReference):SV_Target {
 float4 texel=sourceTex.Sample(sourceSampler,i.uv.xy*uvTransform.zw+uvTransform.xy);
 float alpha=texel.a*alphaScale;
 // 原NiAlphaProperty=4845：SRC_ALPHA/INV_SRC_ALPHA且GREATER阈值8。白RGB/零alpha边框必须不可见。
 clip(alpha>alphaReference?1:-1);
 return float4(texel.rgb*(1+emission),alpha);
}
"""
PROGRAM=r"""// IRIS_DRILL_OPTICS_V1：仅前向队列83内的自有钻头；参数由Ogre自动绑定，无ABI偏移。
vertex_program IrisArsenal_DrillMetal_VP hlsl
{
 source iris_drill_optics.hlsl
 entry_point iris_drill_metal_vp
 target vs_4_0
 default_params
 {
  param_named_auto worldViewProjMatrix worldviewproj_matrix
  param_named_auto worldMatrix world_matrix
  param_named_auto normalMatrix inverse_transpose_world_matrix
  param_named_auto cameraPosition camera_position
 }
}
fragment_program IrisArsenal_DrillMetal_FP hlsl
{
 source iris_drill_optics.hlsl
 entry_point iris_drill_metal_fp
 target ps_4_0
 default_params
 {
  shared_params_ref SharedSkyParams
  shared_params_ref AmbientParams
 }
}
// 066仅小箍及四个圆环材质使用；14个实体钻片与双翼仍走原程序，无custom9依赖。
vertex_program IrisArsenal_DrillRingMetal_VP hlsl
{
 source iris_drill_optics.hlsl
 entry_point iris_drill_ring_metal_vp
 target vs_4_0
 default_params
 {
  param_named_auto worldViewProjMatrix worldviewproj_matrix
  param_named_auto worldMatrix world_matrix
  param_named_auto normalMatrix inverse_transpose_world_matrix
  param_named_auto cameraPosition camera_position
  param_named_auto ringState custom 9
 }
}
vertex_program IrisArsenal_DrillRingOptic_VP hlsl
{
 source iris_drill_optics.hlsl
 entry_point iris_drill_ring_optic_vp
 target vs_4_0
 default_params
 {
  param_named_auto worldViewProjMatrix worldviewproj_matrix
  param_named_auto ringState custom 9
 }
}
fragment_program IrisArsenal_DrillOptic_FP hlsl
{
 source iris_drill_optics.hlsl
 entry_point iris_drill_optic_fp
 target ps_4_0
}
"""
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def vector(values):return ' '.join('%.9f'%v for v in values)
def prepare():
    source=SOURCE/'Meshes/SW/Iris/EXDrill1.nif';meshes,_=read_nif(source);assert len(meshes)==19
    # 原BC7 DDS已经由本次真实D3D11日志报告加载失败；仅解码相同像素到PNG，不重新绘制/调色。
    anim=SOURCE/'Textures/Soulworker/Iris/anim.dds';image=Image.open(anim).convert('RGBA');buf=BytesIO();image.save(buf,format='PNG')
    png=buf.getvalue();assert np.array_equal(np.array(image),np.array(Image.open(BytesIO(png)).convert('RGBA')))
    png_name='iris_anim_rgba_179f128b96e16ff2.png';put(A/png_name,png,'源BC7纹理兼容转存','相同RGBA像素转PNG，保留原DDS不覆盖；不编译任何代码','游戏PNG/新HLSL加载仍待实机')
    materials={};bindings=[]
    for i,mesh in enumerate(meshes):
        sh=mesh['shader_data'];alpha=mesh['alpha_data'];opaque=alpha is None
        role='energy_shell' if i==0 else 'metal' if i<15 else 'optical'
        assert opaque==(i<15);assert not mesh['colours'],'本次源无顶点色，不能误称已完整移植未知顶点色'
        texture=SOURCE/mesh['textures'][0].replace('\\','/');texture_name=png_name if i==0 else 'iris_'+digest(texture)[:16]+'.dds'
        assert (A/texture_name).is_file()
        data={'role':role,'texture':texture_name,'emission':[v*sh['emissive_mult'] for v in sh['emissive']],
              'glossiness':sh['glossiness'],'specular':sh['specular'],'specular_strength':sh['specular_strength'],
              'uv':sh['uv_offset']+sh['uv_scale'],'alpha':alpha,'alpha_scale':sh['alpha'],'clamp_mode':sh['clamp_mode']}
        name='IrisArsenal/DrillOpticsV1/'+role+'_'+hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()[:12]
        materials[name]=data;bindings.append({'sub':i,'source_node':mesh['name'],'runtime_material':name,'source_shader':sh,'source_alpha':alpha,'source_texture':str(texture)})
    text=[]
    for name,d in materials.items():
        opaque=d['alpha'] is None
        if not opaque:assert (d['alpha']['flags'],d['alpha']['source_blend'],d['alpha']['destination_blend'],d['alpha']['test_function'])==(4845,6,7,4)
        lines=['// '+CONTRACT+'；源角色 '+d['role'],'material '+name,'{',' technique',' {','  pass','  {','   lighting off','   depth_check on','   depth_write '+('on' if opaque else 'off'),'   cull_hardware none','   scene_blend '+('one zero' if opaque else 'alpha_blend'),
               '   vertex_program_ref '+('IrisArsenal_DrillRingMetal_VP' if d['role']=='energy_shell' else 'IrisArsenal_DrillMetal_VP' if opaque else 'IrisArsenal_DrillRingOptic_VP')+' {}',
               '   fragment_program_ref '+('IrisArsenal_DrillMetal_FP' if opaque else 'IrisArsenal_DrillOptic_FP'),'   {',
               '    param_named emission float3 '+vector(d['emission']),'    param_named uvTransform float4 '+vector(d['uv'])]
        if opaque:lines+=['    param_named specularColour float3 '+vector(d['specular']),'    param_named glossiness float %.9f'%d['glossiness'],'    param_named specularStrength float %.9f'%d['specular_strength']]
        else:lines+=['    param_named alphaScale float %.9f'%d['alpha_scale'],'    param_named alphaReference float %.9f'%(d['alpha']['threshold']/255)]
        # NiTexClampMode 0..3分别是夹/夹、夹/环绕、环绕/夹、环绕/环绕；本招不自行制造UV滚动。
        modes=['clamp clamp','clamp wrap','wrap clamp','wrap wrap'];assert d['clamp_mode'] in range(4)
        lines+=['   }','   texture_unit','   {','    texture '+d['texture'],'    tex_address_mode '+modes[d['clamp_mode']],'    filtering trilinear','   }','  }',' }','}'];text.append('\n'.join(lines))
    put(A/'iris_drill_optics.hlsl',SHADER,'源金属/能量/弧光着色器','世界法线镜面/环境近似；实体alpha=1、源弧光透明测试/混合；源发光不再除16','不编译HLSL，真实Ogre加载/光照仍待验证')
    put(A/'iris_drill_optics.program',PROGRAM,'钻头GPU程序声明','仅使用网格已有输入及Ogre自动矩阵/相机和本机已存在天空/环境共享参数','游戏编译待用户运行')
    put(A/'iris_drill_optics.material','\n\n'.join(text)+'\n','钻头分层材质','保留源不同镜面强度1/10与能量发光3；四张弧光按原alpha混合，不影响普通武器材质','视觉适配不等于滚5ENB完全一致')
    profile=(A/'drill.csv').read_text('utf-8').splitlines();assert profile[0]=='IRIS_DRILL 2 8 19' and len(profile)==29
    profile=profile[:10]+[str(x['sub'])+' '+x['runtime_material'] for x in bindings]
    put(A/'drill.csv','\n'.join(profile)+'\n','运行时绑定文本','只替换19层绑定名；头、时间、几何及八胶囊数值不变，现有v2消费者可读','需整包带新program/material/shader/PNG')
    # 旧导出材质仅作兼容后备，也不再让实体工厂尝试加载已知失败的BC7贴图。
    p=A/'iris.material';legacy=p.read_text('utf-8');legacy=legacy.replace('texture iris_179f128b96e16ff2.dds','texture '+png_name)
    put(p,legacy,'旧材质兼容纹理引用','只将钻头旧能量材质纹理引用改为同像素PNG；普通武器材质/参数保持','运行时钻头实际使用独立新材质')
    record={'contract':CONTRACT,'source_nif':str(source),'source_nif_sha256':digest(source),'source_anim_sha256':digest(anim),'png':png_name,
            'decoded_pixels_identical':True,'bindings':bindings,'materials':materials,
            'adaptation':'原ENB环境不可复制，金属用Kenshi天空/地面/太阳的前向镜面近似；发光/纹理/光泽/透明来自源；无新增几何或人物动作',
            'cpp_ring_contract':'IRIS_DRILL_RING_GATE_066','cpp_changed':True,'compiled':False,'deployed':False,'runtime_verified':False}
    put(ROOT/'docs/drill-optics.json',json.dumps(record,ensure_ascii=False,indent=2),'源材质与运行绑定合同','逐层记录源身份、镜面/发光/透明和无损PNG，解释有意覆盖旧mesh默认材质名','HLSL真实编译及新画面未验证')
    print('OPTICS_PREPARED',len(bindings),'layers',len(materials),'materials; no C++/HLSL compilation or game deployment')
if __name__=='__main__':prepare()
