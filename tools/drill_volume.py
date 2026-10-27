"""R120终结的空间覆盖层：共享原纹理，有限3D源粒子卡片，不创建碰撞或独立伤害。"""
import math,itertools,numpy as np

def build(a):
    # 1个核心、6个内层、42个外层：位置分布在三维球体，不能只把地面的平面圆放大。
    directions=[]
    for v in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)):directions.append((np.asarray(v,float),.30,.65))
    for i in range(42):
        y=1-2*(i+.5)/42;phi=i*math.pi*(3-math.sqrt(5));r=math.sqrt(1-y*y)
        directions.append((np.array([r*math.cos(phi),y,r*math.sin(phi)]),.82,.72))
    layers=[];bounds=[]
    for blue in (True,):
        key='Blue' if blue else 'Fire';name='IrisArsenal/DrillField/'+key;start=0 if blue else .56;life=.52 if blue else 1.65
        tex='textures/effects/GlowSlightFlash.dds' if blue else 'textures/effects/FXSteamThinAnim.dds'
        palette='textures/effects/gradients/GradShockRune.dds' if blue else 'textures/effects/gradients/GradFireExplosion.dds'
        # 保留原羽化/动态图集细节；gamma只提可见边缘，不画不透明球壳、不借地震贴地喷流。
        spec={'opaque':False,'particle':True,'burst_particle':True,'coverage_field':True,'texture':a.texture(tex),'palette':a.texture(palette),'has_palette':True,'shader_flags':[16,32],'atlas':1 if blue else 8,'gain':1.5 if blue else 4.5,'base_color':[1,1,1,1],'grey_color':True,'grey_alpha':False,'ion_blue':blue,'uv':[0,0,1,1] if blue else [0,0,1,-1],
              'colors':[[.75,.75,.75,0],[.80,.80,.80,.22 if blue else .80],[.25,.25,.25,0]],'intervals':[0,.12,.18,1],'fade_in':.08 if blue else .045,'fade_out':.24 if blue else .55,'size_curve':[.25,.85,1,.92,.8],'blend':'src_alpha one' if blue else 'src_alpha one_minus_src_alpha','profile':[1,.75,0,0]}
        a.MATS[name]=spec;particles=[]
        particles.append([0,0,0,0,0,0,start,life,.82,0])
        for i,(d,radius,size) in enumerate(directions):
            p=d*radius;v=d*(.12 if blue else .09)
            if not blue:v[1]+=.06
            birth=start if blue else start+.002*(i%5)
            # 每层有独立3D位置/扩张，蓝相必须先消失；火相另有升腾和64格纹理动画。
            particles.append([*p,*v,birth,life if not blue else .52-birth,size,(i*.61803398875%1)*math.tau])
        for p in particles:
            extent=p[8]*max(spec['size_curve'])*math.sqrt(2)
            for c in (np.array(p[:3]),np.array(p[:3])+np.array(p[3:6])*p[7]):
                bounds.extend(c+np.array(sign)*extent for sign in itertools.product((-1,1),repeat=3))
        layers.append({'name':'R120 '+key+' volume','material':name,'particles':particles,'plugin_capacity':49,'size_curve':spec['size_curve'],'atlas':spec['atlas'],'coverage_field':True,'source_texture':tex,'source_palette':palette,'adaptation':'为用户R120蓝相进行透明三维覆盖；火相已使用独立原火球组件；共享原纹理，不宣称原NiPSys位置逐点相同'})
    q=np.array(bounds);return layers,{'layers':layers,'bounds':q.tolist(),'reference_radius':1,'particle_count':sum(len(l['particles']) for l in layers),'additional_draw_calls':1,'source_texture_reused':True,'hard_damage_radius_game_units':120,'dense_uniform_opaque_sphere':False}
