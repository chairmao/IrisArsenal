"""只提取EXanim1的武器/准星刚性顶点；不读取或移植源身体网格。"""
import sys,copy,json
from pathlib import Path
import numpy as np
from safeio import ROOT
from fx_timeline import raw_blocks
from nif_reader import Reader
from iris_wings import transform

def read_parts(path):
    raw,strings=raw_blocks(path);nodes={};shapes=[];textures={};shaders={}
    for i,(kind,data) in raw.items():
        r=Reader(data)
        if kind in ('NiNode','BSFadeNode','BSTriShape'):
            ni=r.read('I');name=strings[ni] if ni!=0xffffffff else '';[r.read('i') for _ in range(r.read('I'))];r.read('i');r.read('I');r.read('3f');r.read('9f');r.read('f');r.read('i');nodes[i]=name
            if kind!='BSTriShape':continue
            if not(name.startswith('Desirefx.me_Body144.') or name in ('TwinChakrams:62','Ch0145_Halo')):continue
            r.read('4f');skin,shader,alpha=r.read('3i');desc=r.read('Q');nt,nv=r.read('2H');size=r.read('I');assert desc==0x5b0007065040a and nt==nv==size==0 and alpha==-1;assert r.read('I')==0;r.done();shapes.append((i,name,skin,shader))
        elif kind=='BSShaderTextureSet':textures[i]=[r.string() for _ in range(r.read('I'))];r.done()
        elif kind=='BSLightingShaderProperty':
            if not any(s[3]==i for s in shapes):continue
            typ=r.read('I');r.read('I');[r.read('i') for _ in range(r.read('I'))];r.read('i');flags=r.read('2I');off=r.read('2f');scale=r.read('2f');tex=r.read('i');emission=r.read('3f');mult=r.read('f');clamp=r.read('I');alpha=r.read('f');refraction=r.read('f');gloss=r.read('f');specular=r.read('3f');strength=r.read('f');light=r.read('2f');r.done()
            shaders[i]={'texture':tex,'emissive':emission,'emissive_mult':mult,'alpha':alpha,'uv_offset':off,'uv_scale':scale,'shader_type':typ,'clamp_mode':clamp,'flags':flags,'refraction':refraction,'glossiness':gloss,'specular':specular,'specular_strength':strength,'lighting_effect':light}
    out=[]
    for index,name,skin,shader in shapes:
        r=Reader(raw[skin][1]);data_id,part_id,root=r.read('3i');n=r.read('I');bones=r.read(str(n)+'i');bones=bones if isinstance(bones,list) else [bones]
        if raw[skin][0]=='BSDismemberSkinInstance':parts=r.read('I');assert parts==1;r.read('2H')
        r.done();assert all(nodes[b] in ('NPC Root [Root]','AnimObjectA','AnimObjectB') for b in bones)
        r=Reader(raw[data_id][1]);base=transform(r);assert np.allclose(base,np.eye(4),atol=1e-5);assert r.read('I')==n and r.read('B')==1;bind=[];membership={}
        for j in range(n):
            bind.append(transform(r));r.read('4f');count=r.read('H')
            for _ in range(count):
                vi,weight=r.read('Hf');assert abs(weight-1)<1e-6 and vi not in membership;membership[vi]=j
        r.done();count=len(membership);assert sorted(membership)==list(range(count))
        r=Reader(raw[part_id][1]);assert r.read('I')==1;size,stride=r.read('2I');desc=r.read('Q');assert stride==40 and desc==0x5b0007065040a and size==count*stride;buffer=r.data[r.pos:r.pos+size];r.pos+=size
        nv,nt,nb,ns,nw=r.read('5H');assert nv==count and nb==n and ns==0 and nw==4;palette=r.read(str(nb)+'H');palette=palette if isinstance(palette,list) else [palette];assert palette==list(range(n))
        assert r.read('B')==1;vm=r.read(str(nv)+'H');assert vm==list(range(nv));assert r.read('B')==1;pw=np.array(r.read(str(nv*nw)+'f')).reshape(nv,nw);assert np.allclose(pw[:,0],1) and np.allclose(pw[:,1:],0)
        assert r.read('B')==1;tris=np.array(r.read(str(nt*3)+'H')).reshape(nt,3);assert r.read('B')==1;bi=np.array(r.read(str(nv*nw)+'B')).reshape(nv,nw);r.read('B');r.read('B');assert r.read('Q')==desc;copies=np.array(r.read(str(nt*3)+'H')).reshape(nt,3);r.done();assert np.array_equal(tris,copies)
        verts=[];normals=[];uv=[]
        for vi in range(nv):
            q=Reader(buffer[vi*stride:(vi+1)*stride]);verts.append(q.read('3f'));q.read('f');uv.append(q.read('2e'));normals.append([(v/127.5-1) for v in q.read('4B')[:3]]);q.read('4B');w=q.read('4e');indices=q.read('4B');q.done();assert abs(w[0]-1)<1e-6 and max(w[1:])==0 and indices[0]==membership[vi] and bi[vi,0]==membership[vi]
        verts=np.array(verts);normals=np.array(normals);uv=np.array(uv)
        for j in range(n):
            chosen=np.array([v for v in range(nv) if membership[v]==j]);ids={v:k for k,v in enumerate(chosen)};tt=[]
            for tri in tris:
                groups={membership[int(v)] for v in tri};assert len(groups)==1
                if groups=={j}:tt.append([ids[int(v)] for v in tri])
            sh=copy.deepcopy(shaders[shader]);p=verts[chosen]@bind[j][:3,:3].T+bind[j][:3,3];normal=normals[chosen]@np.linalg.inv(bind[j][:3,:3]);out.append({'index':index,'name':name+'_'+nodes[bones[j]],'bone':nodes[bones[j]],'vertices':p.tolist(),'normals':normal.tolist(),'uv':uv[chosen].tolist(),'colours':[],'triangles':tt,'matrix':np.eye(4),'shader':shader,'shader_data':sh,'textures':textures[sh['texture']],'alpha_data':None})
    assert len(out)==11
    return out

