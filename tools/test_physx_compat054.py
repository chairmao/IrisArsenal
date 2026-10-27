"""054真实文件/版本门与旧DLL拒绝的非编译验证；不加载PhysX、不创建SDK、不启动游戏。"""
from pathlib import Path
import ctypes,hashlib,json,re,struct
from safeio import ROOT
from historical047 import assert_047_hash
from test_melee_block043 import function


def file_version(path):
    # 和生产入口同样读取实际Core的VS_FIXEDFILEINFO，不用安装包版本或文件夹名替代。
    api=ctypes.WinDLL('version',use_last_error=True)
    api.GetFileVersionInfoSizeW.argtypes=[ctypes.c_wchar_p,ctypes.POINTER(ctypes.c_ulong)];api.GetFileVersionInfoSizeW.restype=ctypes.c_ulong
    api.GetFileVersionInfoW.argtypes=[ctypes.c_wchar_p,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_void_p];api.GetFileVersionInfoW.restype=ctypes.c_int
    api.VerQueryValueW.argtypes=[ctypes.c_void_p,ctypes.c_wchar_p,ctypes.POINTER(ctypes.c_void_p),ctypes.POINTER(ctypes.c_uint)];api.VerQueryValueW.restype=ctypes.c_int
    ignored=ctypes.c_ulong();size=api.GetFileVersionInfoSizeW(str(path),ctypes.byref(ignored));assert 0<size<=1048576
    data=ctypes.create_string_buffer(size);assert api.GetFileVersionInfoW(str(path),0,size,data)
    value=ctypes.c_void_p();length=ctypes.c_uint();assert api.VerQueryValueW(data,'\\',ctypes.byref(value),ctypes.byref(length)) and length.value>=52
    info=struct.unpack('<13I',ctypes.string_at(value,52));assert info[0]==0xFEEF04BD
    return [info[2]>>16,info[2]&0xffff,info[3]>>16,info[3]&0xffff]


def pe_exports(path):
    # 只读PE导出表，不用LoadLibrary载入未知二进制，不执行所谓“无崩溃即兼容”探针。
    b=Path(path).read_bytes();u16=lambda p:struct.unpack_from('<H',b,p)[0];u32=lambda p:struct.unpack_from('<I',b,p)[0]
    pe=u32(0x3c);assert b[:2]==b'MZ' and b[pe:pe+4]==b'PE\0\0' and u16(pe+4)==0x8664
    opt=pe+24;assert u16(opt)==0x20b;section=opt+u16(pe+20)
    sections=[struct.unpack_from('<8sIIIIIIHHI',b,section+40*i) for i in range(u16(pe+6))]
    def offset(rva):
        for name,vsz,va,sz,ptr,*_ in sections:
            if va<=rva<va+max(vsz,sz):return ptr+rva-va
        raise AssertionError('RVA outside sections')
    def string(rva):
        start=offset(rva);return b[start:b.index(0,start)].decode('ascii')
    export=offset(u32(opt+112));count=u32(export+24);names=offset(u32(export+32))
    return [string(u32(names+4*i)) for i in range(count)]


