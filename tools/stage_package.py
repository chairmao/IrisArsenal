# 059必须包含PA10肩持/源准星与R9枪口光流；旧058及更早DLL不能混用14类源曲线。
"""用户编译后仅组包到本项目；绝不编译或写游戏mod目录。"""
from pathlib import Path
import json,hashlib,struct,re
from safeio import ROOT,put
# 十招事件格式保持042，实际效果清单去掉未用heavy；新版代码/资源必须同包。
# 072：用户编译后才能部署原生近战资格/回退；日常Update仍只组包并复制既有构件。
MELEE_CONTRACT='IRIS_NATIVE_MELEE_072'
# 075多持有者独立起手必须来自新用户DLL，拒绝把旧串行实现当作修复已部署。
ACTOR_CONTRACT='IRIS_MULTI_ACTOR_075'
# 076不能以旧DLL冒充Hook预筛已部署；日常Update仍只组包/复制。
HOOK_CONTRACT='IRIS_HOOK_FAST_076'
# 077环境组修复须来自用户新编译DLL，仍只组包/复制，不调用编译器。
TERRAIN_CONTRACT='IRIS_NATIVE_TERRAIN_077'
# 078仅新增可关闭诊断，仍以实际用户DLL识别，不运行编译。
AUDIT_HOOK_CONTRACT='IRIS_HOOK_AUDIT_078'
# 079修复工作空手状态；仅识别用户产物，更新不编译。
EQUIPMENT_CONTRACT='IRIS_EQUIPMENT_STATE_079'
# 080只识别用户新编译产物；不以旧DLL冒充查询/可视优化。
PERFORMANCE_CONTRACT='IRIS_PERFORMANCE_080'
# 081新策略必须来自用户实际编译DLL，避免旧版自动对照仍运行却标成已修改。
CAPSULE_POLICY_CONTRACT='IRIS_CAPSULE_POLICY_081'
# 082阶段检测只认可用户新编译DLL，不用旧版混合physics_busy冒充已分项。
WINDOW_AUDIT_CONTRACT='IRIS_WINDOW_AUDIT_082'
# 083医疗门必须来自用户实际编译产物，不能将旧DLL标成已解除多余等待。
MEDICAL_GATE_CONTRACT='IRIS_MEDICAL_GATE_083'
# 084只接收用户编译的新单笔/服务机会诊断；关闭诊断时仍保留083实际战斗流程。
NATIVE_PROFILE_CONTRACT='IRIS_NATIVE_PROFILE_084'
# 085仅接受用户实际编译的伤口细分产物，Update仍只校验/复制，不代编译。
WOUND_PROFILE_CONTRACT='IRIS_WOUND_PROFILE_085'
# 086日常更新仍只复制实际用户产物；同时确认查询索引与医疗分支合同，不执行编译。
MEDICAL_BRANCH_CONTRACT='IRIS_MEDICAL_BRANCH_086'
SWEEP_INDEX_CONTRACT='IRIS_SWEEP_SHAPE_INDEX_086'
# 087完整消费链与诊断同合同；拒绝旧DLL混入新工作包，不改变迁移/资源重建流程。
CONTACT_WORK_CONTRACT='IRIS_CONTACT_WORK_087'
# 088同步批量与局部预留必须来自真实用户产物，不重做资源或代编译。
QUERY_BATCH_CONTRACT='IRIS_QUERY_BATCH_088'
# 089只接受真实用户编译的空区/完整查询复用产物，不生成或修改DLL身份。
RANGED_WORK_CONTRACT='IRIS_RANGED_WORK_089'
# 090解除活动弹体门与空间聚组必须来自用户真实编译，迁移脚本仍只复制。
SPATIAL_PROJECTILES_CONTRACT='IRIS_SPATIAL_PROJECTILES_090'
# 091新追踪与长度查找只能来自用户实际编译产物，更新脚本不编译。
WORK_TRACE_CONTRACT='IRIS_WORK_TRACE_091'
# 092全量归因/单段A-B监视必须来自用户真实编译产物，不代编译。
INTERFACE_PROBE_CONTRACT='IRIS_INTERFACE_PROBE_092'
# 093查询边界及两项精确优化需要真实用户DLL。
QUERY_BOUNDARY_CONTRACT='IRIS_QUERY_BOUNDARY_093'
# 094必须使用用户实际编译的保守映射实现，不能拿093旧DLL冒充。
CONSERVATIVE_QUERY_CONTRACT='IRIS_CONSERVATIVE_QUERY_094'
# 095必须来自真实用户新DLL；不能将现有094产物标为已含省工/同输入测试。
# 097旧扩盒内核已删除；实际新DLL必须带原生扇形合同，不能接收095/096旧产物。
NATIVE_SECTOR_CONTRACT='IRIS_NATIVE_SECTOR_097'
# 098用户新编译DLL与真实钻头包络配套；旧097不能标为已含本轮球查询。
DRILL_SPHERE_CONTRACT='IRIS_DRILL_SPHERE_098'
# 099必须来自用户真实编译的超龄积压追赶；不把旧098标为已含新消费者。
DAMAGE_CATCHUP_CONTRACT='IRIS_DAMAGE_CATCHUP_099'
# 100必须验证用户新DLL；旧099不能当作已含精细查询门。
QUERY_GATE_CONTRACT='IRIS_QUERY_GATE_100'
# 102新时序资产只接受已解绑弹速并反解原FX时钟的新DLL，不以100混用。
PROJECTILE_TIMELINE_CONTRACT='IRIS_PROJECTILE_TIMELINE_102'
# 103直接读取INI数值，不再设业务上下限；必须匹配用户新编译DLL，不能用旧102。
# 104人数与片尾合同：不允许旧103产物被标作此轮新实现。
HOLDER_TIMELINE_CONTRACT='IRIS_HOLDER_TIMELINE_104'
INI_VALUES_CONTRACT='IRIS_INI_DIRECT_103'
BUILD_CONTRACT='IRIS_DRIVE_REBUILD_059'
# 066的Shader消费实例custom9，旧DLL没有初始化/更新，必须明确拒绝混用。
RING_CONTRACT='IRIS_DRILL_RING_GATE_066'
BURST_CONTRACT='IRIS_BURST_CALIBRATION_068' # 独立爆炸需要游戏秒消费者，禁止旧DLL重复加速。
SOURCE_FX_CONTRACT='IRIS_THREE_SOURCE_FX_067' # 组合效果已烘焙时钟，需要配套消费者。
FINISHER_CONTRACT='IRIS_DRILL_FINISHER_064' # 烘焙时钟和源环体显示分支必须配同版DLL。
MUZZLE_CONTRACT='IRIS_SOURCE_MUZZLE_063' # 两份源准星/脉冲原火焰需要新版显示分支，旧DLL不能配新资源。
GATE_CONTRACT='IRIS_RANGED_GATE_062' # 用户编译产物需包含远程起手修复，不能用061旧DLL冒充。
POLICY_CONTRACT='IRIS_COMBAT_POLICY_061'
AIM_CONTRACT='IRIS_NATIVE_AIM_060' # DLL还必须包含实际共享瞄准实现，不能只满足旧059资源合同。

