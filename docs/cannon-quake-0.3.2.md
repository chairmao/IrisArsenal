# IrisArsenal 0.3.2：三远程、两近战与源地震

本轮用户要求已写入项目代码/资产，未编译、未部署。游戏DLL仍是0.3.0，不把新CSV/材质单独混入旧DLL。

| 招式 | 路由 | FCS attack distance | 当前伤害事件 | INI权重 |
|---|---|---|---|---|
| 极速火神炮 vulcan | 游戏勾选远程 | 0～360 | 20发，各0.2倍；弹体/爆炸R4.5 | 1 |
| 脉冲之焰 pulse | 游戏勾选远程 | 0～360 | 3发，各2倍；弹体R4.5、爆炸R36 | 1 |
| 极致驱动 drive | 游戏勾选远程 | 0～360 | 连续光炮4次独立脉冲，各1.5倍；平端柱体R9、最大长度360 | 1 |
| 螺旋飞舞 spiral | 取消远程后的近战池 | 0～30 | 3次武器命中，各1倍 | 1 |
| 地震 earthquake | 取消远程后的近战池 | 0～45 | 4次独立三维球形震击，各1.5倍、R36 | 1 |

其他三招权重0。FCS公共chance=0/disabled仍保持，只有本锤枪私有选招可以使用。远程整套结束后的原生装填时间由`RangedActionInterval=1.0`控制；无需弹药。原生AI/视线/走位/装填计时沿用既有适配，未增加钩子；仍4个C++单元、16钩子。

## 光炮：同一半径、长度与光学模型

`IrisCombat.cpp`的RangedMove/HasRangedMoves/RangedRange/PickRanged及Publish资格全部纳入drive，近战两个加权分支排除drive。身体源动作和四个事件时间不变。

`native/NativeMultiContact.cpp::CylinderAll`先保留此前第一堵非角色阻挡策略，再用官方PhysX2.8.4.6的精确OBB批量候选读取真实球/胶囊/盒/凸网格。`native/FiniteCylinder.h`以实际形状支持函数判断有限平端圆柱，球形体走精确距离式；不是以角色根位置/水平距离假装物理命中。任一形体数据不支持、容量溢出或窄相位未收敛时整条结果不消费、下个安全帧重试；不猜命中。没有创建SDK、actor或覆盖全局contact回调。该新增C++算法尚未执行，必须实机验证。

五层源beam能量管/纹理/颜色UV与扩散曲线保留；作者将动态源包络归一为r≤1、z=0～1，运行时直接缩放为R9和查询返回的墙前长度。成功的物理快照同时更新方向/起点/长度，查询后同帧刷新可视，避免显示穿墙伸长。四次健康事件仍各自去重，同cast只有一份连续可视，不叠四根重合光管或重置UV。源三层程序闪电仍未执行，不宣称完全复刻。

## 地震：按真实资源链制作

`docs/quake-chain.json`保存只读记录位置/字段：源Iris.ini:38的IrisExplosion4→Skyrim.esm SPEL0002FFD2 crGiantStomp→MGEF00104D44→EXPL00072675 crGiantStompExplosion→Effects/FXdustBurstTiny.nif。源动画是一次首跃及后续震击组合，保留四个独立事件。

从本机BSA提取原NIF同字节缓存，只读源档案。`tools/author_quake.py`读取真实发射面/法线、速度、出生率、寿命、棕灰尘色、淡入淡出和8×8/4×4图集；第一层曲线积分19粒、第二层6粒，每波100顶点/2个submesh。GPU做有限相机朝向sprite，独立游戏秒寿命约12.44s，自然散尽；不按动作结束强制切掉，不额外追加健康事件。

适配边界：保留上述源参数与纹理；随机种子固定以便复现，速度/尺寸包络是受控翻译，完整Skyrim NiPSys风场/拖曳/重力和所有修饰器尚未执行。尚未在Kenshi内验收可见效果，不能保证与录像完全一致。原NIF字段类型参考[NifTools公开格式定义](https://raw.githubusercontent.com/niftools/nifxml/develop/nif.xml)。

## AOE优化与边界

采用EphnelSpear经验中适用部分：真实原生一次accurateCollision球形批量查询；同一角色多形体按完整hand身份去重；同一安全Tick完全相同且完整成功的球事实缓存16份；每帧清空、不跨帧存shape/角色指针。每波、每发的健康事件仍独立，不合并伤害，不省略敌人。enemy/玩家保护继续在收集和医疗两处检查。

每安全更新查询预算64；柱体预留最多2次原生调用；医疗仍12次/1ms软预算，FIFO保留未完成工作。新增最多16份汇总日志记录查询CPU耗时/实际调用/缓存/原始形体与唯一接触数，不能替代FPS/GPU测量。Iris的原生精确球重叠与Ephnel旧骨点扫掠不同，未照搬其影子校验/旧路径回退，也不声称全部优化逐项相同。原有墙体语义保持。

## 验收与下一步

`tools/verify_moves.py`通过：16份身体/握点动画、8招源事件、FCS往返、11个源特效、分层动态包围、粒子实际序列化参数/图集/保守包围、光炮动态r≤1/z0～1、8个平端反例、原生SDK声明、8份C++/头语法树及乱码检查。分析模型不等于执行C++窄相位。源Iris376文件、游戏mod96文件哈希不变，详见`docs/validation-0.3.2.json`、`docs/safety-0.3.2.json`。

遵守[code-modification-principles](C:/Users/周凡稀/.agents/skills/code-modification-principles/SKILL.md)编译边界：“Never attempt to compile, build, link, or regenerate binaries during a conversation.” 未调用C++/HLSL编译器、未链接、未部署。请用户编译`IrisArsenal.sln`，**Release|x64 / v100**，再运行`PreparePackage.cmd`完整组包；旧030 DLL会被合同032拒绝。

实机重点：远程三招能轮换且保持1.0间隔；取消远程后两招近战；光炮侧面/平端/高低差/墙前截断；地震四次伤害及趴地敌人、尘土自然结束；多人查询重试/日志、暂停变速、重复施放/读档回收。性能改善幅度和完整运行安全性尚未测量。

作者工具新增局部依赖lz4==4.4.5（约99kB wheel），仅`D:/CodexWorkSpace/Tools/IrisArsenal-lz4`，用于原烟尘DDS在BSA内的关联帧解压；没改全局解释器/PATH/注册表。其他机器重做资产可用IRIS_LZ4_PATH指定相同版本局部目录。运行游戏不需要Python/lz4。逐文件双备份与编码见`docs/cannon-quake-0.3.2-files.json`。
