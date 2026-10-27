# 088：高压局部预留与同窗同步远程提交

源码版本 **0.4.39 / IRIS_QUERY_BATCH_088**。本轮未编译、未部署，游戏实际仍为用户编译的0.4.38；正式版2.0封存不改写。

## 调用链与实际修改

| 路径 | 调用链 | 改动与约束 |
|---|---|---|
| 安全入口 | 原SafeHook → IrisCombat::Tick → AdvanceEffects / ResolveJobs → 原Flush | Tick、物理/AI/暂停门、读档Clear、原生医疗链逐token保持。没有新增Hook、线程、场景锁。 |
| 胶囊 | ResolveJobs → TryCapsuleBatch → OverlapCapsules → Collect → 原独立Hurt/FIFO | 去掉PlannedJobCost整轮预占，只有当前连续2～8条真实胶囊才判局部count+1。成功仍按count条逻辑路径收费，实际广相1次，不增加本帧采样量。 |
| 飞弹 | AdvanceEffects → PrepareShotBatch → RunRangedBatch → IrisNative::RangedBatch → 原逐发过滤/Blast | 最多8发本来即将访问的连续远程飞弹；不为凑批等下一帧，不跨越翻滚/零步长。完整有限地形射线先同步完成，再提交完整角色球扫掠，同窗结束后按原cast/event顺序消费。 |
| 光炮 | ResolveJobs → PrepareBeamBatch → RangedBatch → 原CylinderCollector → Collect | 只取队首连续、各剩一条圆柱路径的作业，攻击段各自独立。集中环境射线；角色仍调用原overlapOBBShapes(...,true)及原真实凸形体窄相位。 |

旧胶囊全局策略在逻辑预算用满64时spare=0，使高压恰好不能合批。本轮把恢复成本放在当前批内部：count≤budget−1，因此失败广相+count次参考查询也守住64。原参考查询中途失败仍只推进原成功前缀。**真实合批失败后，本次ResolveJobs余下路径走旧路，下次安全窗口重新允许**，防止同窗反复失败多花广相。成功无故障时保持原逐作业8路径及服务顺序；真实失败或显式影子测试会花额外预算，极限压力下后续路径可能依法留待下窗，绝不伪称这些情况也逐帧等价。

远程使用官方NxSceneQueryDesc/NX_SQE_SYNCHRONOUS及execute()/finish(true)，没有NX_SQE_ASYNCHRONOUS。SDK注明ALL_HITS扫掠返回数量恒0，因此仅消费原收集器的回调名单及状态。原TerrainRayCollector、Collector、CylinderCollector和共用排序/错误处理保留。SDK查询对象、报告、NxShape指针均只在同步调用栈内，先完成/释放查询对象，再析构报告及收集器。跨调用工作区只有插件自有结果和稳定身份值；未消费预取不跨安全窗口使用。

官方批量OBB接口没有accurateCollision=true参数，直接替换会引入精度差异；本轮明确保留光炮角色体积的原精确接口。原生弩箭飞行组0x087FDE47、完整球扫掠位移/半径、墙同距优先、原敌我资格、枪口/方向/射程/倍率/动作/特效均未改。

医疗维持配置2.5ms软预算、32次上限、FIFO和最终资格检查。未添加2ms查询软预算，仍使用原64查询硬界。

## 功能与诊断开关（重启生效）

| INI项 | 本地值 | 含义 |
|---|---:|---|
| EnableCapsuleBatching | 1 | 0恢复逐胶囊查询；1使用局部预留合批。 |
| EnableRangedQueryBatching | 1（新增） | 0回原逐条远程查询；1同窗集中提交。独立于日志开关。 |
| EnableCapsuleBatchShadow | 0 | 测试专用旧查询对照，保留默认关闭；开启确实增加工作与预算费用。 |
| EnableCollisionDetailProfiling | 1 | 新批量时序与本轮工作计数；设0关闭新增QPC、统计提交。 |
| EnableLogging / EnablePerformanceLogging / EnableCombatDetailLogging | 1 / 1 / 1 | 新诊断还需要这三个父开关。关闭总日志不会关闭优化。 |

