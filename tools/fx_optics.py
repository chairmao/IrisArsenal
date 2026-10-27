"""034光学轴与尺寸校准；源网格保留，新增环/电弧明确按参考图与录像重建，不冒称运行NiPSys。"""
import copy,math,struct
import numpy as np

def canonical_disc(meshes,a):
    # PlasmaBall的源圆盘法向转换后为Y，运行时所有飞弹以Z为前向；在作者端统一整个层级和法线。
    B=np.eye(4);B[:3,:3]=[[1,0,0],[0,0,-1],[0,1,0]];H=np.eye(4);H[:3,:3]=a.C*a.SCALE
    out=copy.deepcopy(meshes)
    for mesh in out:mesh['matrix']=np.linalg.inv(H)@B@H@mesh['matrix']
    return out

def ground_unit(meshes,d,a):
    # 旧整段3D最大包围半径114.85把最亮的地面层27单位一起缩小，主火环因此不到AOE边缘。
    # 每源层XZ最大半径仍归一为1；Y独立按角色尺度校准，不能被原XZ大包围半径压成地面薄片。
    # 仅可视层升腾：不移动球形伤害中心、不扩大健康半径；火焰像素不冒充球形接触壳。
    H=np.eye(4);H[:3,:3]=a.C*a.SCALE;out=copy.deepcopy(meshes);allp=[];scales=[];source_vertical=d['peak_radius']
    for mesh,tr in zip(out,d['tracks']):
        p=(np.asarray(mesh['vertices'])@mesh['matrix'][:3,:3].T+mesh['matrix'][:3,3])@a.C.T*a.SCALE
        points=[p]
        for state in tr['frames']:
            m=np.asarray(state[13:]).reshape(3,4);points.append(p@m[:,:3].T+m[:,3])
        radius=max(float(np.linalg.norm(q[:,[0,2]],axis=1).max()) for q in points);assert radius>0
        source_top=max(float(q[:,1].max()) for q in points);assert source_top>0
        target_top=.72 if mesh['name'].startswith('LowerFlame') else .36 if mesh['name']=='Plane01' else .16 if mesh['name'].startswith('WispsGround') else .025
        vertical=source_top/target_top
        N=np.diag([1/radius,1/vertical,1/radius,1]);Ni=np.linalg.inv(N);mesh['matrix']=np.linalg.inv(H)@N@H@mesh['matrix']
        p=(np.asarray(mesh['vertices'])@mesh['matrix'][:3,:3].T+mesh['matrix'][:3,3])@a.C.T*a.SCALE
        for state in tr['frames']:
            m=np.eye(4);m[:3]=np.asarray(state[13:]).reshape(3,4);m=N@m@Ni;state[13:]=m[:3].reshape(-1).tolist();allp.append(p@m[:3,:3].T+m[:3,3])
        scales.append({'mesh':mesh['name'],'source_horizontal_radius':radius,'source_top':source_top,'target_top':target_top})
    p=np.concatenate(allp);d['bounds']=[p.min(0).tolist(),p.max(0).tolist()];d['peak_radius']=float(np.linalg.norm(p,axis=1).max());d['ground_normalization']={'horizontal_radius':1,'vertical_source_scale':source_vertical,'vertical_adaptation':'LowerFlame top .72*AOE radius, Plane .36, wisps .16, glow .025; XZ unchanged','layers':scales}
    return out

def submesh(a,name,verts,indices):
    decl=a.chunk(0x5100,b''.join(a.chunk(0x5110,struct.pack('<5H',0,t,s,o,0)) for t,s,o in [(2,1,0),(2,4,12),(3,5,24),(1,7,40)]))
    vb=b''.join(struct.pack('<12f',*v) for v in verts);geom=a.chunk(0x5000,struct.pack('<I',len(verts))+decl+a.chunk(0x5200,struct.pack('<HH',0,48)+a.chunk(0x5210,vb)))
    return a.chunk(0x4000,name.encode()+b'\n'+struct.pack('<?I?',False,len(indices),False)+struct.pack('<%dH'%len(indices),*indices)+geom)

def energy_geometry(a,mats,ion=False):
    # 真正三维的环面/细管电弧，顶点预算固定；不使用不透明幕布，不给装饰层添加物理或健康事件。
    verts=[];idx=[];kind=2 if ion else 0;name='IrisArsenal/Eight/'+('MuzzleIon' if ion else 'BeamRings')
    def vertex(p,n,c,uv):verts.append((*p,*n,*c,*uv));return len(verts)-1
    def quad(i,j,k,l):idx.extend([i,j,k,i,k,l])
    if not ion:
        for z in np.linspace(.025,.96,8):
            base=len(verts)
            for j in range(49):
                u=j*2*math.pi/48
                for k in range(9):
                    v=k*2*math.pi/8;r=.87+.055*math.cos(v)
                    vertex((r*math.cos(u),r*math.sin(u),z+.0014*math.sin(v)),(math.cos(u)*math.cos(v),math.sin(u)*math.cos(v),math.sin(v)),(1,.55,.14,1),(j/48,k/8))
            for j in range(48):
                for k in range(8):i=base+j*9+k;quad(i,i+9,i+10,i+1)
    else:
        # 录像159.8秒蓝色喷流：八条独立螺旋光丝，围绕枪口短距离散开；相位由游戏时钟推进。
        for strand in range(8):
            base=len(verts)
            for j in range(41):
                t=j/40;angle=strand*math.pi/4+t*math.pi*2;r=.12+.85*math.sin(t*math.pi*.8)
                for k in range(5):
                    v=k*math.pi/2;thick=.018
                    vertex(((r+thick*math.cos(v))*math.cos(angle),(r+thick*math.cos(v))*math.sin(angle),-.22+t*.75+thick*math.sin(v)),(math.cos(angle)*math.cos(v),math.sin(angle)*math.cos(v),math.sin(v)),(.12,.52,1,math.sin(math.pi*t)**.45),(t,k/4))
            for j in range(40):
                for k in range(4):i=base+j*5+k;quad(i,i+5,i+6,i+1)
    mats[name]={'energy_kind':kind,'reference_reconstruction':True,'basis':'用户光炮图/原录像159.8秒；固定三维几何，不是原NiPSys运行'}
    return submesh(a,name,verts,idx),name,np.array([v[:3] for v in verts])

