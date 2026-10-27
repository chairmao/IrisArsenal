# 077：三远程环境射线与原生弩箭飞行分组对齐

源码目标 **0.4.28 / IRIS_NATIVE_TERRAIN_077**，包括此前076预筛。当前用户bin/项目package/游戏DLL仍是0.4.26/075，未编译或部署077；没有启动、停止、附加游戏，没有改存档或模组顺序。

## 问题与原生证据

用户报告同一露天建筑原生弩箭可射出、Iris远程刚出生即碰撞。20:28:47.615—20:33:18.740的旧075日志出现794次travel=0、fraction=0、terrain_contact=1，全部选中BUILDING类型的简写身份1:256347664；对每发cast/event配对，impact.point与spawn.origin一致。672发方向Y>0，不能全部归因于向地面瞄准。

本轮重新读取本机kenshi_x64.exe、KenshiLib导出和Steam_1.0.65.br映射，EXE SHA256为504b362cde850d56afb1cea6f5b7b0ee014d9dd7b47e188599d91c804502cd3e：

| 原生环节 | 实际证据 | 结论 |
|---|---|---|
| GunClass::shoot | RVA0x43A680 `mov r9d,0x87fde47` | 构造弩箭追踪器的飞行组 |
| Harpoon飞行单步 | RVA0x437E30向追踪记录+0x78写0x87fde47 | 每次飞行沿用同一组 |
| ConstantTracer worker | 读取+0x78，经栈参数交给NxScene slot112/+0x380 | raycastClosestShape，NX_ALL_SHAPES、空groupsMask，SDK形体射线 |
| 开火前GunClass::trace/trace2 | 0x435835/0x43443F选择0x087F9E07或0x087F9E04 | 用途不同，不能错用于弹体飞行 |

原Iris的RayBlocker使用0xffffffff、仅在回调排除CHARACTER。已确认它比原生飞行多查碰撞组；原建筑具体命中shape组/类型/trigger旧日志没记录，尚不能证明该794次一定来自某个触发体。

## 修改后的调用链和保留范围

- 火神/脉冲：AdvanceEffects → Contacts → ProjectileAll → RayBlocker，以 `caller_groups & 0x087FDE47` 调用有限中心射线；另一次SweepAll继续使用原caller_groups和R4.5移动球。
- 极致驱动：ResolveJobs → Contacts → CylinderAll → 同一RayBlocker裁短环境有效长度；角色仍用原groups、R9平端圆柱，绘制继续消费同一实际长度。射程10000保持。
- 环境使用ALL回调，只为跳过角色后继续找最近环境；原生closest可先返回角色，不能直接据此吞掉我们的独立带半径查询。相同组内仍使用真实SDK形体射线，完整motion归一fraction，最近环境胜出、墙同距优先。
- 不增加trigger/建筑/t=0通用跳过；由原生组与SDK已有射线标记决定有效性。没有改shape/actor组、共享场景过滤、全局报告或原生枪械。
- 没有改开火前许可、射程、枪口位置、瞄准/提前量、弹速、人物碰撞半径、伤害倍率、敌我/昏迷门、护甲/部位/经验、后效时钟、075多持有者起手或076预筛。
- 维持原物理/AI静止门、两查询预算和完整结果提交；失败重试不移动弹体或消费pending；没有跨帧NxShape/NxActor指针、后台调用、新锁/Hook/线程。

本次对齐的是**环境射线的碰撞组、形体精确查询和SDK过滤语义**，没有将自定义能量攻击整体迁移成原生Harpoon。原生弩箭的重力、前方距离阈值、材质触发的插入/消失/音效及原生友伤策略属于不同消费者，未擅自移植。有限移动区间与角色独立宽度是用户已指定的设计。

## 日志与验收

既有EnableLogging和EnableCombatDetailLogging控制明细，无需新增INI项：

- 初始化一次 `ranged_terrain_ready contract=IRIS_NATIVE_TERRAIN_077 terrain_groups=0x087FDE47`。
- projectile_impact追加terrain_mask、terrain_distance、terrain_metadata、terrain_shape_type、terrain_group、terrain_trigger和完整blocker容器两值。terrain_metadata=1时才解读形体类型/组/trigger；关闭明细不读取这些附加SDK字段。字段描述的是本次最近环境候选，不一定是最后胜出的角色/环境。
- beam_collision每次成功光炮查询记录cast/event、实际裁短长度actual_length、请求长度及相同环境字段；不能再把发射前10000长度当作实际绘制长度。
- 只修正projectile_impact的显示：有hand身份的建筑应显示world_geometry=1、direct_contact=0。旧标签按身份是否为空命名，容易误读；Blast/直接受击业务AST保持，没有借日志修正变更伤害。

用户编译 `E:\KenshiProject\2.Projects\IrisArsenal\IrisArsenal.sln`，**Release|x64 / v100**。正常退出游戏后运行该项目UpdateMod.cmd；脚本仍只组包并全量复制现有构件，077合同与源码时间门阻止旧DLL冒充修复。包ready=false、version仍保留0.4.26，只pending_version为0.4.28。

下一次实机应在原建筑同一位置射击并读取上述077标记，核对是否还有terrain_distance=0、对应组/类型以及光炮actual_length。原建筑形体尚未采集，不能承诺本次修改已在游戏内消除所有起点碰撞。真正枪口穿入实体墙面时，合法t=0仍应阻挡。

## 已实际执行的验证

- 本轮重新从实际EXE提取7段指令，核对原生飞行组、瞄准组与worker参数传递；本机SDK声明确认所用形体API。
- 1152组组掩码矩阵、3580组环境最近命中规格，与原生立即数独立oracle对比。包含旧全组“额外组t=0遮住后墙”反例、新版保留合法零命中和不同trigger诊断值不改变策略。
- 原057的3010排序、连续球与平端柱体解析边界、双查询预算/失败/64发轮转规格通过。
- 20个关键函数正文保持；Configure/ResolveJobs/AdvanceEffects删除日志专用AST节点后业务AST与备份一致。角色Sweep/静态AOE、健康、瞄准、Emit、Contacts安全门及帧时钟保持。
- 732原生资格、1152多持有者条件，以及076的228 Hook/128选招/180动态类别/7744发布交错规格再次通过。
- 10份C++/头语法解析（MSVC扩展规范化）和3份Python AST通过；未运行MSVC/HLSL/链接。
- 129运行包文件哈希与266受保护文件保持，实际用户bin和游戏DLL/资产不变；21更新隔离用例20通过、1因系统符号链接权限跳过。
- 编码/BOM/换行保持，中文和新增乱码扫描通过。

以上是离线反汇编、实际源码AST和Python规格，不是C++/PhysX或游戏执行，不是FPS测量。

## 每个文件的变更与安全记录

逐文件即时报告和双备份清单位于本任务reports及baseline.json；另有最终逐文件报告，说明Role/Code location/Before/Changes/Reasons/After/Impact/Validation/Safety/Unresolved。

任务目录：`D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-Iris-NativeTerrain077-20261022-204714-d04da4`。

双备份根：`D:\CodexBackups\Task-Iris-NativeTerrain077-20261022-204714-d04da4`、`E:\AIWorkSpace\_backups\Task-Iris-NativeTerrain077-20261022-204714-d04da4`，其下保留盘符及完整原路径；未覆盖原日志、旧正式1.0快照或原运行产物。
