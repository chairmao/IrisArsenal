# 062：撤销额外远程起手步骤

源码0.4.19 / IRIS_RANGED_GATE_062，未编译、未部署。当前实际游戏DLL为用户编译的0.4.18/061。

## 错误与范围纠正

061为了匹配弹速预判，未经用户要求把私有选招提前到原生射击许可之前，并增加AnimationHook要求上一安全帧aim.target与本次原生目标相等的条件。这不是伤害修复所必需，也改变了已经工作的起手链。此前专项验证了局部条件和数据保护，但没有覆盖原生重新选敌和缓存发布交错的起手活性，不能以那些通过结果保证整条链能启动。

当前日志证据：IrisArsenal-20261020-201757-916-35856.log，PID35856、创建FILETIME134369722456767194，真实DLL0.4.18。观察片段20:19:39资源就绪、20:20:19开始选招、plugin_ready/native_aim_ready/gun_ready均曾为1，却没有ranged_action_requested。三个gate采样点aim_timer为0.4；旧日志没有原生动画回调的实际布尔条件，因此不能声称计时全程恒定或缓存门是该次运行的唯一原因。

本机实际PE原生顺序：updateT先reAssessTargeting，再animationUpdate，然后takeTheShotCheck；动画未就绪的检查路径将aimTimer重新设为0.4。合法目标更新可以与上一安全帧缓存不一致，这个额外条件存在阻断路径，应撤掉而不继续叠加补丁。离线模型证明该边界可停滞；它不是游戏复现证据。

## 最终实现

- 完全删除提前选招/Actor.rangedChoice与目标预约；亦撤销本轮中途拟加的publishedMove/requestedMove招式快照传递，没有部署过该中间方案。
- 恢复原先流程：发布实际炮口与原就绪值 → 原生选敌、视线、瞄准等待、装填与开火许可 → ShotHook只提交目标 → 安全阶段TakeRequest → 按该目标FCS距离/INI权重PickRanged → 原生动画。
- AnimationHook就绪表达式与工作版060相同，不以haveAim、目标缓存相等或招式预测模型增加门槛。原生评分、getAimDir、lookatPosition参数与Gun起手shotSpeed=320恢复原值。
- 仅实际Emit指定本发有效弹速800/440×动作速率；调用原生getAimPos时临时传给本插件独占Gun，局部析构恢复shotSpeed及_lastAimAheadAmount，异常同样恢复，不改下一轮许可状态。即时光炮在Emit取原生同源身体点。默认Publish只读currentAimPos，不改写它；故原生起手检查与实际发射之间仍存在时间/预判差异，不能宣称逐发重新许可或受阻自动换位。
- 保留061的原生四项受伤资格、不可伤角色透射、直接接触身份加入同段名单、FCS10000真实飞行上限及无限事件日志。DamagePolicyReason、Contacts、AdvanceEffects、Blast、ResolveJobs、Flush等与本轮修改前061逐函数相同。
- 地形仍为中心射线，火神/脉冲角色仍R4.5连续球扫掠，光炮仍R9平端圆柱。Muzzle、所有NativeMultiContact/FiniteCylinder、材质、动画、FCS和配置数值保持。18个Hook，无新增线程、锁或移动控制。
- 新ranged_animation_gate仅在原生回调状态变化时诊断，记录实际ready/available/pending/eligible和缓存一致性；缓存一致性只是诊断，不参与开火。新运行标记IRIS_RANGED_GATE_062。

## 已执行验证

8项通过：原就绪表达式256组布尔组合；原生重新选敌交错的起手模型；许可之后选招整个控制块与060逐字符比较（只允许CanDamage替代旧Enemy及注释差异）；原方向/评分/默认参数；实际发射预测局部恢复；061伤害/几何函数保持；137资源及配置值保持；旧061 DLL被062身份门拒绝。10个C++/H语法树无错误。不执行编译、C++、PhysX或游戏，不声称已实测恢复射击。

此前061专项保留为历史证据，不改旧断言冒充本轮已通过；062检查在任务目录test_restore062.py，未接入UpdateMod。日常Update仍只组包、复制和校验，不重建资源或运行这些测试。

## 使用与备份

请用户编译IrisArsenal.sln / Release|x64 / v100；正常退出游戏后运行UpdateMod.cmd。只运行更新脚本不会产生新DLL。当前包ready=false明确等待用户编译；不拿旧061当作修复版。

任务证据：D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-Iris-RangedGate062-20261020-202431-650392。逐文件报告及精确双备份见ranged-start-062-changes.json。原UTF-8/BOM/换行保持，中文无新增乱码。备份在D:\CodexBackups及E:\AIWorkSpace\_backups下同名Task-Iris-RangedGate062-*目录；初始任务保存实际061原文件，RestoreNative/Finalize分别保存撤销中间方案前的版本，报告逐次注明。未修改运行中的游戏目录、日志或存档，没有操作游戏进程。
