"""057非编译验证：实际源码/官方SDK接口核对及独立命中、预算、失败规格。

Python解析模型不执行C++/PhysX，不代表游戏表现或FPS；现有游戏目录及DLL只读。
"""
from pathlib import Path
import hashlib,json,math,random,re
from safeio import ROOT
from test_melee_block043 import function

def sha(value):return hashlib.sha256(value).hexdigest()

def ordering_cases():
    # 分离查询的SDK返回次序任意；地形流式求最小，角色原扫掠排序后先排除友军。
    # 将源码实际比较条件抽成纯布尔表达式，独立oracle按几何时间及“墙同距优先”排序。
    source=function((ROOT/'IrisCombat.cpp').read_text('utf8'),'AdvanceEffects')
    expression=re.search(r'if\((!hit\|\|hits\.items\[k\]\.fraction<f)\)',source).group(1)
    expression=expression.replace('!hit','not hit').replace('||',' or ').replace('hits.items[k].fraction','contact')
    def implementation(walls,people):
        wall=None
        for t in walls:
            if wall is None or t<wall:wall=t
        hit=wall is not None;f=wall if hit else 1;who='wall' if hit else None
        for contact,kind in sorted(people):
            if kind in ('caster','player','ally'):continue
            if eval(expression,{'__builtins__':{}},dict(hit=hit,contact=contact,f=f)):hit=True;f=contact;who=kind
            break
        return who,f if hit else None
    def oracle(walls,people):
        all_hits=[(t,0,'wall') for t in walls]+[(t,1,k) for t,k in people if k not in ('caster','player','ally')]
        if not all_hits:return None,None
        first=min(all_hits);return first[2],first[0]
    examples=[([],[],(None,None)),([.5],[(.1,'ally'),(.8,'enemy')],('wall',.5)),
              ([.8],[(.1,'player'),(.3,'enemy')],('enemy',.3)),([.5],[(.5,'enemy')],('wall',.5)),
              ([.9,.2,.7],[(.3,'enemy')],('wall',.2)),([],[(0,'caster'),(0,'ally'),(0,'enemy')],('enemy',0)),
              ([],[(.2,'neutral'),(.4,'enemy')],('neutral',.2)),([1],[(1,'enemy')],('wall',1)),
              ([0],[(0,'enemy')],('wall',0)),([],[(1,'enemy')],('enemy',1))]
    for walls,people,expected in examples:assert implementation(walls,people)==expected
    rng=random.Random(570041);cases=len(examples)
    for _ in range(3000):
        walls=[rng.randrange(101)/100 for _ in range(rng.randrange(15))]
        # 相同TOI的角色身份不影响“墙优先”和所选最早TOI，避免同距人物随机次序被当成规范。
        people=[(rng.randrange(101)/100,rng.choice(('ally','player','caster','enemy','neutral'))) for _ in range(rng.randrange(50))]
        a=implementation(walls,people);b=oracle(walls,people)
        assert a==b,(walls,people,a,b);cases+=1
    # 世界形体流不受角色256容量限制；独立墙输出不挤掉完整角色名单。
    assert implementation([.99-i*.0001 for i in range(2000)],[(.9,'enemy')])[0]=='wall'
    people=[(i/512,'ally') for i in range(255)]+[(.8,'enemy')]
    assert len(people)==256 and implementation([.9],people)==('enemy',.8)
    return {'ordering_cases':cases,'terrain_stream_shapes':2000,'character_capacity_preserved':256,'tie':'wall first','neutral_blocker_rule':'preserved; health still enemy only'}

def geometry_cases():
    # 水平路径(0,h,0)→(100,h,0)：地形地面不随角色球半径膨胀；角色球连续TOI解析解。
    def sweep_t(center,body_radius,r=4.5):
        x,y,z=center;d2=y*y+z*z;radius=r+body_radius
        if d2>radius*radius:return None
        a=(x-math.sqrt(max(0,radius*radius-d2)))/100
        b=(x+math.sqrt(max(0,radius*radius-d2)))/100
        return max(0,a) if b>=0 and a<=1 else None
    assert 2<4.5 # 球外缘原本擦地，但水平中心射线高2，不与y=0地面相交。
    assert sweep_t((50,4,0),.5) is not None and sweep_t((50,5.1,0),.5) is None
    assert sweep_t((50,0,0),.5)==.45 and sweep_t((0,0,0),.5)==0
    assert sweep_t((110,0,0),.5) is None
    # 低帧率跨越整个人物仍命中；不是只在本帧终点做球重叠。
    assert sweep_t((50,0,0),.5)<1 and abs(100-50)>5
    # 原光炮平端柱体只改变墙截断长度；圆柱不向墙后延长成胶囊。
    def cylinder_point(x,y,z,length=40,r=4.5):return 0<=x<=length and y*y+z*z<=r*r
    assert cylinder_point(39,4,0) and not cylinder_point(41,0,0)
    assert not cylinder_point(40.01,0,0) and not cylinder_point(20,4.6,0)
    return {'continuous_ball_analytic_cases':7,'flat_cylinder_cases':4,'grazing_ground':'ray axis only','radius':4.5,'models_execute_PhysX':False}

