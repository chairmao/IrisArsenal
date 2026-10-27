# 092 完整战斗接口归因与远程空区成本对照

2026-10-24。源码：0.4.43 / `IRIS_INTERFACE_PROBE_092`。**尚未编译或部署**。当前真实工作包及游戏 DLL 仍为用户已编译的 0.4.42 / 091；没有以旧 DLL 冒充新版本。

## 依据与范围

上一轮 091 双倍压力日志中，扣除首次可视创建后的统计口径包含：其他战斗处理 201.4117ms、物理 198.0037ms。远程批次的空区宽相累计 24.2772ms；但同一次运行没有关闭它的成本对照，不能用省掉扫掠次数直接证明净收益。旧 WorkTrace 只抽中 26 次，其中附件的一个慢样本占该抽样附件耗时约 91.3%，不足以认定附件是全部战斗余量的主要来源。

本轮先补全归因与成本实验，不凭这些稀疏样本删除功能或改调度。没有修改医疗、目标资格、倍率、范围、动画、特效、FCS、投射物数量或安全窗口；医疗仍 2.5ms / 32 次 / FIFO，物理仍 64 次硬预算。远程仍为地形射线、角色原有带半径精确查询。

## 调用链与计时边界

`SafeHook` 在原安全检查及原锁内，进入 `CombatInterfaceFrame → 原 Scope(COMBAT_TICK) → Tick → IrisCombat::Advance / AdvanceEffects / ResolveJobs`。只围住原来已经调用的函数，没有新增引擎 Hook 或执行线程。原 COMBAT_TICK Scope 将原有的起止时间借给完整接口根；结束时先封口，随后该 Scope 自己的 Record 和根汇总不混入已结束的父计时。

接口探针只在当前线程的固定栈结构内记录。线程局部槽只借当前根的地址，既不保存引擎指针，也不跨帧缓存查询结果。子接口结束时从本接口耗时扣除其子调用；根结束后用原诊断锁一次合计纯数值。原本 Add/Record/Log 的锁仍保持，其调用成本尽量标为 diagnostics；没有为每个新接口另加统计锁。读档或清理推进代次，失效根丢弃；同线程嵌套根不重复建立统计根；普通 C++ 异常通过 RAII 收尾。不声称已验证任意异步 SEH 或真实引擎线程行为。

输出 38 个分类（只输出本窗口实际出现的分类）：

| 范围 | channel |
| --- | --- |
| 根与编排 | root_unwrapped、wrapper、setup、tail |
| 演员 | actor_ready、actor_request、actor_animation、actor_pose、actor_finish |
| 武器和附件 | weapon_lookup、source_pose、attachments、trail、blade_paths、blade_ledger |
| 发射与爆炸 | emit、blast、beam_draw |
| 可视实例 | pool_borrow、pool_return、visual、visual_node、visual_parameters、visibility |
| 已产生的后效 | effects、shot_batch_prepare、shot_consume、shot_terminate、residues |
| 任务消费 | jobs、contact_gate、contact_collect、damage_enqueue、job_rotate |
| 扣除项 | physics、resource_lifecycle、prewarm、diagnostics |

`audit_combat_interface` 按原摘要窗口输出 window 和 process。`inclusive_ms` 包含子接口，**不可相加**；`exclusive_ms` 扣除子接口。同一根的所有 exclusive 加 root_unwrapped 闭合到原 COMBAT_TICK 的同一次起止。max_call_ms 是单接口包含子调用的最大值；exclusive_frame_max_ms 和 exclusive_p95_upper_ms 是根调用粒度的扣除子调用统计，后者是桶上界。

`root_unwrapped` 是仍未单独包裹的耗时，包含部分循环、分支和计时观察成本；它不是已确认的某个引擎 API。若余量仍大，下一轮再围绕其代码位置细分。总计是观察到的墙钟，不能冒充纯 CPU、GPU 或 FPS 测量。诊断开启本身也有成本；不能将拆分后某父项下降称为优化成功。

`combat_interface_slow` 默认根调用达到 2ms 才输出，首次 4 条、其后每 10 秒至多一条；带各 exclusive 和 partition_error_ms。完整摘要没有 N32 抽样，旧 091 抽样仍保留作兼容对照。若 invalid_roots、tls_failures 或明显 partition_error 出现，先核查探针完整性，再解释占比。

## 空区宽相对照

真实调用为 `PrepareShotBatch / PrepareBeamBatch → RunRangedBatch → 原 Native RangedBatch → 原顺序消费结果`。Native 只把原有批次、射线、体积、宽相 Scope 的起止差复制给本批纯值 audit，不额外取一对时钟，也不在 SDK 回调里写日志或取得新统计锁。

`audit_ranged_probe_cost` 分别输出 single_off、single_on、configured 三组：批数、输入数、球/柱数、命令数、复用、省掉扫掠、busy、unknown、失败、总耗时、射线/体积/宽相耗时，以及输入距离和半径总和。总耗时与子阶段重叠，不能重复相加。输入距离/半径用于检查两组负载差异，不能据此消除全部目标密度差异。

