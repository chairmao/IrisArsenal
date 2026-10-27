# 极致驱动重做 059 / 0.4.16

本轮只重做极致驱动。其他九招的源规格、动画/效果原文件、配置和医疗/物理安全链逐项核对，保持原值。当前为待用户编译的源码/资产版本；没有运行C++/HLSL编译器，没有部署游戏，没有操作游戏进程。现有bin/package/游戏DLL仍是057/0.4.14，SHA256均为`14f3ee85645fe3079ceb67d7657f9f7480864338dec64f5bfc6034e935cefe0e`。

## 源动作与资源

- 已解码本地演示视频157.5～162秒，对照用户给出的四张截图。
- 正确身体是`999977000/mco_powerattack10.hkx`（5.5秒/331帧），不是PA6坐锤。NA6明确指向下一PA10；3.16654秒发出`IrisEXAnimSHOOT`。保留四次独立伤害脉冲，间隔0.25源动画秒；INI倍率、长度10000保持。
- `IrisEXAnim1`沿SPEL/MGEF/ARMO/ARMA指向`EXanim1.nif`。蓝准星`Ch0145_Halo`实际180顶点，分AnimObjectA/B两组；003.dds红形体9组与004.dds蓝形体均是原发光几何，不是实体炮身。源身体网格不移植。
- 按原EXanim旋转频率5/4.125和演示展开过程，烘焙连续旋转、小→大的变化，停止旋转时保留角度，避免瞬跳。径向展开/握点与相位是Kenshi适配，不能声称源NIF存有同样的缩放键。
- 源发射链是`StokesCannonAttack1`脚本调用冲击/爆炸，不是旧代码误用的坐锤`beam.nif`。枪口蓝相复用该链的`Magic/ShoutAreaExplosionSmall01.nif`及可支持的源发射器；火相使用同帧`IrisExplosion`/`0x3F9ED FireWave`的`VoiceFlameWaveProject03.nif`八层。蓝相后再进入火相，均围绕实际枪口。
- `IrisExplosion4`的Skyrim.esm 0x2FFD2实际是`crGiantStomp`→`FXdustBurstTiny.nif`，不是蓝光资源；不据名字乱配蓝色特效。本轮不承诺完整移植源尘土、风场、折射、拖曳或全部NiPSys行为。

## 光流与碰撞

用户允许原模组不是光束时采用外部离子光流。实际查看[Alexander123的原资源页面](https://opengameart.org/content/fire-texture-laser-texture-for-unity)及[CC0授权](https://creativecommons.org/publicdomain/zero/1.0/)，下载原ZIP，使用原Laser1.png与FlamesTexture.png字节。许可/摘要见`tools/source-cache/drive059/LICENSE.json`和包内`CREDITS-drive059.txt`。未生成AI贴图。

三层共轴闭合平端圆柱：归一半径1/0.72/0.32、Z为0～1；运行时同一组`muzzle / barrel axis / radius / wall-truncated length`驱动碰撞与绘制。外层角色碰撞半径9，长度仍取FCS初始距离上限10000。地形保持中心射线，角色保持原生安全窗口内真实柱体查询；原友军过滤、防御策略、每段去重、2.5ms/32伤害队列和后效时钟保持。纹理按实际长度重复与游戏秒流动，不将一张图拉满10000。

## 身体与生命周期

站立肩持只发生在离线男女动画导出：PA10源双腿/根轨道保留；右手过伸时沿轴收回到肩前，复用固定骨长两骨IK；左手落在真实枪杆前握位。没有运行时写角色位置、朝向、骨骼、TagPoint或全局移动锁。发射方向读同一原生Prop2矩阵，不另朝目标生成偏离炮口的光线。

`ShowParts`以PA10绝对游戏动作秒绘制自己的ion复合资产；`Emit(kind8)`分别创建四次独立伤害任务，同cast只保留一份连续beam后效；`Contacts/ResolveJobs`仍同步完成地形/柱体查询后才提交医疗；`DrawBeam`消费成功查询的同一空间快照。其他招式的分支和共享医疗函数保持。

曲线生产者/文件头/DLL消费者从13同步为14类；资产格式仍是042/FX4/曲线1。新程序、材质和资产只服务drive；旧DLL不能通过059合同门。

## 已实际执行的验证

- 完整`tools/verify_moves.py`通过：20份男女序列化骨架、20种效果、FCS往返/私有隔离、源图与源曲线、历次范围/敌我/医疗/查询/暂停/后效回归，以及10个C++文件的Tree-sitter语法树。详情见[完整验收](validation-drive-059.json)。没有将语法解析冒充MSVC类型或链接验证。
- 059专项读取真实男女发射帧：四段均沿正前炮轴，左掌误差低于0.000002游戏单位；原生骨长保持。重新调用实际生产作者在隔离目录导出四份动画/握点文件，和当前包逐字节相等，确认更新脚本走同一生产链。
- 比较其他九招规格完全相等；120个受保护运行文件、16个安全/医疗/物理函数保持原摘要。FCS仅`17-IrisArsenal.mod`驱动技巧记录变化。详见`drive059-preserved.json`与`authorized-delta-059.json`。
- 22项更新脚本/日志IO沙盒测试通过；旧057 DLL被059组包门正确拒绝。
- 已用实际生成的骨架/网格/原纹理/层曲线进行CPU蒙皮和光栅化，检查侧面/背面姿势、准星旋转与展开、蓝火时序、R9光柱近场以及流动帧。此为诊断预览，未模拟游戏完整GPU、HDR、后处理或FPS。

## 实际资产CPU预览

![实际男女肩持姿势](previews059/pose.jpg)

![原红蓝准星与蓝火阶段](previews059/reticle-muzzle.jpg)

![R9光流近场动画](previews059/stream.gif)

以上是实际资产的CPU诊断图，身体用灰模以便检查接触；不是游戏截图。预览仅展示长10000光流的枪口近场，网格总长度未缩短。

## 构建与更新

请用户编译`IrisArsenal.sln`，目标`IrisArsenal / Release|x64 / v100`；正常退出游戏后执行`UpdateMod.cmd`。该脚本会重建059源资源、验证新DLL、重新组包并同步。没有新DLL时明确失败，不把旧DLL当059。包保持`ready=false`，直到用户完成编译/组包。

双份修改前备份：

- `D:/CodexBackups/Iris-Drive059-20261019-195324-61c8e2/E/KenshiProject/2.Projects/IrisArsenal`
- `E:/AIWorkSpace/_backups/Iris-Drive059-20261019-195324-61c8e2/E/KenshiProject/2.Projects/IrisArsenal`

所有现有文本保留原UTF-8/BOM和换行，新文件UTF-8，已检查中文与乱码。逐文件变更/备份/验证/未验证范围另见`change-report-drive059.json`。最终MSVC/HLSL运行时编译、游戏中的遮挡/骨架混合/PhysX命中及GPU性能尚需新DLL运行验证，不承诺已经逐像素一致或FPS提升。
