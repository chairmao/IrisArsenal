# 094保守伤害查询（源码0.4.45）

开始：2026-10-24；完成：2026-10-25（Asia/Shanghai，按客户端日期）。用户要求正常数据“可以略多、不能漏原命中”，异常跳过该项，避免重算，并要求公开API与数学依据、实际减少工作量。

## 身份和范围

- 实测基线是用户真实0.4.44/093；bin/package/game DLL同SHA256 `9b7b69c97b5fe4628a7a8a3f9826715a809be7ad93d3deeb79425ca2ef7db748`。
- 新源码0.4.45，合同 `IRIS_CONSERVATIVE_QUERY_094`，未编译/部署。工作包保留真实0.4.44身份，ready=false/pending0.4.45。禁止用旧DLL冒充优化产物。
- 改爆炸球、静态近战胶囊和固定光柱的角色查询。**飞行炮弹仍是原一次真实球扫掠确定停止/爆炸中心**，其爆炸AOE才近似；环境仍原有限中心射线/原生组。
- 不改伤害倍率、招式权重、动画/特效/FCS、射速/射程、敌我/昏迷/当前目标原则、逐段去重、医疗语义。2.5ms/32次/FIFO、64次查询、每作业访问8路径保持；近似合批取消专为旧重查预留的第count+1预算，但仍按count条逻辑路径收费。

## 公开依据（测试不是证明的替代品）

