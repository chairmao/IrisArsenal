# 090：空间分组空区省查与解除活动弹体上限

源码版本：0.4.41，合同：IRIS_SPATIAL_PROJECTILES_090。尚未编译、部署或进行游戏测试。
真实运行/已编译产物为0.4.40/089；game、package、bin DLL同SHA256 9bd97dd01831c600d174581b0ec9c60c0021ca3fdadf7e1eaa21422fed230370。

## 依据与本轮目标

前轮089日志的非预热窗口里，物理查询占安全更新独占统计约72.53%，远程球扫掠约54.30%；全批宽相实际两次都遇角色，省查0次。按实际扫掠数与回调数保守推算，至少73.75%的批量球扫掠未报告形体。工作负载的飞行总距离约为前轮2.08倍，不能以相近发射次数声称同压力、不能把CPU日志直接换算FPS。

因此本轮将同窗最多8项分成局部空区；一个有角色的小组不再阻止其他空组。独立组的宽相属于可关成本试验，是否更快需要测量，不声称命令少就必然提速。用户同时要求解除活动弹体数上限。

## 调用链与安全边界

SafeHook原生先执行 → 原主线程/物理/AI安全门 → IrisCombat::Tick → AdvanceEffects → PrepareShotBatch → RunRangedBatch → IrisNative::RangedBatch。

1. 输入仍按原弹体轮转顺序取最多8项；不对全局弹体重排，不合并cast/event伤害。
2. 原有限中心环境射线先按原生bolt groups同步完成；圆柱角色判定仍原精确OBB候选和窄相。
3. 对可用的球扫掠纯值构造完整AABB，覆盖起点球及原可接收t≤1.001f；双精度计算、向外余量后转float。
4. BuildRangedSpatialGroups在栈上最多8组，反复选择最紧凑一对；仅当联合体积≤两组体积和时合并。原paths、tags、slots和结果顺序不动。
5. ProbeRangedSpatial逐组调用原PhysX overlapAABBShapes，同scene/groups/安全窗口，流式64形体缓冲，不限制总候选数。组内没有任何角色且报告完整才省去该组球扫掠。
6. 有角色只让该组走原精确扫掠；坏身份/不完整报告停止后续试探，其余未证明路径仍原扫掠。极端包络不可用时只禁该项省查。显式shadow开启时，始终执行原扫掠并消费原结果。
7. 最坏原查询已占满预算则先短路，不做聚组计算。额外宽相连同原查询/失败别名恢复的最坏命令数先预留，只有实际证明可省的扫掠才抵扣后续试探。shadow不抵扣。原真实查询硬预算不突破。
8. RangedValue → 原最近有效接触消费 → Blast/命中作业 → ResolveJobs → 原逐段去重/资格 → Flush → 原生医疗。过滤、TOI、墙同距优先、完整飞行路径、瞄准/射程/倍率、2.5ms/32/FIFO均保持。

参考项目自带官方PhysX 2.8.4头：native/physx284/SDKs/Physics/include/NxScene.h:2561起说明AABB重叠和双缓冲。本轮不假定shape getter当前姿态等于查询快照，不自行按getter几何剔除，不缓存跨帧shape/actor指针。
未新增线程、Hook或场景锁；SDK query/report仍原栈内同步执行/finish/release。原主线程/安全窗口调用链未改。

## 三类限制区别

| 项目 | 旧行为 | 本轮 |
|---|---|---|
| 活动弹体数量 | shots.size()>=64拒绝发射 | 删除该门，vector按实际数量增长；仍受可用内存/引擎资源约束 |
| 活动可视合计 | shots+residues+pool达到96时可能借不到可视 | 删除该门，缺匹配闲置实例就正常创建 |
| 空闲实例缓存 | 原门混入活动数量 | 只保留最多96个已结束实例，多余的归还时销毁，不拒绝活动弹体 |
| 每次安全更新查询预算 | 碰撞作业与弹体共用64额度 | 保留；远程新宽相计入实际SDK命令，胶囊沿用原路径预算语义 |
| 未处理弹体 | 轮转保留pending游戏秒 | 保留；下次完整扫过待推进路径，不丢弹或截断范围 |
| 医疗伤害 | 2.5ms软预算、32次上限、FIFO | 保留，独立于64物理查询预算 |

