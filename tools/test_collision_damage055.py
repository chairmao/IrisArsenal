"""055非编译回归：真实源码/资产不变量与独立密集命中、调度、缓存和等待模型。

这些模型不执行C++/PhysX，不宣称MSVC、FPS或实际游戏行为已经验证。
"""
from pathlib import Path
import ast,configparser,hashlib,itertools,json,random,re
from safeio import ROOT
from historical047 import assert_047_hash
from test_melee_block043 import function

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def identity_cases(native):
    body=function(native,'Hash');seed=int(re.search(r'h=(\d+)U',body).group(1));parts=re.findall(r'h=\(h\^k\.(\w+)\)\*(\d+)U',body)
    end=int(re.findall(r'\*(\d+)U',body)[-1])
    assert [p[0] for p in parts]==['type','container','containerSerial','index','serial']
    def bucket(key):
        h=seed
        for i,(_,factor) in enumerate(parts):h=((h^key[i])*int(factor))&0xffffffff
        return ((h^int(key[5]))*end)&511
    def collect(stream,indexed):
        # 独立旧规格：输出顺序由首次实际相交确定，重复肢体不额外占容量；第257唯一身份整批拒绝。
        found=[];slots=None;comparisons=0;probes=0
        def insert(i):
            nonlocal probes
            at=bucket(found[i])
            while slots[at] is not None:probes+=1;at=(at+1)&511
            probes+=1;slots[at]=i
        for key,hit in stream:
            if not key[5] or key[0]!=21:continue
            if indexed and len(found)>=8 and slots is None:
                slots=[None]*512
                for i in range(len(found)):insert(i)
            at=None
            if slots is None:
                for i,existing in enumerate(found):
                    comparisons+=1
                    if existing==key:at=i;break
            else:
                pos=bucket(key)
                for _ in range(512):
                    probes+=1;i=slots[pos]
                    if i is None:break
                    comparisons+=1
                    if found[i]==key:at=i;break
                    pos=(pos+1)&511
            if at is not None:continue
            if not hit:continue # 圆柱候选未实际相交不能提前登记为命中，后续肢体仍须判断。
            if len(found)==256:return None,comparisons,probes
            found.append(key)
            if slots is not None:insert(len(found)-1)
        return found,comparisons,probes
    rng=random.Random(550042);cases=0
    for count in (0,1,7,8,9,20,91,128,255,256,257):
        keys=[(21,3,9,i,1,True) for i in range(count)]
        for repeats in (1,2,6):
            stream=[(k,True) for k in keys for _ in range(repeats)];rng.shuffle(stream)
            assert collect(stream,False)[0]==collect(stream,True)[0];cases+=1
    for _ in range(120):
        keys=[(21,rng.randrange(3),rng.randrange(3),rng.randrange(100),rng.randrange(4),True) for i in range(180)]
        stream=[(rng.choice(keys),rng.random()>.25) for i in range(550)]
        assert collect(stream,False)[0]==collect(stream,True)[0];cases+=1
    # 故意让256个完整身份落在同一桶，验证碰撞探测、满容量重复和第257个溢出，不把hash当身份。
    colliders=[];serial=0
    while len(colliders)<257:
        k=(21,2,8,serial,17,True)
        if bucket(k)==0:colliders.append(k)
        serial+=1
    stream=[(k,True) for k in colliders[:256]]*2
    assert collect(stream,True)[0]==colliders[:256];assert collect(stream+[(colliders[-1],True)],True)[0] is None;cases+=2
    base=(21,1,2,3,4,True)
    for field in range(1,5):
        changed=list(base);changed[field]+=1;stream=[(base,True),(tuple(changed),True)]*3
        assert len(collect(stream,True)[0])==2;cases+=1
    stream=[(base,False),(base,True),(base,True)]
    assert collect(stream,True)[0]==[base];cases+=1
    dense=[((21,5,7,i,3,True),True) for i in range(256) for _ in range(5)]
    old=collect(dense,False);new=collect(dense,True);assert old[0]==new[0] and new[1]<old[1]
    return {'cases':cases,'forced_same_bucket':257,'representative_dense_identity_comparisons_before':old[1],
            'representative_dense_identity_comparisons_after':new[1],'hash_probes_after':new[2],
            'measurement':'Python规格操作数；非C++耗时或FPS'}

