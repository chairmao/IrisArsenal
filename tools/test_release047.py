# 054仅更新当前交付版本/组包合同断言，原伤害、配置和资源回归条件保持。
"""047非编译验收：实际骨架枪口比例、入站反应边界、源范围特效、图标投影与刷新隔离。"""
import json,sys,math,hashlib,configparser,tempfile,itertools,struct
from pathlib import Path
import numpy as np
from safeio import ROOT
import verify_prototype as v,port_math as m,author_prototype as author,kenshi_mod_writer as fcs
from test_melee_block043 import function

def states(path,spec):
    bones,L,tracks=v.skeleton(path,spec['animation']);names={b['name']:b['id'] for b in bones};out=[]
    # 静止Foot在脚底平面上方；扣除该骨架自身站立高度，避免把骨中心当成地面。
    rest=m.world(bones,[b['orientation'] for b in bones]);foot_offset=min(rest[names['Bip01 '+side+' Foot']][0][1] for side in ('L','R'))
    for k in range(spec['frames']):
        wp=[]
        for b in bones:
            row=tracks[b['id']][k] if b['id'] in tracks else (0,0,0,0,1,0,0,0)
            q=m.qmul(b['orientation'],(row[4],row[1],row[2],row[3]));p=m.vadd(b['position'],row[5:])
            if b['parent']>=0:
                pp,pq=wp[b['parent']];p=m.vadd(pp,m.rotate(pq,p));q=m.qmul(pq,q)
            wp.append((p,q))
        grip,q=wp[names['Bip01 Prop2']];q=m.qmul(q,m.axis((1,0,0),-90))
        muzzle=np.array(grip)+m.rotate(q,(1.807138657,0,8.534358047))
        foot=min(wp[names['Bip01 '+side+' Foot']][0][1] for side in ('L','R'))-foot_offset
        out.append([*muzzle,float(foot),*q,*wp[names['Bip01']][0]])
    return out