def budget_failure_cases():
    # 一条飞弹的有限中心射线和球扫掠必须有两次预算；失败只记已实际调用的次数。
    def update(budget,ray=True,sweep=True):
        pending=1;pos=0;contacts=[];terrain=[];calls=0;retries=0
        if budget<2:return pos,pending,calls,retries,contacts,terrain
        calls+=1
        if not ray:return pos,pending,calls,retries+1,contacts,terrain
        terrain=[.8];calls+=1
        if not sweep:return pos,pending,calls,retries+1,[],[]
        contacts=[.4];pos=40;pending=0
        return pos,pending,calls,retries,contacts,terrain
    for b in (0,1):assert update(b)==(0,1,0,0,[],[])
    assert update(2,False)==(0,1,1,1,[],[]) and update(2,True,False)==(0,1,2,1,[],[])
    assert update(2)==(40,0,2,0,[.4],[.8])
    assert update(2,True,False)[:2]==update(1)[:2] # 重试保留原位置与未消费游戏秒。
    cursor=0;served=[0]*64
    for _ in range(8):
        budget=48;visits=64
        while visits and budget:
            visits-=1
            if budget<2:cursor+=1;continue
            served[cursor%64]+=1;cursor+=1;budget-=2
        assert budget==0
    assert min(served)==max(served)==3
    return {'atomic_failure_cases':6,'shots':64,'all_shots_served_after_8_windows':3,'job_scene_budget_reserved':16,'hard_total_limit':64,'wall_clock_time_budget_added':False}

def verify_ranged057():
    c=(ROOT/'IrisCombat.cpp').read_text('utf8');n=(ROOT/'native/NativeMultiContact.cpp').read_text('utf8');h=(ROOT/'native/NativeMultiContact.h').read_text('utf8')
    ray=function(n,'RayBlocker');pair=function(n,'ProjectileAll');column=function(n,'CylinderAll');contacts=function(c,'Contacts');advance=function(c,'AdvanceEffects')
    collector=n[n.index('class TerrainRayCollector'):n.index('static QueryStatus RayBlocker')]
    assert ray.count('scene->raycastAllShapes(')==1 and 'groups,length,NX_RAYCAST_SHAPE|NX_RAYCAST_DISTANCE' in ray
    assert 'travel/length' in ray and 'if(&scene->getPhysicsSDK()!=sdk)' in ray
    assert 'if(key.present&&key.type==unsigned(CHARACTER))return true;' in collector
    assert 'fraction<output.items[0].fraction' in collector and 'CONTACT_CAPACITY' not in collector
    for name in ('NX_RAYCAST_SHAPE','NX_RAYCAST_DISTANCE','Finite(hit.distance)','hit.distance<0'):assert name in collector
    assert 'RayBlocker(world,from,motion,groups,terrain,queryCalls)' in pair
    assert 'SweepAll(world,from,motion,radius,groups,characters,swept,true)' in pair
    assert 'characters.count=terrain.count=0' in pair and pair.index('if(status!=QUERY_COMPLETE)return status')<pair.index('SweepAll(')
    assert 'RayBlocker(world,from,motion,groups,obstruction,queryCalls)' in column and 'SweepAll(' not in column
    assert 'box.extents.set(radius,radius,actualLength*.5f)' in column and 'actualLength=length*limit' in column
    assert '(path.cylinder||terrain)?2U:1U' in contacts and 'ProjectileAll(' in contacts
    assert contacts.index('queuesAreClearMT()')<contacts.index('ProjectileAll(')
    assert advance.index('if(budget<required)')<advance.index('Contacts(w,Path(')
    assert 'const bool split=RangedMove(s.move)' in advance and 'terrain.count=0;' in advance
    assert 'hits,budget,0,split?&terrain:0)' in advance and 'if(!hit||hits.items[k].fraction<f)' in advance
    assert advance.index('IgnoreRangedContact(caster,c)')<advance.index('if(!hit||hits.items[k].fraction<f)')
    assert 's.pos=end;s.travel+=step;s.pending=' in advance and 'step*f' in advance
    assert 'NxShape*' not in h and 'NxActor*' not in h
    for forbidden in ('CreateThread(', 'EnterCriticalSection(', 'setUserContactReport(', 'createActor(', 'getCharacter(', 'Log('):assert forbidden not in ray+pair+collector,forbidden
    assert 'return i==5||i==6||i==7;' in function(c,'RangedMove')
    baseline=json.loads((ROOT/'docs/ranged-ray-057-baseline.json').read_text('utf8'))
    changed={'Contacts','AdvanceEffects','Configure'}
    preserved=0
    for name,before in baseline['functions']['IrisCombat.cpp'].items():
        if name not in changed:
            from historical047 import assert_047_hash
            assert_047_hash('function:'+name,sha(function(c,name).encode()),before);preserved+=1
    # 全部非DLL素材/配置/动画/FCS字节保持；用户可编译替换DLL，实际PE/合同/时间门另验。
    for rel,before in baseline['runtime'].items():
        if rel not in ('IrisPackage.json','IrisArsenal.dll'):assert_047_hash('package:'+rel,sha((ROOT/'package/IrisArsenal'/rel).read_bytes()),before)
    sdk=(ROOT/'native/physx284/SDKs/Physics/include/NxScene.h').read_text()
    assert re.search(r'raycastAllShapes\s*\(const NxRay& worldRay, NxUserRaycastReport& report',sdk)
    import stage_package
    assert stage_package.BUILD_CONTRACT=='IRIS_DRIVE_REBUILD_059'
    assert 'IRIS_RANGED_RAY_057' in function(c,'Configure') or 'IRIS_RANGED_RAY_057' in c
    return {'version':'0.4.16','code_contract':stage_package.BUILD_CONTRACT,'ordering':ordering_cases(),'geometry':geometry_cases(),'budget_failure':budget_failure_cases(),'preserved_combat_functions':preserved,'preserved_package_files':len(baseline['runtime'])-2,'new_threads':0,'new_hooks':0,'shape_pointer_lifetime':'native synchronous stack only','compile':False,'C++_executed':False,'PhysX_executed':False,'game_tested':False,'FPS_measured':False}

if __name__=='__main__':print(json.dumps(verify_ranged057(),ensure_ascii=False,indent=2))
