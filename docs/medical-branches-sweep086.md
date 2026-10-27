# 086：局部扫掠索引与原生医疗分支归因（源码0.4.37）

2026-10-24。Owner: Codex。用户要求沿原生安全调用链推进优化，并特别区分游戏自身缺陷和模组成本；随后指定只读检查Buffitem与Example。当前真实游戏包仍0.4.36/085；本轮源码0.4.37未编译、未部署，不宣称已有FPS改善。

## 实际修改与调用链

查询：原安全Tick → Contacts → 原SweepAll/ProjectileAll → PhysX完整扫掠 → Collector::onEvent → 同形体查找 → 原TOI/接触替换与排序 → 稳定身份 → 原伤害队列。

仅将Collector原先逐项比较NxShape*的查找，改为少于16条时原线性路径、达到16条后本查询局部开放寻址表。128个内联槽、半载扩容、哈希冲突仍比较完整形体指针。表存已有shapes名单下标，不按角色合并不同形体；每个形体仍保留最早接触，之后仍用原排序。超过256形体时沿用既有动态shapes存储，没有新人数上限。

索引分配失败或内部表不变量异常时，只禁用本次索引并退回原线性查找；不重做PhysX查询、不漏掉既有名单、不改变原失败重试。所有形体指针仅在本次同步Collector栈内借用，最终输出仍只有稳定身份和纯值，不跨帧缓存NxShape/NxActor，不添加线程、锁或引擎调用。

原医疗路径：Flush → 每笔原世界/物理/AI/暂停检查 → 原资格和目标相关伤害计算 → 一次_NV_hitByMeleeAttack → addWound → applyDamage → 原医疗分支 → 原受击反应/反馈/经验。2.5ms/32/FIFO不变，不合并不同攻击段，不将医疗转到后台。

另将IrisDiagnostics::Add的零增量在共用锁之前短路。零增量没有统计贡献；原窗口快照、读档和非零累计不依赖这次空锁。这样新增索引字段为0时不会让其他查询多拿统计锁，也减少旧零计数的同类开销。关闭日志时新索引不做统计、不增加计时；索引本身仍工作。

## 原生实现是否有缺陷

本机kenshi_x64.exe、KenshiLib.dll和Steam_1.0.65.br哈希与085证据一致。离线重新核对真实导出槽位和完整相邻展开片段，没有附加游戏进程。

| 原生入口 | 本机真实RVA | 已确认行为 |
|---|---|---|
| Character::ragdollMode | 0x5CB2D0 | 先检查已有ragdoll部位/整体状态，并检查待处理消息；不能用一个isRagdoll替换它的部位/消息语义 |
| MedicalSystem::amputate | 0x64E330 | 读取真实LimbState；存在义肢/原肢/碎裂/残端的不同分支，并可创建断肢物品、外观、出血和AI重评 |
| MedicalSystem::ragdollPartCollapse | 0x648DE0 | 根据部位、肢体状态和角色状态决定局部ragdoll，不是单纯改一个布尔值 |
| MedicalSystem::updateDamageState | 0x645DD0 | 更新伤残移动状态、最大速度，还可能发气味消息 |
| SeveredLimbItem::setupFromCharacter | 0xCECD0 | 获取角色外观、骨架和骨尺寸等同步工作 |
| RootObjectFactory::createItem（六参数重载） | 真实符号精确匹配 | amputate实际调用此重载；源码用精确成员指针选择，再交KenshiLib解析，不写死RVA |

085中applyDamage子树占伤口耗时87.6%、高伤档占伤口总时间83.8%，但这并不能证明原生代码有缺陷。原生已有防重复逻辑，直接再加短路可能跳过必要状态/经验/其他Hook。本轮没有发现足以安全替换原生医疗分支的证据，因此只细分计时。必要的断肢造物成本、原生可消除冗余、其他模组包装以及系统调度尚须分开。

## Buffitem和Example

实际加载顺序：IrisArsenal → fixed/Example.dll → fixed/Buffitem.dll。两份游戏DLL分别与各自bin/Release DLL一致；这不是源码可复现构建证明。

Example.cpp:123的HookedApplyDamage会检查玩家、装备并改写伤害，亦Hook截肢/踉跄/medicalUpdate。Buffitem/RegenModule.cpp:563的HookedApplyDamage会做部位保护、装备检查和减伤，亦Hook截肢/局部倒地等入口。都保持只读，没有修改两个工程、配置或加载顺序。

后装包装可能在我们的阶段探针外侧，其包装费用可进入父范围的unattributed。新六阶段仍只覆盖本探针到保存的original；既不能称纯原版，也不保证覆盖全部第三方包装。outside_bridge仅指不在Iris命中TLS内，并非无mod对照。

## 新分支探针和配置

EnableWoundBranchProfiling程序缺省0；本地distribution与package显式1，真实游戏INI本轮未写。还需EnableWoundDetailProfiling、EnableNativeHitProfiling及日志/性能/明细总开关有效。设新项0则六个新增Hook不安装；关闭总日志也不安装这些诊断Hook。发布时可关闭，不能把本地测试配置误当发布配置。

只在既有addWound根TLS中记录六个新阶段：amputate、item_create、limb_setup、update_damage_state、part_collapse、ragdoll_mode。各Hook保留全部引用/参数/返回和异常，原函数同步调用一次；不增加医疗次数。普通造物/布娃娃调用没有伤口根时只转发，不创建新根或保存引擎对象。

