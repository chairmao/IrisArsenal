# 079：远程锤枪阻断家具工作的持械状态修复

日期2026-10-23。用户确认：勾选远程时，到达研究/耕作家具后站着且工作进度不增长。根因核查、源码修复及非编译回归完成；尚未编译、部署或游戏实测。

## 明确的错误与原生调用链

旧IrisRanged.cpp的HasHook在Eligible成立且Slot发布时恒真。Eligible只要求主/副武器槽存在该锤枪及远程等资格，不要求手里拿着它。于是角色已经收起武器仍被报告为“弩已装备”。

本机Steam 1.0.65真实EXE经KenshiLib导出桩/RVA映射只读核对：

1. AI::hasCrossbowEquipped 0x595FE0调用角色getCurrentWeapon，再调用当前武器isCrossbow；没有当前武器返回假。
2. AI::hasAnythingEquipped 0x60DAB0先调用hasCrossbowEquipped，真则立即返回真，否则才查hasWeaponEquipped。因此旧HasHook会把原生“手中已空”结果污染为“有装备”。
3. AI::_NV_stateIsTrue 0x60E8F0调用注册谓词，与TaskStateData.val相等才满足要求。AI::_setupGOAPFuncs中157/156分别注册HAS_ANYTHING_EQUIPPED/HAS_CROSSBOW_EQUIPPED。
4. Task_SheatheWeapon的真实vtable runAction经跳板解析到0x336BC0，调用角色sheatheWeapon；CharacterHuman::sheatheWeapon 0x5CBD90卸载手中附件、setEquipmentInHand(false,false,NULL)、清CharStats.weapon。旧Hook在这之后仍为真，这是明确反例。
5. Task_OperateMachine startAction 0x35B3D0（0x35B4E6）同样先sheatheWeapon；runAction 0x35BC30读取家具动画并playAction，后续产出/经验由原生处理。
6. Task_RangedAttack runAction 0x33BF70才调用远程setup/updateT；其endAction 0x33C060调用远程end。远程end会stopAllAnimation，不能为修工作在任意通用动画Hook内额外调用它。

证据和原始反汇编保存在本会话任务目录；“有能力”与“已经拿在手里”不是同一谓词。用户现象与明确反例吻合；本轮没有附加进程，未直接读取故障角色的运行时任务，因此不把本次源码/离线证据称作故障现场完整回放。

## 最小完整修复

- Held仅用getCurrentWeapon的真实FCS身份。HasHook仍发现库存能力，但仅实际手持锤枪时返回本枪已发布状态；空手、其他真弩/武器等原样转原生，传参保持且只调用一次。
- GunHook同样只为实际手持锤枪返回私有Gun，不能因库存里还有锤枪接管手里的真弩/炮台。
- UseHook、ScoreHook库存能力发现保持，避免未拔枪就永远失去远程能力。
- 新Equipping只在既有主线程AI/物理静止安全窗口读取当前CharBody任务，识别原生EQUIP_CROSSBOW。Prepare在该任务或原有远程combatMode分支调用原生drawWeapon。修正Has后，未拔枪→原生装备任务→安全拔枪→Held真→原生远程setup/LOS/装填/射击，不依靠伪造“已装备”跳过阶段。
- 不因远程勾选就新增工作时的拔枪；既有combatMode路径保留。原生Task_RangedAttack退出会关闭该模式。没有添加工作任务黑名单、修改动画/任务状态、永久强制收武器、后台线程、新锁或新Hook。
- 18个安装Hook数不变。Start/Run仅修改本插件技巧，六特效近战/三远程抗打断只在真实专属播放窗口工作；三连例外、医疗/站姿、伤害、敌我、射线地形/带半径角色、特效、INI、FCS保持。
- 新构建版本0.4.30；启动一次ranged_equipment_ready/IRIS_EQUIPMENT_STATE_079。现有0.4.29的DLL原字节保持，包ready=false并记录pending，不冒充已修复。

## 已执行验证及限制

实际C++分支AST解释240组：库存能力、空手/持本枪/持其他弩剑、无数据、槽未建/发布开关、原生返回值及参数/恰一次转发；旧版本空手真值反例被检出，新版为空手假。56组实际Prepare拔枪条件覆盖原生装备/收起/工作/射击/移动与空任务、已有武器和模式。反复收起/拔出序列保持能力与真实状态分离。

六个其他远程Hook业务token及资格/瞄准/发布代码保持；323份受保护源码/运行资源/配置/FCS及现有DLL哈希保持。9份C++/H语法、3份Python AST与3个精确SDK/实际链接库符号检查通过。更新隔离21项：20通过，1项符号链接权限不足跳过；旧DLL被079合同门正确拒绝。没有MSVC类型/链接验证，没有引擎线程及家具进度实测，不能宣称实机已恢复。

## 交付与备份

用户编译E:/KenshiProject/2.Projects/IrisArsenal/IrisArsenal.sln，Release|x64，v100；正常退出游戏后运行UpdateMod.cmd。脚本不编译，只有识别到新合同的实际用户DLL才完整组包/更新。当前游戏目录未写入，不能热更新运行中的Hook。

双备份目录：
D:/CodexBackups/Iris-NonCombat079-20261023-011120-d1d80c
E:/AIWorkSpace/_backups/Iris-NonCombat079-20261023-011120-d1d80c

原编码/换行保持：IrisRanged.cpp、IrisDiagnostics.cpp为UTF-8无BOM/CRLF，rc及Python/包清单UTF-8无BOM/LF；每次写入后严格解码/回读和中文乱码扫描通过。逐文件报告见任务reports目录。
