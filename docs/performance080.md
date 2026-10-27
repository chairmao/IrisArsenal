# 080：保守性能优化与可视负载对照

日期2026-10-23。源码0.4.31／`IRIS_PERFORMANCE_080`，保留079家具/实际手持修复。用户授权处理四个性能方向，并要求正确逻辑及线程安全。本任务没有编译、链接、生成DLL、部署游戏、修改存档、控制游戏进程或附加调试器。当前DLL原字节保留，包ready=false/pending0.4.31。正式版1.0封存未改。

## 本轮实际改动

### 1. 远程查询只省精确零点阻挡后的无用角色扫掠

NativeMultiContact.cpp:270的ProjectileAll仍先走077原生环境组中心射线。只有该射线成功、有最近环境接触、fraction精确等于0且半径有限且大于0时，直接返回空角色名单和原环境名单，实际调用数为1。

证明依据：AdvanceEffects原消费者对完全同距优先环境；SweepAll合法输出TOI均>=0。环境在0时，没有角色能够更早。因此角色查询不会改变有效命中。非法半径仍走原SweepAll错误路径；地形查询失败原样返回，非零地形与无地形段仍对完整原motion做原球扫掠。没有epsilon、近零吸附、分段裁短、缩小半径或重标fraction。光炮圆柱、近战球/胶囊、源形体查询、初始重叠修复和排序正文未改。

本轮没有贸然实现一般墙前截短扫掠：改动会引入归一化TOI与数值边界差异，现有环境下不能直接执行PhysX作对照。先落实能独立证明的零点快路。预留2次调用的入口及每帧64次硬限保持；实际只用1次就按1次记账，余量可服务原排队工作，不降低查询频率或增加积压。精确零墙快路不再触发那次无关角色扫掠中的错误/溢出；这不是忽略已执行查询的失败。

### 2. 特效参数复用与光炮统一更新

IrisCombat.cpp:123的Visual增加三个已初始化浮点输入快照及valid位。仅age、opacity、extent逐位完全相同才省去同实例custom1..8重复写入和25通道轨道插值。没有时间量化或浮点epsilon。节点变换、最终可见位仍正常更新；钻头custom9仍由原ShowParts独立设置。参数写成功后才更新快照，Clear失效；预热首次Draw之前就按值入池，所以数组在构造时全部初始化，避免读未初始化浮点。对象池转移一并转移同一自有Entity对应的快照，不保存额外SDK裸指针或按层大数组。

原光炮在AdvanceEffects和ResolveJobs后的最终遍历重复更新。本轮只保留后者，消费同帧最新墙前长度。独立后效age推进、收尾、暂停/原点门、伤害四段和查询顺序保持；其他招式后效循环token保持。更新函数的两次调用原先不等于GPU真实绘制两次，本轮明确优化的是CPU节点/参数重复工作。

没有依据alpha值猜测并删除源层，也没有改造网格/Shader、贴图、演出范围或源时序。参数复用命中率取决于实际场景，新计数用于判断收益，不能声称已有显著FPS提升。

### 3. 单次查询内相邻接触资格复用

IrisCombat.cpp:510的RangedContactMemo是AdvanceEffects当前查询循环中的栈对象，只保存上一接触ObjectKey的六项完整字段及布尔结果。下一项只有present/type/container/containerSerial/index/serial都相等时才复用；否则立刻getCharacter并按原IgnoreRangedContact规则判断。没有哈希碰撞、容器容量问题、跨帧身份/敌我缓存或新的共享表。非远程接触仍按原自身过滤，缓存不参与。

原DamagePolicyReason、CanDamage、Collect、Flush及格挡/受击/经验函数均未改。原生临时敌对记忆、伪装参数与主动目标分支保留；入队和医疗前仍按当前状态复核。没有把阵营中立当作isEnemy恒假，也不改三远程防御策略。查询处理期间没有医疗回调，AI/物理处于原安全窗口；跨查询关系改变时新建memo，不能继承旧结果。

### 4. 可关闭的特效可视负载对照和采样工具

新增INI `DiagnosticHideEffects=0`，默认正常显示。设1并重启后，仅隐藏本插件Visual实体与手动刀光；CPU特效更新、同样的资源预热/池、角色与实际武器、动画、弹体、碰撞、倍率和医疗保持。它没有卸载共享纹理，不能用于直接测资源卸载效果；改变渲染提交/裁剪也会影响CPU，所以对照差值不等于纯GPU时间。

`tools/measure_gpu080.py`手动调用现有nvidia-smi，默认30次/1秒，输出全新目录的gpu.csv、metadata.json、driver-details.txt；不安装依赖、修改时钟/功耗/温控、启动游戏或常驻轮询。已实际执行1次采样，驱动详细查询成功。此工具仅测全卡利用率、温度、显存等，包含其他进程/驱动，不是本mod显存、呈现帧时间或每进程GPU执行时间。

[MISSING] 本轮没有接入呈现帧时间/GPU时间追踪器，也未用新DLL做游戏A/B。未来须在相同场景/视角/敌人数和持有者数下，分别正常与隐藏特效，记录帧时间及温控状态后才决定是否优化透明层重叠/材质批次。没有据一次全卡采样宣布渲染瓶颈。

## 线程与行为边界

