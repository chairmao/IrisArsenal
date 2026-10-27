"""地震FXdustBurstTiny的两层有限粒子翻译；源发射面、速度、寿命、颜色、图集，不运行Skyrim系统。"""
import struct,json,hashlib,math
import numpy as np
from nif_reader import Reader,parse
from fx_timeline import raw_blocks,sample

def export(a,texture,mats):
    path=a.ROOT/'tools/source-cache/FXdustBurstTiny.nif';decoded=parse(path);blocks={v['index']:v for v in decoded['parsed_blocks']};raw,strings=raw_blocks(path);nodes={}
    for i,(kind,b) in raw.items():
        if kind not in ('BSFadeNode','NiNode','BSTriShape','NiParticleSystem'):continue
        r=Reader(b);name=r.read('I');extras=[r.read('i') for _ in range(r.read('I'))];r.read('i');r.read('I');p=r.read('3f');rot=r.read('9f');scale=r.read('f');r.read('i');m=np.eye(4);m[:3,:3]=np.asarray(rot).reshape(3,3)*scale;m[:3,3]=p
        children=[r.read('i') for _ in range(r.read('I'))] if kind in ('BSFadeNode','NiNode') else []
        nodes[i]={'matrix':m,'children':children,'parent':-1}
    for i,n in nodes.items():
        for c in n['children']:
            if c in nodes:nodes[c]['parent']=i
    def world(i):return nodes[i]['matrix'] if nodes[i]['parent']<0 else world(nodes[i]['parent'])@nodes[i]['matrix']
    r=Reader(raw[54][1]);r.read('I');[r.read('i') for _ in range(r.read('I'))];r.read('i');r.read('I');r.read('3f');r.read('9f');r.read('f');r.read('i');r.read('4f');r.read('3i');descriptor=r.read('Q');nt=r.read('H');nv=r.read('H');r.read('I');assert descriptor==0x900000040005
    positions=[]
    for _ in range(nv):positions.append(r.read('3f'));r.pos+=8
    triangles=np.array([r.read('3H') for _ in range(nt)]);W=world(54);p=(np.asarray(positions)@W[:3,:3].T+W[:3,3])@a.C.T*a.SCALE
    normals=np.cross(p[triangles[:,1]]-p[triangles[:,0]],p[triangles[:,2]]-p[triangles[:,0]]);areas=np.linalg.norm(normals,axis=1);normals/=np.maximum(areas[:,None],1e-12);cdf=np.cumsum(areas);cdf/=cdf[-1]
    rng=np.random.default_rng(284032);subs=[];allp=[];bounds=[];records=[];lifeMax=0
    for layer,(emitter,colour,shader,data_id) in enumerate([(62,64,58,56),(82,84,79,77)]):
        e=blocks[emitter];c=blocks[colour];sh=blocks[shader];assert e['velocity_type']==0 and e['emission_type']==3 and e['emitter_meshes']==[54]
        particle_data=raw[data_id][1];capacity=struct.unpack_from('<H',particle_data,4)[0];assert capacity in (30,6)
        # 从完整表验证实际图集，不能把8x8/4x4大图当一张烟纹理直接显示。
        frames=64 if layer==0 else 16;at=particle_data.index(struct.pack('<I',frames));rects=np.array([struct.unpack_from('<4f',particle_data,at+4+j*16) for j in range(frames)]);grid=int(math.sqrt(frames))
        assert np.allclose(rects[:,1],1/grid) and np.allclose(rects[:,3],1/grid) and np.allclose(rects[:,0],np.arange(frames)%grid/grid) and np.allclose(rects[:,2],np.arange(frames)//grid/grid)
        if layer==0:
            ts=np.linspace(0,1/3,2001);rate=np.array([float(sample(blocks[22],t,0)) for t in ts]);integral=np.r_[0,np.cumsum((rate[1:]+rate[:-1])*.5*np.diff(ts))];count=min(capacity,int(integral[-1]));births=np.interp(np.arange(count)+.5,integral,ts)
        else:count=capacity;births=np.arange(count)/600000.
        name='IrisArsenal/Eight/Quake'+str(layer);tex=texture(sh['source_texture']);rgb=c['colors'][1][:3];maxAlpha=c['colors'][1][3]
        # 固定两组各自材质，沿用原烟尘颜色/最大透明度；不是普通火焰add或无alpha的黑贴片。
        mats[name]={'particle':True,'texture':tex,'atlas':grid,'atlas_frames':frames,'atlas_fps':24 if layer==0 else 0,'rgb':rgb,'alpha':maxAlpha,'fade_in':c['fade_in_percent'],'fade_out':c['fade_out_percent']}
        verts=[];indices=[];audit=[]
        for j,birth in enumerate(births):
            tri=min(len(triangles)-1,int(np.searchsorted(cdf,rng.random())));u,v=rng.random(2)
            if u+v>1:u,v=1-u,1-v
            t=p[triangles[tri]];start=t[0]+(t[1]-t[0])*u+(t[2]-t[0])*v;velocity=normals[tri]*(e['speed']+rng.uniform(-e['speed_variation'],e['speed_variation']))*a.SCALE
            life=e['life_span']+rng.uniform(-e['life_span_variation'],e['life_span_variation']);size=(e['initial_radius']+rng.uniform(-e['radius_variation'],e['radius_variation']))*a.SCALE;angle=rng.uniform(0,math.tau)
            assert life>0 and size>0;lifeMax=max(lifeMax,float(birth+life));audit.append([float(birth),float(life),float(size),*start.tolist(),*velocity.tolist()]);allp.append(start)
            # Shader只有匀速移动/尺寸包络的明确适配；完整Skyrim风场/拖曳/重力未执行。保守边界包住整段。
            for center in [start,start+velocity*life]:bounds.extend([center-size*math.sqrt(2),center+size*math.sqrt(2)])
            base=len(verts);verts.extend([(*start,*velocity,float(birth),life,size,angle,x,y) for x,y in [(0,0),(1,0),(1,1),(0,1)]]);indices.extend([base,base+1,base+2,base,base+2,base+3])
        decl=a.chunk(0x5100,b''.join(a.chunk(0x5110,struct.pack('<5H',0,t,s,o,0)) for t,s,o in [(2,1,0),(2,4,12),(3,5,24),(1,7,40)]));vb=b''.join(struct.pack('<12f',*v) for v in verts)
        geom=a.chunk(0x5000,struct.pack('<I',len(verts))+decl+a.chunk(0x5200,struct.pack('<HH',0,48)+a.chunk(0x5210,vb)))
        subs.append(a.chunk(0x4000,name.encode()+b'\n'+struct.pack('<?I?',False,len(indices),False)+struct.pack('<%dH'%len(indices),*indices)+geom))
        records.append({'layer':layer,'emitter':emitter,'source_capacity':capacity,'actual_particles':count,'texture':tex,'grid':[grid,grid],'source_parameters':e,'source_colour':c,'particles':audit})
    positions=np.array(allp);bound=np.array(bounds);radius=float(np.linalg.norm(bound,axis=1).max());blob=b'\x00\x10[MeshSerializer_v1.41]\n'+a.chunk(0x3000,b'\0'+b''.join(subs)+a.chunk(0x9000,struct.pack('<7f',*bound.min(0),*bound.max(0),radius)))
    return blob,[r for r in mats if r.startswith('IrisArsenal/Eight/Quake')],positions,{'source':str(path),'source_sha256':decoded['sha256'],'life':lifeMax,'peak':radius,'bounds':[bound.min(0).tolist(),bound.max(0).tolist()],'layers':records,'adaptation':'仅本NIF两个有限发射器；源曲线积分/发射面法线、寿命/颜色/图集；匀速与尺寸包络、随机种子适配，未运行完整NiPSys/风场/粒子物理'}

SHADER=r"""
// 两组源尘土的相机朝向sprite；每顶点打包birth/life/size/rotation，时钟仍为实例游戏秒。
VOut iris_quake_vp(VIn i,uniform float4x4 worldMatrix,uniform float4x4 vp,uniform float4x4 inverseView,uniform float4 clock,uniform float4 atlas,uniform float4 dustColour,uniform float4 dustFade){
 VOut o;float elapsed=clock.x-i.c.x,life=i.c.y;float t=saturate(elapsed/life);float active=step(0,elapsed)*(1-step(life,elapsed));
 float fade=saturate(t/max(.001,dustFade.x))*saturate((1-t)/max(.001,dustFade.y));
 float3 center=mul(worldMatrix,float4(i.p.xyz+i.n*max(0,elapsed),1)).xyz;float size=i.c.z*(.4+.6*saturate(t*4))*length(float3(worldMatrix[0][0],worldMatrix[1][0],worldMatrix[2][0]));
 float2 corner=(i.uv*2-1)*size;float cs=cos(i.c.w+t*.3),sn=sin(i.c.w+t*.3);corner=float2(cs*corner.x-sn*corner.y,sn*corner.x+cs*corner.y);
 float3 right=float3(inverseView[0][0],inverseView[1][0],inverseView[2][0]),up=float3(inverseView[0][1],inverseView[1][1],inverseView[2][1]);
 o.p=mul(vp,float4(center+right*corner.x+up*corner.y,1));o.c=float4(dustColour.rgb,dustColour.a*fade*active*clock.y);
 float frame=atlas.z>0?min(atlas.w-1,floor(max(0,elapsed)*atlas.z)):floor(frac(i.c.w*.371)*atlas.w);o.uv=(i.uv+float2(fmod(frame,atlas.x),floor(frame/atlas.x)))/atlas.xy;o.n=0;o.view=0;return o;
}
float4 iris_quake_fp(VOut i):SV_Target {float4 texel=t0.Sample(s0,i.uv);float alpha=texel.a*i.c.a;clip(alpha-.001);return float4(texel.rgb*i.c.rgb,alpha);}
"""
