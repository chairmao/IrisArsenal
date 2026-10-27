伊莉丝·锤枪 | Iris Arsenal [RE_Kenshi]
工坊首发准备：2026-10-23；现有用户编译DLL：0.4.34 / IRIS_MEDICAL_GATE_083。

安装：正确安装RE_Kenshi及其KenshiLib运行库后启用IrisArsenal。
已测试环境：Windows x64 / Steam Kenshi 1.0.65 / RE_Kenshi 0.3.5 / KenshiLib 0.5.0。
RE_Kenshi官方发布：https://github.com/BFrizzleFoShizzle/RE_Kenshi/releases

获取：完成“伊莉丝锤枪·验证原型”研究（前置Basic Weapon Smithing）后锻造“伊莉丝·锤枪”。
使用：装备武器并正常攻击；近战自动选招；勾选“远程”使用三种远程招式，无需弹药。
本体没有任何RACE覆盖；角色使用专属动作需相应的独立种族动画补丁，放在种族模组与IrisArsenal之后。已有两个兼容补丁独立分发，不打包进本体。

配置位于本模组目录IrisArsenal.ini，修改后重启游戏。
若要彻底关闭诊断采集与日志，将[IrisArsenal]下这些项均设为0：
EnableLogging=0
EnablePerformanceLogging=0
EnableHookAuditLogging=0
EnableCombatDetailLogging=0
EnableWindowAuditLogging=0
EnableResourceLogging=0
保留DiagnosticHideEffects=0，以正常显示特效。

本次发布资料准备保留现有测试INI，未替玩家更改数值或诊断开关。
大规模群伤和多人同时使用会有性能开销，密集命中可能延后结算；不保证无帧率影响。
完整介绍见WORKSHOP_DESCRIPTION.txt，来源见CREDITS.txt。
preview.jpg为800×800 JPG封面；_IrisArsenal.img是相同JPG字节，供Kenshi本地预览读取。
封面为AI宣传插画，不是实机截图。
