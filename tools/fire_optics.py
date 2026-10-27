"""源特效分类与辉光遮罩；不把折射辅助壳误画为实体，不修改源NIF/贴图。"""
import copy

def refractive(mesh):
    sh=mesh['shader_data']
    # niftools官方SkyrimShaderPropertyFlags1：0x8000为Refraction；本源GeoSphere强度0.6。
    return not sh.get('effect') and bool(sh.get('flags',[0])[0]&0x8000)

def flame_meshes(meshes):
    out=copy.deepcopy(meshes)
    for mesh in out:
        fx=mesh['shader_data'].get('effect')
        if fx and not fx['source_texture'] and mesh['name'].startswith('Glow'):
            # 原无遮罩Glow只靠顶点透明，当前前向适配容易变成实心色片；借同一源库羽化光斑遮罩。
            # 仅改这份火焰mesh的材质描述，保留源颜色/UV/曲线；不能污染武器和其他技能共享材质。
            fx['source_texture']='textures/effects/GlowSlightFlash.dds'
            mesh['visual_adaptation']='untextured glow masked with source library GlowSlightFlash; not original texture binding'
    return out