def scheduling_cases():
    def run(spec,copying):
        pending=[dict(x,cursor=0,failed=False,victims=[]) for x in spec];emitted=[];trace=[];copied=0;frames=0
        while pending:
            frames+=1;assert frames<2000;budget=(0,1,8,64,16)[frames%5];visits=len(pending)
            for _ in range(visits):
                if not pending or not budget:break
                job=pending[0];used=0
                while job['cursor']<job['paths'] and budget and used<8:
                    used+=1
                    if job.get('fail_once') and not job['failed']:job['failed']=True;trace.append(('retry',job['id'],job['cursor']));break
                    trace.append(('query',job['id'],job['cursor']));budget-=1;job['victims'].append(job['cursor']%5);job['cursor']+=1
                if job['cursor']<job['paths']:
                    if copying:
                        moved=dict(job,victims=list(job['victims']));copied+=job['paths']+len(job['victims']);pending.append(moved)
                    else:pending.append(job)
                    pending.pop(0)
                else:emitted.extend((job['id'],x) for x in sorted(set(job['victims'])));pending.pop(0)
        return trace,emitted,copied
    for n in (1,3,16,64,256):
        spec=[dict(id=i,paths=1+(i*17)%65,fail_once=i%5==0) for i in range(n)]
        old=run(spec,True);new=run(spec,False);assert old[:2]==new[:2] and new[2]==0
    # 医疗容量满时仅轮转、不消费；以下只验证顺序规格，实际2048门另由源码断言。
    ids=list(range(8));rotated=ids[:]
    for _ in range(len(ids)):rotated.append(rotated.pop(0))
    assert rotated==ids
    return {'job_counts':[1,3,16,64,256],'path_and_failure_order_preserved':True,'rotation_copied_elements_after':0,'medical_capacity_rotation_preserved':True}

def cache_cases():
    # 共享的是本安全窗口完整成功的接触值；事件身份、段数和收集后的enemy门互相独立。
    cache={};queries=0;health=[]
    def query(key,result,status,event):
        nonlocal queries
        if key not in cache:
            queries+=1
            if status!='complete':return False
            if len(cache)<16:cache[key]=list(result)
        for target in set(cache.get(key,result)):health.append((event,target))
        return True
    k=((0.,0.,0.),(0.,0.,90.),4.5)
    assert query(k,[1,1,2],'complete',0) and query(k,[999],'complete',1)
    assert queries==1 and sorted(health)==[(0,1),(0,2),(1,1),(1,2)]
    altered=(k[0],(0.,0.,91.),k[2]);assert query(altered,[3],'complete',2) and queries==2
    bad=((1.,2.,3.),(2.,3.,4.),2.)
    assert not query(bad,[5],'overflow',3) and bad not in cache
    assert query(bad,[6],'complete',3) and (3,5) not in health
    cache.clear();query(k,[7],'complete',4);assert (4,7) in health
    for i in range(40):query(((i,0,0),(i,0,1),1),[], 'complete',100+i)
    assert len(cache)==16
    cache.clear() # 暂停下一Tick与读档都清空；无新查询仍不推进伤害事件。
    assert not cache
    return {'cases':8,'cross_event_health_merged':False,'capacity':16,'partial_failure_cached':False,'cross_frame_cached':False}

