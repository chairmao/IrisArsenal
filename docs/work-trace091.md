# 091：轻负载优先的同次查找优化与抽样追踪

源码版本0.4.42 / IRIS_WORK_TRACE_091，待用户编译。未编译、未部署、未启动或附加游戏。
本轮实际核对bin及游戏DLL均为用户已编译0.4.41 / IRIS_SPATIAL_PROJECTILES_090，SHA256 ce9636559aaf4e5cd1ccc875f6110ab2f33b9148d95d55b15664b29c3677b28b。090文档中的“待编译”是当轮历史状态。

## 依据与范围

双倍压力090日志的安全更新1051.518ms包含首次资源创建681.0745ms；算术扣除首次创建后370.4435ms中，未细分战斗余量145.996ms（39.41%）、物理109.8921ms（29.67%）、外层原生受击63.5839ms（17.16%），其他医疗34.0003ms（9.18%）。
该样本没有独立的完整暖机活动窗口，不能把扣除后的结果称为稳态，更不能换算FPS。

原生根受击62.7807ms中的未归因26.5118ms，两个最长样本主要发生在已知伤口探针之外。既有本机原生链证据见docs/native-profile084.md：原生受击还包括关系/AI/经验/声音/攻击者反馈，分支并非每次全执行。不能猜某个入口冗余，不能跳过、缓存或重放原生医疗。
用户强调不能以极端压力处理拖慢轻负载。因此先做确知的同调用重复读取消除，再补可关、固定内存抽样；不增加常驻角色扫描、优先堆、后台线程或新引擎Hook。

## 实际功能优化

IrisCombat::Tick原来对每招先Loaded，再重复getAnimationState/getLength；Loaded内部还重复取长度。
现在AnimationLength在同次资格检查中保留hasAnimation，状态与长度各取一次，缺失/非有限/非正长度仍返回0；Loaded保留布尔接口。

对10招都已加载的单角色一次Tick，就绪部分的状态读取20次→10次、长度读取30次→10次。hasAnimation不变。
这是源码调用次数减少，不是实测CPU或FPS提升。不跨帧缓存，不跨startCombatAnimation/runCombatAnimation等原生更新复用状态，种族、义肢、武术回退与姿态条件不变。

## 调用链

SafeHook原生回调 → 原主线程/世界/物理/AI及每帧一次门 → 原锁内Tick → IrisCombat::Tick中的WorkTrace(COMBAT) → 原准备、角色、后效、作业、收尾顺序。
锁外原Flush → WorkTrace(MEDICAL) → 原逐笔安全门 → FIFO取值身份 → 资格 → 原伤害计算 → 一次_NV_hitByMeleeAttack → 原经验及结果。
原生Hit同步TLS上下文 → 既有四PartScope进出；新间隙跟踪复用其原有时间戳 → 原根返回后在既有统计锁中合计。

追踪不读游戏对象、不申请许可、不重试伤害。阶段Mark只操作当前调用栈；抽中调用结束后仅一次既有互斥量汇总。未增加锁对象或锁序，医疗仍不持插件锁进入原生。
2.5ms/32/FIFO、安全检查、游戏秒、射线地形/带半径角色碰撞、物理64预算、活动弹体无门、逐攻击段去重、范围/倍率/敌我过滤均保持。

## 新配置

两份工作INI（distribution和package）同步：

| 项 | 本地测试值 | 程序缺项值 | 作用 |
|---|---:|---:|---|
| EnableWorkPhaseProfiling | 1 | 0 | 抽样Tick/Flush互斥阶段 |
| EnableNativeGapProfiling | 1 | 0 | 抽样原生受击探针之间的未归因间隙 |
| WorkPhaseSampleEvery | 32 | 32 | 各域首次及每N次，整数1～65536 |

两组均还须EnableLogging、EnablePerformanceLogging、EnableCombatDetailLogging为1；原生间隙另须EnableNativeHitProfiling为1。
新项设0即可关闭本轮追踪，不关闭功能优化；父门关闭也不新采集。配置启动读取，修改后重启。
关闭路径只有标量初始化/布尔短路，仍有轻量函数调用和固定栈空间，不能称绝对零成本；无新增QPC、采样原子、统计锁、堆分配。
启用但未抽中时仅一个域采样原子及分支，Mark不读新时钟。原生间隙即使抽中也不增加QPC；只借现有根/PartScope时钟。
深查可短暂将N设1，但会增加计时和统计开销；周期抽样可能遗漏偶发慢样本，不能从抽样总量直接推算全量。
正式发布副本可将两新项设0。本轮未改真实游戏INI、发布副本、正式版2.0归档。

## 日志口径与后续判断

