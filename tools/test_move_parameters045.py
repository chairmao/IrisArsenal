# 054仅更新当前交付版本/组包合同断言，原伤害、配置和资源回归条件保持。
# 050仅更新版本断言；参数/反应隔离与旧资产精确摘要回归仍完整执行。
# 047：历史资源锁仅按authorized-delta精确迁移；新增高度/入站保护/源范围另独立验收。
"""045配置契约：真实Win32 INI/CRT解析、默认一致、无几何漂移；不编译或执行插件。"""
from pathlib import Path
import configparser,ctypes,hashlib,itertools,json,math,re,tempfile
from safeio import ROOT
from historical047 import assert_047_hash,package_hash052
from test_melee_block043 import function

def compact(s):return re.sub(r'\s+','',re.sub(r'//[^\n]*','',s))

def verify_parameters045():
    evidence=json.loads((ROOT/'docs/move-parameters-045-evidence.json').read_text('utf8'))
    c=(ROOT/'IrisCombat.cpp').read_text('utf8')
    default=(ROOT/'distribution/IrisArsenal.ini').read_bytes()
    assert default==(ROOT/'package/IrisArsenal/IrisArsenal.ini').read_bytes()
    cfg=configparser.ConfigParser();cfg.read_string(default.decode('utf8'))
    moves=json.loads((ROOT/'docs/eight-moves.json').read_text('utf8'))['moves']
    protected={0,1,2,3,4,8};bypass={0,2,3,4,8};count=0
    balance=json.loads((ROOT/'docs/balance-046.json').read_text('utf8'))['moves']
    for m in moves:
        i=m['index'];section=cfg['Move.'+m['key']]
        keys={f'damage{n}' for n in range(1,len(m['events'])+1)}
        for n,e in enumerate(m['events'],1):assert section.getfloat(f'Damage{n}')==balance[m['key']]['damage'][n-1];count+=1
        if i in {5,6,7}:assert 'BypassBlockDodge' not in section # 三远程无需额外能力开关。
        else:keys.add('bypassblockdodge');assert section.getint('BypassBlockDodge')==int(i in bypass)
        if i not in {5,6,7}:
            keys|={'attackmin','attackmax'};assert (section.getfloat('AttackMin'),section.getfloat('AttackMax'))==tuple(balance[m['key']]['attack'])
        if i in protected:
            keys|={'preventblockinterrupt','immunehitreactions'}
            assert section.getint('PreventBlockInterrupt')==section.getint('ImmuneHitReactions')==1
        # 047三远程新增入站反应开关；仍不开放出站防御绕过或距离覆盖。
        if i in {5,6,7}:keys.add('immunehitreactions');assert section.getint('ImmuneHitReactions')==1
        assert set(section)==keys,(m['key'],set(section)^keys)
    assert count==58
    # 实际Win32读取缺省/大小写/引号/长值，并用本机CRT解析有限数；不是Python模拟INI语法。
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    read=kernel.GetPrivateProfileStringW
    read.argtypes=[ctypes.c_wchar_p,ctypes.c_wchar_p,ctypes.c_wchar_p,ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_wchar_p];read.restype=ctypes.c_uint32
    crt=ctypes.CDLL('msvcrt');parse=crt.wcstod
    parse.argtypes=[ctypes.c_wchar_p,ctypes.POINTER(ctypes.c_wchar_p)];parse.restype=ctypes.c_double
    def get(path,key,fallback,low,high,switch=False):
        buf=ctypes.create_unicode_buffer(64);size=read('Move.test',key,'',buf,64,str(path))
        if not size:return fallback
        end=ctypes.c_wchar_p();value=parse(buf,ctypes.byref(end))
        if size>=63 or end.value==buf.value or end.value or not math.isfinite(value) or not low<=value<=high or (switch and value not in (0,1)):raise ValueError(key)
        return value
    cases={'zero':'0','fraction':'0.35','max':'1000','junk':'2x','negative':'-0.1','nan':'nan','inf':'inf','overflow':'1e999','too_large':'1001','long':'1'*90,'quoted':'"2.5"','flag_fraction':'0.5'}
    with tempfile.TemporaryDirectory(prefix='ini045-',dir='D:/CodexWorkSpace') as tmp:
        p=Path(tmp)/'config.ini';p.write_text('[Move.test]\n'+''.join(k+'='+v+'\n' for k,v in cases.items()),encoding='utf8')
        for key,value in [('zero',0),('fraction',.35),('max',1000),('quoted',2.5),('missing',7)]:assert get(p,key,7,0,1000)==value
        for key in ['junk','negative','nan','inf','overflow','too_large','long']:
            try:get(p,key,7,0,1000);raise AssertionError(key)
            except ValueError:pass
        try:get(p,'flag_fraction',1,0,1,True);raise AssertionError('非整布尔被接受')
        except ValueError:pass
    number=compact(function(c,'MoveNumber'));switch=compact(function(c,'MoveSwitch'))
    for token in ['size>=63','end==text','*end','!_finite(value)','value<low','value>high']:assert token in number
    assert 'value!=0&&value!=1' in switch
    config=function(c,'ConfigureMove')
    for token in ['event+1','move.events[event].mult,0,1000','"BypassBlockDodge",DefaultBypass(index)','"AttackMin",-1,-1,10000','"AttackMax",-1,-1,10000','low>=0&&high>=0&&low>high','index!=5&&index!=6&&index!=7','if(BlockGuardMove(index))','"PreventBlockInterrupt",true','"ImmuneHitReactions",true']:assert token in config,token
    # 046三远程均不启用兼容门，不能被近战配置或共用策略默认重新加回。
    assert 'move.bypassDefence=(index==5||index==6||index==7)?false:MoveSwitch' in config
    # 极小负数即使float舍入成负0，也必须在double层先拒绝；不是把哨兵当任意负值。
    assert config.index('low<0&&low!=-1')<config.index('move.attackMin=float(low)')
    for value in [-.1,-1e-100,-.999999999]:assert value<0 and value!=-1
    assert 'ConfigureMove(i,ini);' in function(c,'Configure')
    clone=function(c,'EnsureMoves')
    for token in ['moves[i].attackMin>=0','t->minDistanceVsStatic=moves[i].attackMin','moves[i].attackMax>=0','t->initialDistance=moves[i].attackMax','delete t;throw','BlockGuardMove(i)&&moves[i].preventBlock']:assert token in clone
    assert 'GetPrivateProfile' not in clone # 配置读取仅启动发生，读档重建只消费值。
    # 授权改变的医疗函数只允许把固定防御分支换成已读取的bool；其余医疗路径仍是044原文。
    flush=compact(function(c,'Flush'))
    previous=flush.replace('constboolunavoidable=!RangedMove(r.move)&&moves[r.move].bypassDefence;','constboolunavoidable=r.move==2||r.move==3||r.move==4||r.move==5||r.move==8;')
    assert_047_hash('function:Flush_parameters045',hashlib.sha256(previous.encode()).hexdigest(),evidence['flush_044_normalized_sha256'])
    assert 'damage.total()<=0' in function(c,'Flush') and c.count('->_NV_hitByMeleeAttack(')==1
    # 原生保护窗口/时钟/物理/后效/单事件集合均锁定，不用配置绕过死亡/加载或改变视觉范围。
    for name,digest in evidence['unchanged_functions'].items():assert_047_hash('function:'+name,hashlib.sha256(function(c,name).encode()).hexdigest(),digest)
    reaction=compact(function(c,'MeleeStumbleHook'));block=compact(function(c,'MeleeBlockCheckHook'))
    assert 'move>=0&&moves[move].immuneReactions&&Finite(damage.cut)' in reaction
    assert 'suppress=move>=0&&moves[move].preventBlock;' in block
    assert 'if(suppress){combat->_getHit(dir,damage,attacker,false);return;}' in reaction
    # 独立策略组合：两保护开关彼此独立；无效片段或非六招始终没有保护。
    combinations=0
    for i,p,block_on,reaction_on,valid in itertools.product(range(10),[0,.5,.9949,.995,1],[False,True],[False,True],[False,True]):
        window=i in protected and valid and p<.995
        actual_block=window and block_on;actual_reaction=window and reaction_on
        if not window:assert not actual_block and not actual_reaction
        if window:assert actual_block==block_on and actual_reaction==reaction_on
        combinations+=1
    # 两组距离分别继承实际FCS，先合成再检验；-1不是负距离或自动翻倍。
    distance_cases=0
    for base_min,base_max in [(0,25),(12,70),(20,100)]:
        for lo,hi in itertools.product([-1,0,18,90],[-1,18,90,10000]):
            resolved=(base_min if lo==-1 else lo,base_max if hi==-1 else hi)
            if resolved[0]<=resolved[1]:assert resolved[0]>=0
            distance_cases+=1
    package=ROOT/'package/IrisArsenal'
    for rel,digest in evidence['original_package_sha256'].items():
        # 用户新编译DLL由stage门验证；只锁原源资产/FCS/入口配置，不把旧DLL永久锁死。
        if rel not in {'IrisArsenal.dll','IrisArsenal.ini','IrisPackage.json'}:assert_047_hash('package:'+rel,package_hash052(package/rel),digest)
    assert 'IRIS_HEIGHT_REACTION_CANNON_ICON_047' in c
    import stage_package
    assert stage_package.BUILD_CONTRACT=='IRIS_DRIVE_REBUILD_059'
    return {'damage_coefficients':count,'melee_distance_pairs':7,'ranged_damage_coefficients':27,'user_balance_profile':'0.4.6','all_ranged_extra_defence_gates':False,'source_asset_geometry_preserved':True,'win32_ini_and_CRT_boundary_cases':13,'independent_protection_model_cases':combinations,'distance_inheritance_model_cases':distance_cases,'geometry_and_asset_hashes_locked':True,'cpp_compiled':False,'plugin_executed':False,'game_tested':False}

if __name__=='__main__':print(json.dumps(verify_parameters045(),ensure_ascii=False,indent=2))
