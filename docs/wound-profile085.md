# 085：原生伤口子树与桥接外受击对照

2026-10-24。用户授权本轮对照并修改。源码0.4.36 / IRIS_WOUND_PROFILE_085；当前用户实际运行的是0.4.35 / 084。未编译、未部署，不把新源码当作已加载代码。本轮重点为伤口处理归因，未改查询、调度或伤害结果。

## 已确认的事实

084日志1133笔受击根调用共439.5553ms，addWound独占388.6784ms，占88.425%。这足以把调查重点移到医疗同步子树，但不足以证明纯原版某函数有缺陷。

重新读取本机kenshi_x64.exe、KenshiLib.dll和Steam_1.0.65.br，三者哈希与084证据相同。真实符号槽位映射如下；代码使用KenshiLib::GetRealAddress，不写死这些RVA：

| 函数 | 本机真实RVA | 对照结果 |
|---|---|---|
| MedicalSystem::addWound |0x64FE40|Iris桥接、Character::hitByMeleeAttack及Character::iShotYou均进入此入口|
| MedicalSystem::applyDamage |0x64E870|实际部位/血液/状态、可选断肢/倒地等同步处理|
| AppearanceBase::addWound |0x52FC90|0x52FCB9附近先访问woundsListMutex，随后追加伤口外观列表|
| ForgottenGUI::createScreenLabel |0x73EFC0|分配ScreenLabel、执行构造并加入GUI列表|
| MedicalSystem::splatBlood |0x792F80|计算喷血参数并交血液效果系统；需包含全部连续展开片段至0x7931AC|

addWound内部还包含部位权重临时容器、护甲覆盖、韧性减伤、伤口对象/字符串、飘字格式化等工作。新四阶段未覆盖的成本明确归入unattributed；不能将它当作零，不能把createScreenLabel之外的文本格式化费用错归GUI创建。

本轮发现当前加载日志有fixed → Buffitem.dll；kenshi.log:9255明确记录RegenModule已成功安装MedicalSystem::applyDamage Hook；已安装Buffitem.dll与其bin/Release DLL哈希一致，二进制包含MedicalSystem::applyDamage钩子名称。对应工程RegenModule.cpp:563的Hook会做装备检查、减伤与肢体保护。静态源码不是可复现构建证明，也未量出它的成本，不能断言它就是7ms原因，更不能顺手改另一个mod。

所以当前结论是：原生本身确实有这些同步成本，Iris大量命中会放大调用次数；本轮未发现Iris重复补调医疗。但“纯原版就会出现同样3～7ms长尾”仍为[MISSING]，要由新对照数据判断。

## 实际调用链与修改

IrisDiagnostics::Initialize → 原IrisNativeAudit::Configure → 新IrisWoundAudit::Configure；IrisNativeAudit::Install先装既有addWound根Hook，根成功且新开关有效才安装四个子阶段Hook。

Flush → 既有Hit TLS上下文 → 原生hitByMeleeAttack → WoundHook → 新Scope（只保存入口伤害纯值与来源）→ 原addWound → ApplyHook / AppearanceHook / LabelHook / BloodHook → 各自原函数一次 → 原样返回 → Scope提交固定统计。

桥接之外进入同一个WoundHook的受击也用同样的Scope和四阶段计时。来源iris_bridge仅指处于本插件Hit TLS同步调用域，outside_bridge仅指不在此域；它不是武器身份检查，outside_bridge可能包含其他插件/其他伤害来源，不能命名成“无mod纯原版”。同线程嵌套addWound不另算重叠根时间，嵌套及混合来源次数单列。

计时从本探针进入保存的original。加载日志显示Iris早于fixed，后装插件可能把包装放在apply_damage子探针外侧；该包装仍在外层addWound时间里，却可能归入unattributed。故子阶段既不能保证是纯原版本体，也不能保证涵盖所有插件包装。运行日志stage_chain_coverage和later_wrappers_may_be_unattributed明确这点；不为了改计时层次而运行中重挂Hook或改变mod加载顺序。

原来的IrisCombat.cpp、IrisRanged.cpp、IrisArsenal.cpp及NativeMultiContact.cpp字节保持；IrisNativeAudit.cpp和IrisDiagnostics.cpp剥离新增观察语句/版本文字后全文件token与原084相等。原生参数、Damages引用、返回、异常和每段次数保持，不补HP、不重试医疗、不合并攻击段。2.5ms/32/FIFO、范围/倍率/敌我/护甲/经验/动作和特效不变。

## 新日志

| 前缀 | 用途 |
|---|---|
| wound_profile_ready | 085实际启用、根和四探针覆盖、TLS/锁初始化状态 |
| audit_wound_profile | window/process、两来源的根/四阶段inclusive和exclusive/余量，逐根调用固定桶 |
| audit_wound_damage_bucket | 入口cut+blunt+pierce分层：≤50、(50,200]、(200,1000]、>1000、无效值 |
| audit_wound_max_sample | 同一最慢根样本的四项独占及余量，避免把不同样本的各阶段最大值相加 |
| wound_profile_status | TLS故障等导致诊断关闭时明确报告；不关闭游戏/武器 |

