"""042枪口细节：只读取原MPS尺寸与旋转，独立52字节顶点；不增加贴图/发射器。"""
import numpy as np,struct,re
from nif_reader import Reader
from fx_timeline import raw_blocks

def decorate(source,layers,materials):
    raw,_=raw_blocks(source);rng=np.random.default_rng(284042)
    for layer in layers:
        # 原BSPSysScaleModifier通常含数十个点；旧5点近似会抹去快胀/回卷细节。
        target=layer['source_parameters']['target'];shape=np.ones(17)
        for kind,data in raw.values():
            if kind!='BSPSysScaleModifier':continue
            r=Reader(data);r.read('II');owner=r.read('i');active=r.read('B');n=r.read('I');values=np.asarray(r.read(str(n)+'f'));r.done()
            if owner==target and active:shape*=np.interp(np.linspace(0,1,17),np.linspace(0,1,n),values)
        layer['size_curve17']=shape.tolist();d=materials[layer['material']];d['muzzle_detail']=True;d['size_curve17']=shape.tolist()
        rotation=layer.get('source_rotation')
        for p in layer['particles']:
            omega=0.
            if rotation:
                omega=rotation['speed']+rng.uniform(-rotation['variation'],rotation['variation'])
                if rotation['random_sign'] and rng.integers(0,2):omega=-omega
            p.append(float(omega))
    return {'source_size_samples':17,'source_spin_per_particle':True,'source_textures_and_colours':'unchanged','limitations':'源random_axis在相机卡片上仅保留绕卡片法线的角速度；原Drag/受控湍流尚未执行，不声称完整NiPSys'}

def submesh(a,layer):
    # 前十个粒子值仍是旧合同；仅该附件追加角速度到TEXCOORD0.z，不改变其他效果布局。
    verts=[];indices=[]
    for p in layer['particles']:
        assert len(p)==11;base=len(verts)
        verts.extend([(*p[:10],u,v,p[10]) for u,v in ((0,0),(1,0),(1,1),(0,1))]);indices.extend([base,base+1,base+2,base,base+2,base+3])
    decl=a.a.chunk(0x5100,b''.join(a.a.chunk(0x5110,struct.pack('<5H',0,t,s,o,0)) for t,s,o in ((2,1,0),(2,4,12),(3,5,24),(2,7,40))))
    vb=b''.join(struct.pack('<13f',*v) for v in verts)
    geom=a.a.chunk(0x5000,struct.pack('<I',len(verts))+decl+a.a.chunk(0x5200,struct.pack('<HH',0,52)+a.a.chunk(0x5210,vb)))
    return a.a.chunk(0x4000,layer['material'].encode()+b'\n'+struct.pack('<?I?',False,len(indices),False)+struct.pack('<%dH'%len(indices),*indices)+geom),np.asarray([v[:3] for v in verts])

def material(text,d):
    points=d['size_curve17'];uniforms=''
    for i in range(4):uniforms+=' param_named sizeSamples%d float4 '%i+' '.join('%.9f'%v for v in points[i*4:i*4+4])+'\n'
    uniforms+=' param_named sizeSampleEnd float %.9f\n'%points[-1]
    # 新程序不再消费旧5点常量；删除绑定，避免HLSL优化后Ogre找不到常量而禁用整个材质。
    text=re.sub(r' param_named size(?:Curve|End) float4[^\n]*\n','',text)
    return text.replace('vertex_program_ref IrisBurstVP {','vertex_program_ref IrisMuzzleVP {\n'+uniforms)

def shader(shared):
    # 和既有透明度/原图集完全同源，只在该附件用更密尺寸曲线和真实角速度。
    core=shared[shared.index('VOut iris_burst_vp('):shared.index('// 源NiBillboardNode')]
    core=core.replace('iris_burst_vp(VIn i','iris_muzzle_vp(MuzzleInput i').replace('uniform float3 sourceAcceleration)', 'uniform float3 sourceAcceleration,uniform float4 sizeSamples0,uniform float4 sizeSamples1,uniform float4 sizeSamples2,uniform float4 sizeSamples3,uniform float sizeSampleEnd)')
    size=' float curve[17]={'+','.join('sizeSamples%d.%s'%(i,j) for i in range(4) for j in 'xyzw')+',sizeSampleEnd};float x=t*16;int segment=min(15,(int)x);float size=lerp(curve[segment],curve[segment+1],saturate(x-segment));\n'
    core=re.sub(r' float x=t\*4;[^\n]*\n',lambda _:size,core)
    core=core.replace('uniform float4 sizeCurve,uniform float4 sizeEnd,','')
    core=core.replace('i.uv','i.uv.xy').replace('cos(i.c.w),sn=sin(i.c.w)','cos(i.c.w+i.uv.z*et),sn=sin(i.c.w+i.uv.z*et)')
    # 051源Fade Out Percent是开始淡出的寿命位置，原pFireGlow为0.15；旧1-0.15令亮球滞留至85%。
    # 仅该枪口程序使用正确的源开始时刻，原火焰核心/火星/余烬五层和20发出生点完全保留。
    # 不修改其他招式共享的IrisBurstVP；没有额外亮度、半径或颜色臆造。
    # 原引擎Update在第二颜色区间宽度==0时明确保持中间色；Glow的[0,0.3,0,0]正是此例。
    # 旧代码用max(.001,0)强行插值到第三色，0.3寿命后把暗红中间色换成高亮橙色，掩盖火苗。
    # 证据仅为离线SkyrimSE.exe RTTI定位Update的01323673/013236ed分支；插件不调用/存储这些地址。
    old='float4 color=t<intervals.y?lerp(color0,color1,saturate((t-intervals.x)/max(.001,intervals.y-intervals.x))):t<intervals.z?color1:lerp(color1,color2,saturate((t-intervals.z)/max(.001,intervals.w-intervals.z)));'
    new='float4 color=color1; if(intervals.y!=intervals.x && t<intervals.y)color=t<intervals.x?color0:lerp(color0,color1,saturate((t-intervals.x)/(intervals.y-intervals.x))); else if(intervals.w!=intervals.z && t>intervals.z)color=t>intervals.w?color2:lerp(color1,color2,saturate((t-intervals.z)/(intervals.w-intervals.z)));'
    assert old in core;core=core.replace(old,new)
    core=core.replace('(t-(1-fades.y))/max(.001,fades.y)', '(t-fades.y)/max(.001,1-fades.y)')
    core=core.replace('t>1-fades.y?alphaOut', '(fades.y>0 && t>fades.y)?alphaOut')
    return '\n// 042原枪口专用布局；其他粒子保留48字节/5点路径。\nstruct MuzzleInput {float4 p:POSITION;float3 n:NORMAL;float4 c:COLOR;float3 uv:TEXCOORD0;};\n'+core

PROGRAM="""
vertex_program IrisMuzzleVP hlsl
{
 source iris_eight.hlsl
 entry_point iris_muzzle_vp
 target vs_4_0
 default_params {
 param_named_auto wvp worldviewproj_matrix
 param_named_auto inverseWorldView inverse_worldview_matrix
 param_named_auto clock custom 1
 }
}
"""
