"""按原演示158.9秒准星重建平面光学标记；未确认其独立NIF，不冒称Tips1或其他网格直移。"""
import math,struct,hashlib
import numpy as np

def export(a,mats):
    subs=[];allp=[]
    for layer,rgb in [('Cyan',(0,.55,1)),('Red',(1,.015,.025))]:
        name='IrisArsenal/Eight/Reticle'+layer;verts=[];indices=[]
        def polygon(points):
            base=len(verts)
            for x,y in points:verts.append((x,y,0,0,0,1,*rgb,1,0,0));allp.append((x,y,0))
            for k in range(1,len(points)-1):indices.extend([base,base+k,base+k+1])
        if layer=='Cyan':
            # 录像中两排青蓝四分环，中轴留出红刻线的空隙；z恒0，绝不变成球/陀螺。
            for inner,outer in [(.64,.71),(.90,1.)]:
                for sector in range(4):
                    for n in range(24):
                        u=math.radians(sector*90+17+56*n/24);v=math.radians(sector*90+17+56*(n+1)/24)
                        polygon([(inner*math.cos(u),inner*math.sin(u)),(outer*math.cos(u),outer*math.sin(u)),(outer*math.cos(v),outer*math.sin(v)),(inner*math.cos(v),inner*math.sin(v))])
        else:
            for sector in range(4):
                angle=math.radians(sector*90);co,si=math.cos(angle),math.sin(angle);points=[]
                # 圆端刻线按录像的内外间距重建；只是显示，没有物理/伤害对象。
                for center,begin in [(.48,90),(1.10,-90)]:
                    for n in range(9):
                        theta=math.radians(begin+180*n/8);r=center+.055*math.cos(theta);t=.055*math.sin(theta);points.append((r*co-t*si,r*si+t*co))
                polygon(points)
        mats[name]={'reference_reticle':True,'rgb':list(rgb),'alpha':.96,'basis':'video 158.9s, reconstructed flat arcs/ticks; no verified NIF'}
        decl=a.chunk(0x5100,b''.join(a.chunk(0x5110,struct.pack('<5H',0,t,s,o,0)) for t,s,o in [(2,1,0),(2,4,12),(3,5,24),(1,7,40)]));vb=b''.join(struct.pack('<12f',*v) for v in verts)
        geom=a.chunk(0x5000,struct.pack('<I',len(verts))+decl+a.chunk(0x5200,struct.pack('<HH',0,48)+a.chunk(0x5210,vb)))
        subs.append(a.chunk(0x4000,name.encode()+b'\n'+struct.pack('<?I?',False,len(indices),False)+struct.pack('<%dH'%len(indices),*indices)+geom))
    p=np.array(allp);blob=b'\x00\x10[MeshSerializer_v1.41]\n'+a.chunk(0x3000,b'\0'+b''.join(subs)+a.chunk(0x9000,struct.pack('<7f',*p.min(0),*p.max(0),np.linalg.norm(p,axis=1).max())))
    return blob,['IrisArsenal/Eight/ReticleCyan','IrisArsenal/Eight/ReticleRed'],p

SHADER=r"""
// 准星是对照录像重绘的薄环/刻线；颜色独立于日照，透明度只跟随当前动作游戏时钟。
float4 iris_reticle_fp(VOut i,uniform float4 clock):SV_Target {
 float pulse=.94+.06*cos(clock.x*6.2831853);return float4(i.c.rgb*1.15,i.c.a*clock.y*pulse);
}
"""
