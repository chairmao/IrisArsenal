# 054仅更新当前交付版本/组包合同断言，原伤害、配置和资源回归条件保持。
"""053静态合同、真实FCS和独立调度规格模型；不编译，不执行C++或生成运行二进制。"""
from pathlib import Path
import json,hashlib,re,math,configparser,copy
from safeio import ROOT
from historical047 import assert_047_hash
from verify_prototype import records,fields
from test_melee_block043 import function
import weapon_balance053 as wb

def model(requests,budget=2.5,max_hits=12,target=40,safe=True,clock=True,now=100):
    # 独立规格：进入的单笔不可抢占，先到先服务；过时仅记账，失效请求也占耗时。
    pending=list(requests);cost=0;done=[];popped=[];late=[];reason='empty'
    if not safe:return pending,done,popped,late,'safety',cost
    while pending and len(done)<max_hits and len(popped)<256:
        if popped and clock and cost>=budget:reason='time_budget';break
        request=pending.pop(0);popped.append(request['id'])
        if clock and now+cost-request['queued']>=target:late.append(request['id'])
        cost+=request['cost']
        if request.get('valid',True):done.append(request['id'])
    if pending and reason=='empty':reason='count_budget' if len(done)>=max_hits else 'scan_budget'
    return pending,done,popped,late,reason,cost

