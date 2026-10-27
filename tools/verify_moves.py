"""0.3.1非编译验收：序列化身体/握点、源事件、FCS隔离、网格/纹理、真实查询接口和静态语法。"""
from pathlib import Path
import ast,hashlib,json,math,re,struct,sys,xml.etree.ElementTree as ET
import numpy as np
from safeio import ROOT,put
# 070：握点证明表只用于开发验证，生成/读取统一移出运行assets。
from asset_paths070 import PROOFS
import verify_prototype as base
import port_math as m
P=ROOT/'package/IrisArsenal';A=P/'assets'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def body_check(s,sex,animation_path):
    bones,length,tracks=base.skeleton(animation_path,s['animation'])
    count=s['frames'];assert abs(length-s['duration'])<1e-5 and all(len(v)==count for v in tracks.values())
    names={b['name']:b['id'] for b in bones};proof=np.loadtxt(PROOFS/('iris_'+s['key']+'_weapon_proof_'+sex+'.csv'),skiprows=1);assert proof.shape==(count,10)
    positions=[];angles=[];left=[];heights=[]
    for k in range(count):
        wp=[]
        for b in bones:
            v=tracks[b['id']][k] if b['id'] in tracks else (0,0,0,0,1,0,0,0);q=m.qmul(b['orientation'],(v[4],v[1],v[2],v[3]));pos=m.vadd(b['position'],v[5:]);parent=b['parent']
            assert abs(np.linalg.norm(q)-1)<1e-5
            if parent>=0:pp,pq=wp[parent];pos=m.vadd(pp,m.rotate(pq,pos));q=m.qmul(pq,q)
            wp.append((pos,q))
        root=tracks[names['Bip01']][k];forward=root[7];grip,q=wp[names['Bip01 Prop2']];expected=proof[k,:3]+[0,0,forward]
        positions.append(float(np.linalg.norm(np.asarray(grip)-expected)));actual=m.qmul(q,m.axis((1,0,0),-90))
        angles.append(math.degrees(2*math.acos(min(1,abs(float(np.asarray(actual)@proof[k,3:7]))))))
        left.append(float(np.linalg.norm(np.asarray(wp[names['Bip01 L Hand']][0])-proof[k,7:10]-[0,0,forward])));heights.append(root[6])
    assert max(positions)<2e-4 and max(angles)<.15,(s['key'],sex,max(positions),max(angles))
    return {'move':s['key'],'sex':sex,'frames':count,'weapon_position_error_max':max(positions),'weapon_angle_error_degrees_max':max(angles),'left_unreachable_error_max':max(left),'root_vertical_range':[min(heights),max(heights)],'runtime_verified':False}
def category_ids(record,name):
    # 消费实际序列化的FCS引用，不从导出规格臆测种族已加载哪些动画集。
    found=[]
    for raw in record['cats']:
        category,pos=base.fcs.Reader(raw).string(0)
        count=struct.unpack_from('<I',raw,pos)[0];pos+=4
        for _ in range(count):
            key,pos=base.fcs.Reader(raw).string(pos);pos+=12
            if category==name:found.append(key)
        assert pos==len(raw),'FCS引用类别长度错误'
    return found

def animation_references(moves,records=None,package=P):
    # 从FCS字段沿真实部署相对路径打开骨架，并核对内部动画名及长度；不是仅验证猜出的文件名。
    # 此检查在组包之前执行，缺文件、旧DrillProof混入或本体混入种族覆盖都会阻止发布。
    package=Path(package).resolve();records=base.records(package/'IrisArsenal.mod') if records is None else records
    by_id={r['key']:r for r in records};assert len(by_id)==len(records)
    references=[];required=set()
    for move in moves:
        key=str(30+move['index'])+'-IrisArsenal.mod';required.add(key)
        assert key in by_id and by_id[key]['type']==112,('缺少动画集',key)
        values=base.fields(by_id[key]);tech=base.fields(by_id[move['technique']])
        assert tech['anim name']==move['animation'],('技巧动画名不一致',key)
        for sex in ('male','female'):
            name=values.get(sex+' animation','').replace('\\','/');prefix='./mods/IrisArsenal/'
            assert name.startswith(prefix),('动画路径超出本mod',key,name)
            path=(package/name[len(prefix):]).resolve()
            assert path.is_relative_to(package) and path.is_file(),('FCS动画文件不存在',key,sex,name)
            _,length,_=base.skeleton(path,move['animation'])
            assert abs(length-move['duration'])<1e-5,('FCS动画长度错误',key,sex)
            references.append({'move':move['key'],'sex':sex,'record':key,'path':str(path.relative_to(package)),
                               'animation':move['animation'],'sha256':sha(path)})
    # 用户要求本体无种族覆盖；仍验证全部实际动画文件／名字／时长，但种族接入由独立补丁承担。
    assert not any(r['type']==7 for r in records),'本体混入种族动画覆盖'
    return references

