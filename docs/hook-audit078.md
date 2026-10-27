# 078：十六个既有Hook的可关闭性能审计

源码目标 **0.4.29 / IRIS_HOOK_AUDIT_078**，同时包含077原生环境组修复和076预筛。当前游戏、用户bin及包内DLL仍0.4.26/075；未编译、未部署、未启动/停止/附加游戏。后续用户一次编译即可取得这三轮源码修改。

## 覆盖范围

| 日志hook名 | 原有入口/职责 |
|---|---|
| choose | ChooseHook，专用武器选招 |
| start / run | StartHook / RunHook，身体动作 |
| block / stumble | MeleeBlockCheckHook / MeleeStumbleHook，主动防御与受击反应 |
| defence | VulcanDefenceHook，原生受击防御桥接，保留现有TLS |
| frame / safe | FrameHook / SafeHook，原生帧入口与本模组安全更新 |
| ranged_use / ranged_has | UseHook / HasHook，角色及AI远程能力 |
| ranged_score / ranged_within | ScoreHook / WithinHook，远程评分和射程 |
| ranged_gun | GunHook，取得本枪适配器 |
| ranged_animation | AnimationHook，原生远程状态机的身体动画适配 |
| ranged_shot / ranged_reload | ShotHook / ReloadHook，射击许可和间隔 |

全部是已安装入口，没有增加任何Hook。RAII在回调入口创建，所有正常早退和C++异常展开均截止样本；16个入口剥除新增诊断后，实际业务token逐项与077备份相同。原生调用次数/参数、角色资格、武器身份、攻防结果、医疗、枪口和瞄准均保持。

## 采集、线程与开销边界

沿用EnableHookAuditLogging、EnableLogging、EnablePerformanceLogging，三项都为1才采集。程序没有INI项时仍默认关闭；本轮按用户测试要求把distribution及package两份INI的EnableHookAuditLogging显式改1，其他配置值保持。

- HookAuditSampleEvery=128：每入口按全部调用序号每128次抽样回调总墙钟；另按进入已有锁的回调序号每128次抽样获取锁和保护段。两套样本独立，不可用其总和互减。N范围仍1～65536，启动读取。
- 原五入口、Safe及八个远程Hook的现有临界区可传审计指针；没有增加一次实际锁获取，没有调整锁范围或带锁原生调用关系。
- 十六组64字节对齐的固定64位原子累计，不跨线程清零；摘要用累计差值。没有为统计分配TLS/堆、创建线程或取得Iris公共锁；原防御TLS保留。
- 单次回调只在选中的样本上取QPC，计数是原子累计；每次调用不格式化字符串、不写文件。每个既有摘要窗口输出32行（16入口×window/process），默认每60秒一次；读档/退出的既有强制摘要保留。
- 关闭Hook审计、总日志或性能采集时，新增审计不调用原子计数或QPC；新增本地对象和开关判断仍有极小指令成本，未做真实CPU开销基准，不声称实测零开销。
- 摘要沿用已有诊断锁和文件缓冲机制；本轮没有重构日志IO。开启审计本身仍有观测成本，测试结束可设EnableHookAuditLogging=0。

## 如何阅读audit_hook

- calls、calls_per_second：此窗口/进程实际入口次数及频率；elapsed_ms为墙钟并含暂停，暂停负载不应直接与正常战斗相比。
- fast_returns、locked_callbacks、lock_entries：未进入/进入“本次显式挂接审计的锁”的回调数和锁次数。fast_returns保留旧字段名，不等于该回调只用了原生，也不代表完全没有任何其他锁；frame/defence尤其如此。
- sampled_total_callbacks、callback_wall_ms_sampled：被选中样本的回调总墙钟，含原函数、嵌套Hook、可能的等待和本次计时调用费用。除以样本数得到样本平均；不能当全量CPU总和。
- sampled_no_audited_lock_callbacks、no_audited_lock_wall_ms_sampled：总样本中未进入所审计锁的一组，仍可能含原生耗时。
- sampled_locked_total_callbacks、locked_total_wall_ms_sampled：总样本中进过所审计锁的一组。
- sampled_callbacks、acquire_wall_ms_sampled、protected_wall_ms_sampled：另一套“每N次进锁”样本；获取锁墙钟包含获取操作本身，不等于全部是竞争等待；保护段含其内部调用。
- max_callback_ms_process、max_acquire_ms_process、max_protected_ms_process：相应样本的进程最大值；不是全量最高峰，也不是窗口最大值。

明确输出includes_original=1、total_and_lock_samples_independent=1、nested_timings_not_additive=1、FPS_measured=0。Hook父子会嵌套，因此不能把16入口耗时加起来当模组总耗时或20FPS损失。frame包含原生一帧执行，safe包含原生安全入口；原safe_tick/combat_tick、sweep/cylinder、native_damage和log_flush分项继续用于拆分本模组CPU来源。GPU特效开销、驱动等待及整游戏呈现FPS未测，不能用这些CPU日志排除。

## 构建与测试

1. 用户编译 `E:\KenshiProject\2.Projects\IrisArsenal\IrisArsenal.sln`，**Release|x64 / v100**。
2. 正常退出游戏，再执行项目UpdateMod.cmd；仍只组包并全量复制已有构件，脚本没有新增资源重建/编译步骤。
3. 新游戏日志应含0.4.29、`IRIS_NATIVE_TERRAIN_077`、`hook_audit_ready contract=IRIS_HOOK_AUDIT_078 hooks=16`。
4. 为便于分析，分别保持相近场景/敌人数，记录空闲、单持有者和三持有者战斗，最好每段超过一个60秒摘要窗口；记录画面FPS和大致操作时间。日志本身不测FPS。

如果测试后需要完全关闭日志，沿用原说明关闭EnableLogging；只关闭这轮Hook观测则将EnableHookAuditLogging改0，重启生效。配置及默认采样128已经准备好，无需为了本轮观测重新填写倍率或范围。

## 已执行验证

- 16个实际Hook业务token与077备份一致，原AddHook数量保持；所有原生参数/返回条件未变。
- 实际关闭路径AST的构造、析构、三个锁方法及摘要共6方法，不提供QPC/原子/锁函数仍通过；35组抽样边界规格通过。不是C++原子并发压力测试。
- 076选招/动作/保护分支、原生资格及多持有者条件继续通过；077重新提取的原生飞行组证据、1152组掩码/3580环境阻挡规格及原排序/预算/失败回归继续通过。
- 30个关键函数正文保持；077 NativeMultiContact及角色几何/物理/医疗链不变，264受保护文件保持。
- 10份C++/头语法解析及3份Python AST通过，未运行MSVC/链接/游戏。
- 129项待编译包SHA256匹配；21更新隔离用例20通过、1因系统符号链接权限跳过。真实旧075 DLL仍在076门被正确拒绝，没有冒充078。
- 两份INI逐值对比，只有EnableHookAuditLogging从0改1；编码/BOM/换行及中文检查通过。

任务产物与最终验证：`D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-Iris-HookAudit078-20261022-210234-8ec870`。验证文件validation078.json，逐文件即时报告在reports，最终报告file-change-reports-final078.md。

双备份：`D:\CodexBackups\Task-Iris-HookAudit078-20261022-210234-8ec870`、`E:\AIWorkSpace\_backups\Task-Iris-HookAudit078-20261022-210234-8ec870`，其下保留完整盘符和原路径；每次修订有独立备份，不覆盖原始记录。
