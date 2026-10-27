# 095：命中包含、条件成本证明与同输入耗时验收

源码0.4.46 / `IRIS_CONSERVATIVE_PROOF_095`。这份文档替代“只要近似就必快”的说法。实际已运行DLL仍为0.4.45/094；本轮没有编译或部署。用户接受明确条件的计算成本证明＋真实耗时验证，且明确要求**额外纳入人物产生的后续医疗结算成本不计入碰撞效率验收**。

## 1. 调用链和修改范围

原安全主线程 → `IrisCombat::Tick` → `ResolveJobs` → `TryCapsuleBatch` → `IrisNative::OverlapCapsules` → 原一次联合AABB查询 → 当前栈内候选与路径判定 → 每路径完整身份去重 → 原`Collect/CanDamage` → 原逐段去重/伤害FIFO → 原`Flush`。

095只删胶囊合批中的重复类型读取及部分平行轴检查。没有新增线程、Hook、场景锁、跨帧NxShape指针，也没有修改资格、倍率、范围、预算、调度或原生医疗。球、独立胶囊、圆柱映射保留094；飞弹停止仍是原角色带半径扫掠＋地形中心射线。

## 2. 明码映射和包含证明

候选真实形体为S，合法世界AABB为B，线段为L=[a,b]，伤害半径r>0。

- 094球/独立胶囊：`MapExactSphereToAABBQuery/MapExactCapsuleToAABBQuery`保留查询体，SDK `accurateCollision=false`测试形体AABB。S⊆B，因此Q∩S≠∅ ⇒ Q∩B≠∅。
- 094胶囊合批：`MapExactCapsuleToExpandedAABBTest`把L⊕Ball₂(r)改为L与B⊕Cube∞(r)的slab相交。Ball₂(r)⊆Cube∞(r)，故原精确命中必在近似名单。三个轴共享同一t∈[0,1]，不是三个互不关联投影。
- 094圆柱：`MapExactCylinderToConservativeOBB`使用包含平端圆柱的原同向紧凑OBB，对形体AABB求交；不变成长路径世界大盒。
- 095胶囊内核：`ConservativeCapsuleIntersectsAABBReference`保留094逐行算法；新`ConservativeCapsuleIntersectsAABB`必须在原`pathBounds[p].intersects(candidate.bounds)`前缀之后使用。若dᵢ=bᵢ−aᵢ=0，前缀已经要求aᵢ处于[Bminᵢ−r, Bmaxᵢ+r]，所以省掉此轴的重复扩盒与比较。非平行轴slab代码不变。删除拒绝条件不会删除原命中，即H094⊆H095。

浮点边界：前缀路径和候选盒有`4*FLT_EPSILON*scale`向外余量；平行轴可能在这条薄余量带多收，不能反向漏原命中。源码实际float舍入还带约1 ULP；不能把这个量当精确世界距离常量。若原平行轴仅因外扩前缀通过但原slab会拒绝，下面“相同控制流成本”定理不适用，人数增加仍单独统计。异常/分配失败按项跳过，包含保证针对合法有限数据及成功容量分配；异常不重查。

## 3. 成本证明的明确条件

比较对象必须分清：095重复工作删除证明针对094；不能冒充“094各SDK分支比093必然更快”。SDK文档只声明几何语义，没有给任意场景的耗时上界。

成本模型：对相同已收集候选、路径、世界bounds快照，按执行的算术、比较、转换、类型读取、分支、结果写入分类计数。假定数据合法，原平行检查不会仅因浮点外扩带而拒绝，且诊断关闭。此时：

1. 每个候选删掉一次`NxShape::getType()`虚接口调用和原类型分类；`getWorldBounds()`次数不变。接口定义是本机SDK `NxShape.h`的virtual getType，不猜内部纳秒成本。
2. 每个实际经过的平行轴删掉2次浮点到double转换、一次减法、一次加法、1～2次坐标比较及OR短路；非平行轴算术相同。若没有平行轴，纯slab内核不承诺省工。
3. 仍存在模式选择等控制成本，不能忽略。令K为候选数，P为经过前缀的候选路径数，A为实际经过的平行轴数，Cg为类型读取及分类成本，Cd为新增策略选择成本，Cs为每平行轴省去成本，Cf为固定新门成本。**在K·Cg+A·Cs>P·Cd+Cf时，095碰撞计算工作量严格减少**；这是一条可检查的充分条件，不是任何输入无条件成立。新增正式路径不增K×P扫描、场景查询、堆分配或精确形体检查。
4. 原精确→094映射的候选成本，只有实测同输入`approximate_stage_ms < exact_shape_ms`时才验收为该输入下收益。exact参考复用同一次bounds且不把bounds读取计时，刻意偏向参考；比较不包括公共SDK广相成本，也不包括参考名单对比自身。整个查询的绝对收益还要看正常模式日志，不能把局部收益当整帧收益。

