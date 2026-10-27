# IrisArsenal 0.2.1：极速火神炮修复

用户本轮明确要求：只开火神炮，武器伤害降至原1/10，子弹球半径4.5，修复黑色效果与朝地射击；已物理命中的火神炮伤害不可格挡/闪避。

## 真实证据与根因

0.2.0 PID34456日志18:43:03起确实选中vulcan并消费20个发射事件，因此不是上一轮的FCS加载故障。游戏日志没有发现Iris着色器编译失败，不能把黑色归因为已证实的GPU编译错误。已确认旧生产者把所有材质设为alpha_blend、固定在调色图y=0.5取样、把本应驱动LUT的基色RGB再次相乘，并无条件乘顶点RGBA。这些规则与实际NiAlpha/shader_flags不一致。

本机源配置IrisShoot1→SPEL0x847→MGEF0x858→PROJ0x85D指定Magic/FireballProjectile01.nif；旧实现却复用PlasmaBall.nif。源火球从本机Skyrim - Meshes1.bsa只读提取，sha256=f8fd57a3e4fe73cfc1558813446d7187f4120673b7f0a718b474eb4bb5a114db，4层真实几何/纹理，不修改源mod或档案。

旧Target使用目标根位置+2，位于近地面；火神枪口离地约6.4～7.2（源女性骨架离线样本），R5球沿下降路径容易先触地。旧日志没有记录每弹坐标，所以不能声称已捕获每一次游戏落地的具体坐标。新瞄准优先目标当前Spine2/Pelvis/Head并换回游戏浮动原点；缺标准骨点明确回退root+8，不冒称命中了胸部。

## 改动

- 当前20发事件不变，球形连续扫掠半径与爆炸半径均为4.5；source Fireball取代错误PlasmaBall用于火神。自出生即设置正确可视变换/alpha，飞行按真实球心更新。
- 材质按源混合模式逐层恢复，27种材质中23种src_alpha/one、1种普通alpha、3种不透明。分别遵循调色图颜色/alpha、绿通道密度、基色红通道纵坐标、顶点开关、源增益、视角衰减。保留源像素，不通过染成统一橙色掩盖错误。
- 仅火神的物理爆炸请求在一次同步原生受击内绕过HIT_MISSED/HIT_SWORD。Win32 TLS核对CombatClass、Damages引用、攻击者；原链先执行通知，许可调用前消费，退出恢复。原生护甲/部位/医疗、敌对过滤、玩家保护继续，其他7招防御策略保持。
- 武器基础cut/blunt从1降到0.1，pierce仍0；不再重复给技能倍率乘0.1。20发每发0.2倍不变。
- INI仅vulcan=1，其他7招=0；FCS火神起手距离仍35～180，未擅自调整。贴身超出此区间时可能没有可选招式。

## 当前安装状态

已安全同步旧0.2.0 DLL可直接读取的INI、FCS武器参数、moves.csv半径及实际安装校验清单。游戏DLL与FX资产未动。0.2.1全部代码、材质和9类FX资料已在项目包，ready=false；整包必须在用户重新编译后组包。不要把新effects.csv v3或新mesh/material孤立复制给旧DLL。

用户打开IrisArsenal.sln，编译Release | x64 / v100，然后运行PreparePackage.cmd。此脚本不编译、不部署；它只接受IRIS_EIGHT_021和新于源码的用户DLL。全修复仍需同步完整包并重启游戏验证。

## 验证与限制

通过16个真实FCS→骨架内部动画名/长度→种族引用、旧路径/旧DrillProof等5个反例、16份身体握点、事件次数、9份源效果网格、源纹理/27种混合参数、球包络半径4.5、单招配置、SDK声明/链接符号、C++语法树及Python语法；旧DLL组包拒绝检查通过。没有执行MSVC/HLSL编译，没有启动游戏或恢复轮询。没有实际画面、破防效果、FPS收益的新版实机结论。

完整NiPSys、程序闪电、所有逐帧控制器和终结钻头蒙皮仍未完全迁入；本轮修复共同的黑色材质路径，不等于所有招式视觉已经复刻完成。

材质算法参考：[NifSkope源效果shader](https://github.com/niftools/nifskope/blob/develop/res/shaders/sk_effectshader.frag)、[nifxml字段定义](https://github.com/niftools/nifxml/blob/develop/nif.xml)。它们是格式/重建参考，实际游戏效果需测试。

逐文件修改、双备份、编码与验证见vulcan-fix-0.2.1-files.json；完整证据与已安装参数见vulcan-fix-0.2.1-validation.json。小文件均在写前备份至D:/CodexBackups及E:/AIWorkSpace/_backups，文本保持原UTF-8/BOM/换行，不覆盖历史审计或源文件。
