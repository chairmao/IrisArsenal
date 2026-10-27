# 054仅更新当前交付版本/组包合同断言，原伤害、配置和资源回归条件保持。
# 050仅更新版本断言；参数/反应隔离与旧资产精确摘要回归仍完整执行。
# 047：历史资源锁仅按authorized-delta精确迁移；新增高度/入站保护/源范围另独立验收。
# 045：原044免疫窗口和单次医疗不变，新增每招免疫开关的边界另作专项。
"""044六招全部普通受击反应免疫：窗口/大小反应/医疗隔离/结束边界；不编译或运行游戏。"""
from pathlib import Path
import hashlib,itertools,json,math,re
from safeio import ROOT
from historical047 import assert_047_hash,package_hash052
from test_melee_block043 import function

def verify_reaction044():
    e=json.loads((ROOT/'docs/melee-reaction-044-evidence.json').read_text('utf8'))
    c=(ROOT/'IrisCombat.cpp').read_text('utf8');main=(ROOT/'IrisArsenal.cpp').read_text('utf8');ranged=(ROOT/'IrisRanged.cpp').read_text('utf8')
    expected={0,1,2,3,4,8};actual={int(n) for n in re.findall(r'move==(\d+)',function(c,'BlockGuardMove'))};assert actual==expected==set(e['scope'])
    assert 'DrillProtected(' not in c and 'DrillStumbleHook(' not in c and 'originalDrillStumble' not in c
    window=re.sub(r'//[^\n]*','',function(c,'ProtectedMeleeMove'));window=re.sub(r'\s+','',window)
    assert hashlib.sha256(window.encode()).hexdigest()==e['window_normalized_sha256'] # 043窗口语义原样，仅共用命名/注释变化。
    reaction=function(c,'MeleeStumbleHook');block=function(c,'MeleeBlockCheckHook')
    assert 'ProtectedMeleeMove(combat)' in reaction and 'ProtectedMeleeMove(self)' in block
    assert 'move>=0&&moves[move].immuneReactions&&Finite(damage.cut)&&Finite(damage.blunt)&&Finite(damage.pierce)&&Finite(damage.extraStun)' in reaction
    assert 'if(suppress){combat->_getHit(dir,damage,attacker,false);return;}' in reaction
    assert reaction.count('combat->_getHit(')==1 and reaction.count('originalMeleeStumble(self,dir,damage,part,attacker)')==1
    assert reaction.index('}catch')<reaction.index('combat->_getHit(')<reaction.index('originalMeleeStumble(')
    code=re.sub(r'//[^\n]*','',reaction)
    for forbidden in ['addWound(', 'startStumble(', 'startCombatAnimation(', 'runCombatAnimation(', 'setCombatState(', 'setPosition(', 'health=', 'flesh=', 'damage.extraStun=', 'damage.cut=', 'damage.blunt=']:
        assert forbidden not in code,forbidden
    assert 'move=' in reaction and 'small=immune large=immune medical=unchanged' in reaction
    assert 'actor.stumbles<=3' in reaction and 'melee_stumbles_suppressed=' in function(c,'End')
    assert '<<(a.move==3?a.stumbles:0)' in function(c,'End') # 旧drill计数不能误报其他五招。
    assert 'Native(&Character::_startStumble,"melee_stumble_gate")' in main
    assert (main+c+ranged).count('KenshiLib::AddHook(')==18 and c.count('->_NV_hitByMeleeAttack(')==1
    assert 'IRIS_MELEE_REACTION_044' in c and '[IrisArsenal 0.4.16]' in (main+(ROOT/'IrisDiagnostics.cpp').read_text('utf8')) and 'FILEVERSION 0,4,16,0' in (ROOT/'IrisArsenal.rc').read_text('utf8')
    # 045仅两函数增加策略/私有距离，新的专项分别核验；其余044函数仍逐字节锁定。
    for name,digest in e['unchanged_functions'].items():
        if name not in {'Flush','EnsureMoves'}:assert_047_hash('function:'+name,hashlib.sha256(function(c,name).encode()).hexdigest(),digest)
    for rel,digest in e['resource_sha256'].items():
        if rel=='IrisArsenal.ini':continue # 唯一授权的运行包文本变更。
        assert_047_hash('package:'+rel,package_hash052(ROOT/'package/IrisArsenal'/rel),digest)
    sdk=Path('E:/KenshiProject/1.Dependencies/KenshiLib_0.5.0')
    for symbol in [b'?_startStumble@Character@@QEAAXW4CutDirection@@AEAVDamages@@PEAVGameData@@PEAV1@@Z',b'?_getHit@CombatClass@@QEAAXW4CutDirection@@AEBVDamages@@PEAVRootObject@@_N@Z']:
        for p in [sdk/'Libraries/KenshiLib.lib',Path('D:/steam/steamapps/common/Kenshi/KenshiLib.dll')]:assert symbol in p.read_bytes()
    # 独立受击流水规格：医疗先发生一次，反应门不按伤害大小放行。这里是规格模型，非C++执行。
    valid=dict(accepting=True,world=True,loading=False,ready=True,alive=True,conscious=True,upright=True,stumbling=False,shackled=False,identity=True,finished=False,playing=True)
    def protected(move,p,flags,damage):
        valid_state=all(flags[k] for k in ('accepting','world','ready','alive','conscious','upright','identity','playing')) and not any(flags[k] for k in ('loading','stumbling','shackled','finished'))
        return move in expected and valid_state and math.isfinite(p) and 0<=p<.995 and all(math.isfinite(x) for x in damage)
    cases=0;suppressed=0
    for move,p,attack,force in itertools.product(range(10),[0,.01,.4,.9,.9949,.995,1],['melee','ranged'],[0,.001,1,25,100,10000,1e30]):
        damage=(2.,3.,1.,force);health_before=500.;health_after=health_before-6.;medical_calls=1
        immune=protected(move,p,valid,damage);reaction_plays=not immune
        native_hit_accounting=1 # 两条支路都保留一次原生受击记账，模型不添加第二次伤害。
        assert health_after==494 and medical_calls==native_hit_accounting==1
        if move in expected and p<.995:assert not reaction_plays;suppressed+=1
        else:assert reaction_plays
        cases+=1
    boundaries=0
    for key in valid:
        invalid=dict(valid);invalid[key]=not invalid[key]
        for move in expected:assert not protected(move,.5,invalid,(2,3,1,1e30));boundaries+=1
    for values in [(math.nan,0,0,0),(0,math.inf,0,0),(0,0,0,-math.inf)]:assert not protected(0,.1,valid,values);boundaries+=1
    # 医疗令角色死亡或昏迷时，本次反应仍走原生，不将演员保持为可战斗/免伤状态。
    for state in ['alive','conscious','upright']:
        flags=dict(valid);flags[state]=False
        assert not protected(3,.4,flags,(999,999,999,999))
    import stage_package
    assert stage_package.BUILD_CONTRACT=='IRIS_DRIVE_REBUILD_059'
    return {'version':'0.4.4','protected_move_indices':sorted(expected),'excluded':[5,6,7,9],'reaction_pipeline_model_cases':cases,'suppressed_model_cases':suppressed,'invalid_boundaries':boundaries,'unchanged_functions':len(e['unchanged_functions'])-2,'unchanged_resource_files':len(e['resource_sha256'])-1,'hooks':18,'medical':'one native wound before reaction; only _getHit(false) retained','compiled':False,'game_tested':False,'model_is_runtime_proof':False}

if __name__=='__main__':print(json.dumps(verify_reaction044(),ensure_ascii=False,indent=2))
