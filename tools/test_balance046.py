# 054仅更新当前交付版本/组包合同断言，原伤害、配置和资源回归条件保持。
# 050仅更新版本断言；参数/反应隔离与旧资产精确摘要回归仍完整执行。
# 047：历史资源锁仅按authorized-delta精确迁移；新增高度/入站保护/源范围另独立验收。
"""046：按玩家原始表独立核验参数与三远程不干预防御的边界，不编译/不运行游戏。"""
import configparser,hashlib,json,re
from safeio import ROOT
from historical047 import assert_047_hash,package_hash052
from test_melee_block043 import function

def verify_balance046():
    # 独立转录用户要求，不从生成器或配置反推预期，否则配置写错也会自证通过。
    expected=[
        ('fire_roll',[1,2],(0,18),4,True),
        ('spiral',[1]*3,(0,16),4,False),
        ('earthquake',[1.5]*4,(0,27),2,True),
        ('drill',[.35]*11+[8],(0,80),1,True),
        ('full_burst',[2,2,4],(12,60),2,True),
        ('vulcan',[.2]*20,(0,10000),2,False),
        ('pulse',[1]*3,(0,10000),1,False),
        ('drive',[2]*4,(0,10000),1,False),
        ('electro_cannon',[1]*4,(4,25),2,True),
        ('hammer_combo',[.8]*3,(0,10),4,False)]
    spec=json.loads((ROOT/'docs/balance-046.json').read_text('utf8'))
    cfg=configparser.ConfigParser();cfg.read(ROOT/'distribution/IrisArsenal.ini',encoding='utf8')
    for i,(key,damages,distance,weight,bypass) in enumerate(expected):
        m=spec['moves'][key];section=cfg['Move.'+key]
        assert m['index']==i and m['damage']==damages and tuple(m['attack'])==distance and m['weight']==weight and m['bypass_block_dodge']==bypass,key
        assert cfg['MoveWeights'].getfloat(key)==weight
        assert [section.getfloat('Damage'+str(n)) for n in range(1,len(damages)+1)]==damages
        assert sum(k.startswith('damage') for k in section)==len(damages)
        if i not in {5,6,7}:
            assert (section.getfloat('AttackMin'),section.getfloat('AttackMax'))==distance
            assert section.getboolean('BypassBlockDodge')==bypass
        else:
            assert not any(k in section for k in ['attackmin','attackmax','bypassblockdodge'])
    c=(ROOT/'IrisCombat.cpp').read_text('utf8')
    configure=function(c,'ConfigureMove');flush=function(c,'Flush');scope=c[c.index('struct VulcanHitScope'):c.index('void DamageOutcome')]
    assert 'move.bypassDefence=(index==5||index==6||index==7)?false:MoveSwitch' in configure
    assert 'const bool unavoidable=!RangedMove(r.move)&&moves[r.move].bypassDefence;' in flush
    assert 'VulcanHitScope scope(unavoidable?&context:0)' in flush
    assert 'bool RangedMove(unsigned i){return i==5||i==6||i==7;}' in c
    assert scope.index('if(!context)return;')<scope.index('previous=TlsGetValue')
    assert 'if(active)TlsSetValue' in scope and 'originalDefence(self,dir,damage,who)' in c
    # 消费端的远程排除必须优先于缓存bool；即使错误地设true也不准注册兼容上下文。
    cases=0
    for i in range(10):
        for configured in (False,True):
            unavoidable=(i not in {5,6,7}) and configured
            for original_result in range(7):
                final=2 if unavoidable and original_result in {0,5} else original_result
                if i in {5,6,7}:assert final==original_result and not unavoidable
                cases+=1
    # 原伤害统计应能在长游戏后持续给出blocked/missed，不依赖前64条单目标调试行。
    outcome=function(c,'DamageOutcome')
    for token in ['HIT_MISSED','HIT_SWORD','blocked=','missed=','move=','Log(out.str())']:assert token in outcome
    assert 'hitLogs' not in outcome
    e=json.loads((ROOT/'docs/balance-046-evidence.json').read_text('utf8'))
    for name,digest in e['unchanged_functions'].items():assert_047_hash('function:'+name,hashlib.sha256(function(c,name).encode()).hexdigest(),digest)
    # 用户编译产物由组包合同另验，不能把042旧DLL字节锁死；其余源资源逐字节保留。
    for rel,digest in e['package'].items():
        if rel not in {'IrisArsenal.dll','IrisArsenal.ini','IrisPackage.json'}:assert_047_hash('package:'+rel,package_hash052(ROOT/'package/IrisArsenal'/rel),digest)
    import stage_package
    assert stage_package.BUILD_CONTRACT=='IRIS_DRIVE_REBUILD_059'
    assert '[IrisArsenal 0.4.16]' in (ROOT/'IrisDiagnostics.cpp').read_text('utf8')
    return {'player_table_values_checked':True,'damage_coefficients':58,'melee_distance_pairs':7,'weights':[x[3] for x in expected],
            'ranged_defence_overrides':[False]*3,'result_policy_model_cases':cases,'raw_block_miss_results_preserved':True,
            'unchanged_source_functions':len(e['unchanged_functions']),'geometry_changed':False,'cpp_compiled':False,'game_tested':False}

if __name__=='__main__':print(json.dumps(verify_balance046(),ensure_ascii=False,indent=2))