def syntax_check():
    # Tree-sitter只解析语法树，不调用C++预处理器/编译器，也无法代替MSVC类型/链接检查。
    task=Path('D:/CodexWorkSpace/Sessions/20261002-235652-kenshi-crash-407794f2/Task-IrisArsenal-EightMoves-20261016-012351-58b640')
    dep=task/'tools/syntax';sys.path.insert(0,str(dep))
    import tree_sitter,tree_sitter_cpp
    parser=tree_sitter.Parser(tree_sitter.Language(tree_sitter_cpp.language()));results=[]
    for rel in ['IrisArsenal.cpp','IrisCombat.cpp','IrisCombat.h','IrisRanged.cpp','IrisRanged.h','native/NativeMultiContact.cpp','native/NativeMultiContact.h','native/FiniteCylinder.h','IrisDiagnostics.cpp','IrisDiagnostics.h']:
        text=(ROOT/rel).read_text('utf-8');normalized=re.sub(r'\b__fastcall\b','',text)
        tree=parser.parse(normalized.encode('utf-8'));errors=[]
        def visit(n):
            if n.type=='ERROR' or n.is_missing:errors.append({'kind':n.type,'line':n.start_point.row+1,'column':n.start_point.column})
            for c in n.children:visit(c)
        visit(tree.root_node);assert not errors,(rel,errors)
        results.append({'file':rel,'errors':errors,'ignored_for_grammar':['__fastcall'],'compiled':False})
    return results