distribution和package只加入新功能开关，个人既有键值不改；两份旧注释差异保留。真实游戏INI没有由本轮改写，用户组包更新后才得到新增配置。

## 日志应如何读

启动核对0.4.39和query_batch_ready / IRIS_QUERY_BATCH_088，以及战斗配置行ranged_batch=1。

| 通道/计数 | 用途 |
|---|---|
| capsule_batch_eligible / local_reservations / local_blocked | 真实连续胶囊机会、取得局部预留、仅因当前预算不足未批。旧no_headroom索引保留但不再用旧死门计数。 |
| capsule_batch_attempts / successes / saved_calls / fallbacks / extra_calls | 验证实际减少场景查询；失败日志window_batch_allowed=0表示仅本次服务停批。 |
| ranged_batch / create / rays / bodies / release | 批量总耗时和创建、同步射线、角色体积、释放子阶段。含SDK纯值回调，QPC墙钟并非纯CPU/GPU。 |
| ranged_batch_attempts / items / rays / sweeps / cylinders | 实际提交批数、各独立输入和实际角色查询量；零距离墙或射线失败不虚报角色查询。 |
| ranged_batch_unavailable / failures / unused | 尚未提交而走旧路、逐项失败、队列水位等提前结束导致未消费预取。unused不是漏伤害，原作业下窗重查；大于0时意味着有预取工作浪费，必须纳入收益评估。 |
| query_calls / query_job_age / damage_queue_age / query_retry | 原64硬界的实际查询命令、碰撞与医疗等待、失败重试，继续结合队列深度及最老等待检查。 |

批量对象每组在同窗创建/释放，成本被明确计入；不把接口替换当作已经更快。远程仍执行全部必要射线/角色检测，**集中提交不等于减少物理检测次数**。胶囊则真正减少广相调用。新的sweep/cylinder父计时一次可包含一批，跨版本不能直接比较每个Scope的平均耗时；应看父通道总耗时/单安全帧最大值及实际query_calls、ranged_batch_items等工作量。ranged_batch及其子阶段与父通道嵌套，不能重复相加。

## 已执行验证及边界

11,700组实际C++预留AST、2,700组实际预取AST、290组实际报告路由AST、7,800组飞弹调度规格对照、15,600组胶囊调度规格回放通过；覆盖0～64预算、零墙/零步长、删除/失败/奇数预算、回调分块和未知标签。无故障满负载64胶囊模型保持完整原路径顺序，实际场景查询64→9；这是离线模型，**不是实测FPS提升**。

91个未涉战斗函数、原过滤/Blast/位置消费片段、原失败重试循环、Tick/Clear/Flush、旧物理收集器和7条原SDK查询链逐token核对。14份C++/H语法树检查通过；仅在解析器输入中剥离MSVC属性和替代既有成员指针typedef，未修改产品声明，不能等同MSVC类型/链接检查。医疗7种重入/100目标FIFO、102目标预算及9代次规格通过。

新增计时80种实际AST开关组合通过，关闭路径新增QPC/Record为0。更新脚本沙盒20项通过/1项符号链接权限跳过；真实旧0.4.38 DLL被088门拒绝。游戏与工作包各135项静态哈希核验有效，工作包ready=false/pending0.4.39，保留真实旧DLL版本/哈希；游戏文件未改。

没有执行C++/HLSL编译、PhysX运行、游戏线程/画面/FPS实测。需要用户编译 **IrisArsenal.sln / Release|x64 / v100**，正常退出游戏后运行原UpdateMod.cmd。更新仍按既有简单清空/完整复制流程，不重新导出资源。压测先核对新版本身份，再比较相近招式次数、实际射程、query_calls、等待、fallback/unused及创建成本；若需要隔离远程收益，可只将EnableRangedQueryBatching设0做对照。

双备份：
- D:/CodexBackups/Task-Iris-QueryBatch088-20261024-114303-057567
- E:/AIWorkSpace/_backups/Task-Iris-QueryBatch088-20261024-114303-057567

逐文件/逐修订记录、原始对照和验证产物：D:/CodexWorkSpace/Sessions/20261002-235652-kenshi-crash-407794f2/Task-Iris-QueryBatch088-20261024-114303-057567。