def verify_physx054():
    native=(ROOT/'native/NativeMultiContact.cpp').read_text('utf8');baseline=json.loads((ROOT/'docs/physx-compat-054-baseline.json').read_text('utf8'))
    suffix=native[native.index('const char* AvailabilityReason()'):]
    digest=lambda b:hashlib.sha256(b).hexdigest()
    assert_047_hash('native_query_suffix',digest(suffix.encode()),baseline['query_suffix_sha256'])
    for rel,expected in baseline['unchanged_cpp_h'].items():assert_047_hash('root:'+rel,digest((ROOT/rel).read_bytes()),expected)
    # 用户编译/组包后DLL理应变化，不能把旧DLL哈希当作资源不变量；其他资产逐项保持。
    # 实际编译输出仍由stage_package.validate_dll检查PE、054合同和源码时间；不放宽部署入口。
    protected_assets={rel:value for rel,value in baseline['unchanged_package'].items() if rel!='IrisArsenal.dll'}
    for rel,expected in protected_assets.items():assert_047_hash('package:'+rel,digest((ROOT/'package/IrisArsenal'/rel).read_bytes()),expected)
    initialize=function(native,'Initialize');minimum=function(native,'AtLeastMinimum');gate=function(native,'RuntimeVersionGate')
    # 执行从实际C++抽取的纯整数布尔表达式，预期表独立指定；不把Python模型说成运行C++。
    expression=re.search(r'return\s+(.*?);',minimum,re.S).group(1)
    family=re.search(r'if\((v\.major!=.*?)\)return "runtime_sdk_family_not_supported";',gate).group(1)
    def evaluate(expr,version):
        for key,value in zip(('major','minor','bugfix','revision'),version):expr=expr.replace('v.'+key,str(value))
        assert not re.search(r'[^\d\s()>=<!&|]',expr),expr
        return bool(eval(expr.replace('&&',' and ').replace('||',' or '),{'__builtins__':{}},{}))
    def decision(version,export=True):
        if version is None:return 'runtime_version_unavailable'
        if not evaluate(expression,version):return 'runtime_below_minimum_2_8_4_6'
        if evaluate(family,version):return 'runtime_sdk_family_not_supported'
        if not export:return 'runtime_sdk_export_missing'
        return 'candidate'
    cases=[([2,8,4,6],True,'candidate'),([2,8,4,7],True,'candidate'),([2,8,4,100],True,'candidate'),([2,8,4,65535],True,'candidate'),([2,8,4,5],True,'runtime_below_minimum_2_8_4_6'),([2,8,4,0],True,'runtime_below_minimum_2_8_4_6'),([2,8,3,65535],True,'runtime_below_minimum_2_8_4_6'),([1,99,99,99],True,'runtime_below_minimum_2_8_4_6'),([2,8,5,0],True,'runtime_sdk_family_not_supported'),([2,9,0,0],True,'runtime_sdk_family_not_supported'),([3,0,0,0],True,'runtime_sdk_family_not_supported'),([5,6,0,0],True,'runtime_sdk_family_not_supported'),(None,True,'runtime_version_unavailable'),([2,8,4,7],False,'runtime_sdk_export_missing')]
    for version,export,expected in cases:assert decision(version,export)==expected,(version,export)
    assert 'if(!v.known)return "runtime_version_unavailable";' in gate
    assert initialize.index('if(!core||!loader)')<initialize.index('availability=-1') and 'if(availability)return availability>0;' in initialize
    assert initialize.index('RuntimeVersionGate(version)')<initialize.index('GetProcAddress(loader,"NxGetPhysicsSDK")')
    assert 'MAKELONG(6,4)' not in initialize and 'runtime_requires_2_8_4_6' not in native
    for token in ('IRIS_PHYSX_COMPAT_054','newer_patch_attempt','validation=file_version_and_export_only','runtime_verified=0'):assert token in native
    # 不因“尝试”增加SDK创建、场景写入、接触回调替换、SEH吞错误或后台轮询。
    for token in ('LoadLibrary','NxCreatePhysicsSDK(', 'setUserContactReport(', 'createActor(', 'getInternalVersion(', 'CreateThread(', 'Sleep('):assert token not in native,token
    assert native.count('if(&scene->getPhysicsSDK()!=sdk)')==5 and 'if(&scene->getPhysicsSDK()!=sdk)' in function(native,'OverlapCapsules')
    assert 'RequireFullSceneAPI' in native and 'RequireSweepHit64' in native and 'RequirePhysX284' in native
    actual=Path('D:/steam/steamapps/common/Kenshi');version=file_version(actual/'PhysXCore64.dll');exports=pe_exports(actual/'PhysXLoader64.dll')
    assert decision(version)=='candidate' and 'NxGetPhysicsSDK' in exports
    import stage_package
    assert stage_package.BUILD_CONTRACT=='IRIS_DRIVE_REBUILD_059'
    # 资源验收必须在编译前/后都可运行，不能断言本机编译输出一定是旧DLL。
    # 旧合同拒绝和新合同接受已由总验收中的test_melee_block043隔离用例覆盖；
    # UpdateMod进入重建前及stage_package组包前仍各自验证实际编译DLL，本专项不重复假定其状态。
    cfg=__import__('configparser').ConfigParser();cfg.read(ROOT/'distribution/IrisArsenal.ini',encoding='utf8')
    assert cfg.getfloat('IrisArsenal','DamageFlushBudgetMs')==2.5 and cfg.getint('IrisArsenal','DamageFlushMaxHits')==32
    return {'minimum':[2,8,4,6],'api_family':[2,8,4],'exact_revision_lock_removed':True,'version_and_export_cases':len(cases),'current_core_version':version,'current_loader_export_present':True,'query_suffix_unchanged':False,'query_suffix_delta':'055身份索引/窄相缓冲；Initialize版本门逐字保持','protected_cpp_h':len(baseline['unchanged_cpp_h']),'protected_assets':len(protected_assets),'old_new_DLL_gate_regression':'test_melee_block043.verify_block043; real build validated at UpdateMod/stage entry','callbacks_and_sdk_creation_added':False,'compiled':False,'C++_executed':False,'game_tested':False,'newer_patch_runtime_verified':False}

if __name__=='__main__':print(json.dumps(verify_physx054(),ensure_ascii=False,indent=2))