def main():
    doc=json.loads((ROOT/'docs/eight-moves.json').read_text('utf-8'));moves=doc['moves'];assert doc['contract']=='IRIS_EIGHT_042' and len(moves)==10
    checks={'contract':doc['contract'],'compiled':False,'HLSL_compiled':False,'game_tested':False}
    expected=[2,3,4,12,3,20,3,4,4,3];assert [len(s['events']) for s in moves]==expected
    rows=(A/'moves.csv').read_text('utf-8').splitlines();assert rows.pop(0)=='IRIS_EIGHT 1 10';kinds={'weapon':0,'ground_shell':1,'shockwave':2,'drill':3,'heavy_shell':4,'blade':5,'bullet':6,'shell':7,'beam':8,'front_sphere':9}
    for s in moves:
        head=rows.pop(0).split();assert int(head[0])==s['index'] and head[1:3]==[s['key'],s['animation']] and int(head[4])==len(s['events'])
        for e in s['events']:
            v=rows.pop(0).split();assert abs(float(v[0])-e['time'])<1e-8 and int(v[1])==kinds[e['kind']]
        for source,digest in s['source_hashes'].items():assert sha(source)==digest
    assert not rows
    checks['events']={s['key']:len(s['events']) for s in moves}
    r=base.records(P/'IrisArsenal.mod');assert len({x['key'] for x in r})==len(r)
    checks['FCS_animation_references']=animation_references(moves,r)
    resolved={(x['move'],x['sex']):P/x['path'] for x in checks['FCS_animation_references']}
    checks['serialized_body']=[body_check(s,sex,resolved[s['key'],sex]) for s in moves for sex in ['male','female']]
    for s in moves:
        f=base.fields(next(x for x in r if x['key']==s['technique']));assert f['anim name']==s['animation'] and f['chance']==0 and f['disabled'] and f['max simultaneous hits']==0 and f['power 1']==0
        assert f['attack distance']==s['attack_max'] and f['attack distance min vs static']==s['attack_min']
        assert f['gains ground']==(abs(s['motion'][-1][1])>.01 or s['key']=='fire_roll')
    weapon=base.fields(next(x for x in r if x['key']=='1-IrisArsenal.mod'))
    # 053参考实际Falling Sun五字段；攻击事件倍率/武器几何仍由各专项独立验证。
    from weapon_balance053 import expected_fields
    assert all(abs(weapon[key]-value)<1e-7 for key,value in expected_fields().items()) and weapon['pierce damage multiplier']==0
    assert base.fcs.roundtrip(str(P/'IrisArsenal.mod'))['identical'];checks['FCS']={'private_moves':10,'shared_chance':0,'disabled_public_pool':True,'native_automatic_damage_targets':0,'damage_only_once_via_physical_event':True,'ranges':{s['key']:[s['attack_min'],s['attack_max']] for s in moves}}
    # 063新增两种源附件；旧20资产不被删改，主验收同步核对22份实际绑定。
    effects=json.loads((ROOT/'docs/eight-effects.json').read_text('utf-8'));rows=(A/'effects.csv').read_text('utf-8').splitlines();assert rows.pop(0)=='IRIS_FX 4 22'
    for x in effects['assets']:
        vertices,mats=base.mesh(A/('iris_fx_'+x['key']+'.mesh'),52 if x['key']=='muzzle_fire' else 48,x['key'] in effects.get('timelines',{}) or x.get('particle_mesh',False));assert mats==x['materials'];assert sha(x['source'])==x['sha256']
        p=np.concatenate(vertices);assert np.allclose(p.min(0),x['min'],atol=1e-4) and np.allclose(p.max(0),x['max'],atol=1e-4)
        center=(p.max(0)+p.min(0))*.5;bound=np.linalg.norm(p-center,axis=1).max();assert np.allclose(center,x['center'],atol=1e-4) and abs(bound-x['bound_radius'])<1e-4
        head=rows.pop(0).split();assert head[:3]==[x['key'],'iris_fx_'+x['key']+'.mesh',str(len(mats))] and np.allclose(list(map(float,head[3:6])),center,atol=1e-4)
        assert rows[:len(mats)]==mats;del rows[:len(mats)]
    assert not rows
    materials='\n'.join(p.read_text('utf-8') for p in A.glob('*.material'))
    for texture in re.findall(r'\btexture\s+(\S+\.(?:dds|png))',materials):assert (A/texture).is_file(),texture
    for path in A.glob('*.program'):
        data=path.read_text('utf-8');shaders=re.findall(r'\bsource\s+(\S+)',data)
        for shader in shaders:assert (A/shader).is_file()
        all_hlsl='\n'.join((A/shader).read_text('utf-8') for shader in set(shaders))
        for entry in re.findall(r'\bentry_point\s+(\w+)',data):assert re.search(r'\b'+entry+r'\s*\(',all_hlsl),entry
    for path in list(A.glob('*.material'))+list(A.glob('*.program'))+list(A.glob('*.hlsl')):
        text=re.sub(r'//[^\n]*','',path.read_text('utf-8'));assert text.count('{')==text.count('}'),path
    checks['effects']={'source_assets':len(effects['assets']),'source_RGBA_and_UV':True,'references_exist':True,'not_ported':effects['not_ported']}
    # 真正普通武器顶点全部落在拟合代理内；不是武器length/2的猜测。
    import author_prototype as author
    ms,_=author.read_nif(author.SOURCE/'Meshes/SW/Iris/2.nif')
    vertices=np.concatenate([(np.asarray(x['vertices'])@x['matrix'][:3,:3].T+x['matrix'][:3,3])@author.C.T*author.SCALE for x in ms])
    capsules=np.loadtxt(A/'weapon_collision.csv',skiprows=1);covered=np.zeros(len(vertices),bool)
    for x,y,lo,hi,radius in capsules:
        closest=np.stack([np.full(len(vertices),x),np.full(len(vertices),y),np.clip(vertices[:,2],lo,hi)],1);covered|=np.linalg.norm(vertices-closest,axis=1)<=radius+1e-5
    assert covered.all();checks['weapon_proxy']={'vertices_covered':len(vertices),'capsules':8,'precision':'conservative, not triangles'}
    main=(ROOT/'IrisArsenal.cpp').read_text('utf-8');combat=(ROOT/'IrisCombat.cpp').read_text('utf-8');native=(ROOT/'native/NativeMultiContact.cpp').read_text('utf-8')
    assert main.count('KenshiLib::AddHook(')==7 and combat.count('KenshiLib::AddHook(')==3 and 'IrisCombat::Tick(w,scene,frameDelta)' in main and 'IrisCombat::Flush(w)' in main
    assert 'profile.appear+.08f' in main and '(t-.416666667f)/.08f' in combat
    assert 'scene->overlapSphereShapes(sphere,NX_ALL_SHAPES,64,batch,&collector,groups,0,true)' in native
    assert 'new CombatTechniqueData(d);t->maxTargetHits=0;' in combat and combat.count('->_NV_hitByMeleeAttack(')==1
    assert 'jobs.splice(jobs.end(),jobs,jobs.begin());IrisDiagnostics::Add(IrisDiagnostics::JOB_ROTATIONS);continue;' in combat and 'size_t visits=jobs.size();' in combat
    for bad in ['movedBy','Havok','?_NV_','setUserContactReport','NxCreatePhysicsSDK','addWound(']:
        assert bad not in re.sub(r'//[^\n]*','',main+combat+native),bad
    project=ET.parse(ROOT/'IrisArsenal.vcxproj');ns={'m':'http://schemas.microsoft.com/developer/msbuild/2003'}
    units=[x.attrib['Include'] for x in project.findall('.//m:ClCompile[@Include]',ns)]
    assert set(units)=={'IrisArsenal.cpp','IrisCombat.cpp','IrisRanged.cpp','native\\NativeMultiContact.cpp','IrisDiagnostics.cpp'} and project.find('.//m:PlatformToolset',ns).text=='v100'
    for rel in units:assert (ROOT/rel).is_file()
    from test_vulcan_contract import verify_vulcan
    checks['vulcan_036']=verify_vulcan()
    from test_projectile_aim import verify_aim
    checks['aim_pulse_resources_036']=verify_aim()
    from test_ranged_contract import verify_ranged
    checks['ranged_036']=verify_ranged()
    from test_fx_timeline import verify_fx_timeline
    checks['source_layer_timelines_036']=verify_fx_timeline()
    from test_cannon_quake import verify_cannon_quake
    checks['cannon_quake_036']=verify_cannon_quake()
    from test_optics import verify_optics
    checks['optics_036']=verify_optics()
    from test_drill_037 import verify_drill037
    checks['drill_finisher_037']=verify_drill037()
    # 文件合法不等于可见：额外检查真实GPU粒子布局、有效蓝相与中段透明度。
    from test_drill_visibility import verify_visibility
    checks['drill_visibility_038']=verify_visibility()
    from test_drill_r120 import verify_r120
    checks['drill_r120_039']=verify_r120()
    from test_fire_039 import verify_fire039
    checks['fire_and_cycle_039']=verify_fire039()
    from test_combat_036 import verify_combat036
    checks['combat_036']=verify_combat036()
    from test_range_metal041 import verify_range041
    checks['range_metal_041']=verify_range041()
    from test_ten_moves042 import verify_ten042
    checks['ten_moves_042']=verify_ten042()
    from test_melee_block043 import verify_block043
    checks['melee_block_043']=verify_block043()
    from test_melee_reaction044 import verify_reaction044
    checks['melee_reaction_044']=verify_reaction044()
    # 045配置专项不会编译或运行插件；与源资产/原生窗口回归一起执行。
    from test_move_parameters045 import verify_parameters045
    checks['move_parameters_045']=verify_parameters045()
    # 046新增按用户原表独立核对及三远程原链结果保留的专项。
    from test_balance046 import verify_balance046
    checks['balance_046']=verify_balance046()
    from test_release047 import verify_release047
    checks['release047']=verify_release047()
    # 048必须验完整重建的稳定性，手工准备包通过不能代表UpdateMod重建包能通过。
    from test_icon_rebuild048 import verify_icon_rebuild048
    checks['FCS_rebuild048']=verify_icon_rebuild048()
    from test_source_alignment049 import verify_049
    checks['source_alignment049']=verify_049()
    from test_surface050 import verify_surface050
    checks['surface050']=verify_surface050()
    # 051复核原颜色零宽区间、真实源尺度、像素预览与资产不变边界。
    from test_source_effects051 import verify_source051
    checks['source_effects051']=verify_source051()
    checks['code_contract']='IRIS_DRIVE_REBUILD_059'
    from test_audit052 import verify_audit052
    checks['audit052']=verify_audit052()
    from test_queue_balance053 import verify_queue053
    checks['queue_balance053']=verify_queue053()
    # 054专项检验真实本机Core版本/C导出、边界决策和查询函数字节保持，不冒称新修订已实机。
    from test_physx_compat054 import verify_physx054
    checks['physx_compat054']=verify_physx054()
    from test_collision_damage055 import verify_collision_damage055
    checks['collision_damage055']=verify_collision_damage055()
    # 056同步合批与原路径对照，纯Python规格不冒称实际PhysX或游戏执行。
    from test_capsule_batch056 import verify_batch056
    checks['capsule_batch056']=verify_batch056()
    # 057有限射线/连续球扫掠/墙前圆柱的分离合同与失败/预算规格，不执行游戏或编译。
    from test_ranged_ray057 import verify_ranged057
    checks['ranged_ray057']=verify_ranged057()
    from test_fire_cannon058 import verify_fire_cannon058
    checks['fire_cannon058']=verify_fire_cannon058()
    from test_drive059 import verify_drive059
    checks['drive059']=verify_drive059()
    checks['syntax']=syntax_check()
    for path in (ROOT/'tools').rglob('*.py'):ast.parse(path.read_text('utf-8-sig'))
    for path in [ROOT/'IrisArsenal.cpp',ROOT/'IrisCombat.cpp',ROOT/'IrisCombat.h',ROOT/'native/NativeMultiContact.cpp',ROOT/'native/NativeMultiContact.h',ROOT/'native/FiniteCylinder.h',ROOT/'IrisDiagnostics.cpp',ROOT/'IrisDiagnostics.h']:
        text=path.read_text('utf-8');assert '\ufffd' not in text and '\u951f\u65a4\u62f7' not in text and '\u00c3' not in text
    checks['runtime_boundaries']={'hooks':18,'physics_budget':64,'damage_budget':'INI default32 calls /2.5ms soft; FIFO/40ms advisory; no timeout drop','query_failure':'isolated round-robin retry, no partial current batch or permanent actor/world disable','health':'native armour, enemy-only, player protected; configurable unconscious targets; three ranged moves never override defence; melee per-config, defaults fire_roll/earthquake/drill/full_burst/electro_cannon','FPS_verified':False}
    checks['unresolved']=['MSVC Release|x64/v100编译、链接待用户执行','HLSL运行时编译/全部贴图可视未实机','PhysX球形/真实柱体窄相位与失败重试需实机，不把分析模型冒称C++或游戏验证','10招头/双手/根位移/方向/倒地目标与密集多人待实机','完整NiPSys/程序闪电/风场与多骨蒙皮未完成；EXDrill2严格单骨与原ALS已接入，爆炸发射器为有界翻译']
    put(ROOT/'docs/validation-drive-059.json',json.dumps(checks,ensure_ascii=False,indent=2),'八招非编译验收证据','20份真实骨架/握点、源事件、20个特效网格、源纹理、FCS、查询接口和语法树','未编译、未游戏测试，不能据此宣布最终完成')
    print(json.dumps({'contract':checks['contract'],'events':checks['events'],'body_files':len(checks['serialized_body']),'effects':checks['effects']['source_assets'],'syntax':'passed grammar only','compile':'not run','runtime':'pending'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()