离线实际C++ AST验证已检查运算执行次数和命中包含。它证明本代码分支删除关系，**不能代替MSVC机器码、真实PhysX、缓存、线程调度或游戏耗时验证**。

## 4. 人数误差与性能分开

按用户要求，碰撞效率不加额外受击人数的原生医疗成本。人数误差单列：

`rho = sum(|Happrox,p|) / sum(|Hexact,p|)`，`extra=sum(|Happrox,p\\Hexact,p|)`，`missing=sum(|Hexact,p\\Happrox,p|)`。

这是完整六字段稳定角色身份去重后的逐路径集合比；不是形体数、体积比或最终受伤人数。CanDamage资格和逐段名单仍由原消费者处理。精确人数为0时rho无定义（日志-1，读取器null）。任意空间分布下，体积比不能证明人数比；不编造“必然只多百分之几”。同一角色在不同独立路径出现属于分路径统计，不是本轮合并伤害。

`missing_unique`正常数据应为0；异常批计invalid，不能拿残缺参考名单假称无漏项。不会因为对照名单不同而回退或重算正式结果。

## 5. 可关闭日志、同输入测量

INI重启读取；工作配置保留原日志父门。

| 项 | 默认/工作值 | 用途 |
|---|---:|---|
| EnableConservativeDamageQueries | 1 | 094保守判定；设0回原精确策略 |
| EnableConservativeKernelReuse | 1 | 095省重复工作；设0走094内核/类型读取 |
| EnableConservativeQueryLogging | 1 | 同时受原EnableLogging/EnablePerformanceLogging/EnableCombatDetailLogging父门控制 |
| EnableConservativeProofAudit | 0 | 正常关闭；显式1才做同输入精确参考和内核微测 |
| ConservativeProofSampleEvery | 128 | 每128个非空合格批抽1个；测试可暂调小，不截断正式名单 |

诊断由原安全入口一次配置。正常audit=0：没有新增QPC精确对照、场景重查、参考名单或微测；计数复用已有循环，不另扫描。全部诊断关后无新增QPC/统计锁，但固定分支和栈成本仍存在。

audit=1且诊断父门开：同一次同步函数里借当前有效shape及自有bounds做精确参考，结果只用于日志、不进入医疗。每候选只读一次参考类型；参考形体检查和名单构造计`exact_shape_ms`。正式映射/读取/结果分发计`approximate_stage_ms`。仅完整有效批进入`timed_batches`及阶段耗时比。内核微测同一输入最多64对，每对旧/新各64次，交替顺序并使用volatile函数指针防纯函数循环外提。

新日志`audit_conservative_proof`输出window/process两组。`audit_total_ms`包含测试参考、名单比较及微测，**外层根计时仍含该测试成本，不应当作正常性能**；正常CAPSULE_RESULTS已在测试之前结束。`type_reads_saved/parallel_axes_saved`为删除工作计数，非CPU指令或毫秒。

读取：`python -B tools/read_conservative095.py <log> [--since "2026-10-25 03:00:00"]`。只合计有`audit_summary_end`的window，不把process累计重复相加；首窗口可能跨since边界。不换算FPS。

## 6. 验收与未完成实测

本轮执行实际C++ AST/语法/容量与异常路径/名单与统计回归，详细结果在当前任务目录。没有启动游戏、编译或部署；旧094 DLL被新打包合同正确拒绝，避免伪装成095。

用户需编译`IrisArsenal.sln / Release|x64 / v100`，退出游戏后执行原`UpdateMod.cmd`。先确认日志0.4.46及095合同；audit=0看正常负载，短期开audit=1采同输入成本和rho，再关闭。验收分开看：包含证明、条件操作量、配对真实耗时、正常整体查询耗时。未测不能宣称FPS或绝对耗时已提升。

## 公开依据

- 本机PhysX2.8.4 `native/physx284/SDKs/Physics/include/NxScene.h`：accurateCollision=false的AABB语义；`NxShape.h` virtual getType。公开[NVIDIA 2.8.4 overlap说明镜像](https://stuff.lanowen.com/PhysX2.8.4_OverlapTests_Doc.pdf)。
- [PBRT 4e / Ray–Bounds Intersections](https://www.pbr-book.org/4ed/Shapes/Basic_Shape_Interface#RayndashBoundsIntersections)：slab区间相交算法。平行轴重复条件删除的具体前提和成本式是本项目在该算法上的推导。
- [MDN / 3D collision detection](https://developer.mozilla.org/en-US/docs/Games/Techniques/3D_collision_detection)：AABB比较的常见低成本用途；不把社区一般描述当本DLL耗时保证。

更新/纠正：094文档的几何包含依据仍适用，但其“逐候选无精确虚调用”不能单独证明全查询更快；任务早期ProofBoundary.md含医疗成本的式子属于旧讨论边界。依用户最新要求，本次碰撞效率验收明确排除额外医疗，人数误差独立报告。
