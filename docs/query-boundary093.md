# 093 查询边界归因与精确省写（源码 0.4.44）

本轮是源码交付，未编译、未部署。当前 bin、工作包、游戏 DLL 都仍为真实 0.4.43 / 092，SHA256 为 `1651254682d2bc628f1bc7634d6b337c74c93b54f6521668fb11c0a4351e994f`。工作包保留真实版本，`ready=false`、`pending_version=0.4.44`；正式版2.0、FCS、动画、材质、Shader、贴图与外置种族补丁均未改动。

## 1. 本轮依据及处理范围

092最近三个活动窗口中，去创建后的安全更新累计1827.2793ms，物理854.0183ms（46.74%），其他战斗653.2243ms（35.75%），可视104.6188ms（5.73%）。完整接口树显示就绪102.5225ms、参数提交73.4644ms、武器查找45.9338ms。它们属于不同层级的计时，不能互相直接相加。原生受击保持原链，本轮不动医疗内部。

| 方向 | 实际处理 | 有意保留的边界 |
|---|---|---|
| 物理执行与自定义回调 | 拆提交、执行、finish、报告块、初始重叠补验 | 原SDK调用、输入、查询顺序、失败语义均保持；不为每个形体读时钟 |
| 就绪与武器附件 | 单列十招动画长度扫描；附件只在当前骨骼内复用子节点数量 | 不猜测动画不会改变，不跨帧缓存长度或武器指针，不跨原生动画更新复用附件 |
| 可视参数 | 对源键相同的候选参数组，比较本实例上次成功提交的真实输出位；完全相同才省写 | 不跳轨道插值，不近似时间/浮点，不改custom1及钻头custom9 |
| 空区省查 | 保留原single=1，停止相邻批次一半关闭single的092实验；保留成本监视 | 未删除有收益证据的宽相；未知身份、查询失败、预算不足仍按原策略保留精确查询 |

092现场single on/off按输入成本分别为0.159230/0.187099ms，三个窗口同方向，但输入并不完全相同。这支持保留该路径，不能把14.9%差异直接当作本轮FPS收益。没有新证据前，不再叠加未经证实的新碰撞策略。

证据文件：本会话 `Task-Iris-Performance092-Double-20261024-204139/Analysis092.md`、`Task-Iris-NativeCeiling-20261024-205243/NativeCeilingReview.md`。原生弩弹最近命中零半径射线与本模组全命中扫掠/圆柱及过滤承担的工作不同，不能因使用原生SDK就断言已经达到引擎瓶颈。

## 2. 调用链及所有权

```text
原有安全主线程入口 → Iris::Tick → IrisCombat::Tick
  ├─ ActorReady → AnimationLength逐招检查（ready_animation_scan）
  ├─ ActualWeapon → 原骨骼顺序 → 子节点 → TagPoint → 可见/归属/Entity/网格谓词
  ├─ AdvanceEffects / ResolveJobs → RunRangedBatch → IrisNative::RangedBatch
  │    ├─ 原环境射线提交 → execute / finish → RangedReport → TerrainRayCollector
  │    ├─ 原宽相省查 → 块回调读取身份 → 空区证明或原精确查询
  │    └─ 原球扫掠/圆柱 → 块报告 → 收集/去重 → 原名单消费/独立伤害事件
  └─ 附件/独立后效/弹体绘制 → Visual::Draw → 原插值 → SubmitParameter
       ├─ 实际值与上次成功提交值逐位相同 → 省略该组setter
       └─ 不同/动态组/无缓存 → 原setCustomParameter → 成功后Store
```

原生资格、敌我/主动目标/昏迷策略、逐攻击段去重、远程地形射线与带半径角色查询、医疗2.5ms/32/FIFO、物理64次硬预算、任务轮转、事件时点、弹速/射程/范围/倍率与资源时钟均保持。