各阶段每根都取样，未调用阶段为0；stage_invocations说明实际次数。inclusive允许嵌套不可相加；exclusive加余量与根时间核对。按根退出归属窗口，活动根跨窗口时将在退出后的窗口提交；不是逐帧FPS测量。Hook未安装时该阶段仍算余量，不能断言无耗时。

入口伤害是在addWound入口、护甲处理前快照，可能已经过此前其他插件的改写；不能当实际扣血。伤害分层只能减少对照偏差，不能消除护甲、种族、肢体、视距、倒地/断肢、其他插件与系统调度差异。

判断办法：若同档位的outside_bridge也有相同长尾且同阶段占大头，说明不是Iris独有的调度/碰撞代码所致，但仍需区分原生和同装插件；若主要落在apply_damage，进一步检查必要医疗、倒地/断肢与现存applyDamage Hook；若主要落在appearance_wound或screen_label/splat_blood，则优先核查外观锁/GUI创建/血液显示成本，不能直接删医疗；若仅Iris显著更慢，要先对照伤害档位和同时命中量，不将相关性当因果。

## 开关、开销和安全

新增EnableWoundDetailProfiling程序缺省0；本地distribution与package显式1。还需EnableLogging、EnablePerformanceLogging、EnableCombatDetailLogging及EnableNativeHitProfiling为1，启动读取。设新项0时四个新Hook不安装；已有084根Hook仍按旧开关决定。发布副本可设0，不回写正式版2.0。

没有额外角色/装备/医疗状态查询，没有逐笔字符串分配或IO；根及四阶段只在当前线程栈计时。开启会增加TLS/QPC及短聚合锁成本，不能称零开销，需开/关对照。不缓存游戏对象，不新建线程，不转移原生医疗线程。

新statsMutex只保护固定值聚合/快照/代数切换；锁内没有游戏调用、日志或Iris::mutex获取。摘要先复制再释放此锁，之后才格式化/日志；不存在statsMutex→Iris::mutex反向持锁。原游戏或其他插件自身的锁不被替换。窗口清零与提交互斥，进程累计不清零。

读档只推进代数，旧栈自然退出并计invalidated，不释放TLS/锁；异常退出用RAII恢复TLS及阶段栈，原异常仍传播。所有新增TLS读写/计时保存恢复LastError；TLS写失败将原子关闭本诊断，后续在读取旧栈地址前返回，仍转发原函数，不恢复/重放医疗。

## 已执行验证

- 本机十个符号函数离线指令/真实槽位及SDK签名对照，未附加进程。splatBlood等函数含连续pdata展开片段，不能把第一个片段当整个函数；另保存full-context证据。
- 352个实际Stat::Add AST输入、7个分位、11个伤害边界；192个阶段析构；64个开关/失败组合、3个关闭短路与2个TLS写入结果。
- 四新Hook共160组实际转发调用AST用例，含异常哨兵；旧两Hook64组转发保持。不是ABI机器码执行。
- 原084根/诊断全token对照；8份战斗/查询源字节不变；14份C++/H语法树通过。旧的__declspec(align(64))仅在语法工具输入里剥离，生产源码未改。
- TLS隔离/混合嵌套/读档和摘要/提交两种顺序是纯值规格，不冒充Windows并发实测；既有7种重入/FIFO、102目标软预算和9个epoch表达式规格保持。
- 更新脚本隔离21项中20通过，1因Windows没有创建测试符号链接权限跳过。旧084实际DLL被明确拒绝为085，无伪造产物。

尚未执行：MSVC编译/链接、真实Hook ABI、Windows并发、引擎医疗、视觉和性能开关A/B；没有新运行统计或FPS改善承诺。技能编译边界原文：“Never attempt to compile, build, link, or regenerate binaries during a conversation.”，来源C:/Users/周凡稀/.agents/skills/code-modification-principles/SKILL.md。

## 用户编译与下一次采样

编译E:/KenshiProject/2.Projects/IrisArsenal/IrisArsenal.sln，Release|x64 / v100；正常退出游戏再运行UpdateMod.cmd。源码0.4.36待编译，当前包保留实际084 DLL及版本，同时ready=false/pending_version=0.4.36，防止误认为已部署。

本地新开关已1；真实游戏目录未修改。下一轮日志先核对0.4.36和wound_profile_ready的root/apply/appearance/label/blood均1，再比较两来源的伤害档位和各阶段。没有outside_bridge样本时不能凭空得出原版对照结论。

## 产物与逐文件报告

任务证据：D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-Iris-Wound085-20261024-020930-624034。native-evidence085.json / external-context085.json / validation085.json；原始指令文件只新建。

每次改动即时逐文件报告在reports/，含File、Role、Code location、Before、Changes、Reasons、After、Impact、Validation、Safety、Unresolved。备份根：D:\CodexBackups\Task-Iris-Wound085-20261024-020930-624034；第二盘：E:\AIWorkSpace\_backups\Task-Iris-Wound085-20261024-020930-624034。原UTF-8/BOM/CRLF或LF保持，中文与乱码扫描通过；新文件UTF-8/LF。原DLL、FCS、资源、真实游戏配置、独立种族补丁及正式版2.0封存不改。
