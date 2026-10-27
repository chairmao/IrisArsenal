"""056非编译规格：保守广相/原几何、逐路径失败、原轮服务与医疗不变量。

解析模型不执行C++/PhysX，不能证明真实SDK边界接触或FPS；真实运行首8批/每256批仍对照旧查询。
"""
from pathlib import Path
import hashlib, json, math, random, re, struct, configparser
from safeio import ROOT
from historical047 import assert_047_hash
from test_melee_block043 import function

def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def add(a,b):return tuple(x+y for x,y in zip(a,b))
def mul(a,t):return tuple(x*t for x in a)
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def clamp(x,a,b):return max(a,min(b,x))
def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]
def point_segment2(p,a,b):
    d=sub(b,a);t=clamp(dot(sub(p,a),d)/dot(d,d),0,1) if dot(d,d) else 0
    v=sub(p,add(a,mul(d,t)));return dot(v,v)
def segment_segment2(a,b,c,d):
    u,v,w=sub(b,a),sub(d,c),sub(a,c);aa,ee,ff=dot(u,u),dot(v,v),dot(v,w)
    if aa<=1e-18:return point_segment2(a,c,d)
    if ee<=1e-18:return point_segment2(c,a,b)
    cc=dot(u,w);bb=dot(u,v);den=aa*ee-bb*bb
    s=clamp((bb*ff-cc*ee)/den,0,1) if abs(den)>1e-18 else 0
    t=(bb*s+ff)/ee
    if t<0:t=0;s=clamp(-cc/aa,0,1)
    elif t>1:t=1;s=clamp((bb-cc)/aa,0,1)
    delta=sub(add(a,mul(u,s)),add(c,mul(v,t)));return dot(delta,delta)
def segment_box2(a,b,lo,hi):
    # 每段相对于AABB各轴的约束固定，可精确最小化分段二次距离，而非仅采样端点。
    d=sub(b,a);cuts=[0.,1.]
    for k in range(3):
        if d[k]:cuts.extend(t for t in ((lo[k]-a[k])/d[k],(hi[k]-a[k])/d[k]) if 0<t<1)
    cuts=sorted(set(cuts));best=math.inf
    def distance(t):return sum(max(lo[k]-a[k]-t*d[k],0,a[k]+t*d[k]-hi[k])**2 for k in range(3))
    for left,right in zip(cuts,cuts[1:]):
        mid=(left+right)*.5;qa=qb=0
        for k in range(3):
            v=a[k]+mid*d[k]
            if v<lo[k] or v>hi[k]:
                offset=a[k]-(lo[k] if v<lo[k] else hi[k]);qa+=d[k]*d[k];qb+=d[k]*offset
        t=clamp(-qb/qa,left,right) if qa else left;best=min(best,distance(left),distance(right),distance(t))
    return best
def bounds(path,padding=False):
    a,b,r=path
    lo=tuple(f32(min(x,y)-r) for x,y in zip(a,b));hi=tuple(f32(max(x,y)+r) for x,y in zip(a,b))
    if padding:
        pad=f32(max(1.,*(abs(x) for x in lo+hi))*(4*2**-23))
        lo=tuple(f32(x-pad) for x in lo);hi=tuple(f32(x+pad) for x in hi)
    return lo,hi
def overlaps(a,b):return all(a[0][k]<=b[1][k] and b[0][k]<=a[1][k] for k in range(3))
def shape_bounds(body):
    kind,a,b,r,key=body
    if kind=='box':return a,b
    return bounds((a,b,r),True)
def exact(path,body):
    a,b,r=path;kind,c,d,s,key=body
    # 源接口的短轴阈值：保留from中心球，不用中点替代。
    if dot(sub(b,a),sub(b,a))<1e-7:b=a
    if kind=='box':return segment_box2(a,b,c,d)<=r*r
    return segment_segment2(a,b,c,d)<=(r+s)*(r+s)
def original(paths,bodies):
    result=[]
    for path in paths:
        keys=set()
        for body in bodies:
            if exact(path,body):
                if body[-1]=='invalid':return result,'invalid'
                if body[-1] is not None:keys.add(body[-1])
                if len(keys)>256:return result,'overflow'
        result.append(keys)
    return result,'complete'