`Asset::constantGroups`只在资源加载时生成七组候选位。它不能证明插值结果永久不变：相同源浮点键的插值也可能出现舍入差异。因此运行时保留原25维插值，再对候选组输出做逐位比较。动态组沿原提交路径。

`ParameterCache`只属于插件自有`Visual`，与原entity/node采用同一手动转移方式。池、Shot和容器转移只复制指针，不复制大数组；现有归还流程重置源Visual。只有成功setter后更新有效位；异常时未提交值不会标为有效。`Clear`先释放CPU缓存并清零，再考虑scene/alive，故读档/场景失效仍释放缓存。未启用、无候选或可选缓存分配失败时沿原提交路径。没有新增析构自动释放，避免改变既有按值转移的所有权约定。

附件扫描仍有原256骨骼、512子节点的扫描保护。所有权和候选顺序不变，缓存仅是当前骨骼的数量标量。两次查找之间可能执行原生动画启动/更新，因此不把第一次附件结果复用到后一次。

兼容性核对发现：SDK的Entity附件枚举受`ENABLE_INCOMPATIBLE_OGRE_2_0`控制，实际库无对应Entity导出；OldNode子迭代器在本机头/导入库与游戏DLL返回容器的修饰名也不同。本轮已撤去这两种枚举，不启用宏、不读私有偏移、不改依赖；最终附件路径只使用原代码已经调用的Ogre方法。

## 3. 日志及开关

全部改后重启游戏生效。本地distribution与package INI配置值一致，原有注释差异保留，新增项如下：

| INI项 | 程序缺项值 | 本地工作值 | 用途 |
|---|---:|---:|---|
| EnableQueryBoundaryProfiling | 0 | 1 | 查询边界监视；还须总日志、性能、明细、完整接口监视开启 |
| EnableAttachmentCountReuse | 1 | 1 | 功能项：当前骨骼内数量复用；0回原搜索 |
| EnableVisualParameterGroupReuse | 1 | 1 | 功能项：实例参数精确省写；0回原整组提交 |
| EnableRangedSingleProbeABTest（已有） | 0 | 0 | 停止已完成的相邻批次实验；可显式1复测 |
| EnableRangedSingleEmptyProbe（已有） | 0 | 1 | 保留原本启用的单段空区省查 |

保留`EnableCombatInterfaceProfiling=1`、`EnableRangedProbeCostLogging=1`等本地诊断配置。新查询监视设0，或关闭其父日志门时，不取对应TLS/QPC、不增加对应统计锁；仍有固定函数/分支成本。总日志`EnableLogging=0`可关闭记录，功能优化开关独立于日志。日常轻负载只需关闭深度监视，无须关闭精确省写。

启动身份包括`query_boundary_ready`、`parameter_group_reuse_ready`、`weapon_attachment_lookup_ready`，合同为`IRIS_QUERY_BOUNDARY_093`。原`audit_combat_interface`新增：

- `ready_animation_scan`：十招动画长度/就绪扫描。
- `weapon_attachment_scan`：真实武器骨骼/子节点扫描。
- `query_submit`：原命令循环及输入/收集器准备，可能包含同步执行子阶段。
- `query_execute`：SDK调用段扣除已插桩子报告块后的余量。
- `query_finish`：同步finish等待/报告后余量。
- `query_report`：身份读取、形体去重、候选/结果存储等报告块；圆柱还含原精确几何工作。
- `query_narrow_recovery`：初始t=0恢复需要的原SDK重叠补验。

`query_report`不逐形体打点。单条直接射线逐个`onHit`仍包含在execute中；批量射线由外层RangedReport包住整个报告。`query_execute`不能称为纯SDK计算时间。所有数值为CPU侧墙钟观测，不是线程CPU计数、GPU时间或FPS测量。

