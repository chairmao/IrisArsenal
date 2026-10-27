# 0.4.13 / IRIS_CAPSULE_BATCH_056：同步碰撞优化

当前只完成源码。没有编译、部署、操作游戏或恢复轮询；不能将已有0.4.12运行当作本版实测。正式版1.0（内部0.4.11/054）归档保持独立。

## 依据与目标

已核对0.4.12/055实际运行日志 `IrisArsenal-20261018-231436-406-37900.log`：id13样本中胶囊缓存命中0，胶囊7945调用累计1047.6695ms、最高单帧7.9564ms；原生受击1653次累计114.3679ms、最高单次4.3848ms。均为CPU侧/墙钟诊断，不是FPS，也没有证明原生受击内部具体子系统的成本。

这轮减少重复查询，增加慢原生受击证据；不通过缩小范围、减少人数/攻击段、合并受击或推迟更多刀路来改善数字。资源首次创建和日志I/O不在本轮改动范围。

## 同步调用链与安全边界

`原SafeHook → 原Idle/主线程门 → 原Tick互斥区 → ResolveJobs → TryCapsuleBatch → IrisNative::OverlapCapsules → 返回纯值结果 → 原Collect/事件去重/伤害队列 → 离开互斥区 → 原Flush/原生受击`。

- 不增加线程、Hook、SDK、Actor、全局contact report或移动锁；原18个Hook保持。
- 仅合批同一Job本轮的2～8条连续静态胶囊；球、圆柱、移动弹体、墙体阻挡仍走原路径。每个原胶囊的端点/半径、短轴退化阈值完整保留。
- 先用保守联合AABB在原场景取得候选。回调只收候选和稳定身份；回调完全结束后，逐原路径用官方 `NxShape::checkOverlapCapsule/checkOverlapSphere` 精确检查。AABB不能直接作为伤害命中。
- 逐形体只取一次世界AABB，向外留浮点余量；各路径仅排除明确不相交候选。临时候选512、潜在精确检查1024是优化保险，超过即回退原查询，不是新的伤害目标上限。每路径原256唯一身份上限保持。
- 只适配球/胶囊/盒/凸形角色体；其他类型回退。SDK版本门、scene所属SDK校验和引擎物理/AI安全阶段保持。所有NxShape地址只存在一次同步Native调用的栈内；没有游戏/医疗回调介入，不跨帧保存。
- 固定批量工作区只存插件自有Contacts值，原Tick互斥区独占，避免每批堆分配或大栈输出。下一调用重置有效count，不能当跨帧缓存使用。

原生API依据：项目自带PhysX 2.8.4 `NxScene.h:2592` 的overlapAABBShapes和 `NxShape.h:796/847` 的精确重叠接口；只是API证据，真实SDK结果/耗时仍待编译运行。

## 对照、失败、服务顺序

每次清理/读档重新要求连续8批实际执行了形体精确检查的结果匹配；空场景不能计作验证通过，首次出现新的形体类型强制对照，之后每256个非空批次再对照。对照期间始终消费原查询结果，完整身份逐字段排序比较，不依赖PhysX枚举次序或哈希相等。对照失败丢弃新名单并重新验证，不永久关闭其他演员或整个世界。

新路径失败就地回退原逐路径查询。若原第k路径失败，只推进原已成功前缀，保留失败游标、原轮转和逐事件账本；没有先扣半份血再重放。没有余量时直接执行原路径，不等待合批槽位。

`PlannedJobCost`先保守预留原轮会访问的全部路径成本；合批/影子/失败回退额外调用只用剩余预算，避免将本来能在本帧检查的移动目标挤到下一帧。快速批次仍按原N条路径收取逻辑预算，不把1次广相当成可以服务8倍刀路。保留每轮每Job最多8路径、64次场景调用硬限、原FIFO轮转和2048伤害队列。

原几何、enemy/小队保护、原生护甲/部位/经验、防御策略、倍率、范围、权重、攻速、游戏时钟、暂停/后效生命周期不变。医疗仍2.5ms软预算/INI32次上限/FIFO；单次原生调用不可抢占。

## 可配置诊断

`[IrisArsenal] EnableCapsuleBatching=1`：0回到原逐路径胶囊查询；已删除实际零命中的055胶囊缓存，原同Tick球缓存保留。日志旧capsule_cache字段保留索引并为0，启动明确retired。

`NativeHitSlowMs=1.0`：0.1～1000ms，只控制慢受击诊断；需EnableLogging、EnablePerformanceLogging、EnableCombatDetailLogging同时开启，启动读取。

- `capsule_batch`：新广相、包围剔除、精确检查与身份去重阶段；`capsule_batch_reference`：旧对照/回退查询及收集阶段。`query_jobs`才是包含两路和调度/收集的总阶段，不可把嵌套耗时相加。
- `capsule_batch_attempts/successes/shadows/matches/mismatches/fallbacks`、`candidates/shape_tests/no_headroom`记录实际使用与回退；`saved_calls`是快路省下的场景调用，需扣除`extra_calls`的验证/回退开销。原query_calls始终记录实际场景调用，logical_charge另记保守预算。
- `native_hit_slow`记录cast/event/move、完整caster/target身份、原生阶段墙钟、真实出队前queue_wall_ms、pre_native_ms、当前flush中的序号、倍率与结果。每次慢调用累计，文本前8次、之后至少5秒间隔。内部原因标为未确认，不猜护甲/死亡/AI是哪一个耗时。
- 明细关闭后不执行新慢调用QPC/文本，不改变任何战斗行为；影子校验独立于日志开关。总日志不截断，故障/变化文本限频。

## 已执行验证与限制

非编译规格覆盖289组解析形体/大坐标保守包围/身份容量边界（随机场景实际281个命中键）、16250组原轮服务顺序/快路/影子/未适配/失败回退用例；64场景调用、每Job8路径、无额外延期保持。13个战斗函数、8个原Native函数按优化前摘要锁定；医疗Flush除新增三条诊断语句外逐字等价。

完整既有非编译回归覆盖20份身体动画、20类效果、源纹理/FCS/参数、历史失败和身份规格；10份C++文件通过语法树检查；22项更新脚本/IO沙盒测试通过。没有编译、链接、实际PhysX、凸形运行或FPS测试，解析模型不能证明这些结果。真实首8批/周期对照与长期耗时日志用于下一次游戏验收。

参见 `validation-capsule-batch-056.json`、`capsule-batch-056-baseline.json`、`authorized-delta-056.json` 和逐文件 `capsule-batch-056-files.md`。既有文本经双备份，UTF-8/BOM及原CRLF/LF保持，中文/乱码扫描通过。

用户编译 `IrisArsenal.sln → Release|x64 / v100`，正常退出游戏后执行 `UpdateMod.cmd`。成功后新日志应显示0.4.13/IRIS_CAPSULE_BATCH_056；包ready=false及现有0.4.12 DLL不代表优化已运行。
