# 060：三远程共享炮口和原生瞄准点

本次源码版本为0.4.17。现有包内和游戏DLL仍为0.4.16/059，没有冒充新编译结果，也没有自动部署。

## 实际改动

- IrisCombat.cpp 的 Emit 继续用原公式 `Muzzle(weapon)+a.origin`。Muzzle、Tick及动作/模型资源没有修改，所以射出位置仍随当帧真实炮口，不增加高度、平移或头部偏移。
- IrisRanged.h 的 AimFrame 传递世界坐标纯值和稳定目标身份。IrisRanged.cpp 的 CaptureAim 把上述实际炮口原样同步给同一个 HybridGun，目标点读取原生 RangedCombatClass::currentAimPos，不再由三招自行另选身体骨点。
- 火神炮、脉冲之焰、极致驱动使用相同的目标点减炮口并归一化。弹道/光柱绘制与角色碰撞消费同一快照；原生 getAimDir 保留其目标参数，也采用同一个归一化函数。
- 当前动作中目标失效时，仅保留最后一次有效的原生瞄准值。没有有效值且空闲时不发布开火许可；Finish/Reset清除缓存。没有缓存Character、骨骼节点或PhysX裸指针。
- IrisArsenal.rc 标识0.4.17。stage_package.py 增加 IRIS_NATIVE_AIM_060 身份校验，旧DLL不能作为新源码部署。UpdateMod日常流程仍不重建资产、不调用历史回归、不编译。

## 原生证据与边界

已从本机KenshiLib导出槽、Steam_1.0.65.br映射和真实游戏PE核对：原生 updateMT 生成 currentAimPos，射击检查通过Gun的getAimDir/getBarrelPos取方向和起点。原生目标身体点和现有Character骨骼包装使用同一AnimationClassBase世界坐标方法；currentAimPos不应再加插件浮动原点。

取证文件在同会话 Task-Iris-NativeRangedLOS-20261020-182055，以及其中的coordinates-identity.json和对应反汇编。头文件RVA注释没有作为真实函数入口使用。

本次没有再次调用 takeTheShotCheck、getAimPos 或原生Tracer，没有新增Hook/线程/锁/查询，没有修改原生YES/NO/MAYBE、装填、权重、伤害或移动状态机。原生许可与后续发射存在时间间隔；这次共享当阶段数据并不等于重新做每发原生遮挡判定，也没有实现受阻后走位反馈。

## 已执行验证

本次 tools/test_shared_aim060.py 的7项检查全部通过；对10个C++/H文件运行Tree-sitter语法检查无语法错误。该检查不能代替MSVC类型/链接验证或游戏运行。

修改前摘要与当前逐函数核对：15个战斗函数、14个远程函数保持；139个非清单包内文件（含旧DLL）保持。专项检查覆盖炮口原样传递、原生点/方向共享、缓存生命周期、无额外查询及旧DLL被拒绝。未编译、未启动游戏、未进行FPS或运行画面验证。

## 编译与使用

由用户编译 IrisArsenal.sln，Release|x64，v100。编译完成后正常退出Kenshi，执行UpdateMod.cmd。只有新DLL包含060合同且通过时间与构件校验后才可组包部署。仅运行更新脚本不能替代编译。

## 备份与报告

原文件逐一双备份，目录为：

- D:\CodexBackups\Task-Iris-SharedAim060-20261020-184455\E\KenshiProject\2.Projects\IrisArsenal
- E:\AIWorkSpace\_backups\Task-Iris-SharedAim060-20261020-184455\E\KenshiProject\2.Projects\IrisArsenal

逐文件报告、修改前副本和validation.json在 D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-Iris-SharedAim060-20261020-184455。旧文件保持原UTF-8/BOM及换行风格，新文件UTF-8/LF；已回读检查中文和乱码。