固定数组由4项扩到10项，复用原TLS、epoch、统计锁和摘要。没有新增线程或锁对象，没有逐击IO。子阶段计时从父exclusive中扣除；跨085/086版本应比较两轮apply_damage的inclusive，不能把086父exclusive下降误报为优化。统计所有exclusive加unattributed与根守恒；同一次最慢根的十项一同保存，不能相加不同命中的最大值。item_create次数是同步子树内的该重载调用数，不能无条件叫作截肢次数。

启动核对medical_branch_ready的enabled及六个_hook均为1。audit_wound_profile继续按window/process和iris_bridge/outside_bridge输出。audit_wound_max_sample追加六项独占时间；某Hook失败只意味着未覆盖，时间归入父项或余量，不禁用武器。

sweep_shape_index_ready标记IRIS_SWEEP_SHAPE_INDEX_086。长期摘要追加sweep_shape_comparisons、sweep_shape_probes、sweep_shape_linear_equivalent、sweep_shape_tables、sweep_shape_index_fallbacks。linear_equivalent根据实际找到的原名单下标推导旧线性比较数，没有执行旧扫描或额外旧查询。比较工作量时还要看探测、重建和真实sweep耗时，不能把比较数下降直接当FPS改善。

## 实际验证与范围

- 实际索引方法C++语法树解释：73组、10043次查找与原线性下标一致，覆盖16/64/256边界、哈希全冲突、扩容、分配失败、满表退路、关闭统计和查询间重建。
- 1024形体重复三遍的纯值规格：旧线性等价1573376次比较，实际指针比较2937次，含重建7492次探测、6次表构建。只是算法工作量，不是C++/PhysX耗时或FPS。
- 原Collector消费体移除查找替换/纯计数后逐token相等；Collector外全部Native代码相等；整个IrisCombat移除新增计数后逐token相等。原命中集合、TOI、初始重叠恢复、排序、地形射线/角色半径、调度和医疗正文保持。
- 10个Hook的320组实际转发调用AST检查；480组实际阶段析构；8组分支门、352统计输入/7分位/11伤害分桶；TLS嵌套/混源/读档/摘要顺序为纯值规格。24组零计数AST、1024医疗门、972ready条件及7种FIFO重入/102目标软预算/9个epoch条件通过。
- 14份C++/H语法工具检查通过；工具不支持合法成员函数指针typedef及既有对齐声明，仅解析输入中精确替换，生产源码不变。真实重载已对SDK和导出核对；这不是MSVC类型/链接验证。
- 更新隔离21项：20通过、1因系统符号链接权限跳过。旧真实085 DLL被086合同明确拒绝，未制造假产物。实际游戏清单全部文件哈希有效，版本仍0.4.36。
- 每次既有文件修改前双备份；UTF-8/BOM/CRLF或LF保持，新中文C++注释使用ASCII闭合块注释，避免上次v100中文行注释吞行。变更后读取检查点用于验证后续文件保持，不伪称全任务初始快照。未修改游戏文件、存档、FCS、模型/特效或正式版2.0。

未执行MSVC编译/链接、真实Hook ABI、Windows并发、游戏或GPU/FPS实测。新探针开启有TLS/QPC与聚合成本，不能称零开销。原生游戏缺陷仍未确认；下一轮先看哪条具体原生分支出现毫秒长尾，再决定是否有可保持语义的冗余可删。

## 用户操作

编译 E:/KenshiProject/2.Projects/IrisArsenal/IrisArsenal.sln 的 Release|x64 / v100；正常退出游戏后运行UpdateMod.cmd。源码/日志/RC为0.4.37，组包要求两个086合同。工作包保留真实0.4.36 DLL与身份，ready=false/pending_version=0.4.37；不得把旧DLL当作本轮已部署。Update流程仍只校验和复制构件，不代编译或重做资源。

证据、原生指令、验证和即时逐文件报告：D:/CodexWorkSpace/Sessions/20261002-235652-kenshi-crash-407794f2/Task-Iris-Medical086-20261024-030412-760704。
双备份根：D:/CodexBackups/Task-Iris-Medical086-20261024-030412-760704 与 E:/AIWorkSpace/_backups/Task-Iris-Medical086-20261024-030412-760704；零增量入口的第二次修改在revision-2内。逐文件角色、改动、影响、原/后哈希、验证、编码与未验证范围见reports/及revision-2/reports/。

| 文件 | 原状态与本轮变化 |
|---|---|
| native/NativeMultiContact.cpp | 原同形体线性查找改为局部索引；原SDK调用及消费者保持 |
| native/NativeMultiContact.h | 原值接口末尾追加五项工作量，不携带SDK指针 |
| IrisCombat.cpp | 仅在原查询完成后汇总五项计数，医疗与调度不改 |
| IrisDiagnostics.h | 原计数枚举末尾追加，旧下标保持 |
| IrisDiagnostics.cpp | 新开关、五计数、版本/合同；零增量锁前返回 |
| IrisWoundAudit.h | 固定栈统计由4项扩为10项，增加独立开关参数 |
| IrisWoundAudit.cpp | 新六分支原样转发探针和摘要，复用原生命周期保护 |
| IrisArsenal.rc | 0.4.37，纠正无关旧资源注释 |
| tools/stage_package.py | 追加086双合同和版本，不编译 |
| tools/test_update_mod.py | 适配真实旧085产物拒绝测试，保留其余隔离用例 |
| distribution/IrisArsenal.ini | 本地测试启用分支诊断，其余键保持 |
| package/IrisArsenal/IrisArsenal.ini | 同上 |
| package/IrisArsenal/IrisPackage.json | 实际旧DLL身份保持，标记新源码待编译并更新INI哈希 |
| docs/medical-branches-sweep086.md | 新增本说明和全部边界 |
| STATE.md | 记录085已实际运行及086待编译状态 |
