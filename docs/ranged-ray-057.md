# IrisArsenal 0.4.14：三远程地形射线与角色体积检测

本轮源码合同为 `IRIS_RANGED_RAY_057`。用户授权只改变三招的环境/角色碰撞分工；没有编译、部署、启动或终止游戏。已安装、bin及package的DLL仍为用户编译的0.4.13/056，同SHA256 `b8fcd19fb79ec209fe05efc7f73d21b452e8abf670a6c01220fa982dc483fcf7`。正式版1.0归档保持。

| 招式 | 地形/非角色物体 | 角色 |
|---|---|---|
| 极速火神炮 | 本次完整位移的有限中心射线 | R4.5连续球扫掠 |
| 脉冲之焰 | 本次完整位移的有限中心射线 | R4.5连续球扫掠；爆炸仍R36 |
| 极致驱动 | 从枪口至本次原路径终点的有限中心射线 | R4.5平端圆柱，截至最近墙前 |

## 调用链与命中合同

飞弹：原Tick安全门 → AdvanceEffects → Contacts（预留2次）→ ProjectileAll → RayBlocker + SweepAll(charactersOnly=true) → 两份完整纯值结果 → 原IgnoreRangedContact过滤 → 比较同一完整步长的fraction → 最近有效角色或墙 → 原Blast/伤害队列。完全同距时墙优先。中立仍可阻挡但不能受特效伤害，玩家/盟友继续不阻挡；enemy与昏迷配置等健康门保持。

光炮：原Job/ResolveJobs → Contacts（仍2次）→ CylinderAll → RayBlocker → 实际墙前长度 → 原OBB候选和真实形体平端圆柱窄相 → 原逐攻击段名单/原生受击。绘制消费同一有效长度，未改变光炮半径、伤害事件或墙前截断的同步流程。

环境射线用官方 `raycastAllShapes`，因为不能把射线最近的角色忽略后就假定后面没有墙，也不假设角色独占某个碰撞组。回调跳过所有角色，仅用常数内存保留最近的非角色阻挡；按实际距离归约，不依赖回调到达次序。路径、最大距离、返回距离、flags和身份都校验；SDK实例及兼容门保持。

两份结果分开，额外一堵墙不会挤占原256个角色形体接触容量。角色查询仍连续扫掠整个实际飞行步长，没有离散球采样或高速漏段。地形只代表中心线，因此外沿可以擦入地形；射线起点位于形体内部时沿用PhysX射线本身的语义，没有额外叠加球体地形判定。爆炸仍用原球形AOE，不在本轮增加爆炸隔墙遮挡规则。

## 安全窗口、失败与预算

PhysX调用仍在已有物理/AI安全窗口中同步完成，不开线程、不加锁、不设全局接触报告、不改角色或世界碰撞组。SDK形体只借当前同步调用栈；回调不进入医疗/日志/资源回收，跨层和跨帧只传身份、距离等纯值。

飞弹预算不足2次时只轮转，保留位置和pending游戏秒，不计作物理失败。射线失败时不发球查询；球查询失败则清空两份结果，两种情况都保留弹体等待重试，不先扣半份伤害。64次场景调用总上限及给原伤害作业预留的16次保持。光炮仍最多2次，火神/脉冲正常从1次变为2次；本轮不承诺FPS提升。

同一帧暂停、攻速、后效寿命、读档清理、逐攻击段去重、2.5ms/32次医疗FIFO、权重、倍率、FCS、材质、动画、特效范围均保持。火焰翻滚不走新的远程分支。

## 日志与构建

启动新增一次 `ranged_collision_ready`，说明terrain=finite_ray、角色形体和existing安全窗口。原有有界projectile_impact追加实际terrain_query/character_query及terrain_contact，射线和球扫掠原始接触数一并计入query_raw、两次实际调用计入query_calls；保留现有sweep/cylinder耗时。没有新增逐帧文件写入或监视轮询。

用户编译 `IrisArsenal.sln` 的 **Release|x64 / v100**，正常退出游戏后执行本项目 `UpdateMod.cmd`。组包门只接受057、实际x64 PE及新于全部源码的DLL；当前package ready=false，不能把旧056产物更新成新版本。无需重做或替换原模组素材。

## 已实际执行的验证及边界

- `tools/verify_moves.py`：完整非编译资产/FCS/20份动画/特效/医疗及旧优化回归通过；10份C++/头文件语法树零错误。语法树不代替MSVC类型/链接检查。
- `tools/test_ranged_ray057.py`：3010组随机与边界命中顺序、2000个世界形体的最近墙归约、256个角色形体容量、连续球与平端圆柱解析反例、失败原子消费/预算不足/64发轮转规格通过。
- 原056的16250组服务顺序/失败与合批回归保持通过；原生医疗、资格与原素材精确不变量通过。
- `python -B -m unittest test_update_mod test_audit_io052`：22项沙盒测试通过，没有写实际游戏目录。
- 所有131个非manifest包文件（含旧DLL）逐项SHA256保持；新旧DLL合同拒绝门通过。

以上是Python独立规格、静态源码/SDK核对、语法树和文件验证，没有执行新C++、实际PhysX、HLSL或游戏，不把这些结果当作实测命中或FPS提升。实际游戏应核对近地射击、友军挡在墙前、墙前/墙后目标、光炮截断与多人连续施放的日志。

## 文件报告与恢复

每次写入均在本任务reports目录即时保存独立逐文件报告，含Role/Code location/Before/Changes/Reasons/After/Impact/Validation/Safety/Unresolved。两个外部备份根目录如下，内部保留完整盘符以下原路径；只恢复指定文件，保留旧DLL/素材，不将其冒充新编译产物。

- `D:\CodexBackups\Iris-SplitRay057-20261019-010626-68ac02`
- `E:\AIWorkSpace\_backups\Iris-SplitRay057-20261019-010626-68ac02`
- 任务证据与逐文件报告：`D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-Iris-SplitRay057-20261019-010626-68ac02`
