# IrisArsenal 0.3.3：准星、火焰地震、脉冲显示和远程距离

本轮继续完整任务授权，仅IrisArsenal项目源码/作者工具/资源/说明修改。实际游戏已是用户编译部署的0.3.2（日志2026-10-16 23:11:33.711）；033未编译/部署。本轮录像11.08秒及对应源视频帧已检查，完整NiPSys等同和游戏内新视觉尚待验收。

## 远处“射击中”而没有动作

已确认旧代码有能造成此现象的关口：032三招FCS最大360；IrisCombat::Tick的inMoveRange严格验证后才Publish available，PickRanged再次校验；超出时没有任何可选动作。IrisRanged::Config私有GUN_DATA还硬编码range=360，部分原生分支可能读取它，与只改maxRange可能不一致。

旧日志没有空等阶段的目标距离/门状态，所以**不能确认用户那一次必然/仅由attack distance造成**。原生瞄准、视线、友军阻挡、装填、模型/动画准备也可能阻止许可，保留这些逻辑，不用强播/跳过检查掩盖问题。

033已把FCS三招都设0～10000，私有GunData和GunClass::maxRange同读已启用FCS范围。新增`ranged_gate`首32个状态变化日志：distance、FCS_max、plugin_ready、gun_ready、state、busy、pending、take_shot、aim_timer、reload；reason区分outside_FCS_range/plugin_not_ready/queued_for_action/action_in_progress/native_reload/waiting_native_shot_gate。它是定位证据，不会调用可能改变状态的takeTheShotCheck，也不判断未实测LOS的具体结论。日志次数耗尽后无新门日志不代表全部通过。

用户已确认光炮也延长到10000：Emit不再写360常量，直接取该招私有FCS initialDistance；**半径9不变**，实际墙前长度同时用于显示。墙体探测改为ALL_HITS回调流式保存最近非角色接触，等同于原先完整列表取min，避免长束沿途世界物体超过256就让整条查询永久重试。角色窄相位仍有256唯一目标上限，完整失败不扣半份伤害。没有新钩子/新SDK实例/actor/全局contact覆盖。

## 准星：按录像重建平面

旧muzzle用了ShoutAreaExplosionWarm0的四层球形爆发，并以世界恒等朝向挂在枪口，不是原录像准星。已用158.9秒参考帧约束重绘双排四分青蓝圆环和四个红色圆端刻线，两个submesh、所有顶点z=0，不使用球面/烟纹理。朝向取实际武器枪口轴，不改角色/武器姿态；蓄力期间维持、脉冲发射时短现，时钟随游戏。

**没有确认这个准星的独立源NIF，明确标为录像重建**。查到的Tips1真实顶点为细长斩线，未把它冒称为准星；本轮试读扩展已撤回。`tools/source-cache/IrisReticle-Reference.png`保存实际帧，`tools/author_reticle.py`为唯一几何生产者。正交网格检查图只验证轮廓，不是游戏渲染验收。

## 地震改为3:35～3:37火焰版

源变体`999977004/mco_powerattack7.hkx`在1.0秒同时触发IrisExplosion4和IrisExplosion3。追加火焰的链：Iris.ini→SPEL0865→MGEF0866→EXPL086A→`SW/Iris/explosionwarm0.nif`。导出六层WispsGround双层、Glow、Plane、LowerFlame双层及4秒原颜色/UV/扩散曲线。底部火焰向外扩散，显示alpha/RGB适配1.35/1.15；仅可视抬高0.8防止地形深度竞争，四个球形伤害中心仍在原位。

原032小烟尘活跃路径退出，程序/材质不再引用IrisQuakeVP或读取quake_profile；其作者和源证据保留作为历史资料，旧PNG/CSV不被当前地震消费者使用。火焰仍是六层真实源网格/曲线的受控移植，没有运行完整Skyrim粒子发射器和飞石物理，不能宣称与原版完全一致。

## 脉冲爆炸

保留真实EldenRim命中源四层、源纹理/调色/分层曲线。只在此特效材质添加独立显示alpha增益2.2、RGB1.45，先按源计算再施加并限制alpha到0～1，避免淡到看不见；其他招式默认1/1保持原输出和共享材质身份。未改变三发、各2倍、弹体R4.5或爆炸球R36。

## 参数和优化保持

| 招式 | 流程 | 起手范围 | 权重 | 伤害 |
|---|---|---|---|---|
| 火神炮 | 远程 | 0～10000 | 1 | 20×0.2，弹/爆炸R4.5 |
| 脉冲之焰 | 远程 | 0～10000 | 1 | 3×2，弹R4.5/爆炸R36 |
| 极致驱动 | 远程 | 0～10000 | 1 | 4×1.5，平端柱R9/最长10000，墙前截断 |
| 螺旋飞舞 | 近战 | 0～30 | 1 | 3×1武器命中 |
| 地震 | 近战 | 0～45 | 1 | 4×1.5，球R36 |

其他三招仍0，武器基础伤害0.1，整套远程后原生间隔INI RangedActionInterval=1.0。AOE继续一次原生精确球重叠、同帧最多16份完整事实缓存、角色多形体去重、独立事件、enemy/玩家保护、64原生查询/帧及医疗12次/1ms软预算。火焰只改变显示，不增加健康事件或逐敌人额外扫描。新FPS/GPU改善未测量。

## 验证、备份及编译边界

`tools/verify_moves.py`核验实际FCS三招10000、16动画/握点、8招原事件数、11个特效、源曲线动态包围、平面准星、独立材质增益、10000柱体平端解析反例、流式最近阻挡的稠密/乱序等价、SDK声明、C++语法树、编码与中文。没有执行新增C++/GPU程序。`docs/validation-0.3.3.json`、`docs/fire-reticle-0.3.3-evidence.json`区分已确认与未确认。

依照[code-modification-principles](C:/Users/周凡稀/.agents/skills/code-modification-principles/SKILL.md)：“Never attempt to compile, build, link, or regenerate binaries during a conversation.” 用户请编译**IrisArsenal.sln / Release|x64 / v100**，再运行PreparePackage.cmd完整组包。现有032 DLL会被033门拒绝，禁止只复制新材质/CSV混用旧DLL。本轮没有自动同步游戏、启动/终止进程、附加调试器或恢复轮询。

逐文件双外部备份及编码见`docs/fire-reticle-0.3.3-files.json`；游戏和源mod哈希不变见`docs/safety-0.3.3.json`。下一次实机重点：准星平面与枪轴、四波火焰/尾焰、脉冲爆炸对比、360以上三招是否获许可、光炮长束墙体/敌群/倒地、暂停变速和读档清理。
