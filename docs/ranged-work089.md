# 0.4.40 / IRIS_RANGED_WORK_089：减少远程物理查询实际工作

## 依据与范围

实际0.4.39/088高压日志的稳定两个摘要：安全更新1831.5011ms，其中物理1009.5479ms（55.12%），远程批量球扫掠666.2667ms（总安全更新36.38%，约物理66%）。这是CPU墙钟日志，不是FPS/GPU测量。088只同步提交，仍执行每条球扫掠，本轮针对它减少真实查询。原生受击2.5ms/32/FIFO及医疗、倍率、范围、姿态、动作、资源、FCS和正式版2.0均未改。

官方本机SDK：native/physx284/SDKs/Physics/include/NxScene.h:2592的overlapAABBShapes支持流式回调/全部静态动态形体；同文件:2772的场景linearCapsuleSweep没有候选缓存参数。NxActor的SweepCache不适用于这个接口。本轮没有创建额外actor、切换碰撞组或自行替代TOI求解。原生Harpoon有限中心射线与物理安全时序作为参照，089空区证明是本插件的优化，不声称原版也如此合批。

## 调用链

既有原生安全更新 → IrisCombat::UpdateDone → Tick → AdvanceEffects → PrepareShotBatch → RunRangedBatch → IrisNative::RangedBatch：

1. 完整输入验证；同批同场景/同groups的球扫掠按起点xyz、motion xyz、radius的float位及cylinder完整比较。最多8项线性比较，不分配哈希表。仅完全相同项建立待定leader；圆柱不共享。
2. 为独立项执行原完整有限地形射线，原生飞行组0x087FDE47与调用groups相交。t=0墙省查沿用080；非零墙不裁短角色球扫掠。
3. 至少3个独立可查球段且空间紧凑、预算足够时，用覆盖起点球和t<=1.001f完整轨迹的联合AABB执行一次宽相。双精度构造、外扩浮点余量，原真实查询的motion/radius不变。
4. **只有整个联合区域没有任何CHARACTER形体才省略这些球扫掠。** 回调流式只读完整身份，不分配候选名单、不读shape当前worldBounds、不留shape地址。不使用当前getter姿态逐路径剔除，避免SDK双缓冲与当前姿态混用。遇到角色、空形体、身份异常或不完整回调均执行原精确扫掠；没有额外形状白名单。
5. 可能接触角色的路径继续原linearCapsuleSweep + Collector + FinalizeSweep。起始重叠、完整TOI、排序、原地形同距优先、敌我/主动目标/昏迷过滤保持。
6. 原查询成功后，同参数项只引用本批较早的自有纯值结果，不复制/分配Contacts数组。原查询失败时不共享失败，别名逐条走原ProjectileAll，保留各自失败重试状态。
7. RangedValue把事实交还原逐发消费者；cast/event、命中去重及伤害入队各自独立。原ResolveJobs光炮圆柱精确链保持，只更新统一结果访问器。查询结束后仍由原Flush进行安全原生受击。

整个过程在原Tick主线程/互斥/物理可查窗口内同步执行；SDK查询报告、标签、收集器与owner沿用原栈内RAII完成/释放。没有新Hook、后台线程、场景锁或医疗后台调用。结果只用于当前预取批次，不跨帧复用；暂停/读档后不会消费旧批次。

## 预算、无收益与收益边界

实际宽相也扣64硬预算。尝试前预留整批原最坏查询数2*N+1；不够则直接原查询。联合AABB体积超过各路径包围盒体积之和时不试探，避免给散布弹体扩大搜索区。查询遇角色/异常无省查收益后，只在本次AdvanceEffects停止继续试探，下次安全更新恢复。

8条不同且联合区域无角色的球段，原8射线+8扫掠=16命令，089是8射线+1宽相=9命令；这是确定性命令数示例，不是实测耗时提升。8条完全相同查询可变为1射线+1扫掠，仍分别处理8个攻击事件。复用机会是否常见须看实际日志。

