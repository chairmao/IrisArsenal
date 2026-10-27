"""077非编译回归：原生二进制证据、真实源码分组表达式、环境阻挡独立规格。

形体距离由规格输入，不执行PhysX；不可用此结果宣称原建筑场景已经实机修复。
"""
from pathlib import Path
import argparse,hashlib,itertools,json,random,re
from safeio import ROOT
from test_melee_block043 import function
from test_ranged_ray057 import ordering_cases,geometry_cases,budget_failure_cases

def main(evidence):
    n=(ROOT/'native/NativeMultiContact.cpp').read_text('utf8')
    c=(ROOT/'IrisCombat.cpp').read_text('utf8');h=(ROOT/'native/NativeMultiContact.h').read_text('utf8')
    value=re.search(r'NATIVE_BOLT_GROUPS=(0x[0-9a-fA-F]+)U;',n).group(1);mask=int(value,16)
    # 原生飞行与开火瞄准是两条链：逐条核对本轮重新提取的实际EXE指令，而非引用旧结论。
    identity=json.loads((evidence/'native-identity.json').read_text('utf8'))
    assert hashlib.sha256(Path('D:/steam/steamapps/common/Kenshi/kenshi_x64.exe').read_bytes()).hexdigest()==identity['exe_sha256']
    assert '00437E30: mov dword ptr [r11 + 0x78], '+hex(mask) in (evidence/'Harpoon-step.txt').read_text('utf8')
    assert '0043A680: mov r9d, '+hex(mask) in (evidence/'GunClass-shoot.txt').read_text('utf8')
    worker=(evidence/'ConstantTracer-worker.txt').read_text('utf8')
    for operation in ('mov eax, dword ptr [rbx + 0x78]','mov dword ptr [rsp + 0x20], eax','mov r8d, 3','call qword ptr [r10 + 0x380]'):assert operation in worker
    assert mask==int(identity['flight_mask'],16) and mask not in [int(v,16) for v in identity['aim_masks']]
    ray=function(n,'RayBlocker');pair=function(n,'ProjectileAll');cylinder=function(n,'CylinderAll')
    # 执行真实源码提取出的纯位运算表达式；oracle独立使用实际原生指令中的立即数。
    expression=re.search(r'const unsigned terrainGroups=([^;]+);',ray).group(1)
    assert expression=='groups&NATIVE_BOLT_GROUPS'
    def selected_groups(groups):return eval(expression,{'__builtins__':{}},{'groups':groups,'NATIVE_BOLT_GROUPS':mask})
    group_cases=0
    callers=[0xffffffff,0,mask,mask^0xffffffff]+[1<<i for i in range(32)]
    for caller,group in itertools.product(callers,range(32)):
        actual=bool(selected_groups(caller)&(1<<group))
        expected=bool(caller&(1<<group)) and bool(0x087fde47&(1<<group))
        assert actual==expected;group_cases+=1
    assert 'NX_ALL_SHAPES,terrainGroups,length,NX_RAYCAST_SHAPE|NX_RAYCAST_DISTANCE,0' in ray
    assert 'travel/length' in ray and ray.count('raycastAllShapes(')==1
    assert 'SweepAll(world,from,motion,radius,groups,characters,swept,true)' in pair
    assert 'overlapOBBShapes(box,NX_ALL_SHAPES,64,batch,&collector,groups,0,true)' in cylinder
    assert 'characters.count=terrain.count=0' in pair
    assert 'if(status!=QUERY_COMPLETE)return status' in pair
    collector=n[n.index('class TerrainRayCollector'):n.index('static QueryStatus RayBlocker')]
    assert 'if(key.present&&key.type==unsigned(CHARACTER))return true;' in collector
    assert 'if(hit.distance<0||' in collector and 'fraction<output.items[0].fraction' in collector
    assert 'terrain.distance=-1' in ray
    # 原生同组真实t=0仍阻挡；trigger仅为诊断值，不能额外猜一套原生没有的通用剔除。
    assert 'getFlag(NX_TRIGGER_ENABLE)?1U:0U' in collector
    assert collector.index('if(!output.count||fraction<')<collector.index('getFlag(NX_TRIGGER_ENABLE)')
    assert 'if(inspect)' in collector and 'IrisDiagnostics::DetailsEnabled()' in ray
    for forbidden in ('CreateThread(', 'EnterCriticalSection(', 'createActor(', 'getCharacter(', 'Log('):assert forbidden not in ray+collector+pair
    assert 'NxShape*' not in h and 'NxActor*' not in h
    assert 'characters.diagnostic.terrain=terrain.diagnostic.terrain' in pair
    assert 'empty.terrain=obstruction.diagnostic.terrain' in cylinder
    assert 'IRIS_NATIVE_TERRAIN_077' in c and 'actual_length=' in c
    assert 'split?terrain.diagnostic.terrain.groups:0U' in c # 翻滚不读未初始化环境诊断。
    def actual(shapes,caller=0xffffffff):
        # shape=(group,character,distance,trigger,SDK_ray_enabled)；距/形体本身由SDK事实提供。
        best=None
        for group,character,distance,trigger,enabled in shapes:
            if not enabled or not selected_groups(caller)&(1<<group):continue
            if character:continue
            if distance<0 or distance>1:continue
            if best is None or distance<best:best=distance
        return best
    def native_oracle(shapes,caller=0xffffffff):
        # 原生closestShape的环境部分，限制到本次完整有限移动区间；人物交给独立带半径查询。
        candidates=[s[2] for s in shapes if s[4] and not s[1] and caller&(1<<s[0]) and 0x087fde47&(1<<s[0]) and 0<=s[2]<=1]
        return min(candidates) if candidates else None
    allowed=[i for i in range(32) if mask&(1<<i)];excluded=[i for i in range(32) if not mask&(1<<i)]
    cases=0
    # 精确反例：原全组把起点辅助形体当阻挡；新组按原生忽略它，仍找到后面的真实墙。
    for bad,good,trigger,origin in itertools.product(excluded,allowed,(False,True),(0,.1)):
        scene=[(bad,False,origin,trigger,True),(good,False,.8,False,True)]
        assert min(s[2]for s in scene)==origin and actual(scene)==native_oracle(scene)==.8;cases+=1
    # 不能一律忽略t=0、建筑、trigger；只让原生分组/SDK事实决定环境有效性。
    for good,trigger in itertools.product(allowed,(False,True)):
        assert actual([(good,False,0,trigger,True)])==0;cases+=1
        assert actual([(good,False,0,trigger,False)]) is None;cases+=1
    rng=random.Random(770022)
    for _ in range(2500):
        shapes=[(rng.randrange(32),rng.choice((False,True)),rng.choice((0,.1,.5,.8,1,1.1)),rng.choice((False,True)),rng.choice((False,True)))for _ in range(rng.randrange(80))]
        rng.shuffle(shapes);caller=rng.choice(callers)
        assert actual(shapes,caller)==native_oracle(shapes,caller);cases+=1
    return {'native_exe_sha256':identity['exe_sha256'],'flight_mask':hex(mask),'native_group_bits':allowed,'group_matrix_cases':group_cases,
            'environment_closest_oracle_cases':cases,'extra_group_zero_hit_negative_control':True,'real_zero_hit_preserved':True,
            'legacy_ordering':ordering_cases(),'legacy_geometry':geometry_cases(),'legacy_budget_and_retry':budget_failure_cases(),
            'character_groups_and_radius_unchanged':True,'callback_has_no_new_game_calls':True,'details_off_skips_shape_metadata':True,
            'compiled':False,'PhysX_executed':False,'game_tested':False,'actual_building_shape_group':'unconfirmed; old log did not record it'}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--evidence',type=Path,required=True);a=p.parse_args()
    print(json.dumps(main(a.evidence),ensure_ascii=False,indent=2))