def verify_release047():
    # 旧值来自改前序列化骨架，当前值从新产物反算；不依赖作者自己的期望CSV。
    e=json.loads((ROOT/'docs/release-047-evidence.json').read_text('utf8'));doc=json.loads((ROOT/'docs/eight-moves.json').read_text('utf8'));results=[]
    for spec in doc['moves']:
        if spec['key']!='vulcan':continue # 059 drive不再使用旧1.5坐姿高度，站姿见059专项。
        assert spec['height047']['muzzle_height_scale']==1.5 and not spec['height047']['runtime_offset']
        for sex in ('male','female'):
            key=spec['key']+'_'+sex;old=np.array(e['height_frames'][key]);new=np.array(states(ROOT/'package/IrisArsenal/assets'/('iris_action_'+key+'.skeleton'),spec))
            times=np.linspace(0,spec['duration'],spec['frames']);active=(times>=spec['events'][0]['time']-.02)&(times<=spec['events'][-1]['time']+.02)
            # 049坐姿令双脚悬起；标尺仍是旧站立脚底，不能拿悬起的Foot重新定义地面。
            ratios=(new[active,1]-old[active,3])/(old[active,1]-old[active,3]);assert np.max(abs(ratios-1.5))<2e-5
            # 射击窗口水平枪口不变；根轨道和脚底在整个动作均不变。
            assert np.max(abs(new[active][:,[0,2]]-old[active][:,[0,2]]))<1e-4
            assert np.max(abs(new[:,[8,9,10]]-old[:,[8,9,10]]))<1e-4
            if spec['key']=='vulcan':assert np.max(abs(new[:,3]-old[:,3]))<1e-4
            assert np.max(abs(abs(np.sum(new[:,4:8]*old[:,4:8],axis=1))-1))<2e-6
            assert np.max(abs(new[[0,-1],:3]-old[[0,-1],:3]))<1e-4
            results.append({'move':key,'height_ratio':[float(ratios.min()),float(ratios.max())],'root_and_foot_unchanged':True})
    c=(ROOT/'IrisCombat.cpp').read_text('utf8');main=(ROOT/'IrisArsenal.cpp').read_text('utf8');ranged=(ROOT/'IrisRanged.cpp').read_text('utf8')
    gate=function(c,'ProtectedRangedMove');reaction=function(c,'MeleeStumbleHook')
    for token in ['Iris::Accepting()','proofOnly','world->gameResetting','isLoadingFromASaveGame()','Iris::ActorReady(c)','isRagdoll()','PS_NORMAL','getChainedModeShackles()','currentlyStumbling()','!a.ranged','!a.active&&!a.reserved','RangedMove(a.move)','IrisRanged::Active(c)','animationRequirements._currentCombatTechnique!=technique','getAnimationProgress(technique)','acceptableEndTime01','stillPlayingAnActionOrSomething()']:assert token in gate,token
    for forbidden in ['getAnimationState(', 'setPosition(', 'startCombatAnimation(', 'currentTechnique=','getObjectsWithin','Target(']:assert forbidden not in gate
    assert 'ProtectedRangedMove(combat)' in reaction and reaction.count('combat->_getHit(')==1
    assert 'ProtectedRangedMove' not in function(c,'MeleeBlockCheckHook')
    assert 'const bool unavoidable=!RangedMove(r.move)&&moves[r.move].bypassDefence;' in function(c,'Flush')
    assert (main+c+ranged).count('KenshiLib::AddHook(')==18
    cfg=configparser.ConfigParser();cfg.read(ROOT/'distribution/IrisArsenal.ini',encoding='utf8')
    for key in ['vulcan','pulse','drive']:
        assert cfg.getboolean('Move.'+key,'ImmuneHitReactions')
        assert not cfg.has_option('Move.'+key,'BypassBlockDodge')
    # 独立边界规格：只有预约/活动中的真实三远程片段保护，停止/换招/后效不保护。
    cases=0
    for move,active,reserved,native,identity,valid,progress,enabled in itertools.product(range(10),(False,True),(False,True),(False,True),(False,True),(False,True),[-1,0,.5,.995,1],(False,True)):
        protected=move in {5,6,7} and (active or reserved) and native and identity and valid and 0<=progress<.995 and enabled
        if move not in {5,6,7} or not native or not identity or not valid or progress<0 or progress>=.995 or not enabled or not(active or reserved):assert not protected
        cases+=1
    # 源范围效果的真实身份/纹理/逐帧包络由总验收复核，此处另校对CAST链和既有球心/朝向。
    source=author.SOURCE;ini=source/'SKSE/PayloadInterpreter/Config/Iris.ini';esp=source/'soulworker_Iris.esp'
    assert hashlib.sha256(ini.read_bytes()).hexdigest()==e['source_ini_sha256'] and hashlib.sha256(esp.read_bytes()).hexdigest()==e['source_esp_sha256']
    raw=ini.read_text('utf8');assert all(('$IrisBeam = @CAST|0X000'+fid+'|') in raw for fid in ['886','824','826'])
    effects=json.loads((ROOT/'docs/eight-effects.json').read_text('utf8'));asset=next(x for x in effects['assets'] if x['key']=='electro_area');timeline=effects['timelines']['electro_area']
    assert Path(asset['source']).name=='ShoutAreaExplosionWarm0.nif' and len(asset['materials'])==4 and timeline['duration']==5
    assert asset['source_chain']==['$IrisBeam','SPEL824','MGEF812','EXPL810'] and timeline['source_normalization']['target_horizontal_radius']==1
    branch=function(c,'Emit');branch=branch[branch.index('if(e.kind==9)'):branch.index('if(e.kind==0||e.kind==3||e.kind==8)')]
    # 058球心/光柱改用同一原生枪口轴；源效果、R25、四次健康事件和不自行追踪目标的语义保持。
    for token in ['ElectroFrame(weapon,a.origin,c->getPosition(),e.radius,frame)','r.pos=center','r.orientation=frame.orientation','r.radius=e.radius','Path(center,center,e.radius,true)']:assert token in branch
    assert 'Target(' not in branch and branch.count('PushJob(j)')==1
    show=function(c,'ShowParts');beam=show[show.index('float cannonAge='):show.index('// 原PROJ.NAM1')]
    assert 'ElectroFrame(w,a.origin,c->getPosition(),moves[8].events.front().radius,frame)' in beam and 'Pose(frame.muzzle-a.origin,frame.orientation' in beam and 'Target(' not in beam
    # 当前FCS仅本武器四个相机字段变化，其他记录与头部原字节一致。
    path=ROOT/'package/IrisArsenal/IrisArsenal.mod';records=author.records(path);weapon=next(r for r in records if r['key']=='1-IrisArsenal.mod');fields=v.fields(weapon)
    changed={k for k in set(fields)|set(e['old_weapon_fields']) if fields.get(k)!=e['old_weapon_fields'].get(k)}
    # 053额外只允许指定五个数值变化，图标四项仍需保持047校准。
    from weapon_balance053 import expected_fields
    expected=expected_fields()
    assert changed=={'auto icon image','icon offset H','icon offset V','icon zoom'}|set(expected) and fields['auto icon image']
    assert all(abs(fields[key]-value)<1e-7 for key,value in expected.items())
    for record in records:
        if record['key']!=weapon['key']:
            from historical047 import assert_047_hash
            assert_047_hash('record:'+record['key'],hashlib.sha256(fcs.write_record(record)).hexdigest(),e['record_sha256'][record['key']])
    raw=path.read_bytes();assert hashlib.sha256(raw[:8+int.from_bytes(raw[4:8],'little')]).hexdigest()==e['FCS_header_sha256']
    vertices,_=v.mesh(ROOT/'package/IrisArsenal/assets/iris_weapon.mesh');points=np.concatenate(vertices)
    q=m.qmul(m.qmul(m.axis((1,0,0),-90),m.axis((0,1,0),-180)),m.axis((0,0,1),90));p=np.array([m.rotate(q,row[:3]) for row in points])
    distance=fields['icon zoom']*5-p[:,2];assert distance.min()>0
    ndc=np.column_stack(((p[:,0]+fields['icon offset H'])/distance/math.tan(math.pi/8)/5,(p[:,1]+fields['icon offset V'])/distance/math.tan(math.pi/8)))
    assert abs(ndc).max()<.88
    # 缓存刷新仅在隔离目录运行；无真实游戏/图标删除，备份失败或游戏运行必须保持原缓存。
    from refresh_icon047 import refresh
    with tempfile.TemporaryDirectory(prefix='Iris047-',dir='D:/CodexWorkSpace') as tmp:
        root=Path(tmp);icons=root/'game/data/icons';icons.mkdir(parents=True)
        own=icons/'1-IrisArsenal.mod.test.png';other=icons/'1-Other.mod.test.png';second=icons/'2-IrisArsenal.mod.test.png'
        for path in [own,other,second]:path.write_bytes(b'png-fixture')
        rows=refresh(root/'game',[root/'backupD',root/'backupE'],lambda:None)
        assert len(rows)==1 and not own.exists() and other.exists() and second.exists()
        assert all(Path(p).read_bytes()==b'png-fixture' for p in rows[0]['backups'])
        own.write_bytes(b'new-cache')
        def running():raise RuntimeError('game running')
        try:refresh(root/'game',[root/'bD',root/'bE'],running);raise AssertionError('运行中也刷新')
        except RuntimeError:pass
        assert own.read_bytes()==b'new-cache'
        # 第二备份根是文件而非目录时，首份备份成功也不能提前删除原缓存。
        bad=root/'blocked';bad.write_bytes(b'not a directory')
        try:refresh(root/'game',[root/'good',bad],lambda:None);raise AssertionError('备份失败也删除')
        except OSError:pass
        assert own.read_bytes()==b'new-cache' and other.exists() and second.exists()
    import stage_package
    assert stage_package.BUILD_CONTRACT=='IRIS_DRIVE_REBUILD_059' and '[IrisArsenal 0.4.16]' in (main+(ROOT/'IrisDiagnostics.cpp').read_text('utf8'))
    return {'height_actual_serialized':results,'ranged_incoming_guard_boundary_model_cases':cases,'ranged_outgoing_defence_override':False,
            'native_hook_count':18,'electro_area_source_verified':True,'electro_sphere_center_forward':20,'electro_radius':25,
            'fixed_heading':True,'icon_native_projection_min':ndc.min(0).tolist(),'icon_native_projection_max':ndc.max(0).tolist(),
            'FCS_other_records_unchanged':len(records)-1,'cache_refresh_isolation':True,'compiled':False,'game_tested':False,'GPU_render_tested':False}
if __name__=='__main__':print(json.dumps(verify_release047(),ensure_ascii=False,indent=2))
