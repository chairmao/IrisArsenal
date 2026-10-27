# IrisArsenal 0.4.4：六招近战小僵直与大踉跄免疫

本轮用户要求：除无特效的破坏之锤三连击外，其他近战招式在演出期间免疫全部普通受击僵直和踉跄。代码已完成，未编译、未部署、未实机验证。新的代码标记为 `IRIS_MELEE_REACTION_044`，资产格式保持 `IRIS_EIGHT_042`。

## 范围与结果

火焰翻滚、螺旋飞舞、地震、螺旋袭击钻天破、全力爆发、电脉加农共六招：在当前原生动作有效期间，免疫原生命中入口产生的小僵直、大踉跄，不再按强度阈值放行大反应。043的主动格挡接管保护仍有效。

破坏之锤三连击及火神炮、脉冲之焰、极致驱动三招远程保持原生反应。不是只要持有锤枪就一直免疫，也不因收招后的弹体/火焰仍存在而继续免疫。

伤害、护甲、流血、部位伤势及原生医疗正常；死亡、昏迷、医学原因造成的倒地/肢体垮塌、已经进入的倒地或受击反应、镣铐、世界加载/重置等仍由游戏处理。没有把角色维持为存活或可战斗状态，也不在动作被合法取消后强行重播。因此这里保证的是阻止本原生入口的小/大受击反应接管，不是死亡、读档或任意其他插件强制取消后也必须继续的绝对演出锁。

## 实现依据

离线读取本机游戏可执行文件、KenshiLib导出及RE_Kenshi映射确认：

- `Character::hitByMeleeAttack`：`MedicalSystem::addWound` 在前，`Character::_startStumble` 在后。
- `Character::iShotYou`（弩/鱼叉命中）：同样先 `addWound`，再 `_startStumble`。
- `_startStumble` 内部会通知身体任务结束，选择大小受击/疼痛动画，并调用 `_getHit(...,true)`，所以需要在此入口前决定保护。
- `CombatClass::_getHit(...,false)` 保留退出潜行、原生deadTime及技巧检查计时；不进入设置 `STARTUP_STATE / STUMBLE` 和反应强度的分支，不会再调用医疗。

完整原生反汇编位于 `melee-reaction-044-evidence.json` 指向的本轮任务目录。地址只用于离线取证；运行代码仍经 `Native(&Character::_startStumble,...)` 地址式绑定，不用修饰函数签名、固定RVA或对象偏移。

`IrisCombat.cpp` 将原仅钻天破的门替换为 `MeleeStumbleHook`。它与原格挡检查共用 `ProtectedMeleeMove`，后者保留043窗口语义，只改为共用名称。必须是六招私有技巧、当前CHOP_WEAPON、未到原生结束门、原生动画仍播放、Requirements与角色缓存身份一致，世界/角色/武器有效。首帧不依赖可能晚一安全帧才认领的特效active标记。

满足窗口且伤害字段为有限值时，跳过原反应函数，离开插件缓存锁后只调用一次 `_getHit(false)`；否则原参数转交原函数。没有修改伤害数据、共享技巧、血量、原生韧性、根位移或人物坐标，也没有第二次医疗、新的全局锁或新增钩子。钩子总数仍18。

## 日志

启动行：`melee_reaction_guard_ready build=IRIS_MELEE_REACTION_044`，附六招名单和三连击/远程排除范围。

受保护命中：`melee_stumble_guard`，含招式名、cast与反应次数，明确 `small=immune large=immune medical=unchanged`。每次已认领动作只记前三次反应细节，收招输出总次数 `melee_stumbles_suppressed`。首帧尚未认领时cast=0，不错误归到上次施放。旧 `drill_stumbles_suppressed` 字段仅钻天破保留真实数值，其他招式为0。日志不设总行数上限，轮询保持关闭。

## 验证与交付

完整非编译验收通过：20份动作/握持轨道、20个特效、FCS/源事件、材质/序列化与C++语法树。专项通过980个近战/远程来袭、招式/进度/强度流水组合和75个失效边界；9个原医疗、事件、移动、选择/攻速函数保持原摘要，共用窗口与043去注释归一后相同。11项同步脚本备份/回退/配置保持/旧DLL拒绝测试通过。

模型没有执行C++或真实AI，语法树不是MSVC编译结果。134个资源文件不变，现有旧DLL及实际游戏文件本轮也未改。修正旧回归测试将DLL误归为不变资产的问题：资源继续核验原哈希，DLL由当前代码标记和源码时间门检查，避免用户第二次更新时被旧DLL哈希阻塞。

仍需实机测试六招首/中/末段反复遭受近战和弩弹、不同反应强度、连续施放、正常收招后恢复受击反应，并对照三连击和远程不免疫、伤势/昏迷死亡、暂停变速及读档。没有FPS、长期稳定或任意第三方插件兼容性结论。

请编译 `E:\KenshiProject\2.Projects\IrisArsenal\IrisArsenal.sln` 的 **Release|x64 / v100**，正常退出游戏后运行 `UpdateMod.cmd`。组包必须找到 `IRIS_MELEE_REACTION_044`；旧043及更早DLL将被拒绝。当前包 `ready=false`，未代编译或部署。

逐文件改动、备份及编码见 `melee-reaction-044-files.json`；完整验证见 `validation-0.4.4.json` 和 `melee-reaction-044-validation.json`。