嵌套的两个同名report阶段，inclusive可能重叠，**比较/相加使用exclusive**；`stage_calls`是范围进入次数，不是查询数或独立报告数量。查询量仍用原query/batch/raw形体计数。新增计数为`parameter_cache_fallbacks`、`weapon_count_reuse_lookups`、`weapon_count_legacy_lookups`、`weapon_child_visits`；参数写入/复用继续使用原`visual_parameter_writes/reuses`，后者包括原整次输入复用和新分组复用。

旧新版对比需重组口径：物理比较`physics + query_submit + query_execute + query_finish + query_report + query_narrow_recovery`的exclusive合计；就绪比较`actor_ready + ready_animation_scan`；附件比较`weapon_lookup + weapon_attachment_scan`。只看到旧physics/actor_ready变小不代表优化。原粗粒度audit_timing及probe成本口径保持，可继续交叉核对。

## 4. 实际验证及限制

所有验证在本会话任务目录保存，没有运行编译器、链接器或会隐式编译的测试。

- 232个原函数及调用约定保持；受击探针、远程桥接、几何接口等9个文件与092逐字节相同。
- 650个实际扫描C++ AST用例与原搜索结果一致，包括无骨架、多个候选、不可见/归属错误、骨骼与子节点预算。用例中数量getter从78,796次降到26,475次；这不是整段耗时比例。
- 17类实际资源生成候选位，执行1,956个实际Draw分组分支AST，逐次输出位与旧提交一致。七组分支setter从13,692次降到6,771次，custom1不计在该数字中；这是分支回放，不能视为完整Draw/游戏帧收益。
- 32个实际缓存清理/手动转移/分配分支用例，含分配失败原路径、已释放二次Clear、scene/alive失效。
- 288个完整计时树情形，含72个同父闭合根、144个关闭路径无新TLS/时钟/锁；12个查询边界开关短路、16个原Scope时钟借用及448个实验策略用例。
- 2,498个真实物理分支AST批次，另560对相同输入single on/off名单/顺序对照，含失败、身份未知、t=0、别名。6,000个包络采样、480次聚组分区、567个原生命周期用例、医疗FIFO/软预算/重入/代数规格通过。
- 上述旧物理/生命周期回归为隔离旧解释器，使用092 Visual替身；新缓存由独立实际AST测试覆盖，不能称为全系统集成实测。
- 14个C++/头语法单位和Python语法通过；头/真实DLL/导入库核对拦住了不兼容枚举接口。语法解释不能替代MSVC类型、ABI、链接和游戏运行验证。
- Update沙盒20通过、1个链接权限用例跳过。真实旧DLL被093合同拒绝，避免更新脚本将旧产物冒充优化版。

未执行：MSVC编译/链接、真实PhysX/TLS并发、游戏视觉/战斗/FPS。是否净收益仍需同规模用户实测；尤其精确省写增加少量比较和缓存访问，日志监视也有观察开销。先看总更新耗时、参数提交耗时、查询与排队长尾，再决定是否保留功能开关，不能只看省写次数。

## 5. 用户构建、复测与恢复

用户编译 `E:/KenshiProject/2.Projects/IrisArsenal/IrisArsenal.sln`，目标`IrisArsenal`，`Release|x64`、v100。随后正常退出游戏，运行现有`UpdateMod.cmd`。本轮不改变更新脚本的复制部署方式；组包校验只增加093身份，不会自行编译。

新运行日志应为0.4.44及093启动标记；没有该标记时仍是旧DLL。建议同场景先保持功能项1、监视项1，再以完全相同监视配置分别关闭两项功能作对照。比较查询输入长度/半径/数量、raw/contacts、原生受击次数、排队和安全更新耗时；游戏FPS需另行测量。

改前文件备份：`D:/CodexBackups/Task-Iris-QueryBoundary093-20261024-210030`及`E:/AIWorkSpace/_backups/Task-Iris-QueryBoundary093-20261024-210030`，按原绝对路径去冒号保留目录。每次再写有唯一revision备份；实际产物未覆盖。逐文件报告及源码/产物散列在本会话`Task-Iris-QueryBoundary093-20261024-210030`。
