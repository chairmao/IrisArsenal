# IrisArsenal 0.3.0：同一锤枪切换远近与两招原生远程间隔

用户目标：仅勾选游戏“远程”时启用极速火神炮和脉冲之焰，走原生远程武器流程，无弹药/装填动作；整套动作结束后，使用原生弩装填时间单位，固定2.0间隔。用户明确选择“保留同一件锤枪切换远近”。

## 行为与实现

- 原来的1-IrisArsenal.mod仍是同一件近战物品，ID/类型/存档和模型不变。没有添加库存弩、替换武器或对Sword做Crossbow强转。插件用合法GunClass派生类作为该锤枪的远程能力适配对象，独占的GameDataCopyStandalone只存运行参数，不加入游戏物品表/存档。
- 只扩展本枪的shouldUseRangedWeapons、AI装备能力/评分/范围、RangedCombatClass::getGun/animationUpdate、GunClass::shoot和reloadCheck，共8个限定入口。原生updateT/updateMT、选敌、接近目标、瞄准、视线与友军遮挡仍调用原生；没有挂移动/旋转/碰撞总回调。未命中的其他角色、弩与炮台快速转发原链，不争用本枪状态锁。
- 从真实主副武器槽发现能力，允许背负状态进入远程AI；原生进入远程模式后，用drawWeapon(item,item->inventorySection)拔出同一物品。发射仍须实际附件枪口、已加载FCS动画、原生目标、FCS距离、权重、并发及暂停许可全就绪。
- 火神与脉冲从近战加权池移除，只有原生GunClass::shoot已经发来的单次射击许可才在安全主线程开始一整套FCS动作。该原生调用对本适配器不生成额外弩箭，伤害仍由20发/3发真实球形特效事件进入既有原生受击队列，避免双伤害。
- 一个Gun的numShots=1表示一整套动作，不是一个特效子弹。收尾/中断才耗去许可，并通过原生reloadCheck建立间隔；reloadTimeMin=reloadTimeMax=2.0，原生calculateReloadTime会钳在两个相同端点，熟练度不会改变当前固定值。计时递减仍由原生完成，无墙钟或自制冷却器。装填完成时去掉原生另加的0.4瞄准等待；目标、遮挡、走位和并发仍可能使下一次动作更晚，2.0不是无条件强制开火时间。
- ammoType和reloadAnimation为空，原生reloadCheck本身会跳过背包找弹/扣弹；弩的CB aim/reload动画由两招真实FCS动画入口替换。身体和已发特效继续跟随角色攻速/游戏速度，2.0间隔使用原生装填单位，不再乘攻击速度；暂停冻结，未发事件随原生中断结束，已发特效按自身寿命继续。
- 保留原生弩的站姿、双臂可用和角色存活/清醒要求，义肢由原生MedicalSystem判定。模式取消、换武器或失效时只结束本适配状态并释放对应许可；FCS首帧零权重最多等待2个游戏秒，不立即误判失败，也不无限占槽/自动重播。
- 活动Gun最多8个，活动加退役合计最多16个；退役对象在AI/物理停止且原生队列清空后走标准GunClass析构；destroyPhysical仍调用原生实现注销异步Tracer，不是只改active。读取回调不碰Ogre/健康；自有队列锁不用于冻结角色移动。

当前INI仍仅vulcan=1、pulse=1，其余六招0。因此未勾“远程”时，当前测试配置不会选择任何攻击；将来启用其他六招权重后，它们仍沿近战FCS流程。火神20发/R4.5/每发0.2倍，脉冲3发/R9/每发2倍，武器基础0.1、enemy过滤、原有火神免格挡/闪避、骨点世界坐标修复与纹理共享/按需预热全部保留。其他六招和资源未重做。

## 直接证据

本机KenshiLib头：Character.h的shouldUseRangedWeapons、CharStats.h的rangedMode、GunClass.h的numShots/reloadTimeMin/Max/ammoType/reloadAnimation，RangedCombatClass.h的state/reloadCheck/timer/updateT/updateMT，Gear.h表明Crossbow是独立具体类型。仅检查开关并继续chooseAttack不能称为原生远程流程。

离线从实际KenshiLib导出桩和Steam_1.0.65.br解析入口并反汇编本机游戏：reloadCheck在ammoType为空时跳过库存流程，原生calculateReloadTime把结果钳在min/max；getGun要求真实枪械能力，updateT/updateMT分别承担动作与异步瞄准/射击，原生射击有hasCrossbowEquipped/scoreRangedAttack/isWithinMyBowRange门槛。GunClass构造只消费参数，标准destroyPhysical会清理Tracer；不是从头文件RVA注释猜地址。完整离线文本在本任务目录，地址只用于证据，运行代码全部用SDK成员指针解析。

本轮任务目录：D:/CodexWorkSpace/Sessions/20261002-235652-kenshi-crash-407794f2/Task-IrisArsenal-RangedFlow-20261016-201558-78132c。

## 验证与交付边界

已完成：4个真实C++输入单元、7个C++/头语法树；16份FCS动画实文件引用；8招事件次数/源姿态/伤害与范围；022骨点/纹理回归；16个钩子的限定与原链转发；无假弩/额外原生箭/墙钟/强制位移；原生2端点恒等；本机SDK声明和链接符号检查。源资产哈希保持，旧022 DLL组包被030合同拒绝。

未完成实证：MSVC类型/链接、实际GOAP完整路由与拔枪、两招姿态/射击视线、2单位间隔的真实日志/暂停/变速、切换模式与反复读档/Tracer释放。静态检查不能证明这些运行行为已成功，也不承诺与所有其他原生钩子模组兼容。下一次实机应依次检查startup IRIS_EIGHT_030、ranged_hooks_ready、ranged_capability_ready、ranged_action_requested、action_start/event_emit/action_end、ranged_interval begin/complete。

当前真实DLL为用户0.2.2（SHA256 87232387965B502261AC025C02EFA21C88564DB8BBDB29254C90AA3670BC1EBE），工程/包/游戏三份字节一致。本轮没有编译、部署、启动游戏或恢复轮询。按代码修改Skill“Never attempt to compile, build, link, or regenerate binaries during a conversation.”以及项目“不代编译”要求，需要用户编译IrisArsenal.sln / Release|x64 / v100，再运行PreparePackage.cmd。该脚本验收并组包，之后再完整更新游戏目录。

安全：改旧文件前双外部备份到D:/CodexBackups与E:/AIWorkSpace/_backups，UTF-8/BOM和换行保持，中文/乱码与字节回读检查；每文件详见ranged-0.3.0-files.json。没有修改游戏/其他项目/依赖/模组勾选/存档，没有新下载。