Borrow只从闲置池复用或创建；Return先隐藏，闲置不足96才存入，否则释放。预热也走同一Return。
Emit临时可视在Draw或vector插入失败时释放再抛回原异常边界，成功仍沿用原按值所有权交接。
原碰撞任务256上限、伤害队列水位及演员追踪槽未变；它们不是活动弹体数门。碰撞任务满时爆炸依旧原逻辑保留该弹体重试，不能伪称所有下游队列也无限。

## 本地配置与诊断

修改后重启读取；distribution/package两份工作INI已同步，下列本地测试为1，真实游戏INI本轮不直接修改。

| INI | 本地值 / 缺项值 | 含义 |
|---|---|---|
| EnableRangedQueryBatching | 1 / 原值 | 原同窗批量提交，关闭回逐条 |
| EnableRangedEmptyPruning | 1 / 原值 | 0完全关闭空区证明；精确复用另有原开关 |
| EnableRangedSpatialPruning | 1 / 1 | 0回089全批联合包络策略 |
| EnableRangedSingleEmptyProbe | 1 / 0 | 成功组成的批内，单项组也试探；不是给批量以外单弹增加查询 |
| EnableRangedEmptyShadow | 0 / 0 | 测试开启后执行原扫掠验证空区结论；关闭不做额外对照 |
| EnableProjectileWorkLogging | 1 / 0 | 每弹自然命中/射程终止汇总一次；受总日志/性能/明细三个父门控制 |
| EnableCollisionDetailProfiling | 1 / 0 | 分组/宽相/体积/真实命令等窗口计时与计数，需父门 |

单项空组：1次宽相替代1次球扫掠，**总命令数相同**；有角色反而多1次宽相。需联合比较ranged_spatial_build、ranged_empty_probe、ranged_batch_bodies与整体查询/队列等待。下一轮若宽相成本超过省下的扫掠，先设EnableRangedSingleEmptyProbe=0对照，不先增大预算掩盖积压。

新增摘要：ranged_spatial_batches/groups/merges/pair_tests、single/multi_groups、covered_paths、skipped_singles、empty_singles/multis；保留原probe_calls/saved_sweeps/真实ray/body计数。另有projectile_spawns/vector_growth/unvisited_updates及idle_pool_trims。
逐弹projectile_work：cast/event/move、自然终止原因、尝试/空结果/等待、拥有的射线体积命令、观察到的预算让出/爆炸让出、游戏秒、行程、pending及峰值。
其中empty是**资格过滤前物理名单为空**，不是没打中敌人；共享宽相只进批次统计，不重复归摊各发。waits_without_command只是该次失败未发命令，不臆断physics_busy原因。读档/清理销毁未自然结束弹体时不会伪造自然终止日志。
关闭父日志门：新Scope不读QPC，逐弹不格式化/更新审计字段，无逐形体IO；仍有必要的普通分支及原安全链检查，不能声称零CPU开销。

## 实际验证与未验证范围

- 实际C++ AST解释：旧路1104批，新空间分组1394批，预算/失败别名恢复/墙/稀疏/部分有角色/显式shadow不一致/禁用。
- 包络6000采样、空间分组480组掩码与包含关系、流式超过64/512直到4097形体。
- 567个实际AST生命周期场景：最多4096模拟活动数不受64/96门，闲置只留96、Draw/入队失败释放、逐弹日志关闭首门返回。
- 174既有函数逐token保持；完整AdvanceEffects去掉纯审计后、Emit去掉上限/所有权保护后、WarmNext归还接口、PrepareShotBatch/ResolveJobs对照通过。
- 48父日志门场景，14C++/H语法单位通过；语法工具仅输入去除既有declspec及一个不支持成员指针typedef，不作为MSVC类型验证。
- 医疗独立规格：7重入、100 FIFO目标、102慢调用预算目标、9代次表达式；未执行原生医疗或游戏线程。
- Update隔离21项：20通过，1项创建符号链接因系统权限跳过；真实旧DLL被正确识别为缺090，未以其冒充本轮实现。
- 未编译、未真实PhysX/线程/游戏运行或FPS测量，无法承诺性能提升幅度；需用户编译IrisArsenal.sln / Release|x64 / v100后正常退出游戏再执行原UpdateMod.cmd。

正式版2.0、资源/FCS和瞄准、射程/倍率未修改。工作清单ready=false/pending0.4.41，保留真实0.4.40 DLL/hash，不伪造产物。备份在D:/CodexBackups/Task-Iris-Spatial090-20261024-153055及E:/AIWorkSpace/_backups/Task-Iris-Spatial090-20261024-153055，含原路径和各次修订；原UTF8/BOM/换行保持。
