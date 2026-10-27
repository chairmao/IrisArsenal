"""Iris两份LE83能量网格的严格只读解码；不执行BSProceduralLightningController。"""
from pathlib import Path
import numpy as np
from nif_reader import Reader
def read_legacy(path):
    raw=Path(path).read_bytes();r=Reader(raw[raw.index(b'\n')+1:])
    assert [r.read(t) for t in ('I','B','I')]==[0x14020007,1,12];count=r.read('I');assert r.read('I')==83
    for _ in range(3):r.string('B')
    types=[r.string() for _ in range(r.read('H'))];ix=[r.read('H') for _ in range(count)];sizes=[r.read('I') for _ in range(count)];ns=r.read('I');r.read('I');strings=[r.string() for _ in range(ns)]
    for _ in range(r.read('I')):r.read('I')
    nodes={};geometries={};shaders={};alphas={};shapes=[]
    for i,(ti,size) in enumerate(zip(ix,sizes)):
        q=Reader(r.data[r.pos:r.pos+size]);r.pos+=size;t=types[ti]
        if t in ('BSFadeNode','NiNode','NiBillboardNode','NiTriShape'):
            ni=q.read('I');name=strings[ni] if ni!=0xffffffff else '';extras=[q.read('i') for _ in range(q.read('I'))];controller=q.read('i');flags=q.read('I');pos=q.read('3f');rot=q.read('9f');scale=q.read('f');collision=q.read('i')
            matrix=np.eye(4);matrix[:3,:3]=np.asarray(rot).reshape(3,3)*scale;matrix[:3,3]=pos
            node={'matrix':matrix,'parent':-1,'children':[],'name':name};nodes[i]=node
            if t=='NiTriShape':
                data=q.read('i');skin=q.read('i');assert skin==-1,'LE蒙皮不在本读取器范围'
                materials=q.read('I');assert materials==0
                active=q.read('i');dirty=q.read('B');shader=q.read('i');alpha=q.read('i');shapes.append({'index':i,'data':data,'shader':shader,'alpha_property':alpha,'name':name})
            else:
                node['children']=[q.read('i') for _ in range(q.read('I'))];effects=[q.read('i') for _ in range(q.read('I'))]
                if t=='NiBillboardNode':q.read('H')
            q.done()
        elif t=='NiTriShapeData':
            group=q.read('I');nv=q.read('H');keep=q.read('B');compress=q.read('B');has_vertices=q.read('B')
            if nv==0:
                assert size==48 and not has_vertices;geometries[i]=None;continue
            assert has_vertices
            vertices=[q.read('3f') for _ in range(nv)];flags=q.read('H');crc=q.read('I');has_norm=q.read('B')
            normals=[q.read('3f') for _ in range(nv)] if has_norm else [(0,0,1)]*nv
            if has_norm and flags&0x1000:
                for _ in range(nv*2):q.read('3f')
            q.read('4f');has_colour=q.read('B');colours=[q.read('4f') for _ in range(nv)] if has_colour else []
            assert flags&63==1,'仅支持本源单UV'
            uv=[q.read('2f') for _ in range(nv)];consistency=q.read('H');additional=q.read('i');nt=q.read('H');points=q.read('I');has_tri=q.read('B')
            assert has_tri and points==nt*3
            triangles=[q.read('3H') for _ in range(nt)];assert all(max(x)<nv for x in triangles)
            groups=q.read('H');assert groups==0;q.done();geometries[i]={'vertices':vertices,'normals':normals,'colours':colours,'uv':uv,'triangles':triangles}
        elif t=='BSEffectShaderProperty':
            q.read('I');extra=[q.read('i') for _ in range(q.read('I'))];controller=q.read('i');flags=q.read('2I');off=q.read('2f');scale=q.read('2f');tex=q.string();clamp=q.read('4B');fall=q.read('4f');colour=q.read('4f');mult=q.read('f');soft=q.read('f');palette=q.string();q.done()
            # 和SSE路径一样保留源shader flags；忽略标志会误乘顶点色并错误启用调色图。
            effect={'shader_flags':flags,'controller':controller,'source_texture':tex,'palette_texture':palette,'base_color':colour,'base_color_scale':mult,'uv_offset':off,'uv_scale':scale,'falloff':fall,'clamp_and_lighting':clamp}
            shaders[i]={'effect':effect,'emissive':[0,0,0],'emissive_mult':0,'alpha':colour[3],'uv_offset':off,'uv_scale':scale}
        elif t=='NiAlphaProperty':
            q.read('I');extra=[q.read('i') for _ in range(q.read('I'))];q.read('i');flags=q.read('H');threshold=q.read('B');q.done();alphas[i]={'flags':flags,'threshold':threshold}
    for node in nodes.values():
        for j in node['children']:
            if j in nodes:nodes[j]['parent']=next(i for i,x in nodes.items() if x is node)
    def world(i,seen=()):
        assert i not in seen;n=nodes[i];return n['matrix'] if n['parent']<0 else world(n['parent'],seen+(i,))@n['matrix']
    output=[]
    for s in shapes:
        assert s['data'] in geometries and s['shader'] in shaders
        if geometries[s['data']] is None:continue
        x={**s,**geometries[s['data']]};x['matrix']=world(s['index']);x['shader_data']=shaders[s['shader']];fx=x['shader_data']['effect'];x['textures']=[fx['source_texture'],'',fx['palette_texture']];x['alpha_data']=alphas.get(s['alpha_property']);output.append(x)
    return output,[]

