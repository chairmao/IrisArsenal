# 084优化第一轮：原生受击归因与服务机会

2026-10-24。源码版本0.4.35 / IRIS_NATIVE_PROFILE_084，**待用户编译**。实际bin/package/游戏仍是正式版2.0的0.4.34 / IRIS_MEDICAL_GATE_083，不改任何现有DLL或真实游戏配置。本轮完成计划第2～4项诊断，暂不修改伤害调度和碰撞算法。

## 对照原生后作出的选择

只读核对当前kenshi_x64.exe、KenshiLib.dll与真实Steam_1.0.65.br的槽位映射。七个实际函数已重取指令并保存，二进制身份与此前队列生命周期取证相同。SDK的签名也与实际调用参数交叉核对，不使用头注释RVA。

`Character::_NV_hitByMeleeAttack`现有桥接所进入的原生主体包含：防御判断 → rememberCharacter → addWound → AI/关系/对话等通知 → 受击特效 → 经验 → 反应 → 声音 → 攻击者punchSomething反馈。不同结果分支会跳过部分步骤；这不是每一击固定都执行全部步骤。因此不删这些工作，不另写医疗，不把它们放到后台，不把多段伤害合并。

当前这份`_NV_mainLoop_GPUSensitiveStuff`的函数体直接调用charsUpdateUT一次。它没有证明同帧还有可用服务机会，因此保留updateDone/每帧一次门。新增观察只核查运行时其他调用是否出现及当时状态，观察结果不能当作下一笔可复用的许可。

查询真实函数名是IrisCombat.cpp的`Contacts`，计划中旧称QueryReady只是误用的逻辑标签。查询端queuesAreClearMT仍保留；083医疗门已独立，仅在原生线程安全条件成立后逐笔消费稳定身份，本次不再改门。

## 实际调用链

1. startPlugin → IrisDiagnostics::Initialize → IrisNativeAudit::Configure。两个新开关程序缺省0，必须同时满足既有总日志/性能/明细开关才生效；QPC不可用导致性能关闭时也不安装新诊断Hook。
2. 既有InstallDefenceGate后调用IrisNativeAudit::Install。只在开启时通过KenshiLib映射安装`MedicalSystem::addWound`与`CombatClass::addEffect`两个诊断Hook。原防御和反应Hook仅增加PartScope，不新增行为Hook。
3. FrameHook → 原FrameScope（真实token独立于日志）→ 服务观察Frame → originalFrame → SafeHook先执行originalSafe → 核对原主线程/同世界 → 观察既有回调 → 原updateDone/Idle门 → 原Tick → 锁外原Flush。
4. Flush仍按2.5ms/32/FIFO处理；原生受击前创建Hit诊断上下文。四阶段Scope只在当前线程存在该上下文时采样。调用原函数的参数、引用、次数和返回值不变；普通角色不会进入诊断累计锁。
5. 每笔受击返回/异常展开后恢复TLS，提交固定内存统计；每次原Flush退出复用before/remaining/done/inspected等值记录服务情况。原游戏时钟、查询/命中/经验/结果处理不变。
6. 新摘要复用IrisDiagnostics::Summary及其完整结束标记，前缀独立，不改变旧audit_timing按帧的口径。Clear只推进诊断代数及重置间隔基点，进程累计仍保留。

## 新日志如何使用

| 日志 | 含义 | 注意 |
|---|---|---|
| native_profile_ready | 实际启用状态、两个Hook覆盖情况、TLS分配/安装结果 | hook=0时该阶段不能被认为没有耗时，余量仍会包含它 |
| audit_native_profile / native_call | 每笔原生根调用退出的固定桶及分位上界 | 包含异常退出，exception_exits单列；不是按帧p99 |
| 同上 defence/add_wound/reaction/add_effect | 每笔根调用内各阶段的inclusive/exclusive统计，零阶段也占一个根样本 | inclusive可嵌套，不能相加；独占量扣除子阶段，仍含探针/既有包装开销 |
| 同上 unattributed | 根耗时扣除已归属独占阶段后的余量 | 包含未探测AI/经验/声音/反馈/调度等，原因未确认，不伪称纯CPU |
| native_profile_slow | 首4个>=1ms根样本及之后每10秒至多一个带分项示例 | 所有调用仍入桶；既有native_hit_slow逐笔明细保留 |
| audit_service | 真实帧、回调、重复回调、当时积压/就绪观察、服务/进展/预算次数 | already_updated_ready_observations只观察，不额外Flush；队列状态不读取 |
| audit_service_timing | 积压时回调间隔、未清积压时服务进展间隔、回调/Flush墙钟、额外探测耗时 | 含暂停，帧回调含原生和嵌套，不是实际呈现帧时间/FPS |

