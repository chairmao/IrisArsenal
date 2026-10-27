"""复用Ephnel验证过的SSE刚体几何读取，不携带旧项目路径/主程序。"""
import numpy as np
import nif_reader as nif
def read_nif(path,excluded_shapes=()):
    # 严格消费 SSE100 块；几何描述符限定已实查的20/28/32字节顶点，保留32字节效果网格的RGBA，拒绝猜测蒙皮布局。
    raw=path.read_bytes();r=nif.Reader(raw[raw.index(b'\n')+1:])
    assert [r.read(f) for f in ('I','B','I')]==[0x14020007,1,12]
    count=r.read('I');assert r.read('I')==100
    for _ in range(3):r.string('B')
    types=[r.string() for _ in range(r.read('H'))];ix=[r.read('H') for _ in range(count)]
    sizes=[r.read('I') for _ in range(count)];ns=r.read('I');r.read('I');strings=[r.string() for _ in range(ns)]
    for _ in range(r.read('I')):r.read('I')
    nodes={};meshes=[];texture_sets={};shaders={};alpha_properties={};collision_types=[];excluded_shaders=set()
    for i,(ti,size) in enumerate(zip(ix,sizes)):
        q=nif.Reader(r.data[r.pos:r.pos+size]);r.pos+=size;t=types[ti]
        if t in ('BSFadeNode','NiNode','NiBillboardNode','BSTriShape'):
            ni=q.read('I');name='' if ni==0xffffffff else strings[ni]
            nx=q.read('I');extra=[q.read('i') for _ in range(nx)];controller=q.read('i');q.read('I')
            pos=q.read('3f');rot=q.read('9f');scale=q.read('f');collision=q.read('i')
            matrix=np.eye(4);matrix[:3,:3]=np.array(rot).reshape(3,3)*scale;matrix[:3,3]=pos
            nodes[i]={'name':name,'matrix':matrix,'parent':-1,'controller':controller,'collision':collision}
            if t!='BSTriShape':
                children=[q.read('i') for _ in range(q.read('I'))]
                nodes[i]['children']=children
                for _ in range(q.read('I')):q.read('i')
                if t=='NiBillboardNode':q.read('H')
                q.done();continue
            q.read('4f');skin=q.read('i');shader=q.read('i');alpha_property=q.read('i')
            # 063只按调用者明确指定的名字排除源附带身体；anim1的3BA不是武器特效，绝不移植。
            # 默认空表保持既有解析；同时跳过该身体独占shader，不能为读准星放宽未知蒙皮/材质布局。
            if name in excluded_shapes:excluded_shaders.add(shader);continue
            assert skin==-1,'刚体移植不接受蒙皮网格'
            descriptor=q.read('Q');assert descriptor in (0x1b00000650407,0x3b00007650408,0x900000040005)
            stride=(descriptor&15)*4
            nt=q.read('H');nv=q.read('H');assert q.read('I')==nv*stride+nt*6
            vertices=[];normals=[];uv=[];colours=[]
            for _ in range(nv):
                begin=q.pos;vertices.append(q.read('3f'));q.read('f');uv.append(q.read('2e'))
                normals.append([v/127.5-1 for v in q.read('4B')[:3]] if stride>=28 else [0,0,1])
                # SSE32顶点末四字节是RGBA；源闪光边缘依赖顶点alpha，丢弃会变成生硬实心面。
                if stride==32:
                    q.pos=begin+28;colours.append([v/255 for v in q.read("4B")])
                q.pos=begin+stride
            tris=[q.read('3H') for _ in range(nt)];assert all(max(t)<nv for t in tris)
            # SSE Particle Data Size以半字为单位；发射器网格另有half顶点/法线/三角，不能当非法尾数据。
            particle_size=q.read('I')
            assert particle_size in (0,nv*6+nt*3)
            q.pos+=particle_size*2;q.done()
            meshes.append({'index':i,'name':name,'vertices':vertices,'normals':normals,'uv':uv,'colours':colours,'triangles':tris,'shader':shader,'alpha_property':alpha_property})
        elif t=='BSShaderTextureSet':
            texture_sets[i]=[q.string() for _ in range(q.read('I'))];q.done()
        elif t=='BSLightingShaderProperty':
            if i in excluded_shaders:continue
            # SSE100：shaderType 后是 NiObjectNET，再是 flags/UV/textureSet。保留原纹理而不读取猜测的尾字段。
            shader_type=q.read('I');q.read('I');nx=q.read('I')
            for _ in range(nx):q.read('i')
            q.read('i');flags=q.read('2I');uv_offset=q.read('2f');uv_scale=q.read('2f');texture=q.read('i');emissive=q.read('3f');emissive_mult=q.read('f');texture_clamp=q.read('I');alpha=q.read('f')
            # SSE100普通/Glow材质的剩余公共字段：折射、光泽、镜面色/强度和两项lighting effect。
            # 钻头原来只有基础灰色，被简化unlit路径压成剪影；必须保留这些字段才能重建光照层次。
            refraction=q.read('f');glossiness=q.read('f');specular=q.read('3f');specular_strength=q.read('f');lighting=q.read('2f')
            assert shader_type in (0,2),'Iris当前普通/Glow材质之外的尾字段尚未确认';q.done()
            shaders[i]={'texture':texture,'emissive':emissive,'emissive_mult':emissive_mult,'alpha':alpha,'uv_offset':uv_offset,'uv_scale':uv_scale,'shader_type':shader_type,'clamp_mode':texture_clamp,'flags':flags,'refraction':refraction,'glossiness':glossiness,'specular':specular,'specular_strength':specular_strength,'lighting_effect':lighting}
        elif t=='NiAlphaProperty':
            # 原四张光学面用src_alpha/inv_src_alpha及阈值8；不能无条件换成add，否则透明白RGB会变成白矩形。
            name=q.read('I');extra=[q.read('i') for _ in range(q.read('I'))];controller=q.read('i');flags=q.read('H');threshold=q.read('B');q.done()
            alpha_properties[i]={'flags':flags,'threshold':threshold,'blend_enabled':bool(flags&1),'source_blend':(flags>>1)&15,'destination_blend':(flags>>5)&15,'test_enabled':bool(flags&512),'test_function':(flags>>10)&7}
        elif t=='BSEffectShaderProperty':
            # 光学效果参数由已有严格SSE解析器读取，几何解析与着色器引用用块编号衔接。
            effect=next(x for x in nif.parse(path)['parsed_blocks'] if x['index']==i)
            texture_sets[i]=[effect['source_texture'],'',effect['palette_texture']]
            shaders[i]={'texture':i,'effect':effect,'emissive':[0,0,0],'emissive_mult':0,'alpha':effect['base_color'][3],'uv_offset':effect['uv_offset'],'uv_scale':effect['uv_scale']}
        elif t.startswith('bhk'):collision_types.append(t)
    for i,node in nodes.items():
        for child in node.get('children',[]):
            if child in nodes:nodes[child]['parent']=i
    def world(i,seen=()):
        assert i not in seen,'循环节点'
        nd=nodes[i];return nd['matrix'] if nd['parent']<0 else world(nd['parent'],seen+(i,))@nd['matrix']
    meshes=[mesh for mesh in meshes if mesh['shader'] in shaders]
    for mesh in meshes:
        mesh['matrix']=world(mesh['index']);mesh['shader_data']=shaders[mesh['shader']];mesh['textures']=texture_sets[mesh['shader_data']['texture']];mesh['alpha_data']=alpha_properties.get(mesh['alpha_property'])
    return meshes,collision_types