1. 工程自带PhysX **2.8.4** 的 `native/physx284/SDKs/Physics/include/NxScene.h`，`overlapSphereShapes`、`overlapCapsuleShapes`、`overlapOBBShapes`的公开声明及参数注释：`accurateCollision=true`检查实际形体，false检查形体AABB。本次只使用这些既存公开接口，没有虚表偏移、自造API或引用新版PhysX猜旧版语义。
2. [CGAL官方Minkowski手册](https://doc.cgal.org/latest/Minkowski_sum_2/index.html)开头给出任意维集合的点对点和定义；这里采用该定义推导三维包含关系，**没有引入CGAL依赖或复制其实现**。
3. [PBRT第4版6.1.2](https://www.pbr-book.org/4ed/Shapes/Basic_Shape_Interface#RayndashBoundsIntersections)推导三轴slab区间交集。这里独立实现有限线段t∈[0,1]，显式处理零方向、保留切触并向外留浮点余量，不是凭经验给半径乘常数。

## 映射函数与包含证明

实现集中在 `native/NativeMultiContact.cpp` 的 `MapExact*` 函数和紧随的 `ConservativeCapsuleIntersectsAABB`。
设真实形体S，其有效包围盒B(S)，S⊆B(S)。以下是不含异常、场景未在同步查询/读取之间变化时的集合包含；不是不同游戏时刻/不同历史战斗的反事实保证。

| 原精确范围 | 明确映射函数 | 近似判定 | 省掉什么 |
|---|---|---|---|
| 球Q(c,r) | MapExactSphereToAABBQuery | 球参数原样；SDK accurateCollision=false，Q∩B(S) | SDK对真实形体的精确窄相 |
| 单条静态胶囊C(a,b,r) | MapExactCapsuleToAABBQuery | 胶囊参数原样；SDK accurateCollision=false | SDK真实形体窄相 |
| 合批静态胶囊 | MapExactCapsuleToExpandedAABBTest → ConservativeCapsuleIntersectsAABB | 一次原联合广相；对每形体，线段[a,b]与[Bmin−r,Bmax+r]做slab区间交集 | 每形体×每路径checkOverlapSphere/checkOverlapCapsule虚调用与精确计算 |
| 墙前平端圆柱光柱 | MapExactCylinderToConservativeOBB | 复用原同向紧凑盒，半尺寸(r,r,L/2)，SDK OBB对AABB | 真实顶点读取/临时顶点数组、凸体GJK/解析圆柱窄相 |

球/单胶囊：若x∈Q∩S，因为S⊆B(S)，x也属于Q∩B(S)。因此不漏真实相交。查询次数仍各一次。

合批：定义欧氏球D₂(r)={v:||v||₂≤r}、立方体D∞(r)={v:||v||∞≤r}。逐坐标|vᵢ|≤||v||₂，故D₂(r)⊆D∞(r)。胶囊为[a,b]⊕D₂(r)。若p=a+t(b−a)+v∈S，0≤t≤1、v∈D₂(r)，则a+t(b−a)=p−v∈B(S)⊕D∞(r)=[Bmin−r,Bmax+r]。因此该**同一个t**必通过三个轴的slab交集。仅三个轴分别有交点但t区间不相交的对象会剔除，避免用整条刀路的巨大世界AABB直接纳入人物。

圆柱：在原正交基(u,v,w)中，Q={c+tu+xv+yw: |t|≤L/2,x²+y²≤r²}。x²+y²≤r²推出|x|≤r、|y|≤r，所以Q⊆同向OBB(r,r,L/2)；再以S⊆B(S)得到包含。原墙前L同时驱动绘制，不加长射程。

近似误差**不是任意放大**：胶囊仅把欧氏半径核换成立方体核，核的最远角√3r；这不是说总命中人数至多√3倍。光柱圆截面换正方形，截面积4/π≈1.273倍，角距√2r；形体自身AABB也可能额外纳入边缘角色，所以总名单增长必须看日志。球/单胶囊不改变查询体半径。

浮点：原合批路径和形体AABB保留4·FLT_EPSILON×坐标尺度向外余量；slab用double、8·DBL_EPSILON区间余量；光柱沿用原盒基，只向外加16·FLT_EPSILON×尺度，避免重算基向量。数学集合证明基于正确有限包围体；这些舍入余量与边界测试不是所有异常浮点/引擎内部算法的形式化证明。NaN/溢出/反向bounds明确视为异常而跳过，不假装正常包含成立。

## 调用链和安全

原安全主线程入口 → IrisCombat::Tick → AdvanceEffects / ResolveJobs → Contacts或TryCapsuleBatch / RunRangedBatch → IrisNative同名公开SDK查询 → 只返回自有Contact/ObjectKey值 → Collect/CanDamage → 原逐段命中名单 → 原伤害FIFO → Flush → 原生受击。

飞弹的SweepAll/ProjectileAll、RayBlocker、FinalizeSweep、AdvanceEffects及Emit/Blast消费者逐token比对保持；RangedBatch只给独立光柱加新模式，原飞弹路径另作实际AST回归。

合批读取形体bounds沿用原本的getWorldBounds路径和同一个同步只读窗口，保留原路径AABB预筛。SDK文档明确形体状态双缓冲，不能声称getter与任意另一次场景查询是同一快照；此处包含证明针对**原合批路径自身**使用的同一有效bounds/形体状态，不拿另一帧/另一接口的名单当证明。单查询路径完全用SDK公开AABB模式，不另读getter筛掉候选。没有把新的getter剔除引入飞弹。

没有新Hook、线程、场景写入、Actor/Shape生命周期操作或场景锁；仍先检查现有世界/物理/队列安全门。NxShape地址仍只借当前同步栈，跨窗口只有稳定五字段身份/插件自有值。回调只收集/计数，不写日志、不拿诊断锁、不调用医疗；SDK结束后才汇总。

异常：身份/形体读取、非法bounds、坏路径或分配失败只跳过该项，保留有效名单继续；不设512/1024/256固定人数字段上限，不整批清空、不回旧路、不影子重算。无可用SDK/场景不属于“坏角色数据”，原游标留待可用窗口，没有无效场景强行查询。原飞弹/环境异常的既有安全恢复语义保持，不在本轮改写。

## 配置与监视

`[IrisArsenal]`，重启读取：

```ini
EnableConservativeDamageQueries=1
EnableConservativeQueryLogging=1
```

第一项独立于日志，默认1；设0选择原精确算法。第二项程序缺项0，本地distribution/package显式1，且需EnableLogging/EnablePerformanceLogging/EnableCombatDetailLogging全为1。设0后新计时/统计锁/异常明细关闭，保守功能仍运行。原已有其他日志需各自关闭。

新模式忽略EnableCapsuleBatchShadow以遵守不重查；若要运行历史精确合批/逐路径诊断，先关保守功能，再显式开旧shadow。不会在正常游戏偷偷运行新旧对照。

摘要追加 `approx_sphere_queries / approx_capsule_queries / approx_cylinder_queries / approx_capsule_batches`（类别1/2/3/4）、`approx_raw / approx_contacts / approx_box_tests` 及 `approx_skipped_identity/geometry/capacity/input`。原计数索引不移动。一次查询仅一次已有统计锁合计，不逐形体QPC；新通道 `capsule_conservative_box_tests` 区分旧capsule_exact，包含每形体bounds读取/校验及盒测试，不是纯算术时间，也不能再加回已包含它的physics父耗时。空合批不计算倒数。

`approx_contacts`是查询去重名单，不是最终扣血人数，仍要经CanDamage与逐段名单。`approx_raw`沿用查询原始报告口径，光柱含原地形报告，合批跨路径候选不重复查询但contacts按独立路径求和；类别计数包括无效输入尝试，真实命令数看query_calls及ranged_batch_rays/sweeps/cylinders。

异常日志 `conservative_query_skipped`：前8条、异常码变化且至少1秒、或持续10秒最多一条；累计数量不丢。geometry零异常码可表示空形体/非有限/反向bounds，不冒称OS异常。capacity明确区分内存不足导致的漏选。geometry计数只覆盖回调空形体及合批显式读取的bounds异常；SDK内部未暴露的数据拒绝不能假称已逐项捕获。

性能验收必须同时比较：相同压力下query_execute、sphere/capsule/cylinder/合批耗时，每实际命令/路径成本，contacts与damage_queued增长，native_damage/伤害队列年龄/超目标及帧峰值。**只看到查询变快不等于总耗时下降**。多纳入的有效目标会增加原生受击调用，可能抵消查询收益；未现场测量不能保证FPS提升。最新093测试主要是飞弹，原飞弹扫掠这轮保持，因此对这部分大头的收益有限，不伪称全部物理开销都已消除。

## 已执行验证与交付

- `tools/test_conservative094.py`：实际C++ AST执行24,000组随机胶囊包含、37边界、900映射输入，合计24,937；实际合批14组（2/4/8路径、坏身份/几何/输入、520独立角色、空区、容量失败替身）、回调异常继续、8组新旧API开关/非法输入。新合批正常一次查询，精确形体函数不可达，异常不重查。19个关键原函数逐token保护。
- 会话flight_regression094.py：当前实际RangedBatch/空区源码AST共2498批及480分组包络；覆盖原飞弹射线/扫掠/失败/别名/硬预算/空区行为。
- Update沙盒21项中20通过，1项系统不允许创建符号链接而跳过；真实093旧DLL被094组包合同正确拒绝。未运行真实更新/资源再生。
- 64组实际日志门/计数AST检查：关闭不进入新增QPC或统计锁，开启每查询一次已有统计锁合计；Kind/Counter旧索引保持，56/129名称一一对应。全部14个本地C++单元语法解析通过（并非编译）。
- 原编码UTF-8无BOM、逐文件原换行保留，中文/乱码检查；138项真实部署文件/二进制哈希保持。双备份与保护清单在会话任务中。
- **未执行MSVC编译、真实PhysX、线程/游戏或FPS测试**。按技能边界由用户编译 `IrisArsenal.sln` / **Release|x64 / v100**，正常退出游戏后执行已有UpdateMod.cmd。新日志需看到0.4.45与IRIS_CONSERVATIVE_QUERY_094，再对照同压力。

任务：D:/CodexWorkSpace/Sessions/20261002-235652-kenshi-crash-407794f2/Task-Iris-Conservative094-20261024-222330。
备份：D:/CodexBackups/Task-Iris-Conservative094-20261024-222330 与 E:/AIWorkSpace/_backups/Task-Iris-Conservative094-20261024-222330（各次改写另存revision，不覆盖）。
