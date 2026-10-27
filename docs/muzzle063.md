# IrisArsenal 0.4.20 / 063：火神与脉冲枪口特效

当前是源码与资源交付，未编译、未部署。现有062 DLL原字节保留，不能称新效果已在游戏中运行。

本轮观看了已下载视频65～69、92～96秒，并核对用户两张参考图、Iris.ini、原ESP与NIF。只处理两招视觉，用户后续回复“可能这就是枪口的橙色扩散层”，据此将原824橙色扩散作为本轮脉冲方向；不冒称截图另有独立火苗已经唯一定位。

火神：原IrisAnim同时调用84B与85C。84B沿MGEF859/ARMO85B加载anim.nif，挂Weapon；85C沿MGEF855/ARTO84C加载anim1.nif，随角色根。原实现遗漏后一份，且前一份没有导出旋转。现在保留18片武器小组、8片人物大组的原几何与源纹理，排除anim1附带的3BA身体和anim中缺贴图的辅助杆。小组按原NiTransformController22的frequency=5、周期4.125、Y旋转关键帧循环；这是约1.21圈/秒，不是5圈/秒。大组不被强制跟着枪管翻转。原INI分别2.4、2.2秒后收回；起点均取IrisAnim事件局部游戏秒。

脉冲：删除原来错误的通用红蓝准星。真实IrisPlasmaShoot还调用SPEL824→MGEF812→EXPL810→ShoutAreaExplosionWarm0。复用已核验的3片源曲面与275源火花、原纹理/调色/UV/寿命；三次独立触发离线展开为12层。只把整套显示按同一相似变换挂到实际枪口，显示标尺6；源是爆发/扩散层，不用别招FireWave或臆造火苗替代。这个显示标尺不是伤害范围，原R36未改。弹体、瞄准、命中、护甲、倍率和权重均未动。

生命周期：复用既有flash自有实例，切换类型前Return到原池；End隐藏、Clear销毁沿用原路径。只是读取原生渲染根或Prop2矩阵，不修改角色、骨骼、移动或枪口数据。没有新增Hook、线程、锁、PhysX查询或伤害事件。

作者入口是tools/muzzle_sources063.py，author_effects.py完整重建最后调用它。日常UpdateMod仍只组包和复制，不重建资源，也不运行这些历史/专项测试。资源表20→22、曲线14→17；每实体32层/每层241样本的原上限保持。新材质独立文件，所有原共享Shader、纹理和其他招式资产保持。63材质注释已通过日常更新相同的引用闭包检查，避免源DDS文件名被误识别成缺失运行文件。

实际验证：

- 10个C++/H文件Tree-sitter语法检查；Python AST和中文/编码扫描通过。不是MSVC类型/链接验证。
- IrisCombat全部函数逐项对照：91个完全不变，仅AssetRequired、Configure、ShowParts变化；IrisRanged及native目录原字节保持。
- 独立按源关键帧核算241个旋转样本，矩阵最大误差4.949e-6；确认首圈后继续转动。
- 三次脉冲逐层与实际源资源序列化buffer对比：只平移粒子出生时间，位置/速度/半径/寿命/纹理相同，未增加伤害。
- 第二次导出逐文件同字节；22资产/17曲线、子材质数量、全部纹理和程序引用闭包通过。
- 以真实男女动画、正常武器网格、最终效果网格/纹理/时间流生成两张联系图和两份16帧GIF，已实际查看。可看到大/小准星及小组旋转，脉冲实际枪口的橙色爆发/扩散。人体使用骨架辅助线，未画完整皮肤遮挡；粒子CPU采用近帧图集，未模拟完整Ogre后处理。火神预览主要隔离准星层，原枪口火焰未重做。

预览及逐文件即时报告、完整验证保存在本会话Task-Iris-Muzzle063-20261020-211449目录。CPU预览不等于游戏/GPU测试，尚不能承诺游戏亮度、遮挡及帧率。

下一步由用户编译 E:\KenshiProject\2.Projects\IrisArsenal\IrisArsenal.sln，Release|x64 / v100；正常退出游戏后运行UpdateMod.cmd。现有旧DLL应被063身份门拒绝，这个预期拒绝已验证。编译遵循[code-modification-principles](C:/Users/周凡稀/.agents/skills/code-modification-principles/SKILL.md)的“Never attempt to compile, build, link, or regenerate binaries during a conversation.”，未由助手执行编译。

备份位于 D:\CodexBackups\Task-Iris-Muzzle063-20261020-211449 及同前缀-r2～-r6，E:\AIWorkSpace\_backups\ 下各有镜像。每次修改前保存原字节，UTF-8/BOM/CRLF或LF按原文件保持，未改动源滚5模组、游戏目录或正式1.0封存。