统计使用16个毫秒上界桶；末桶输出-1表示无有限上界。常规摘要有window/process两套，按既有60秒配置输出；没有新日志线程或逐形体文件输出。TLS失败、读档失效、异常退出显式记录。

## 开关和性能边界

本地distribution及package已显式：

```ini
EnableNativeHitProfiling=1
EnableServiceOpportunityLogging=1
```

还需EnableLogging、EnablePerformanceLogging、EnableCombatDetailLogging为1；原六项本地日志仍全部为1。两新项程序缺省0，启动读取。设新项0可做相同战斗的诊断开关对照；关闭总日志/性能/明细也会关闭新诊断，启动时不分配其TLS/安装其新Hook。

关闭时新增高频观察在QPC/TLS/引擎getter前返回；仍存在轻量函数/布尔分支及纯值帧号推进，不能称完全零成本。开启时会有两个全局入口转发及TLS/计时/累计开销，旧native_damage外层也包含新统计提交开销，因此诊断开启/关闭的成绩不能直接混比成优化收益。

发布时在发布副本关闭诊断；不反写正式版2.0。没有执行资源预热/日志IO重构或特效重做。

## 安全与生命周期

- 没有新线程、全局移动锁、伤害重排或额外医疗调用。新Hook原样同步转发；PartScope中不拿共享锁进入原生。
- 聚合用既有插件互斥量；原生调用已返回后才拿锁提交统计。阶段只写当前线程的栈对象，不保存Character/NxShape/NxActor等引擎对象。
- TLS槽进程期保留、不在读档中释放。根调用内其他同线程重入归入当前子树，不创建重叠根样本，nested_roots_skipped标明；每层阶段RAII退出恢复前驱。
- Frame上下文同样在栈内；嵌套退出恢复父帧。Clear只变代数，尚在栈上的旧调用自然退出并被标记失效，不手动释放或重试。
- TLS读写与新增阶段诊断保存/恢复Win32 LastError。探针失败不授权任何动作，也不绕过原医疗/查询安全门。

## 实际已执行验证

- 当前二进制七函数只读取证；两个新Hook的真实符号/RVA/签名与原生调用位置确认。没有附加调试器或运行游戏。
- 101个原战斗函数：剥离明确列出的纯观察语句后逐token相同；完整Flush、原安全短路顺序、每帧一次、原游戏时钟均保持。
- 实际源码AST：1024医疗门组合、972诊断ready条件、349个单笔桶输入/7个分位条件、192个阶段析构条件、162个三态就绪条件、16个开关组合及4个关闭短路、64组原参数/引用/返回转发。
- 既有7种重入转换/FIFO规格，每种100目标；102目标慢调用/软预算、9组epoch表达式保持。TLS跨线程/嵌套/读档为独立模型，不冒充真实Windows线程执行。
- 保留081合批/异常/哈希冲突/密集目标规格；保留072原生选招732组AST用例。更新器隔离21项中20通过、1因系统无符号链接创建权限跳过。
- 12份C++/H语法树和Python AST检查通过。这不是MSVC编译、ABI执行、PhysX或GPU游戏实测，也没有测得FPS提升。
- 当前旧083 DLL被新084合同正确拒绝；工作包ready=false、pending_version=0.4.35，不能把旧DLL当成已优化产物。

详细验证、原生指令、双备份与逐文件即时报告：`D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-Iris-NativeProfile084-20261024-011541-440673`。每次改动前备份位于`D:/CodexBackups/Task-Iris-NativeProfile084-20261024-011541-440673`及`E:/AIWorkSpace/_backups/Task-Iris-NativeProfile084-20261024-011541-440673`，保留原UTF-8/BOM及换行，中文扫描通过。

## 下一步

用户编译`E:/KenshiProject/2.Projects/IrisArsenal/IrisArsenal.sln`，**Release|x64，v100**；正常退出游戏后执行原UpdateMod.cmd，再进行同场景测试。首先看native_call单笔p95/p99与四阶段独占占比、unattributed余量、积压服务间隔及重复就绪观察。

只有数据确认存在可消除冗余或额外安全机会后，才做下一轮实际调度/查询优化。同帧共享预算、独立攻击段、原生医疗语义与真实碰撞覆盖仍是约束，不能只照搬原生简短同步循环。