def validate_dll():
    # 先读PE和源码时间，拒绝旧产物；不加载DLL，不调用编译器。
    dll=ROOT.parent/'bin/Release/IrisArsenal.dll'
    if not dll.is_file():raise RuntimeError('找不到DLL，请先编译 IrisArsenal.sln / Release|x64 / v100')
    b=dll.read_bytes()
    if len(b)<64 or b[:2]!=b'MZ':raise RuntimeError('DLL不是有效PE文件')
    pe=struct.unpack_from('<I',b,0x3c)[0]
    if pe+24>len(b) or b[pe:pe+4]!=b'PE\0\0' or struct.unpack_from('<H',b,pe+4)[0]!=0x8664:
        raise RuntimeError('必须使用x64 DLL')
    doc=json.loads((ROOT/'docs/eight-moves.json').read_text('utf-8'))
    if doc['contract'].encode('ascii') not in b:raise RuntimeError('DLL与当前资源合同不一致，请重新编译 Release|x64 / v100')
    if HOLDER_TIMELINE_CONTRACT.encode('ascii') not in b:raise RuntimeError('DLL缺少104正式人数无限制与片尾审计，请编译 IrisArsenal.sln / Release|x64 / v100')
    if INI_VALUES_CONTRACT.encode('ascii') not in b:raise RuntimeError('DLL尚未支持INI直接读取（含20ms预算），请编译 IrisArsenal.sln / Release|x64 / v100 后重新更新')
    if PROJECTILE_TIMELINE_CONTRACT.encode('ascii') not in b:raise RuntimeError('DLL缺少102固定弹速与极致驱动分段时钟，请编译 IrisArsenal.sln / Release|x64 / v100')
    if BUILD_CONTRACT.encode('ascii') not in b:raise RuntimeError('DLL缺少059 极致驱动肩持/源准星/蓝火光流代码合同，请重新编译 Release|x64 / v100')
    if AIM_CONTRACT.encode('ascii') not in b:raise RuntimeError('DLL缺少060共享原生瞄准修复，请重新编译 IrisArsenal.sln / Release|x64 / v100')
    if POLICY_CONTRACT.encode('ascii') not in b:raise RuntimeError('DLL缺少061原生资格/实际弹道/直接命中修复，请重新编译 IrisArsenal.sln / Release|x64 / v100')
    if GATE_CONTRACT.encode('ascii') not in b:raise RuntimeError('DLL缺少062远程起手修复，请重新编译 IrisArsenal.sln / Release|x64 / v100')
    if BURST_CONTRACT.encode('ascii') not in b:raise RuntimeError('DLL缺少068独立爆炸游戏秒时钟，请编译 IrisArsenal.sln / Release|x64 / v100')
    if SOURCE_FX_CONTRACT.encode('ascii') not in b:raise RuntimeError('DLL缺少067三招源特效时钟，请编译 IrisArsenal.sln / Release|x64 / v100')
    if RING_CONTRACT.encode('ascii') not in b:raise RuntimeError('DLL缺少066圆环实例显隐修复，请重新编译 IrisArsenal.sln / Release|x64 / v100')
    if FINISHER_CONTRACT.encode('ascii') not in b:raise RuntimeError('DLL缺少064钻天破源爆炸/厚环时序，请重新编译 IrisArsenal.sln / Release|x64 / v100')
    if MUZZLE_CONTRACT.encode('ascii') not in b:raise RuntimeError('DLL缺少063源枪口特效修正，请重新编译 IrisArsenal.sln / Release|x64 / v100')
    if MELEE_CONTRACT.encode('ascii') not in b:raise RuntimeError('DLL缺少072原生近战资格与回退，请先编译 IrisArsenal.sln / Release|x64 / v100')
    if ACTOR_CONTRACT.encode('ascii') not in b:raise RuntimeError('DLL缺少075多持有者独立起手，请先编译 IrisArsenal.sln / Release|x64 / v100')
    if HOOK_CONTRACT.encode('ascii') not in b:raise RuntimeError('DLL缺少076通用Hook预筛，请先编译 IrisArsenal.sln / Release|x64 / v100')
    if TERRAIN_CONTRACT.encode('ascii') not in b:raise RuntimeError('DLL缺少077原生环境射线组修复，请先编译 IrisArsenal.sln / Release|x64 / v100')
    if AUDIT_HOOK_CONTRACT.encode('ascii') not in b:raise RuntimeError('DLL缺少078高频Hook抽样，请先编译 IrisArsenal.sln / Release|x64 / v100')
    if EQUIPMENT_CONTRACT.encode('ascii') not in b:raise RuntimeError('DLL缺少079实际手持/家具工作修复，请先编译 IrisArsenal.sln / Release|x64 / v100')
    if PERFORMANCE_CONTRACT.encode('ascii') not in b:raise RuntimeError('DLL缺少080同窗性能优化，请先编译 IrisArsenal.sln / Release|x64 / v100')
    if CAPSULE_POLICY_CONTRACT.encode('ascii') not in b:raise RuntimeError('DLL缺少081合批/可关对照修正，请先编译 IrisArsenal.sln / Release|x64 / v100')
    if WINDOW_AUDIT_CONTRACT.encode('ascii') not in b:raise RuntimeError('DLL缺少082安全窗口分项诊断，请先编译 IrisArsenal.sln / Release|x64 / v100')
    if MEDICAL_GATE_CONTRACT.encode('ascii') not in b:raise RuntimeError('DLL缺少083医疗安全门修复，请先编译 IrisArsenal.sln / Release|x64 / v100')
    if NATIVE_PROFILE_CONTRACT.encode('ascii') not in b:raise RuntimeError('DLL缺少084原生受击/服务机会诊断，请先编译 IrisArsenal.sln / Release|x64 / v100')
    if WOUND_PROFILE_CONTRACT.encode('ascii') not in b:raise RuntimeError('DLL缺少085伤口细分/原生对照诊断，请先编译 IrisArsenal.sln / Release|x64 / v100')
    if MEDICAL_BRANCH_CONTRACT.encode('ascii') not in b:raise RuntimeError('DLL缺少086医疗分支诊断，请先编译 IrisArsenal.sln / Release|x64 / v100')
    if SWEEP_INDEX_CONTRACT.encode('ascii') not in b:raise RuntimeError('DLL缺少086同步扫掠索引，请先编译 IrisArsenal.sln / Release|x64 / v100')
    if CONTACT_WORK_CONTRACT.encode('ascii') not in b:raise RuntimeError('DLL缺少087查询消费优化，请先编译 IrisArsenal.sln / Release|x64 / v100')
    if QUERY_BATCH_CONTRACT.encode('ascii') not in b:raise RuntimeError('DLL缺少088同步批量查询，请先编译 IrisArsenal.sln / Release|x64 / v100')
    if RANGED_WORK_CONTRACT.encode('ascii') not in b:raise RuntimeError('DLL缺少089远程查询省查，请先编译 IrisArsenal.sln / Release|x64 / v100')
    if SPATIAL_PROJECTILES_CONTRACT.encode('ascii') not in b:raise RuntimeError('DLL缺少090空间查询和无弹体上限，请先编译 IrisArsenal.sln / Release|x64 / v100')
    if WORK_TRACE_CONTRACT.encode('ascii') not in b:raise RuntimeError('DLL缺少091抽样阶段追踪，请先编译 IrisArsenal.sln / Release|x64 / v100')
    if INTERFACE_PROBE_CONTRACT.encode('ascii') not in b:raise RuntimeError('DLL缺少092全量接口和宽相成本监视，请先编译 IrisArsenal.sln / Release|x64 / v100')
    if QUERY_BOUNDARY_CONTRACT.encode('ascii') not in b:raise RuntimeError('DLL缺少093查询边界和实例精确复用，请先编译 IrisArsenal.sln / Release|x64 / v100')
    if CONSERVATIVE_QUERY_CONTRACT.encode('ascii') not in b:raise RuntimeError('DLL缺少094保守范围映射，请先编译 IrisArsenal.sln / Release|x64 / v100')
    if NATIVE_SECTOR_CONTRACT.encode('ascii') not in b:raise RuntimeError('DLL缺少097原生胶囊/动画增量扇形，请先编译 IrisArsenal.sln / Release|x64 / v100')
    if DRILL_SPHERE_CONTRACT.encode('ascii') not in b:raise RuntimeError('DLL缺少098钻头11段球查询，请先编译 IrisArsenal.sln / Release|x64 / v100')
    if DAMAGE_CATCHUP_CONTRACT.encode('ascii') not in b:raise RuntimeError('DLL缺少099超龄积压追赶，请先编译 IrisArsenal.sln / Release|x64 / v100')
    if QUERY_GATE_CONTRACT.encode('ascii') not in b:raise RuntimeError('DLL缺少100精细查询门，请先编译 IrisArsenal.sln / Release|x64 / v100')
    import drill_sphere098;drill_sphere098.validate()
    # 097核对轨道源哈希，防止手动换动画后仍带旧碰撞时序；无编译和骨骼重导出。
    import blade_pose097;blade_pose097.validate()
    # 102只读取序列化数据校验关键字段/时间键，不调用动画转换器或编译器。
    import projectile_drive102;projectile_drive102.validate()
    inputs=[ROOT/p for p in ('IrisArsenal.cpp','IrisCombat.cpp','IrisCombat.h','IrisRanged.cpp','IrisRanged.h','native/NativeMultiContact.cpp','native/NativeMultiContact.h','native/FiniteCylinder.h','native/SectorPlanes.h','native/DamageCatchup.h','native/IniValues.h','native/QueryGate.h','IrisArsenal.rc','IrisDiagnostics.cpp','IrisDiagnostics.h','IrisNativeAudit.cpp','IrisNativeAudit.h','IrisWoundAudit.cpp','IrisWoundAudit.h')]
    if dll.stat().st_mtime_ns<max(p.stat().st_mtime_ns for p in inputs):
        raise RuntimeError('DLL早于最新源码，请重新编译 IrisArsenal.sln / Release|x64 / v100')
    return dll,b