空区探测若遇角色会增加一次宽相，可能用掉后续路径的一次预算；不是承诺每次或每帧都加速，也不宣称与原同帧调度完全相同。所有未查路径仍保留pending/游标，原顺序与公平轮转不变。下一轮必须同时观察实际查询成本和排队等待，不能仅凭帧内耗时下降判断收益。

## INI（启动读取）

| 配置 | 本地工作包 | 含义 |
|---|---:|---|
| EnableRangedQueryBatching | 1 | 088同步批量总门；0回现有逐条查询 |
| EnableRangedQueryReuse | 1 | 本批完整相同成功查询只读复用 |
| EnableRangedEmptyPruning | 1 | 联合区域无角色证明后省球扫掠 |
| EnableRangedEmptyShadow | 0 | 测试专用；1仍运行原扫掠并消费原结果，验证候选空区结论 |
| EnableCollisionDetailProfiling | 1 | 089及087/088碰撞分段诊断门 |

关闭089功能可把Reuse与EmptyPruning设0，仍保留088同步查询。Shadow默认0，不自动做首批/周期对照。开启Shadow时，非空名单或参考查询失败都会记录shadow_mismatches并停本次更新后续试探；原结果仍原样消费。

新增诊断同时依赖EnableLogging、EnablePerformanceLogging、EnableCombatDetailLogging、EnableCollisionDetailProfiling。将EnableCollisionDetailProfiling=0可单独关闭本轮分段统计；EnableLogging=0关闭总日志。关闭后新增Scope不调用Now、不会进入新增统计锁；功能本身与原预算必需时钟仍运行。

## 日志判读

- ranged_reuse_lookup、ranged_empty_probe是原ranged_batch/sweep的子计时，不能与父耗时相加。
- ranged_exact_reuses、ranged_reuse_failures：成功少查和失败独立重查。实际射线/球扫掠命令由ranged_batch_rays / ranged_batch_sweeps记录，不把别名再次计为SDK工作；contacts仍是逻辑查询结果。
- ranged_empty_probes / saved_sweeps：额外宽相次数与实际省掉的球扫掠。净SDK命令节省约为2*exact_reuses + saved_sweeps - probes（别名失败不计成功reuse）；时间收益还须扣探测/查找成本。
- candidates / characters / unknown：实际扫描量、发现角色次数、无法证明为空次数。身份异常代码变化时单独留一条原路处理日志，其余汇总；无逐形体IO/时钟。
- busy / no_headroom / sparse / small / invalid / window_disabled：为什么没有省查。unknown不等于丢弃目标；它保留原扫掠。
- shadow_checks / shadow_mismatches：只在显式测试门下产生。必须与重试、命中次数、队列最老等待一起审阅。

## 实际验证与未验证

tools/test_ranged_work089.py解释实际C++输入、别名、宽相决策、提交、结果和失败分支，SDK为确定性替身；覆盖三维大坐标/边界包络、流式4097个形体、输入异常、原路重试、0..64预算、独立攻击与测试对照反例。168个既有函数token保持，AdvanceEffects/ResolveJobs原消费者除接口替换外完整token相同。医疗FIFO/重入/代次规格与14份C++/H语法树、Python AST检查通过。另运行隔离Update测试21项：20通过，1项符号链接权限不足跳过。

这些不是MSVC类型/链接检查，也不是真实PhysX或线程测试，没有新游戏性能数据。遵守技能不代编译；用户须编译IrisArsenal.sln / Release|x64 / v100，再正常退出游戏执行既有UpdateMod.cmd。编译前工作包ready=false/pending_version=0.4.40，保留真实0.4.39 DLL，089合同会明确拒绝旧DLL；没有自动部署。

本轮双备份：D:/CodexBackups/Task-Iris-RangedWork089-20261024-124808 与 E:/AIWorkSpace/_backups/Task-Iris-RangedWork089-20261024-124808，保留原路径/每次修订；UTF-8无BOM，C++/H保持CRLF，其余保持既有LF。会话任务目录保存逐文件报告、验证结果及运行产物哈希。