显式 A/B 开关只交替现有 `EnableRangedSingleEmptyProbe` 策略：相邻合格球扫掠批，一批关闭单条试探、一批开启。仍保留原多条空间分组省查。它要求原配置允许 single、空间/空区策略开启且本次 allowEmpty 有效；圆柱批、shadow 或不符合条件的批只按原配置观察。每批只运行一个策略，不做双份查询、参考重放或额外的旧路验证。两组查询仍计入同一原 64 次预算，因此不同查询工作量也可能改变后续队列机会，必须同时查看等待。

**相邻两批不是相同输入回放。** 当前只提供现场成本对照；同输入等价性由离线替身回放检查。若需要整个空区优化的开关对照，使用原 `EnableRangedEmptyPruning=0/1` 分别启动两次，并关闭 A/B；不能把 single_off 误称为全空区优化关闭。保留原 `EnableRangedEmptyShadow=0`，免得额外参考查询污染成本。

本轮尚无新 DLL 的实测 A/B 数据，因此没有声称哪类试探已被证实无收益，也没有猜测性删除它。下一轮优先比较两组每输入的 total_ms、probe_ms、bodies_ms、实际命令，以及查询/伤害等待；在输入规模、路径长度和场景差异可接受时，才决定关闭单条试探，或另行缩减确实不合算的策略。不能仅因 saved_sweeps 多就保留，也不能仅因 probe_ms 大就移除。

## 本地配置与测试

distribution 和 package 两份工作配置已显式开启下面三项；真实游戏目录未被直接修改，用户编译并更新后才生效。

```ini
EnableLogging=1
EnablePerformanceLogging=1
EnableCombatDetailLogging=1
EnableCombatInterfaceProfiling=1
CombatInterfaceSlowMs=2
EnableRangedProbeCostLogging=1
EnableRangedSingleProbeABTest=1
```

新三项程序缺省均为 0。全量接口归因独立于旧资源/碰撞子开关；关闭那些旧子开关不会把真实资源或物理成本误归给普通接口，但不会重新开启旧资源日志输出。成本监视也可独立于旧碰撞明细计时开启，仍依赖总日志/性能/战斗明细父门。

普通使用或测诊断关闭后的表现时，把三个 Enable 新项设 0。A/B 关闭后完全服从原 EnableRangedSingleEmptyProbe，不会私自继续交替。关闭新诊断的热路径不增加 QPC、TLS 访问、原子抽样或统计锁，也不初始化完整统计数组；仍有空探针分支和栈对象的固定开销，不能声称绝对零成本。新增摘要按原 LogSummarySeconds 输出，没有逐形体文件日志。

按技能编译边界，本次未编译。用户编译 `E:/KenshiProject/2.Projects/IrisArsenal/IrisArsenal.sln` 的 `Release|x64`、v100，退出游戏后执行原 `UpdateMod.cmd`。打包器要求真实 DLL 含 092 合同，旧 091 DLL 会明确拒绝；现有 manifest 保留真实 0.4.42 身份、ready=false、pending_version=0.4.43。

新运行先核对 `interface_probe_ready contract=IRIS_INTERFACE_PROBE_092` 及三个监视状态。尽量保持同一测试规模并包含预热后的战斗窗口；下一日志再给出阶段占比与试探净收益，不预先承诺 FPS 改善。

## 实际验证与边界

- 240 个既有战斗/Native 函数逐段对比，仅剥离本轮声明的观察代码和显式 A/B 策略选择；原调用约定、医疗/远程关键文件边界保持。
- 288 组实际计时树 AST 用例，包含 72 个同父计时闭合根、144 个关闭路径、嵌套/代次失效/异常退出/封口检查；38 分类及已有计时映射检查通过。
- 448 组实际策略选择 AST 门组合、16 组原 Scope 时钟复用/累加/关闭组合通过。
- 2498 批既有物理 AST 回归，另 560 组相同输入 single 开/关配对；命中消费结果一致，失败/未知/初始碰撞/别名及预算边界通过。用的是确定性 SDK 替身，不是真实 PhysX。
- 6000 个包络采样、480 组空间聚合、567 组可视生命周期用例及医疗 FIFO/重入/代次规格通过；14 份 C++/头语法单位和 Python AST 检查通过。语法工具不代替 MSVC 类型和链接检查。
- 更新器隔离沙盒 20 项通过，1 项因 Windows 链接权限跳过；新合同能正确拒绝当前旧 DLL。真实游戏目录、FCS、资产、已编译 DLL 的最终哈希另存本任务校验报告。

没有执行 MSVC/HLSL 编译、Windows 原生 TLS 并发、真实 PhysX、游戏运行或 FPS 测量。本轮未操作游戏进程、存档或工坊。

逐文件报告、验证数据与改前基线：
`D:/CodexWorkSpace/Sessions/20261002-235652-kenshi-crash-407794f2/Task-Iris-InterfaceProbe092-20261024-191745`。

双备份：`D:/CodexBackups/Task-Iris-InterfaceProbe092-20261024-191745`、`E:/AIWorkSpace/_backups/Task-Iris-InterfaceProbe092-20261024-191745`。原文件 UTF-8 无 BOM，原 CRLF/LF 保持，重要中文与乱码检查在写后及最终校验执行。
