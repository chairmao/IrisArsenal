# IrisArsenal 0.4.12 / 055 碰撞与伤害优化工作版

正式版1.0已先封存，内部DLL保留0.4.11，代码IRIS_PHYSX_COMPAT_054；归档：`D:\CodexBackups\Iris-Formal1-Optimize055-20261018-211300-34f16b-Formal1.0-v2`。见[正式版入口](formal-release-1.0.md)。新工作版只修改源码、诊断与组包门，没有编译或部署，现有运行DLL仍为0.4.11。

## 本轮依据与实际改动

旧日志IrisArsenal-20261018-185126-656-39800.log记录：胶囊查询单安全帧累计最高7.32ms、原生受击计时最高4.41ms，大群伤尾部墙钟等待约467ms。它们不是GPU/FPS测量，也不能把含暂停与安全窗口间隔的等待全部归因于2.5ms预算。

1. 原生球/胶囊和圆柱候选的角色去重：前8个角色保留原顺序线性查找，第9个候选起才建立512槽索引。完整比较present/type/container/containerSerial/index/serial，hash冲突继续探测。输出顺序、256唯一角色容量、完整成功才消费及错误/溢出整批拒绝保持。扫掠按真实shape和TOI的既有去重不改。
2. 作业由deque复制轮转改为list::splice；新作业交换自有vector/set入队。每请求8路径/轮、每帧64调用、原FIFO轮转、坏路径保留、2048医疗队列门保持；不把角色或PhysX对象所有权转移给插件。
3. 增加最多16份胶囊接触值缓存，与既有最多16份球缓存共用单次安全Tick寿命。仅有序端点、半径完全相同的静态体积可复用，不缓存失败/半份名单，不跨帧，不缓存墙阻挡/飞行扫掠。不同事件仍各自enemy筛选、各自独立伤害。
4. 圆柱窄相每次查询复用一个自有顶点缓冲，逐形体清空points/rounding并重新读取几何、位姿。不会跨查询缓存NxShape/NxActor，也没有改变原BodyGeometry/GJK判定。
5. 医疗保留2.5ms软预算、32次INI上限、FIFO和40ms软等待目标；只加分项诊断。身份/敌我、目标相关伤害计算、原生受击、防御策略、经验与结果链仍执行。没有合并不同攻击段、增加health入口、改倍率/范围/权重或将医疗搬到线程。

## 日志配置

在[IrisArsenal]下新增 `EnableCombatDetailLogging=1`，启动读取。需EnableLogging和EnablePerformanceLogging同时为1才生效。设0只关闭055明细，保留原总性能审计；EnableLogging=0关闭插件文件日志与新增统计。预算仍需原有QPC，所以不声称关闭日志后整个插件不调用时钟。新增诊断Scope、作业时间戳和原生去重工作计数在明细关闭时不采集；身份索引本身始终工作。

原周期窗口/进程摘要、PID/创建FILETIME/实际exe、64位计数和不限制总行数保持。没有增加轮询、线程、日志IO重构或资源重做。手动AnalyzeLogs.cmd读取器已能接受新通道，无需修改解析器。

CPU通道：damage_identity、damage_calculate、native_damage（原有TLS作用域和原生受击）、damage_xp_revalidate、damage_result、query_jobs（含查询收集/任务处理）。嵌套计时不能直接相加。新增计数：identity_comparisons/probes/duplicates/tables、cylinder_buffer_growth、job_transfers/rotations、capsule_cache；原query_calls/raw_shapes/contacts/cache等继续输出。

墙钟通道：query_job_age，以及query/medical的ready、paused、physics、ai、unavailable等待分量。query_job_age从作业建立到完整提交，包含其查询/收集时间；medical总等待仍为原damage_queue_age，从实际入队到弹出。分量按相邻主线程观察点的“上一次状态”累计，暂停优先，其次物理、AI、世界无效，余量归ready。它是采样归因，不是精确线程等待，也不能把ready余量全部称为可利用空闲窗口；没有回调期间的短暂状态切换无法被准确还原。日志明确wait_attribution=previous_main_thread_observation，等待通道CPU_side=0。

本轮先减少真实重复工作，**未启用额外2ms查询延后预算**。原因：旧查询已分帧，进一步推迟会改变目标被查询时的位置；应先实测减少复制/比较后的耗时与积压，再考虑调度。

## 验证与边界

实际执行完整非编译验收：20份身体动画、20类效果、十招事件数、真实FCS、源资源与既有原生防御/时钟/失败回归，以及10份C++/头Tree-sitter语法解析；22项沙盒更新/日志事务与解析测试通过。055新增160组身份输入（含257个同桶身份、容量边界、代次差异和圆柱先MISS后HIT）、1/3/16/64/256作业的调度/重试顺序、8组缓存/独立事件和采样等待规格。

独立密集规格的身份比较次数164224→1136，另有1500次hash槽探测。该数字只表示特定Python输入的比较工作量，**不能转换为C++耗时或FPS提升**。现有几何、源资源、事件、防御与资格函数通过改前正式版的不变量核对；INI除一个日志键外逐值保持。哈希清单有精确055迁移，不因合法改动跳过旧回归。

没有执行MSVC/HLSL编译、链接、游戏实测或GPU/FPS采样。静态语法不能保证MSVC类型和链接正确；同一输入规格不能代替真实PhysX。本轮也没有证明后续未知PhysX修订ABI。新版本实际收益、命中完整性和长期稳定性须用户编译后验证。

## 用户下一步

打开 `E:\KenshiProject\2.Projects\IrisArsenal\IrisArsenal.sln`，选择 **Release|x64 / v100** 编译；正常退出游戏后运行项目UpdateMod.cmd。脚本必须识别新IRIS_COLLISION_DAMAGE_055标记；当前旧054 DLL会被拒绝。package目前ready=false，不把旧DLL冒充055，不会自动把优化部署到游戏。

逐文件改动、双备份和编码回读报告：`D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-Iris-Formal1-Optimize055-20261018-211300-34f16b\file-reports`。本次原代码/配置均按UTF-8原BOM及换行保存；原cpp/h为CRLF，原INI/Python/rc为LF。正式版封存独立不可被新工作树覆盖。