def wait_cases():
    # 按前一观察状态分摊，不将未观测的线程执行过程编成“精确物理等待”。
    events=[(0,0),(10,1),(30,2),(40,3),(50,4),(60,0),(100,0)]
    totals=[0]*5;before=None;at=0;state=0
    for now,new in events:
        totals[state]+=now-at;at=now;state=new
        if now==10:before=totals[:]
    delta=[a-b for a,b in zip(totals,before)]
    assert delta==[40,20,10,10,10] and sum(delta)==90
    # 排队墙钟40ms目标仍可包含暂停；新分量只解释，不改变已有预算或排队时钟。
    assert delta[0]+delta[1]+delta[2]+delta[3]+delta[4]==100-10
    return {'sampled_wall_ms':90,'ready':40,'paused':20,'physics':10,'AI':10,'unavailable':10,'exact_thread_runtime':False}

def verify_collision_damage055():
    c=(ROOT/'IrisCombat.cpp').read_text('utf8');n=(ROOT/'native/NativeMultiContact.cpp').read_text('utf8')
    d=(ROOT/'IrisDiagnostics.cpp').read_text('utf8');h=(ROOT/'IrisDiagnostics.h').read_text('utf8');main=(ROOT/'IrisArsenal.cpp').read_text('utf8')
    baseline=json.loads((ROOT/'docs/collision-damage-055-baseline.json').read_text('utf8'))
    # 保持真正控制几何、身份资格、防御和事件的函数；改为PushJob的三处恢复该唯一拼写后逐字核对。
    for name,expected in baseline['combat_functions'].items():
        actual=function(c,name).replace('PushJob(j);','jobs.push_back(j);')
        assert_047_hash(('function:'+name+'_055_normalized') if name in ('Blast','Emit') else 'function:'+name,hashlib.sha256(actual.encode()).hexdigest(),expected)
    for name,expected in baseline['native_functions'].items():assert_047_hash('function:'+name,hashlib.sha256(function(n,name).encode()).hexdigest(),expected)
    for rel,expected in baseline['runtime_assets'].items():
        if rel!='IrisArsenal.ini':assert_047_hash('package:'+rel,digest(ROOT/'package/IrisArsenal'/rel),expected)
    original=baseline['runtime_config'];current=configparser.ConfigParser();current.read(ROOT/'package/IrisArsenal/IrisArsenal.ini',encoding='utf8')
    values={s:dict(current[s]) for s in current.sections()};assert values['IrisArsenal'].pop('enablecombatdetaillogging')=='1'
    # 056额外两个开关不改变原战斗参数，具体合批/回退由新专项验证。
    assert values['IrisArsenal'].pop('enablecapsulebatching')=='1' and values['IrisArsenal'].pop('nativehitslowms')=='1.0'
    assert values==original # 除一个诊断开关外，全部原参数逐值相同。
    assert 'std::list<Job> jobs;std::deque<Hurt> hurts;' in c and 'jobs.push_back(j)' not in c
    resolver=function(c,'ResolveJobs');assert 'jobs.splice(jobs.end(),jobs,jobs.begin())' in resolver and 'used<8' in resolver and '++j.cursor;++used;' in resolver
    assert 'hurts.size()+j.victims.size()>2048' in resolver and 'size_t visits=jobs.size();' in resolver
    swap=function(c,'Swap')
    for field in ['caster','cast','event','move','mult','paths','cursor','victims','blade','failures','createdAt','waits']:assert field in swap,field
    contact=function(c,'Contacts')
    # 056依据真实055运行零命中退役胶囊缓存，球缓存和清理仍逐帧/读档存在。
    assert contact.index('queuesAreClearMT')<contact.index('sphereFacts.size()')
    assert 'status==IrisNative::QUERY_COMPLETE' in contact and 'sphereFacts.size()<16' in contact
    assert 'capsuleFacts' not in c and c.count('sphereFacts.clear();')==2 and 'unsigned budget=64' in c
    flush=function(c,'Flush');assert flush.count('->_NV_hitByMeleeAttack(')==1
    assert 'queueSnapshot.done<damageFlushMaxHits' in flush and 'queueSnapshot.inspected<256' in flush
    assert flush.index('>=damageFlushBudgetMs')<flush.index('hurts.pop_front()')
    for x in ['queuesAreClearMT()','ai->isRunning()','r.generation!=epoch','DamageTarget(caster,victim)','getTotalAttackDamageFor(victim)','damage.multiply(r.mult)','xpMelee(outcome,victim,damage)']:assert x in flush,x
    assert 'DAMAGE_IDENTITY' in flush and 'DAMAGE_CALCULATE' in flush and 'DAMAGE_XP' in flush
    assert 'DAMAGE_RESULT' in function(c,'DamageOutcome')
    assert 'setUserContactReport' not in re.sub(r'//[^\n]*','',c+n)
    assert 'slots[512]' in n and 'probes<512' in n and 'output.count<8' in n
    assert 'scratch.points.clear();scratch.rounding=0;' in n and 'identities.Committed();' in n
    cfg=configparser.ConfigParser();cfg.read(ROOT/'distribution/IrisArsenal.ini',encoding='utf8')
    assert cfg.getfloat('IrisArsenal','DamageFlushBudgetMs')==2.5 and cfg.getint('IrisArsenal','DamageFlushMaxHits')==32
    assert cfg.getint('IrisArsenal','EnableCombatDetailLogging')==1
    assert 'bool DetailsEnabled(){return enabled&&performance&&details;}' in d
    assert 'if(!DetailsEnabled())return;' in function(d,'ObserveWindow') and 'if(!DetailsEnabled()||now<=0)return;' in function(d,'SnapshotWaits')
    assert 'createdAt(IrisDiagnostics::DetailsEnabled()?IrisDiagnostics::Now():0)' in c
    assert 'calculateBegin=detail?IrisDiagnostics::Now():0' in c
    # 只有预算所需旧QPC继续运行；新增诊断关掉后不创建线程、不查文件、不读取额外游戏对象。
    assert (main+c+(ROOT/'IrisRanged.cpp').read_text('utf8')).count('KenshiLib::AddHook(')==18
    enums=[x.strip() for x in re.search(r'enum Counter \{(.*?)COUNTER_COUNT',h,re.S).group(1).split(',') if x.strip()]
    labels=re.findall(r'"([^"]+)"',re.search(r'counters\[COUNTER_COUNT\]=\{(.*?)\};',d,re.S).group(1))
    assert len(enums)==len(labels)==51 and labels[36]=='capsule_cache'
    assert 'wait_attribution=previous_main_thread_observation' in d and 'WaitKind(Kind(i))?0:1' in d
    import stage_package
    assert stage_package.BUILD_CONTRACT=='IRIS_DRIVE_REBUILD_059'
    # 当前真实旧产物必须拒绝；不能要求用户先保留旧产物才能通过资源验收。
    dll=ROOT.parent/'bin/Release/IrisArsenal.dll';raw=dll.read_bytes()
    if b'IRIS_DRIVE_REBUILD_059' not in raw:
        try:stage_package.validate_dll()
        except RuntimeError as error:assert '059' in str(error)
        else:raise AssertionError('旧版DLL通过058组包门')
    else:stage_package.validate_dll()
    return {'version':'0.4.16','formal_release':'1.0/internal0.4.11','identity':identity_cases(n),'scheduling':scheduling_cases(),
            'cache':cache_cases(),'wait_attribution':wait_cases(),'preserved_runtime_assets':len(baseline['runtime_assets']),
            'preserved_combat_functions':len(baseline['combat_functions']),'preserved_native_functions':len(baseline['native_functions']),
            'hooks':18,'query_budget':64,'medical_budget_ms':2.5,'medical_calls':32,'query_time_deferral_added':False,
            'compiled':False,'C++_executed':False,'PhysX_executed':False,'game_tested':False,'FPS_measured':False}
if __name__=='__main__':print(json.dumps(verify_collision_damage055(),ensure_ascii=False,indent=2))
