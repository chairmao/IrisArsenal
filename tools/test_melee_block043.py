# 047：历史资源锁仅按authorized-delta精确迁移；新增高度/入站保护/源范围另独立验收。
# 045：私有技巧的格挡门由独立配置控制；INI默认回归及差异限界由配置专项验证。
"""043近战防御中断：原生两条转移的独立边界模型/SDK/隔离与旧DLL拒绝；不编译。"""
from pathlib import Path
import hashlib,itertools,json,math,re,struct,tempfile,os
from unittest.mock import patch
from safeio import ROOT
from historical047 import assert_047_hash,package_hash052
import verify_prototype as base
import author_prototype as author

def function(source,name):
    m=re.search(r'\b'+name+r'\([^;{}]*\)\s*\{',source);assert m,name
    depth=0
    for j in range(m.end()-1,len(source)):
        if source[j]=='{':depth+=1
        if source[j]=='}':
            depth-=1
            if not depth:return source[m.start():j+1]
    raise AssertionError(name)

def verify_block043():
    evidence=json.loads((ROOT/'docs/melee-block-043-evidence.json').read_text('utf8'))
    c=(ROOT/'IrisCombat.cpp').read_text('utf8');main=(ROOT/'IrisArsenal.cpp').read_text('utf8')
    ranged=(ROOT/'IrisRanged.cpp').read_text('utf8');moves=json.loads((ROOT/'docs/eight-moves.json').read_text('utf8'))['moves']
    # 保护对象来自独立用户范围，不能只核验招式总数。
    expected={'fire_roll','spiral','earthquake','drill','full_burst','electro_cannon'}
    indexes={int(v) for v in re.findall(r'move==(\d+)',function(c,'BlockGuardMove'))}
    assert {moves[i]['key'] for i in indexes}==expected==set(evidence['protected_moves'])
    assert not indexes.intersection({5,6,7,9}) and len(indexes)==6
    clone=function(c,'EnsureMoves');assert 'if(BlockGuardMove(i)&&moves[i].preventBlock)' in clone and 'new CombatTechniqueData(d);t->maxTargetHits=0;' in clone
    assert 'impact->motionStopsAnimationFrame=1.f;' in clone
    for forbidden in ['acceptableEndTime01=','impactAnimationFrame=','combatState=','nextMove=','wantsToBlock=']:
        assert forbidden not in re.sub(r'//[^\n]*','',clone)
    guard=function(c,'ProtectedMeleeMove');hook=function(c,'MeleeBlockCheckHook')
    for required in ['Iris::Accepting()','proofOnly','CHOP_WEAPON','currentTechniqueHasFinished','world->initialized','world->gameResetting','isLoadingFromASaveGame()','Iris::ActorReady(c)','c->getCombatClass()!=self','isRagdoll()','PS_NORMAL','getChainedModeShackles()','currentlyStumbling()','actor->second.ready','actor->second.animation!=c->animation','animationRequirements._currentCombatTechnique!=technique','getAnimationProgress(technique)','progress>=technique->acceptableEndTime01','stillPlayingAnActionOrSomething()']:
        assert required in guard,required
    assert 'actor->second.active' not in guard # 首帧无需等待特效认领，尾效也不能延长。
    assert 'if(suppress)return false;return originalBlockCheck(self,myAttack,incomingAttack);' in hook
    assert hook.index('}catch')<hook.index('return originalBlockCheck') and 'Guard guard' in hook
    for forbidden in ['getAnimationState','getEnabled','startCombatAnimation','stopAnimation','runCombatAnimation','setCombatState','changeState','setPosition','_getHit','_NV_hitByMeleeAttack','Query(']:
        assert forbidden not in re.sub(r'//[^\n]*','',guard+hook),forbidden
    assert 'would_block=not_evaluated' in hook and 'actor.blockCheckLogs<3' in hook
    assert 'Native(&CombatClass::checkForNeedBlock,"melee_block_check")' in main
    assert (main+c+ranged).count('KenshiLib::AddHook(')==18 and 'IRIS_MELEE_BLOCK_043' in c
    # 源接口、库和当前运行库的同名入口同时核验；不载入DLL，不猜ABI。
    sdk=Path('E:/KenshiProject/1.Dependencies/KenshiLib_0.5.0')
    declaration=(sdk/'Include/kenshi/combat/CombatClass.h').read_text('utf8')
    assert 'bool checkForNeedBlock(float thresholdMyAttack, float thresholdIncomingAttack);' in declaration
    symbol=b'?checkForNeedBlock@CombatClass@@QEAA_NMM@Z'
    for p in [sdk/'Libraries/KenshiLib.lib',Path('D:/steam/steamapps/common/Kenshi/KenshiLib.dll')]:assert symbol in p.read_bytes()
    # 原伤害/受击反应、攻速、事件收尾和Tick逐函数原样，源资产和FCS逐字节保持。
    # 044明确替换原drill反应门，并给End追加六招反应计数；其余043基线函数仍逐字节保持。
    reaction_changes={'DrillProtected','DrillStumbleHook','End','Flush'} # 045仅Flush防御来源配置化，专项逐句核验其余医疗。
    for name,digest in evidence['unchanged_functions'].items():
        if name not in reaction_changes:assert_047_hash('function:'+name,hashlib.sha256(function(c,name).encode()).hexdigest(),digest)
    package=ROOT/'package/IrisArsenal'
    for rel,digest in evidence['resource_sha256'].items():
        if rel not in {'IrisArsenal.dll','IrisArsenal.ini'}:assert_047_hash('package:'+rel,package_hash052(package/rel),digest) # 用户编译DLL由当前代码合同门验证。
    records=author.records(package/'IrisArsenal.mod');frames={}
    for i,s in enumerate(moves):
        d=base.fields(next(r for r in records if r['key']==s['technique']))
        frames[i]=(d['anim stop frame 1']/d['num frames'],d['acceptable end time']/d['num frames'])
        assert frames[i]==(.99,.995)
    # 依据本机反汇编建立的有限转移模型，刻意同时施加主动检查和异步排队格挡。
    # 这验证规格边界，不运行C++/AI，不能冒称游戏中的动画已通过。
    cases=0
    for i,p,early,wants in itertools.product(range(10),[0,.001,.2,.49,.75,.989,.99,.992,.9949,.995,1],(False,True),(False,True)):
        stop,finish=frames[i];eligible=i in indexes and p<finish
        def native_result(skip_early,late_stop):
            if early and not skip_early:return 'startup_block'
            if wants and p>=late_stop:return 'decision_from_defence'
            if p>=finish:return 'natural_end'
            return 'attack'
        old=native_result(False,stop);new=native_result(eligible,1 if i in indexes else stop)
        if eligible:assert new=='attack',(i,p,early,wants,new)
        if i not in indexes:assert old==new
        if p>=finish and not early and i in indexes:assert new in ('natural_end','decision_from_defence')
        cases+=1
    # 首帧/自然收尾/后效/异常边界；actor.active不参与身份判断。
    valid=dict(accepting=True,world=True,loading=False,ready=True,alive=True,conscious=True,upright=True,stumbling=False,shackled=False,identity=True,finished=False,playing=True)
    def eligible(flags,progress):
        return all(flags[x] for x in ('accepting','world','ready','alive','conscious','upright','identity','playing')) and not any(flags[x] for x in ('loading','stumbling','shackled','finished')) and math.isfinite(progress) and 0<=progress<.995
    assert eligible(valid,0) and not eligible(valid,.995) and not eligible(valid,float('nan'))
    for key in valid:
        invalid=dict(valid);invalid[key]=not invalid[key];assert not eligible(invalid,.2),key
    # 同资源标记的旧DLL仍拒绝。人工PE头仅是隔离测试字节，不能被加载/当运行产物部署。
    import stage_package
    with tempfile.TemporaryDirectory(prefix='stage043-',dir='D:/CodexWorkSpace') as directory:
        t=Path(directory);fake=t/'project';(fake/'docs').mkdir(parents=True)
        (fake/'docs/eight-moves.json').write_text('{"contract":"IRIS_EIGHT_042"}',encoding='utf8')
        dll=t/'bin/Release/IrisArsenal.dll';dll.parent.mkdir(parents=True)
        raw=bytearray(512);raw[:2]=b'MZ';struct.pack_into('<I',raw,60,64);raw[64:68]=b'PE\0\0';struct.pack_into('<H',raw,68,0x8664);raw[100:114]=b'IRIS_EIGHT_042';dll.write_bytes(raw)
        with patch.object(stage_package,'ROOT',fake):
            try:stage_package.validate_dll();raise AssertionError('旧代码被接受')
            except RuntimeError as e:assert '代码合同' in str(e)
            for rel in ['IrisArsenal.cpp','IrisCombat.cpp','IrisCombat.h','IrisRanged.cpp','IrisRanged.h','native/NativeMultiContact.cpp','native/NativeMultiContact.h','native/FiniteCylinder.h','IrisArsenal.rc','IrisDiagnostics.cpp','IrisDiagnostics.h']:
                p=fake/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'');os.utime(p,(1,1))
            marker=stage_package.BUILD_CONTRACT.encode('ascii');raw[150:150+len(marker)]=marker;dll.write_bytes(raw)
            assert stage_package.validate_dll()[0]==dll
    return {'code_contract':evidence['code_contract'],'protected':sorted(expected),'excluded':['hammer_combo','vulcan','pulse','drive'],'native_transition_model_cases':cases,'invalid_window_boundaries':len(valid)+2,'unchanged_native_functions':len(evidence['unchanged_functions'])-len(reaction_changes),'unchanged_package_files':sum(rel not in {'IrisArsenal.dll','IrisArsenal.ini'} for rel in evidence['resource_sha256']),'old_same_asset_contract_DLL_rejected':True,'compiled':False,'game_tested':False,'model_is_runtime_proof':False}

if __name__=='__main__':print(json.dumps(verify_block043(),ensure_ascii=False,indent=2))
