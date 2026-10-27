"""独立极致驱动HLSL源码；复用实际源贴图/CC0纹理，不由作者工具编译。"""
SHADER=r'''
// 059顶点来自原EXanim1刚性组或闭合三维圆柱；所有时间均由实例游戏时钟提供。
Texture2D texture0:register(t0);SamplerState sampler0:register(s0);
Texture2D texture1:register(t1);SamplerState sampler1:register(s1);
struct Input {float4 p:POSITION;float3 n:NORMAL;float4 c:COLOR0;float2 uv:TEXCOORD0;};
struct Output {float4 p:SV_Position;float3 n:TEXCOORD0;float3 view:TEXCOORD1;float2 uv:TEXCOORD2;};
Output iris_drive_mount_vp(Input i,uniform float4x4 wvp,uniform float4x4 worldMatrix,uniform float4x4 normalMatrix,uniform float3 cameraPosition,uniform float4 delta0,uniform float4 delta1,uniform float4 delta2){
 float4 p=float4(dot(delta0,i.p),dot(delta1,i.p),dot(delta2,i.p),1);
 float3 n=float3(dot(delta0.xyz,i.n),dot(delta1.xyz,i.n),dot(delta2.xyz,i.n));
 Output o;o.p=mul(wvp,p);o.n=mul((float3x3)normalMatrix,n);o.view=cameraPosition-mul(worldMatrix,p).xyz;o.uv=i.uv;return o;
}
float4 iris_drive_mount_fp(Output i,uniform float4 clock,uniform float4 colour,uniform float4 surface):SV_Target {
 float4 texel=texture0.Sample(sampler0,i.uv);float alpha=texel.a*colour.a*clock.y;clip(alpha-.002);
 // 原003炮体保留明暗/金属色，004准星保留原蓝红像素，不能再用统一绿色或灰黑替代。
 float light=.48+.52*abs(dot(normalize(i.n+1e-7),normalize(float3(.3,.8,.52))));
 float highlight=pow(abs(dot(normalize(i.n+1e-7),normalize(i.view+1e-7))),16)*.08;
 // 原NiAlpha为空，不能前后所有三角面相加而变粉白。源发光RGB/倍数保留，微弱漫反射/高光保持方向参数有效。
 float3 rgb=texel.rgb*(.15+.05*light+highlight)+surface.rgb*surface.a;return float4(rgb,alpha);
}
Output iris_drive_stream_vp(Input i,uniform float4x4 wvp,uniform float4x4 worldMatrix,uniform float4x4 normalMatrix,uniform float3 cameraPosition){
 Output o;o.p=mul(wvp,i.p);o.n=mul((float3x3)normalMatrix,i.n);o.view=cameraPosition-mul(worldMatrix,i.p).xyz;o.uv=i.uv;return o;
}
float4 iris_drive_stream_fp(Output i,uniform float4 clock,uniform float4 layer):SV_Target {
 // UV沿实际游戏长度重复，10000长的射程不会把一张纹理拉成静止糊片；蓝白光流只用下载原图采样。
 float facing=abs(dot(normalize(i.n+1e-7),normalize(i.view+1e-7)));
 float along=i.uv.x*clock.w/36-clock.x*(7+layer.x*2);
 float flow=texture1.Sample(sampler1,float2(along,i.uv.y+clock.x*.18+layer.x*.31)).r;
 float core=texture0.Sample(sampler0,float2(along*.2,.5+.32*(1-facing))).r;
 float amount=layer.x<.5?(.16+.84*flow):layer.x<1.5?(.24+.76*flow)*core:core;
 float3 rgb=layer.x<.5?float3(.10,.50,1.45):layer.x<1.5?float3(.26,.72,1.65):float3(.82,1.06,1.36);
 float alpha=saturate(amount*(.28+.72*facing)*clock.y*(layer.x<.5?.52:.86));clip(alpha-.002);
 return float4(rgb*(1.1+.9*flow),alpha);
}
'''

PROGRAM=''
for name,entry,vs in [('IrisDriveMountVP','iris_drive_mount_vp',True),('IrisDriveMountFP','iris_drive_mount_fp',False),('IrisDriveStreamVP','iris_drive_stream_vp',True),('IrisDriveStreamFP','iris_drive_stream_fp',False)]:
    PROGRAM+=('vertex_program ' if vs else 'fragment_program ')+name+' hlsl\n{\n source iris_drive059.hlsl\n entry_point '+entry+'\n target '+('vs_4_0' if vs else 'ps_4_0')+'\n'
    if vs:
        PROGRAM+=' default_params {\n param_named_auto wvp worldviewproj_matrix\n param_named_auto worldMatrix world_matrix\n param_named_auto normalMatrix inverse_transpose_world_matrix\n param_named_auto cameraPosition camera_position\n'
        if name=='IrisDriveMountVP':PROGRAM+=' param_named_auto delta0 custom 5\n param_named_auto delta1 custom 6\n param_named_auto delta2 custom 7\n'
        PROGRAM+=' }\n'
    PROGRAM+='}\n'

def stream_materials():
    return '\n'.join('material IrisArsenal/Drive059/Stream'+str(i)+'\n{ technique { pass {\n lighting off\n depth_check on\n depth_write off\n cull_hardware none\n scene_blend src_alpha one\n vertex_program_ref IrisDriveStreamVP {}\n fragment_program_ref IrisDriveStreamFP { param_named_auto clock custom 1\n param_named layer float4 '+str(i)+' 0 0 0\n }\n texture_unit { texture iris_drive059_laser.png\n tex_address_mode wrap\n }\n texture_unit { texture iris_drive059_flow.png\n tex_address_mode wrap\n }\n } } }\n' for i in range(3))
