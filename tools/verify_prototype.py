"""非编译验收：实际序列化资产、独立源握点、原生隔离与只读边界；不代替实机。"""
from pathlib import Path
import ast,json,math,re,struct,sys,hashlib,xml.etree.ElementTree as ET
import numpy as np
from safeio import ROOT,put
# 070：握点证明表只用于开发验证，生成/读取统一移出运行assets。
from asset_paths070 import PROOFS
import port_math as m
import kenshi_mod_writer as fcs
P=ROOT/'package/IrisArsenal';A=P/'assets'

def verify_sdk_contract(source):
    # 针对本次真实构建失败检查声明和导出名称；仅只读核对，不编译/链接，不推断整个C++工程已通过。
    sdk=Path('E:/KenshiProject/1.Dependencies/KenshiLib_0.5.0')
    scene=(sdk/'Include/ogre/OgreSceneManager.h').read_text('utf-8-sig')
    sub=(sdk/'Include/ogre/OgreSubEntity.h').read_text('utf-8-sig')
    movement=(sdk/'Include/kenshi/CharMovement.h').read_text('utf-8-sig')
    assert '#include <kenshi/CharMovement.h>' in source and re.search(r'class\s+physHit\s*\{',movement)
    assert re.search(r'createEntity\(\s*const String& meshName,\s*const String& groupName',scene)
    assert 'scene->createEntity("iris_drill.mesh",GROUP)' in source and 'name.str(),"iris_drill.mesh"' not in source
    assert 'getSubEntity(i)->setVisible' not in source
    # 066更正：符号存在不能证明传0可隐藏；本机setter在rdx==0时直接返回，064验证遗漏真实语义。
    # 新路径消费SDK内联的实例custom参数，绘制门由配套顶点Shader裁剪，不再依赖索引范围。
    renderable=(sdk/'Include/ogre/OgreRenderable.h').read_text('utf-8-sig')
    evidence=[]
    for name in ['setCustomParameter','getCustomParameter']:
        assert name in renderable and ('->'+name+'(') in source
        evidence.append(name)
    assert 'setIndexDataEndIndex(0)' not in re.sub(r'//[^\n]*','',source)
    assert 'setCustomParameter(9,Ogre::Vector4(optics?1.f:0.f,0,0,0))' in source
    return {'physHit_complete_header':True,'entity_arguments':['meshName','groupName'],'optical_layers':'0,15..18 instance custom9 projected clip gate','declared_inline_API':evidence,'compiled_or_linked':False}

def chunks(b,start,end):
    i=start
    while i<end:
        t,n=struct.unpack_from('<HI',b,i);assert n>=6 and i+n<=end
        yield t,i+6,i+n;i+=n
    assert i==end

def skeleton(path,expected='IrisArsenal_DrillProof'):
    b=path.read_bytes();bones=m.skeleton(path);i=b.index(b'\n')+1;anim=None;tracks={}
    while i+6<=len(b):
        t,n=struct.unpack_from('<HI',b,i)
        if t==0x2000:e=b.index(b'\n',i+6);i+=n+e-(i+6)+1;continue
        if t==0x4000:
            end=i+n;e=b.index(b'\n',i+6);anim=b[i+6:e].decode();length=struct.unpack_from('<f',b,e+1)[0]
            for t,s,ee in chunks(b,e+5,end):
                assert t==0x4100;bone=struct.unpack_from('<H',b,s)[0];keys=[]
                for kt,ks,ke in chunks(b,s+2,ee):
                    assert kt==0x4110 and ke-ks==32;v=struct.unpack_from('<8f',b,ks);keys.append(v)
                tracks[bone]=keys
            i=end
        else:i+=n
    assert anim==expected and len(tracks)==24
    return bones,length,tracks