| 前缀 / channel | 说明 |
|---|---|
| work_trace_ready | 实际门/采样率/091合同；new_hooks=0 |
| audit_work_trace / combat.setup | 现有准备/预热，首次加载也可能在此 |
| combat.actor_ready | 身份就绪、动画长度、原点 |
| combat.actor_request | 原远程许可消费/原生start |
| combat.actor_animation | 当前原生动作状态、续播、生命周期 |
| combat.actor_pose / actor_visual | 真实武器姿态 / 附件与刀光 |
| combat.actor_path / actor_events | 刀路构建 / 事件发射和已有事件日志 |
| combat.actor_finish / effects / jobs / tail | 演员快照 / 弹体后效 / 作业和名单收集 / 原点及光炮刷新、统计 |
| audit_work_trace / medical.* | 逐笔安全门、短锁出队、等待统计、身份、计算、原生范围、经验、结果及原有明细 |
| audit_native_gap / before_* | 上一顶层已知探针退出到当前探针进入的空白；首个即根开始到探针 |
| audit_native_gap / after_last_part | 最后顶层探针退出到根结束；没有探针时为整个根 |
| native_profile_slow / gap_sampled | 沿原首4笔/10秒限频，只在已抽中时附gap0～gap4，不新加慢调用日志行 |

每个work样本的20个互斥阶段之和=该样本调用墙钟；重复进入同阶段先累加，continue/return/异常由栈退出收尾。total及分阶段是同一组样本，各阶段缺席的调用包含零值。
medical追踪覆盖原DamageQueueSnapshot析构的退出审计；该费用归于最后活动阶段。原生范围含原TLS/探针汇总；不与更窄的旧native_damage/root直接相加。
work p50/p95/p99是每次抽中调用的上界；不是旧audit_timing的全安全帧口径。只有同域、同样本、同配置才适合比较阶段占比。旧嵌套计时不可重复相加。
原生gap的5段只标时间位置，不确认具体callee；含其他插件、探针与线程调度。仅抽中根有效代次才累计，嵌套Part不重复切gap。抽中根的gap之和加已知Part独占量=根墙钟。
没有新增逐形体/每次Mark日志；只随原摘要输出window/process，原生慢样本沿原限频。没有FPS/GPU测量或新日志IO架构。

下一轮先查看actor_ready、actor_visual、effects、jobs和medical_result各自占比，区分动作/可视/名单/诊断成本；再结合原有物理子阶段和服务间隔。只有稳定重复出现的热点才作对应优化，不为偶发7ms改医疗语义。

## 已执行验证

- 109个原战斗函数：只剥离列明的纯观察声明/Mark与单独验证的长度替换后，全部原消费者逐token一致；原生入口、Ranged、Wound、物理实现6文件逐字不变。
- 80组真实AnimationLength/Loaded AST边界，覆盖空角色/动画缺失/状态缺失、零/负/非有限/有效长度。
- 1040组WorkTrace实际构造/Mark/析构AST，780关闭组合无新时钟/采样原子/锁路径；未抽中不取时钟，阶段和与总量一致。
- 480组实际PartScope AST顺序/重复/嵌套；1632组Hit构造开关/嵌套/TLS失败/采样检查，既有QPC数量保持。64组原Hook参数、引用身份和返回值转发。
- 原医疗7种重入/FIFO、100目标每种、102目标软预算、9组epoch规格保持。
- 090完整非编译回归：2498批实际AST、6000扫掠包络样本、480聚组、567实例生命周期、174原函数和48日志门通过。只剥本轮已独立验证的观察层，不改SDK替身算法。
- 14份C++/H语法树及Python AST通过；更新器隔离21项，20通过、1因系统无符号链接特权跳过。
- 真实0.4.41旧DLL被091合同正确拒绝；工作包ready=false、pending_version=0.4.42。原DLL、FCS、实际游戏部署文件保持。

这不是MSVC/ABI/PhysX/GPU/真实线程或游戏验收。尚无本轮FPS收益数据。
用户编译 E:/KenshiProject/2.Projects/IrisArsenal/IrisArsenal.sln，Release|x64 / v100；之后正常退出游戏再运行原UpdateMod.cmd。

## 文件安全

所有既有小文件改前在 D:/CodexBackups/Task-Iris-WorkTrace091-20261024-165024 与 E:/AIWorkSpace/_backups/Task-Iris-WorkTrace091-20261024-165024 双份唯一备份，重复修订另存revision目录，不覆盖。
UTF-8无BOM及原CRLF/LF保持，中文往返与乱码扫描通过；逐文件即时报告和所有测试产物位于：
D:/CodexWorkSpace/Sessions/20261002-235652-kenshi-crash-407794f2/Task-Iris-WorkTrace091-20261024-165024