仍为原18个Hook和既有主线程安全窗口：Frame/Safe → Tick持原Iris锁 → AdvanceEffects局部查询/绘制 → ResolveJobs → 最终光炮更新 → 离开原锁 → Flush重查安全条件后原生医疗。没有新线程、Hook、锁对象、锁顺序或异步PhysX。新增可视字段由原自有Visual生命周期持有；新增接触memo不逃逸调用栈。新计数沿用原诊断锁，未在PhysX回调内写日志/医疗。

IrisArsenal.cpp、IrisRanged.cpp全文件保持；原选招/拔枪/家具、肢体/义肢、目标瞄准、炮口、射程、R4.5/R9碰撞、伤害倍率/权重/段数、敌我过滤、2.5ms/32次/FIFO、安全检查和暂停读档清理保持。没有修改资源/动作/FCS，不清理闲置资源池，不扩大到未知原生边界或本轮审查发现的策略差异。

## 新增日志字段

沿用现有周期摘要，无逐帧文本。日志总开关0时不采集；visual_update还要求性能与战斗明细开启。源码条件检查覆盖关闭路径无新增QPC。

| 字段 | 含义 |
|---|---|
| performance_ready / IRIS_PERFORMANCE_080 | 一次启动代码身份及hide_effects模式；实际新DLL是否加载应查这行与0.4.31。 |
| projectile_wall_skips | 精确零墙而省掉的角色扫掠次数。0表示该场景没有触发此快路。 |
| ranged_contact_checks / ranged_contact_reuses | 当前查询接触身份/资格重新求值与相邻完整身份复用次数。自体过滤也计入重新求值，并非每次都调用完整敌我链。 |
| visual_parameter_writes / visual_parameter_reuses | 实际执行/省掉的custom1..8 setter数量；不是GPU draw call或显存上传字节。 |
| visual_update | Visual::Draw节点/参数更新的CPU侧墙钟，嵌套在战斗Tick内，不能与父计时相加当净CPU或FPS。 |

新增枚举只在原索引末尾追加，原名称顺序保持；read_audit052通过新增通道/字段的合成摘要解析兼容检查。合成测试文件明确标注非游戏日志，不写实际游戏log。

## 已执行验证

- `test_performance080.py`：900组实际CPP AST查询条件/输出路径，含非法半径、地形失败、非零/无墙和零墙；4096组接触排序/过滤消费对照，实际观察572次相邻复用，前后最终目标/比例一致；六字段逐项身份差异边界；1029组实际memcmp参数条件，含负零和NaN位型；7个原生查询、17个战斗函数token保持。
- 原`test_native_melee072.py`：732组源码资格/回退分支通过。原`test_noncombat079.py`：240 Hook分支与56拔枪条件通过。
- 独立后效循环除光炮前一次提交外token一致，原生读档全局Clear保持；7种关闭日志/性能/明细组合的实际统计谓词及Scope体无新QPC/Record。
- 10份C++/H语法树与4份Python AST通过；已确认实际vcxproj编入IrisCombat/NativeMultiContact。语法树不是MSVC预处理、类型检查或链接。
- 21项隔离Update回归：20通过，1因WinError1314未允许测试符号链接而跳过；实际游戏目录未参与。更新流程仍组包/清空复制，不加入本轮测试或资源重建。
- 包内129运行构件哈希匹配；旧DLL、FCS和全部资产字节保护对照通过。完整最终清单与逐文件报告在本任务目录，所有原小文件写前D/E双备份；C++/H维持UTF-8无BOM/CRLF，Python/INI/RC/STATE维持UTF-8无BOM/LF，中文回读无新增乱码。

这些是源码AST/脚本规格/字节和接口核对，未执行C++、真实PhysX查询、游戏画面、游戏线程调度或FPS测试。未编译按code-modification-principles明确边界执行，不能拿旧DLL冒充080已生效。

## 用户编译与对照

编译`IrisArsenal.sln`，Release|x64／v100；正常退出游戏后执行`UpdateMod.cmd`。080合同和源码时间门均通过才组包；直接用旧DLL运行Update会明确拒绝，不会把待编译源码当作已优化。正常使用保持DiagnosticHideEffects=0。

需要测GPU相关性时，先用0运行固定场景采样，再以1重启后复现相同场景；相同人数/视角/温控与日志配置。用现有Python运行tools/measure_gpu080.py，传`--label normal`或`--label hidden`与各自全新`--out`任务目录。采样器本身会产生少量测量开销，两组保持一致；如要FPS/帧时间结论须额外实际采集呈现帧时间。

## 文件与恢复

主要源码：IrisCombat.cpp（实例参数复用/局部资格/单次光炮/隐藏诊断）、native/NativeMultiContact.cpp（零墙快路）、IrisDiagnostics.cpp/.h（诊断索引/身份）、IrisArsenal.rc（版本）。配套stage_package/test_update、两份INI、待编译清单、STATE、新专项测试/手动GPU采样器和本文。

原始双备份：

- D:/CodexBackups/Iris-Performance080-20261023-015832-78d04f
- E:/AIWorkSpace/_backups/Iris-Performance080-20261023-015832-78d04f

审查中构造初始化与测试工具的小修订也分别写前双备份，精确路径见任务reports及子目录reports。恢复源码需从最初备份成组恢复上述改动文件；当前游戏DLL/资源没有改，无须回滚游戏目录。新文件清单在最终报告，不能把恢复旧源码与部署新DLL混用。

任务：D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-Iris-Performance080-20261023-015832-78d04f