def verify_queue053():
    c=(ROOT/'IrisCombat.cpp').read_text('utf8');d=(ROOT/'IrisDiagnostics.cpp').read_text('utf8');h=(ROOT/'IrisDiagnostics.h').read_text('utf8')
    cfg=configparser.ConfigParser();cfg.read(ROOT/'distribution/IrisArsenal.ini',encoding='utf8');section=cfg['IrisArsenal']
    # 配置调优：现有053 DLL直接读取32；2.5ms时间门和40ms软目标保持，不修改C++兜底值。
    assert section.getfloat('DamageFlushBudgetMs')==2.5 and section.getfloat('DamageQueueTargetMs')==40 and section.getint('DamageFlushMaxHits')==32
    for key in ('DamageFlushBudgetMs','DamageQueueTargetMs','DamageFlushMaxHits'):assert key in c
    flush=function(c,'Flush');resolve=function(c,'ResolveJobs')
    assert 'queueSnapshot.inspected<256' in flush and 'now-queueSnapshot.begin>=damageFlushBudgetMs' in flush
    assert flush.index('>=damageFlushBudgetMs')<flush.index('hurts.pop_front()')
    assert 'r=hurts.front();hurts.pop_front();++queueSnapshot.inspected;' in flush
    assert 'r.queuedAt=IrisDiagnostics::Now()' in resolve and 'r.queuedAt=IrisDiagnostics::PerformanceEnabled()' not in resolve
    assert 'if(age>=damageQueueTargetMs)' in flush and 'DAMAGE_OVER_TARGET' in flush
    assert 'time_budget' in flush and 'count_budget' in flush and 'scan_budget' in flush
    assert 'w->isPaused()' in flush and 'queuesAreClearMT()' in flush and 'ai->isRunning()' in flush
    assert flush.count('->_NV_hitByMeleeAttack(')==1 and c.count('KenshiLib::AddHook(')==3
    assert 'unavoidable=!RangedMove(r.move)&&moves[r.move].bypassDefence' in flush and 'DamageOutcome(r,int(result))' in flush
    assert 'now-damagePressureLast>=1000' in c and 'target_is_soft=1 no_timeout_drop=1' in c
    # 枚举与标签逐项对齐，新增计数不能错列进原有统计。
    enum=re.search(r'enum Counter \{(.*?)COUNTER_COUNT\}',h,re.S).group(1).split(',')
    enum=[x.strip() for x in enum if x.strip()];labels=re.findall(r'"([^"]+)"',re.search(r'counters\[COUNTER_COUNT\]=\{(.*?)\};',d,re.S).group(1))
    assert len(enum)==len(labels)==51 and labels[24:29]==['damage_over_target','medical_time_yields','medical_count_yields','medical_safety_yields','medical_scan_yields']
    assert 'contract=IRIS_DAMAGE_QUEUE_053' in d and 'dll_version=0.4.16' in d
    # 真实FCS五字段及完整记录非目标值保持；没有用截图或作者变量代替最终数据。
    P=ROOT/'package/IrisArsenal';rs=records(P/'IrisArsenal.mod');weapon=next(r for r in rs if r['key']=='1-IrisArsenal.mod');v=fields(weapon);expected=wb.expected_fields()
    for key,value in expected.items():assert math.isclose(v[key],value,rel_tol=1e-6,abs_tol=1e-7),(key,v[key],value)
    assert v['length']==18 and v['skill category']==3 and v['pierce damage multiplier']==0
    # 生产者共用真实参考函数；对现存记录的生产者数值应用必须为幂等且保持顺序。
    source=(ROOT/'tools/author_moves.py').read_text('utf8');assert 'from weapon_balance053 import expected_fields,apply_existing' in source
    duplicate=copy.deepcopy(weapon);wb.apply_existing(duplicate,expected);assert duplicate==weapon
    oldraw=(P/'IrisArsenal.mod').read_bytes();patched,_=wb.patch_existing_mod(oldraw,expected);assert patched==oldraw
    import kenshi_mod_writer as fcs
    assert fcs.roundtrip(str(P/'IrisArsenal.mod'))['identical']
    baseline=json.loads((ROOT/'docs/queue-balance-053-baseline.json').read_text('utf8'))
    for name,digest in baseline['unchanged_functions'].items():assert_047_hash('function:'+name,hashlib.sha256(function(c,name).encode()).hexdigest(),digest)
    for name,digest in baseline['preserved_package'].items():assert_047_hash('package:'+name,hashlib.sha256((P/name).read_bytes()).hexdigest(),digest)
    # 12组离散规格，覆盖FIFO、不丢事件、超时非丢弃、单笔越预算、计数/失效/安全与时钟失败。
    req=lambda n,cost=.5,valid=True,queued=100:[dict(id=i,cost=cost,valid=valid,queued=queued) for i in range(n)]
    cases=0
    r=model(req(10));assert r[1]==list(range(5)) and r[4]=='time_budget';cases+=1
    r=model(req(3,10));assert r[1]==[0] and r[5]==10 and r[4]=='time_budget';cases+=1
    r=model(req(30,.01));assert len(r[1])==12 and r[4]=='count_budget';cases+=1
    r=model(req(300,.1,False));assert not r[1] and len(r[2])==25 and r[4]=='time_budget';cases+=1
    r=model(req(300,0,False),clock=False);assert len(r[2])==256 and r[4]=='scan_budget';cases+=1
    r=model(req(3),safe=False);assert len(r[0])==3 and not r[2];cases+=1
    r=model(req(3,queued=0));assert r[1]==[0,1,2] and r[3]==[0,1,2];cases+=1
    r=model(req(1000,.01));assert len(r[1])==12 and len(r[0])==988;cases+=1
    mixed=req(8,.25);mixed[2]['valid']=False;r=model(mixed);assert r[1]==[0,1,3,4,5,6,7];cases+=1
    waiting=req(50,.5);all_done=[]
    while waiting:
        waiting,done,_,_,_,_=model(waiting);all_done+=done
    assert all_done==list(range(50));cases+=1
    r=model(req(2,0,queued=60));assert r[3]==[0,1];cases+=1
    r=model(req(4,.5),budget=1);assert len(r[1])==2;cases+=1
    # 另测32次上限：便宜请求可增加吞吐，仍不能越过既有时间门；上面的12次用例保留为可配置边界回归。
    r=model(req(80,.01),max_hits=32);assert len(r[1])==32 and len(r[0])==48 and r[4]=='count_budget';cases+=1
    return {'default_budget_ms':2.5,'soft_target_wall_ms':40,'max_native_calls':32,'inspection_bound':256,'independent_spec_cases':cases,'FIFO':True,'timeout_drop':False,'event_and_geometry_functions_unchanged':len(baseline['unchanged_functions']),'preserved_runtime_assets':len(baseline['preserved_package']),'weapon_fields':v,'cpp_executed':False,'compiled':False,'game_tested':False}

if __name__=='__main__':print(json.dumps(verify_queue053(),ensure_ascii=False,indent=2))