def mesh(path,stride_expected=32,animated_bounds=False):
    b=path.read_bytes();assert b.startswith(b'\x00\x10[MeshSerializer_v1.41]\n');vertices=[];mats=[]
    for t,s,e in chunks(b,b.index(b'\n')+1,len(b)):
        assert t==0x3000
        for t,ss,ee in chunks(b,s+1,e):
            if t==0x4000:
                nl=b.index(b'\n',ss);mats.append(b[ss:nl].decode());shared,count,wide=struct.unpack_from('<?I?',b,nl+1);assert not shared
                off=nl+7;indices=np.array(struct.unpack_from('<'+('I' if wide else 'H')*count,b,off));off+=count*(4 if wide else 2)
                for gt,gs,ge in chunks(b,off,ee):
                    assert gt==0x5000;nv=struct.unpack_from('<I',b,gs)[0];assert indices.max()<nv
                    for vt,vs,ve in chunks(b,gs+4,ge):
                        if vt!=0x5200:continue
                        bind,stride=struct.unpack_from('<HH',b,vs);assert bind==0 and stride==stride_expected
                        for dt,ds,de in chunks(b,vs+4,ve):
                            assert dt==0x5210 and de-ds==nv*stride_expected;p=np.frombuffer(b[ds:de],'<f4').reshape(nv,stride_expected//4);assert np.isfinite(p).all();vertices.append(p[:,:3])
            elif t==0x9000:bounds=struct.unpack_from('<7f',b,ss)
    v=np.concatenate(vertices)
    # 只有031明确带Shader位移曲线的网格允许保守外扩；另一个专项检查会逐帧核对真正动态包络。
    if animated_bounds:assert np.all(v.min(0)>=np.array(bounds[:3])-1e-4) and np.all(v.max(0)<=np.array(bounds[3:6])+1e-4)
    else:assert np.allclose(v.min(0),bounds[:3],atol=1e-4) and np.allclose(v.max(0),bounds[3:6],atol=1e-4)
    return vertices,mats

def records(p):
    b=p.read_bytes();i=fcs.find_records_start(b);out=[]
    while i<len(b):r=fcs.read_record(b,i,len(b));out.append(r);i=r['end']
    assert i==len(b);return out

def fields(r):
    out={}
    for section in r['sections']:
        for name,kind,v in section:
            out[name]=fcs.Reader(v).string(0)[0] if kind in ['filename','string'] else struct.unpack('<'+{'bool':'?','long':'i','f32':'f'}[kind],v)[0]
    return out

def main():
    # 新八招包必须验新合同；保留原型读取辅助用于独立诊断，不以旧无伤害断言误拒完整包。
    if (ROOT/'docs/eight-moves.json').exists():
        import verify_moves
        return verify_moves.main()
    checks={};normal,nm=mesh(A/'iris_weapon.mesh');drill,dm=mesh(A/'iris_drill.mesh');assert len(normal)==2 and len(drill)==19;checks['geometry']={'normal_submeshes':2,'drill_submeshes':19,'drill_vertices':sum(len(p) for p in drill)}
    provenance=json.loads((ROOT/'docs/asset-provenance.json').read_text('utf-8'));slices=np.array(provenance['capsules']);solid=np.concatenate(drill[:15])
    covered=np.zeros(len(solid),bool)
    for a,b,r in slices:
        z=np.clip(solid[:,2],a,b);distance=np.linalg.norm(solid-np.stack([np.zeros(len(z)),np.zeros(len(z)),z],1),axis=1);covered|=distance<=r+1e-4
    assert covered.all();checks['capsule_fit']={'solid_vertices_covered':int(covered.sum()),'optical_planes_excluded':4,'precision':'conservative capsule proxy; not triangle collision'}
    body=[]
    for sex in ['male','female']:
        bones,length,tracks=skeleton(A/('iris_drill_'+sex+'.skeleton'));names={b['name']:b['id'] for b in bones};proof=np.loadtxt(PROOFS/('iris_weapon_proof_'+sex+'.csv'),skiprows=1);assert proof.shape==(339,10)
        errors=[];angles=[];left=[];root_horizontal=[];qnorm=[]
        for k in range(339):
            wp=[]
            for b in bones:
                v=tracks[b['id']][k] if b['id'] in tracks else (0,0,0,0,1,0,0,0)
                delta=(v[4],v[1],v[2],v[3]);q=m.qmul(b['orientation'],delta);pos=m.vadd(b['position'],v[5:]);parent=b['parent']
                qnorm.append(abs(np.linalg.norm(q)-1))
                if parent>=0:pp,pq=wp[parent];pos=m.vadd(pp,m.rotate(pq,pos));q=m.qmul(pq,q)
                wp.append((pos,q))
            grip,q=wp[names['Bip01 Prop2']];actual=m.qmul(q,m.axis((1,0,0),-90));expected=proof[k,3:7]
            errors.append(np.linalg.norm(np.array(grip)-proof[k,:3]));angles.append(2*math.acos(min(1,abs(float(np.array(actual)@expected)))))
            left.append(np.linalg.norm(np.array(wp[names['Bip01 L Hand']][0])-proof[k,7:10]))
            root=tracks[names['Bip01']][k];root_horizontal.append(abs(root[5])+abs(root[7]))
        # Ogre序列化为float32；角度点积误差用弧度容限，不能按double精度要求float资源。
        assert max(errors)<1e-4 and max(angles)<.002 and max(qnorm)<1e-5 and max(root_horizontal)==0
        spin=[v for k,v in enumerate(left) if 1.633333333<=k*length/338<=3.75]
        body.append({'skeleton':sex,'frames':339,'right_weapon_origin_error_max':float(max(errors)),'weapon_orientation_error_degrees_max':math.degrees(max(angles)),'left_hand_error_max':float(max(left)),'left_hand_spin_error_max':float(max(spin)),'root_horizontal_translation':0})
    checks['serialized_body_and_weapon']=body
    assert fcs.roundtrip(str(P/'IrisArsenal.mod'))['identical'];r=records(P/'IrisArsenal.mod');tech=fields(next(x for x in r if x['key']=='3-IrisArsenal.mod'));weapon=fields(next(x for x in r if x['key']=='1-IrisArsenal.mod'))
    assert tech['disabled'] and tech['chance']==0 and tech['max simultaneous hits']==0 and tech['power 1']==0 and not tech['gains ground']
    assert all(weapon[k]==0 for k in ['cut damage multiplier','blunt damage multiplier','pierce damage multiplier','min cut damage mult'])
    checks['FCS']={'roundtrip':True,'shared_pool_disabled':True,'native_target_hits':0,'weapon_damage':0,'distance':[tech['attack distance min vs static'],tech['attack distance']]}
    material=(A/'iris.material').read_text('utf-8');assert all(name in material for name in nm+dm)
    all_materials=material+'\n'+(A/'iris_drill_optics.material').read_text('utf-8')
    for name in re.findall(r'\btexture\s+(\S+\.(?:dds|png))',all_materials):assert (A/name).is_file(),name
    for entry in ['iris_fp','iris_debug_fp']:assert entry in (A/'iris.hlsl').read_text('utf-8') and entry in (A/'iris.program').read_text('utf-8')
    checks['material_references']=True
    ns={'m':'http://schemas.microsoft.com/developer/msbuild/2003'};project=ET.parse(ROOT/'IrisArsenal.vcxproj');cpps=[x.attrib['Include'] for x in project.findall('.//m:ClCompile[@Include]',ns)]
    assert cpps==['IrisArsenal.cpp'] and (ROOT/cpps[0]).is_file();assert project.find('.//m:PlatformToolset',ns).text=='v100'
    source=(ROOT/'IrisArsenal.cpp').read_text('utf-8');assert source.count('KenshiLib::AddHook(')==7
    checks['local_sdk_compile_regression']=verify_sdk_contract(source)
    # 实际序列化mesh、文本生产器、运行消费者三方一致；不把材质名存在当成渲染已通过。
    rows=(A/'drill.csv').read_text('utf-8').splitlines();assert rows[0]=='IRIS_DRILL 2 8 19' and len(rows)==29
    assert np.allclose(np.loadtxt(rows[2:10]),slices,atol=1e-8)
    optics=json.loads((ROOT/'docs/drill-optics.json').read_text('utf-8'));assert optics['contract']=='IRIS_DRILL_OPTICS_V1'
    expected=[str(i)+' '+b['runtime_material'] for i,b in enumerate(optics['bindings'])];assert rows[10:]==expected
    assert len(optics['bindings'])==19 and all(b['sub']==i for i,b in enumerate(optics['bindings']))
    for b in optics['bindings']:assert b['runtime_material'] in all_materials
    assert 'version!=2' in source and 'f>>index>>drillMaterials[i]' in source
    assert 'sub->setMaterialName(drillMaterials[i],GROUP)' in source and 'sub->getMaterialName()!=drillMaterials[i]' in source
    # 上一轮已经出现过默认材质问题，进一步核对源NIF真正得到的材质名，防止手写名单错位。
    import author_prototype as author
    source_drill,_=author.read_nif(author.SOURCE/'Meshes/SW/Iris/EXDrill1.nif')
    assert [author.material(x) for x in source_drill]==dm
    # 运行时名称是有意的材质覆盖；源mesh默认名称保持，用独立逐层合同验证颜色/透明/光泽的来源。
    for i,x in enumerate(source_drill):
        b=optics['bindings'][i];assert b['source_shader']==x['shader_data'] and b['source_alpha']==x['alpha_data']
    import prepare_drill_optics as prepared
    assert (A/'iris_drill_optics.hlsl').read_text('utf-8')==prepared.SHADER
    assert (A/'iris_drill_optics.program').read_text('utf-8')==prepared.PROGRAM
    from PIL import Image
    original=Image.open(author.SOURCE/'Textures/Soulworker/Iris/anim.dds').convert('RGBA');converted=Image.open(A/optics['png']).convert('RGBA')
    assert original.size==converted.size and np.array_equal(np.asarray(original),np.asarray(converted))
    shader=(A/'iris_drill_optics.hlsl').read_text('utf-8');program=(A/'iris_drill_optics.program').read_text('utf-8')
    for entry in re.findall(r'entry_point\s+(\w+)',program):assert re.search(r'\b'+entry+r'\s*\(',shader),entry
    assert 'return float4(diffuse+specular+reflection+base*emission,1)' in shader and 'clip(alpha>alphaReference?1:-1)' in shader
    assert [source_drill[i]['shader_data']['specular_strength'] for i in [1,3,4,14]]==[1,1,10,10]
    assert all(x['alpha_data']['flags']==4845 for x in source_drill[15:])
    assert len(optics['materials'])==6 and 'scene_blend alpha_blend' in all_materials
    # 量化旧白边风险：源零alpha像素仍有亮RGB，旧add直接输出它们；新源alpha混合下贡献必须为零。
    zero_alpha_bright=0
    for name in ['iris_5114b0f90ad5da99.dds','iris_2556c812dc7d68e6.dds','iris_29343c8126431246.dds']:
        pixels=np.asarray(Image.open(A/name).convert('RGBA'));mask=(pixels[:,:,3]==0)&(pixels[:,:,:3].max(2)>127);zero_alpha_bright+=int(mask.sum())
    checks['drill_optics']={'asset_contract':optics['contract'],'opaque_source_parts':15,'transparent_source_parts':4,'runtime_materials':6,'source_BC7_to_PNG_identical':True,'original_format':'BC7 DX10 format98','source_alpha_flags':4845,'source_specular_restored':[1,10],'source_glossiness':20,'zero_alpha_bright_pixels_in_source':zero_alpha_bright,'compiled_HLSL':False,'runtime_visual_verified':False}

    assert "IRIS_DRILL 2 8 19" in (ROOT/'tools/author_prototype.py').read_text('utf-8')
    query=source[source.index('void Query('):source.index('void Probe(')]
    assert 'throw ' not in query and 'RejectQuery(a,"fraction_outside_segment"' in query
    isolation=source[source.index('        if(!paused){\n            try{Probe('):source.index('unsigned stage=t<profile.appear')]
    # 新经验：次数只限日志，失败不能变成角色/世界级诊断停用或冷却；本原型没有正式多接触伤害。
    assert 'querySuppressed' not in source and 'faulted=true' not in isolation and 'Clear(' not in isolation and 'End(' not in isolation
    assert 'failure_scope=current_probe retry=next_safe_update evaluated=0' in isolation and 'probeErrorLogs<16' in isolation
    probe=source[source.index('void Probe('):source.index('void Ensure(')]
    assert 'probeErrors' not in probe and 'probeErrorLogs' not in probe
    assert 'raw_t_bits=0x' in source and 'raw_fraction=' in source and 'queryRejectLogs<16' in source
    assert 'const bool pointValid=hit.distance>0&&Finite(hit.position);' in source and 'if(pointValid)s<<' in source
    assert 'diagnostic_only=1 exhaustive=0' in source and 'query_auto_disable=0 query_cooldown=0' in source
    assert 'DebugDraw=0' in (P/'IrisArsenal.ini').read_text('utf-8') and 'L"DebugDraw",0,' in source
    contract='IRIS_012_DIAGNOSTIC_PATH_RETRY';assert contract in source and contract in (ROOT/'tools/stage_package.py').read_text('utf-8')
    assert 'FILEVERSION 0,1,2,0' in (ROOT/'IrisArsenal.rc').read_text('utf-8')
    checks['drill_runtime_contract']={'version':'0.1.2','profile':2,'source_mesh_material_bindings':len(dm),'bad_sweep_policy':'reject this diagnostic query; no health call; action continues','query_cpp_exception_policy':'discard current probe only; next safe update retries; no actor disable/cooldown','collision_role':'closest first-nonself diagnostic only; not formal damage','initial_overlap_point_policy':'t=0 never reads point','debug_draw_default':0,'runtime_render_verified':False,'repeat_cycles_verified':False}

    for bad in ['?_NV_','movedBy','addWound','_NV_hitByMeleeAttack','_getHit(','setPosition(c->','NxCreatePhysicsSDK','setUserContactReport']:assert bad not in source,bad
    for include in re.findall(r'#include <([^>]+)>',source):
        if include.startswith(('kenshi/','ogre/','core/')):assert (Path('E:/KenshiProject/1.Dependencies/KenshiLib_0.5.0/Include')/include).is_file()
    checks['runtime_static']={'hook_count':7,'health_entry_points':0,'native_motion_hook':False,'cpp_compiled':False,'solution_target':'Release|x64 / v100'}
    for p in (ROOT/'tools').rglob('*.py'):ast.parse(p.read_text('utf-8-sig'))
    for p in ROOT.rglob('*'):
        if p.is_file() and p.suffix in ['.py','.cpp','.rc','.md','.json','.csv','.hlsl','.material','.program','.ini','.sln','.vcxproj','.info']:
            s=p.read_text('utf-8-sig');assert '\ufffd' not in s and '\u951f\u65a4\u62f7' not in s
    refs=json.loads((ROOT/'docs/reference-baseline.json').read_text('utf-8'));sources=json.loads((ROOT/'docs/source-hashes.json').read_text('utf-8'))
    # 原模型/动画/骨架是本次转换的真实输入，变化必须重新审查；其他项目仅为历史设计来源，
    # 已固定复制必要工具，不应因别的任务更新其源码就让Iris无法组包；保留原基线并如实记录差异。
    for name,h in sources.items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==h,name
    observations=[]
    for name,h in refs.items():
        path=Path(name);current=hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        if current!=h:observations.append({'file':name,'baseline':h,'observed':current,'runtime_dependency':False,'writer':'未确认；本任务写入范围仅IrisArsenal'})
    checks['source_inputs_unchanged']=len(sources);checks['historical_reference_differences']=observations
    put(ROOT/'docs/reference-observations.json',json.dumps(observations,ensure_ascii=False,indent=2),'历史引用差异','保留原基线，不覆盖其他项目；差异与真正源输入分开','修改来源未确认；本项目不依赖该实时C++文件')
    checks['unresolved']=['C++/HLSL未编译或游戏验证','左手超出目标骨架可达范围的残余误差仍需视觉确认','代理为保守胶囊，接触日志不等于已经具备最终精确伤害']
    put(ROOT/'docs/validation.json',json.dumps(checks,ensure_ascii=False,indent=2),'非编译验收结果','读取真正输出的网格/骨架/FCS，跨源期望验证坐标，检查其他项目只读','未编译、未实机，不把离线检查称为碰撞已通过')
    print(json.dumps(checks,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