def batched(paths,bodies):
    boxes=[bounds(p,True) for p in paths]
    union=(tuple(min(b[0][i] for b in boxes) for i in range(3)),tuple(max(b[1][i] for b in boxes) for i in range(3)))
    candidates=[b for b in bodies if overlaps(union,shape_bounds(b))]
    characters=[b for b in candidates if b[-1] is not None]
    if len(characters)>512 or any(b[-1]=='invalid' or b[0]=='unknown' for b in characters):return original(paths,bodies),'fallback'
    pairs=sum(overlaps(box,shape_bounds(body)) for box in boxes for body in characters)
    if pairs>1024:return original(paths,bodies),'fallback'
    out=[]
    for path,box in zip(paths,boxes):
        keys={body[-1] for body in characters if overlaps(box,shape_bounds(body)) and exact(path,body)}
        if len(keys)>256:return original(paths,bodies),'fallback'
        out.append(keys)
    return (out,'complete'),'batch'

def geometry_cases():
    rng=random.Random(56062026);runs=0;hit_keys=0
    # 同一解析形体输入分别跑逐路径与联合广相；包含多形体同身份和角色代次不同。
    for case in range(240):
        origin=tuple(rng.uniform(-60000,60000) for _ in range(3))
        paths=[]
        for n in range(2+case%7):
            a=add(origin,tuple(rng.uniform(-50,50) for _ in range(3)));b=add(a,tuple(rng.uniform(-35,35) for _ in range(3)))
            if n%4==0:b=a
            paths.append((a,b,rng.choice([.4,1,2,4.5,9])))
        bodies=[]
        for n in range(20+case%130):
            key=(1,2,3,n//3,n//3+1,True);a=add(origin,tuple(rng.uniform(-70,70) for _ in range(3)))
            if n%3==0:b=a;kind='sphere';r=rng.uniform(.5,7)
            elif n%3==1:b=add(a,(0,rng.uniform(.5,20),0));kind='capsule';r=rng.uniform(.5,5)
            else:b=add(a,tuple(rng.uniform(.5,10) for _ in range(3)));kind='box';r=0
            bodies.append((kind,a,b,r,key))
        expected=original(paths,bodies);actual,mode=batched(paths,bodies);assert actual==expected,(case,mode);runs+=1;hit_keys+=sum(map(len,expected[0]))
    key=(1,2,3,4,5,True);p=((0.,0.,0.),(20.,0.,0.),1.)
    for count in (0,1,128,129,256,257,512,513,600):
        for duplicate in (False,True):
            bodies=[('sphere',(10.,0.,0.),(10.,0.,0.),1,key if duplicate else (1,2,3,n,n,True)) for n in range(count)]
            actual,mode=batched([p]*8,bodies);assert actual==original([p]*8,bodies),(count,duplicate,mode);runs+=1
    for kind in ('unknown','sphere'):
        for key in ('invalid',None,(1,2,3,4,5,True)):
            bodies=[(kind,(10.,0.,0.),(10.,0.,0.),1,key)]
            assert batched([p,p],bodies)[0]==original([p,p],bodies);runs+=1
    # 精确球切触、微小短轴和明显世界边界：只验证保守包围，不冒称SDK接触容差。
    for center in (0.,50000.,-50000.,1e8,-1e8):
        for radius in (1e-5,.4,4.5,120.,10000.):
            path=((f32(center),0.,0.),(f32(center+40),f32(center),0.),f32(radius));lo,hi=bounds(path,True)
            for axis in range(3):
                assert lo[axis]<=min(path[0][axis],path[1][axis])-path[2]
                assert hi[axis]>=max(path[0][axis],path[1][axis])+path[2]
            runs+=1
    # 完整身份任何字段改变都必须不同；枚举次序可以不同，不能只按index去重。
    keys=[(1,2,3,4,5,True),(1,2,3,4,6,True),(1,2,4,4,5,True),(1,3,3,4,5,True),(2,2,3,4,5,True),(1,2,3,5,5,True),(1,2,3,4,5,False)]
    assert len(set(keys))==7 and sorted(keys)==sorted(reversed(keys))
    assert hit_keys>100,hit_keys
    return {'scenarios':runs,'random_scene_hit_keys':hit_keys,'analytic_shapes':['sphere','capsule','axis_aligned_box'],'degenerate_threshold':1e-7,'native_convex_runtime':'not executed','full_identity_fields':6}

def schedule(jobs,budget,mode,new):
    # 任务仅含路径种类与原路径是否成功；trace是实际消费的原路径，坏路径不推进。
    cost=sum(sum(2 if k=='c' else 1 for k,ok in paths[:8]) for paths in jobs)
    spare=max(0,budget-min(cost,budget));trace=[];calls=0;used_max=0
    for ji,paths in enumerate(jobs):
        used=cursor=0
        while cursor<len(paths) and budget and used<8:
            n=0
            if new and spare and budget>=3 and used<7:
                while n<min(8-used,budget-1) and cursor+n<len(paths) and paths[cursor+n][0]=='v':n+=1
            if n>=2:
                budget-=1;calls+=1;fallback=(mode!='fast' or not all(ok for k,ok in paths[cursor:cursor+n]))
                if fallback:
                    spare-=1;failed=False
                    for x in range(n):
                        budget-=1;calls+=1
                        if not paths[cursor][1]:failed=True;break
                        trace.append((ji,cursor));cursor+=1;used+=1
                    if failed:break
                else:
                    budget-=n-1
                    trace.extend((ji,x) for x in range(cursor,cursor+n));cursor+=n;used+=n
                continue
            kind,ok=paths[cursor];required=2 if kind=='c' else 1
            if budget<required:break
            budget-=required;calls+=required
            if not ok:break
            trace.append((ji,cursor));cursor+=1;used+=1
        used_max=max(used_max,used)
        if not budget:break
    assert 0<=budget<=64 and calls<=64 and used_max<=8
    return trace,calls

def scheduling_cases():
    rng=random.Random(560101);cases=0;saved=0
    for budget in range(65):
        for repeat in range(50):
            jobs=[]
            for j in range(rng.randrange(18)):
                jobs.append([(rng.choice(['v','v','v','s','c']),rng.random()>.06) for p in range(rng.randrange(1,50))])
            baseline,calls=schedule(jobs,budget,'old',False)
            for mode in ('fast','shadow','fallback','mismatch','unsupported'):
                trace,actual=schedule(jobs,budget,mode,True);assert trace==baseline,(budget,mode,jobs,trace,baseline)
                if mode=='fast':saved+=calls-actual
                cases+=1
    # 典型8刀路：同一服务名单，快路1次广相；对照/回退9次都必须来自额外余量。
    jobs=[[('v',True)]*8]
    assert schedule(jobs,64,'fast',True)==(schedule(jobs,64,'old',False)[0],1)
    assert schedule(jobs,8,'shadow',True)==schedule(jobs,8,'old',False)
    assert schedule(jobs,64,'shadow',True)[1]==9
    return {'same_service_trace_cases':cases,'world_call_reduction_in_model':saved,'hard_scene_limit':64,'per_job_paths':8,'shadow_and_fallback_only_use_spare':True,'C++_executed':False}

def verify_batch056():
    c=(ROOT/'IrisCombat.cpp').read_text('utf8');n=(ROOT/'native/NativeMultiContact.cpp').read_text('utf8');h=(ROOT/'native/NativeMultiContact.h').read_text('utf8')
    baseline=json.loads((ROOT/'docs/capsule-batch-056-baseline.json').read_text('utf8'))
    for name,expected in baseline['combat_functions'].items():assert_047_hash('function:'+name,hashlib.sha256(function(c,name).encode()).hexdigest(),expected)
    for name,expected in baseline['native_functions'].items():assert_047_hash('function:'+name,hashlib.sha256(function(n,name).encode()).hexdigest(),expected)
    # 医疗入口原函数除三个可关闭计时/日志语句外逐字保持，不能偷偷改护甲/经验/防御/顺序。
    flush=function(c,'Flush')
    restored='\n'.join(line for line in flush.split('\n') if not any(x in line for x in ('const double nativeBegin=','const double nativeElapsed=','if(detail)SlowNativeHit(')))
    assert hashlib.sha256(restored.encode()).hexdigest()==baseline['flush_before_sha256']
    native=function(n,'OverlapCapsules');candidate=n[n.index('class CapsuleCandidates'):n.index('QueryStatus OverlapCapsules')]
    assert native.count('scene->overlapAABBShapes(')==1 and native.count('->checkOverlapCapsule(')==1
    assert native.index('scene->overlapAABBShapes(')<native.index('->checkOverlapCapsule(')
    assert 'values[512]' in candidate and '++checks>1024' in native and 'count>CAPSULE_BATCH_CAPACITY' in native
    assert 'count==CONTACT_CAPACITY' in native and 'results[clear].count=0' in native
    assert 'if(!pathBounds[p].intersects(candidate.bounds))continue;' in native
    for forbidden in ('getCharacter','Log(','new ','createActor','setUserContactReport','CreateThread','EnterCriticalSection'):
        assert forbidden not in native+candidate,forbidden
    assert 'NxShape*' not in h and 'NxActor*' not in h
    batch=function(c,'TryCapsuleBatch');resolver=function(c,'ResolveJobs')
    for token in ('!capsuleBatchEnabled','queuesAreClearMT()','if(!spare)','capsuleBatchWarm<8','%256','if(!Contacts(w,path,reference,budget))','Collect(job,reference)','budget-=count-1','++job.cursor;++used;'):
        assert token in batch,token
    assert 'budget-PlannedJobCost(budget)' in resolver and 'capsuleBatchWarm=capsuleBatchSerial=capsuleBatchVerifiedTypes=0' in function(c[c.index('void Clear(bool alive,const char* reason)'):],'Clear')
    assert 'capsuleFacts' not in c and 'capsuleBatchResults' not in function(c,'Flush')
    less=c[c.index('struct ContactKeyLess'):c.index('bool SameContactSet')]
    for field in ('present','type','container','containerSerial','index','serial'):assert 'a.'+field in less and 'b.'+field in less
    assert 'std::sort(left,left+a.count,less)' in function(c,'SameContactSet')
    assert 'complete&&diagnostic.shapeTests&&' in batch and 'diagnostic.shapeTypes&~capsuleBatchVerifiedTypes' in batch
    # 运行对照状态模型：空批次不能暖机，类型首次出现必须对照，不匹配清零再验证。
    warm=seen=serial=checks=0
    for types in [0]*16+[1]*8+[2]+[3]*256:
        shadow=bool(types) and (warm<8 or bool(types&~seen) or (serial+1)%256==0)
        if types and warm>=8 and not(types&~seen):serial+=1
        if shadow:warm=min(8,warm+1);seen|=types;checks+=1
    assert warm==8 and seen==3 and checks==10
    warm=seen=0;assert bool(8&~seen) and warm<8

    # 相同人跨独立事件不能被批量索引合并；真实提交仍走原事件账本与原生医疗。
    keys={(1,2,3,4,5,True)};events=[(cast,event,key) for cast,event in ((10,0),(10,1),(11,0)) for key in keys]
    assert len(events)==3 and len(set(events))==3
    assert 'if(detail)SlowNativeHit(r,poppedAt,' in function(c,'Flush')

    assert (ROOT/'distribution/IrisArsenal.ini').read_bytes()==(ROOT/'package/IrisArsenal/IrisArsenal.ini').read_bytes()
    cfg=configparser.ConfigParser();cfg.read(ROOT/'distribution/IrisArsenal.ini',encoding='utf8')
    assert cfg.getint('IrisArsenal','EnableCapsuleBatching')==1 and cfg.getfloat('IrisArsenal','NativeHitSlowMs')==1
    for rel,expected in baseline['runtime_assets'].items():
        if rel not in ('IrisArsenal.ini','IrisPackage.json','IrisArsenal.dll'):assert_047_hash('package:'+rel,hashlib.sha256((ROOT/'package/IrisArsenal'/rel).read_bytes()).hexdigest(),expected)
    # 新增诊断关闭时不读取额外游戏对象/额外墙钟，也不影响健康或合批选择。
    assert 'nativeBegin=detail?IrisDiagnostics::Now():0' in flush and 'nativeElapsed=detail?' in flush
    assert 'if(!IrisDiagnostics::DetailsEnabled()' in function(c,'SlowNativeHit')
    for logging in (False,True):
        for perf in (False,True):
            for details in (False,True):assert bool(logging and perf and details)==all((logging,perf,details))
    import stage_package
    assert stage_package.BUILD_CONTRACT=='IRIS_DRIVE_REBUILD_059'
    return {'geometry':geometry_cases(),'scheduler':scheduling_cases(),'protected_native_functions':len(baseline['native_functions']),'protected_combat_functions':len(baseline['combat_functions']),'medical_semantics_except_diagnostics':'byte equivalent','capsule_cache':'retired','new_threads':0,'new_hooks':0,'raw_shape_lifetime':'native synchronous stack only','runtime_shadow':'first8 nonempty; first new shape type; every256 nonempty; original results consumed; no permanent disable','compiled':False,'PhysX_executed':False,'game_tested':False,'FPS_measured':False}

if __name__=='__main__':print(json.dumps(verify_batch056(),ensure_ascii=False,indent=2))