def main(run_checks=True):
    dll,b=validate_dll()
    # 开发验收可以单独执行全套历史回归；日常Update只检查待复制构件，不再审查历史C++函数摘要。
    # 不在日常更新时重新导出动画/特效，避免已确认资产被反复重建或旧断言拦截合法修改。
    if run_checks:
        import verify_prototype
        verify_prototype.main()
    else:
        out=ROOT/'package/IrisArsenal';assets=out/'assets'
        required=['IrisArsenal.mod','IrisArsenal.ini','RE_Kenshi.json','_IrisArsenal.info',
                  'assets/effects.csv','assets/effect_curves.csv','assets/drill.csv','assets/iris_weapon.mesh','assets/blade_poses097.csv']
        moves=json.loads((ROOT/'docs/eight-moves.json').read_text('utf8'))['moves']
        required += ['assets/iris_action_'+m['key']+'_'+sex+'.skeleton' for m in moves for sex in ('male','female')]
        for name in required:
            if not (out/name).is_file():raise RuntimeError('待复制模组包缺少构件：'+name+'；请单独执行rebuild_package.py恢复资源')
        # 轻量检查实际效果表和程序/材质引用的本包文件；不调用编译器或历史回归。
        texts=[assets/'effects.csv',*assets.glob('*.program'),*assets.glob('*.material')]
        for path in texts:
            for name in re.findall(r'(?<![\w/])([\w.-]+\.(?:mesh|skeleton|hlsl|dds|png))\b',path.read_text('utf-8-sig')):
                if not (assets/name).is_file():raise RuntimeError('待复制资源引用缺失：'+path.name+' -> '+name)
    # 工坊资料在清单计算前同步；只复制已有发布文件，保留既有条目身份，不重建资源。
    import workshop_assets
    workshop_assets.prepare()
    out=ROOT/'package/IrisArsenal';put(out/'IrisArsenal.dll',b,'用户编译DLL组包','仅复制已编译正确合同的x64产物到项目package，不部署游戏','实际游戏需用户测试')
    manifest={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*')) if p.is_file() and p.name!='IrisPackage.json'}
    # 058复用现有模型/特效/战斗配置，改变运行时视觉时钟/电脉轴；实际新DLL通过合同/源码时间门后才可标ready。
    # 材质资源可独立修订；先经源/像素/绑定检查，再在完整包中记录光学合同，不伪造新DLL版本。
    put(out/'IrisPackage.json',json.dumps({'version':'0.4.54','holder_timeline_contract':HOLDER_TIMELINE_CONTRACT,'ini_values_contract':INI_VALUES_CONTRACT,'projectile_timeline_contract':PROJECTILE_TIMELINE_CONTRACT,'query_gate_contract':QUERY_GATE_CONTRACT,'damage_catchup_contract':DAMAGE_CATCHUP_CONTRACT,'drill_sphere_contract':DRILL_SPHERE_CONTRACT,'conservative_query_contract':CONSERVATIVE_QUERY_CONTRACT,'native_sector_contract':NATIVE_SECTOR_CONTRACT,'query_boundary_contract':QUERY_BOUNDARY_CONTRACT,'interface_probe_contract':INTERFACE_PROBE_CONTRACT,'work_trace_contract':WORK_TRACE_CONTRACT,'spatial_projectiles_contract':SPATIAL_PROJECTILES_CONTRACT,'ranged_work_contract':RANGED_WORK_CONTRACT,'query_batch_contract':QUERY_BATCH_CONTRACT,'contact_work_contract':CONTACT_WORK_CONTRACT,'medical_branch_contract':MEDICAL_BRANCH_CONTRACT,'sweep_index_contract':SWEEP_INDEX_CONTRACT,'wound_profile_contract':WOUND_PROFILE_CONTRACT,'native_profile_contract':NATIVE_PROFILE_CONTRACT,'medical_gate_contract':MEDICAL_GATE_CONTRACT,'window_audit_contract':WINDOW_AUDIT_CONTRACT,'capsule_policy_contract':CAPSULE_POLICY_CONTRACT,'performance_contract':PERFORMANCE_CONTRACT,'equipment_contract':EQUIPMENT_CONTRACT,'hook_audit_contract':AUDIT_HOOK_CONTRACT,'terrain_contract':TERRAIN_CONTRACT,'hook_contract':HOOK_CONTRACT,'concurrency_contract':ACTOR_CONTRACT,'contract':'IRIS_EIGHT_042','ready':True,'asset_revision':'053-QueueFallingSun','code_contract':BUILD_CONTRACT,'aim_contract':AIM_CONTRACT,'policy_contract':POLICY_CONTRACT,'gate_contract':GATE_CONTRACT,'muzzle_contract':MUZZLE_CONTRACT,'finisher_contract':FINISHER_CONTRACT,'ring_contract':RING_CONTRACT,'source_fx_contract':SOURCE_FX_CONTRACT,'burst_contract':BURST_CONTRACT,'native_melee_contract':MELEE_CONTRACT,'visual_contract':'IRIS_SOURCE_BURST_069','roll_visual_contract':'IRIS_ROLL_SPHERE_073','cleanup_revision':'IRIS_RUNTIME_CLEANUP_070','retired_files':json.loads((ROOT/'docs/retired-runtime-052.json').read_text('utf8'))['files'],'asset_contract':['IRIS_DRILL_OPTICS_V1','IRIS_EIGHT_042','IRIS_FX_4','IRIS_FX_CURVES_1','IRIS_FX_CUES_1','IRIS_WING_CENTERS_1','IRIS_MUZZLE52_042'],'files':manifest},ensure_ascii=False,indent=2),'完整运行包校验','DLL和资源同包哈希，用于后续明确授权的游戏部署')
    print('已组包到 '+str(out)+'；没有修改游戏目录。')
if __name__=='__main__':main()
