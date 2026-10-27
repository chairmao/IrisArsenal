# Hook与状态契约

行为Hook共18处；原生医疗深层探针最多另有12处，是否安装由开关、父探针与地址可用性决定。Hook审计枚举数量不等于实际安装数。

## 行为入口清单

| 原生目标 | 本项目Hook | 目的与转发边界 |
|---|---|---|
| GameWorld::_NV_mainLoop_GPUSensitiveStuff | FrameHook | 保留原函数，建立主线程/帧/世界上下文与游戏dt；帧尾仅日志 |
| GameWorld::charsUpdateUT | SafeHook | 原函数先执行，安全门后Tick与锁外Flush；每帧一次 |
| GameWorld::resetGame | ResetHook | 原复位前清插件世界数据/时钟；仍调用原函数 |
| Renderer::shutDown | ShutdownHook | 先释放自有场景对象和日志，原关闭继续 |
| CharStats::chooseAttack | ChooseHook | 原生一次；只有实际专用武器且资格适用才替换 |
| AnimationClass::startCombatAnimation | StartHook | 私有身份才进慢路；速度归一化，记录起手通知 |
| AnimationClass::runCombatAnimation | RunHook | 私有速度；普通技巧直接原转发 |
| Character::shouldUseRangedWeapons | UseHook | 专用武器发布远程能力；普通角色原转发 |
| AI::hasCrossbowEquipped | HasHook | 必须区分实际拿在手里与仅库存有此物 |
| AI::_NV_scoreRangedAttack | ScoreHook | 是行为选择评分，不是伤害倍率；保留受近战压制及队形评分语义 |
| AI::isWithinMyBowRange | WithinHook | 已发布本枪时用实际范围；否则原函数 |
| RangedCombatClass::getGun | GunHook | 只返回已准备且实际持有/正确装备阶段的HybridGun |
| RangedCombatClass::animationUpdate | AnimationHook | 适配私有身体动作，保留其他枪械原流程 |
| GunClass::shoot | ShotHook | 私有gun只发请求；其他gun原shoot一次 |
| RangedCombatClass::reloadCheck | ReloadHook | 本枪动作间隔，仍由原生装填时序推进 |
| CombatClass::_iHitYouAreYouHit | VulcanDefenceHook（历史命名） | 仅匹配本次同步TLS近战上下文才跳格挡/闪避，三远程不强制命中 |
| Character::_startStumble | MeleeStumbleHook | 只屏蔽本次私有招式允许的受击反应，医疗照常 |
| CombatClass::checkForNeedBlock | MeleeBlockCheckHook | 指定近战演出期间不主动切格挡；非本招照常 |

安装证据：IrisArsenal.cpp的RangedAddress/startPlugin，`IrisRanged.cpp:242`（Install）、`IrisCombat.cpp:1849`（InstallDefenceGate）。都经SDK成员指针与KenshiLib实际版本映射，不用头文件注释RVA代替真实函数入口。插件原子started防重复；先装生命周期与安全入口，选招最后，部分失败running不发布。

## 深层探针清单

IrisNativeAudit：MedicalSystem::addWound、CombatClass::addEffect。IrisWoundAudit：MedicalSystem::applyDamage、AppearanceBase::addWound、ForgottenGUI::createScreenLabel、MedicalSystem::splatBlood；扩展分支为MedicalSystem::amputate、RootObjectFactory::createItem指定重载、SeveredLimbItem::setupFromCharacter、MedicalSystem::updateDamageState、MedicalSystem::ragdollPartCollapse、Character::ragdollMode。

探针保存原入口并转发一次，TLS栈分开本插件同步命中与原生对照，父子inclusive/exclusive不能直接叠加。后来安装的其他mod包装可能在本探针之外，余量必须标未归因。开关关闭后已有detour转发成本可能仍存在；不能宣称进程中已卸载Hook，重启后的安装开关才决定装不装。证据：`IrisNativeAudit.cpp:65`（Install）、`IrisWoundAudit.cpp:120`（Install）。

## 身份、装备与种族

角色资格不是“玩家队员”。敌人同样可以使用本武器并伤害玩家；不按小队先筛。武器身份是实际装备对象/stringID，不是写死SKILL_HEAVY。普通角色先做低成本预筛再进原mutex，身份不确定时回原慢路，不能为优化漏掉保护。私有技巧采用原子发布的不可变身份快照，读者不读可变容器；这不是跨帧角色地址缓存。

近战起手仍有双臂可用、正常站姿、非原生crippled门。类别来自当前FCS，但“双手演出”要求没有因此自动变为任意单手招式。缺肢LIMB_STUMP、摧毁LIMB_CRUSHED、替换LIMB_REPLACED不能统一按“非原装=不可用”处理；正常义肢依赖原生isLeft/RightArmOk及医疗维护。不能自写HP<0就覆盖全部种族/武器资格。原生返回武术/趴地/混合类别时保留；原生空值并不自动禁专属远距。

非原生机器人不能出招还应检查种族动画集合是否有相应body/skeleton资源，不能把资源缺失误判成义肢资格。主FCS不批量塞种族记录；现有IKEMEN、EndPoem补丁分别独立。FCS改类别后需重新验证原生候选与身体演出，不声称支持所有类别的任意身体状态。

## 掩码、枚举和非战斗状态

| 容易混淆 | 正确使用 |
|---|---|
| 当前武器WeaponCategory / 技巧hasSkillType参数 | 用原生真实类别，不按武器中文名推断 |
| swordStateEnum / bool combatMode | 前者不能当任意bitmask，后者不能按枚举相等替代 |
| LockedArmour* shackles返回 | 指针判空不是状态位判断 |
| 敌人/中立/主动目标 | 关系动态变化，不能假定互斥标签永久不变 |
| 库存装备 / 实际手持 / EQUIP_CROSSBOW任务 | 家具工作需要真实空手；勾“远程”不能让Has/Gun永久返回持枪 |
| NxShape组位 / RootObject身份type | 一个是物理层过滤，一个是身份分类；不能混用 |

研究/耕作站住不工作的079反例来自HasHook/GunHook把能力等同于实际手持；修复后DrawWeapon只用于真实战斗或原装备任务。不要增加全局动作锁、移动锁或把所有非战斗动作过滤掉。证据：docs/noncombat-equipment079.md、hook-fast076.md、native-melee072.md及当前函数。

104取消正式Observe/Discover/Prepare的人数条件，动态map/set仍完整身份去重；retired继续等原生队列安全清空后析构。DrillProofOnly诊断原型人数与查询/医疗预算不是正式持有者上限。104已经用户编译并通过项目组包，尚无游戏实测；实际部署103 DLL仍保留旧注册门，归档已分别标明。