def beam_arcs(a,mats):
    # 参考图束外有细密电弧：固定四条三维折线细管，时间只旋转/闪烁自有几何，顶点数与射程无关。
    name='IrisArsenal/Eight/BeamArcs';verts=[];idx=[]
    for strand in range(4):
        base=len(verts)
        for j in range(65):
            z=j/64;angle=strand*math.pi/2+z*18+.28*math.sin(j*4.37+strand);r=.57+.19*math.sin(j*2.47+strand)
            for k in range(5):
                v=k*math.pi/2;th=.009
                verts.append(((r+th*math.cos(v))*math.cos(angle),(r+th*math.cos(v))*math.sin(angle),z,(math.cos(angle)*math.cos(v)),math.sin(angle)*math.cos(v),math.sin(v),.58,.60,1,math.sin(z*math.pi)**.2,z,k/4))
        for j in range(64):
            for k in range(4):i=base+j*5+k;idx.extend([i,i+5,i+6,i,i+6,i+1])
    mats[name]={'energy_kind':1,'reference_reconstruction':True,'basis':'用户光炮参考图外层电弧；四条固定三维光丝，不是原程序闪电'}
    return submesh(a,name,verts,idx),name,np.array([v[:3] for v in verts])

def augment_beam(a,mats,data,names,p,curve):
    extra,name,q=energy_geometry(a,mats);arc,an,ap=beam_arcs(a,mats);extra+=arc;q=np.concatenate([q,ap]);p=np.concatenate([p,q]);head=data.index(b'\n')+1
    # 原五层源能量管仍使用各自源曲线；附加环面只增加一个identity曲线，所有层处于同一单位圆柱。
    body=data[head+6:-34]+extra;data=data[:head]+a.chunk(0x3000,body+a.chunk(0x9000,struct.pack('<7f',*p.min(0),*p.max(0),np.linalg.norm(p,axis=1).max())))
    ident=[1,1,1,1,0,0,1,1,1,1,0,1,1]+np.eye(4)[:3].reshape(-1).tolist()
    for label in ['reference_coaxial_rings','reference_energy_arcs']:curve['tracks'].append({'mesh':label,'frames':[ident.copy() for _ in range(curve['samples'])]})
    curve['bounds']=[np.minimum(curve['bounds'][0],q.min(0)).tolist(),np.maximum(curve['bounds'][1],q.max(0)).tolist()];curve['peak_radius']=max(curve['peak_radius'],float(np.linalg.norm(q,axis=1).max()))
    return data,names+[name,an],p

def ion_asset(a,mats):
    blob,name,p=energy_geometry(a,mats,True)
    data=b'\x00\x10[MeshSerializer_v1.41]\n'+a.chunk(0x3000,b'\0'+blob+a.chunk(0x9000,struct.pack('<7f',*p.min(0),*p.max(0),np.linalg.norm(p,axis=1).max())))
    return data,[name],p

SHADER=r"""
// 光炮金环和枪口离子光只使用自有三维几何；长度/相位来自实例游戏时钟，不用墙钟。
VOut iris_energy_vp(VIn i,uniform float4x4 wvp,uniform float4x4 normalMatrix,uniform float4x4 worldMatrix,uniform float3 cameraPosition,uniform float4 clock,uniform float4 energyKind){
 if(energyKind.x<.5&&clock.w>0)i.p.z*=min(clock.w,240)/clock.w;
 if(energyKind.x>.5){float angle=clock.x*(energyKind.x>1.5?7:2);float co=cos(angle),si=sin(angle);i.p.xy=float2(co*i.p.x-si*i.p.y,si*i.p.x+co*i.p.y);}
 VOut o;o.p=mul(wvp,i.p);o.c=i.c;o.uv=i.uv;o.n=mul((float3x3)normalMatrix,i.n);o.view=cameraPosition-mul(worldMatrix,i.p).xyz;return o;
}
float4 iris_energy_fp(VOut i,uniform float4 clock,uniform float4 energyKind):SV_Target {
 float facing=abs(dot(normalize(i.n+0.00001),normalize(i.view+0.00001)));
 float ripple=.7+.3*sin(i.uv.x*44-clock.x*18);float a=i.c.a*clock.y*(.45+.55*facing);
 float3 c=i.c.rgb*(1.4+1.2*ripple);if(energyKind.x>1.5)c=lerp(float3(.08,.35,1),float3(.65,.9,1.3),pow(ripple,5))*2.0;
 return float4(c,a);
}
"""
