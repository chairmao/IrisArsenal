# 三招源特效重建067（源码0.4.23，待编译）

Owner: Codex

本次仅重建火焰翻滚第二击、电脉加农和全力爆发尾击视觉。实际查看本地演示的198.9～201.8秒、134.7～139.8秒、109.6～112.4秒，并沿HKX事件→PayloadInterpreter→ESP/SPEL/MGEF/PROJ/EXPL→NIF/ADDN→贴图/粒子池追踪。没有用别招火焰主观替代。全力光刃、钻天破064爆炸、066圆环门、伤害判定、倍率、权重和线程模型保持。

## 确认的源链及修正

| 招式 | 原始来源 | 本次修正 |
|---|---|---|
| 火焰翻滚第二击 | IrisBackJump：8DB→8DA→原版EXPL439C0→Magic/FireBallExp01.nif；8DC脚本papaStrikeCast2延迟0.1秒→8CD→8CB→EXPL6051F，同一NIF；同帧IrisExplosion：824→812→810→SW/Iris/ShoutAreaExplosionWarm0.nif | 不再复用全力的FireWave。使用真实火球、Torus/Flash、72火球/120火星池及延迟的第二次源爆发，补回暖色冲击层。隐藏发射网格95只用于出生位置/方向动画，不渲染辅助网格。 |
| 全力爆发尾击 | FullBust_End同时调用824暖色冲击与原版3F9ED→562EB→647BE→VoiceFlameWaveProject03→七个ADDN64→647BC→MPSFireWaveFlames | 保留六源曲面及七发射点共享的两套源池，并补回824的三曲面/275火星。光刃不改。 |
| 脉电/电脉加农 | IrisBeam：886→884→885→SW/Iris/beam.nif，同时824→812→810暖色范围冲击 | 五层真实能量管/原纹理与暖色范围层；每次成功消费攻击事件才重置光束效果年龄，四个AOE事件独立。实际枪口和原ElectroFrame轴不改。 |

参考插件为soulworker_iris.esp、EldenSkyrim.esp、EldenSkyrim_RimSkills.esp及Skyrim.esm；原版NIF来自Skyrim - Meshes1.bsa。未给源资源新增授权或承诺再分发许可，本次只适配用户本地已有文件；源文件没有改写。

实现见[独立作者](../tools/source_effects067.py)、[来源和量测数据](source-effects-067.json)、IrisCombat.cpp的VisualLayerAge/VisualLifetime/ShowParts。原源alpha、UV、RGBA、调色LUT、实际几何与有限发射池保留。整体空间/时间变换作用于出生、寿命、速度、加速度及源控制器，避免只加速网格而把粒子留在慢时钟。运行时不再对翻滚/全力二次乘2。

暖色冲击使用064同Stokes族的4倍显示曝光适配，以补偿此CPU/Kenshi显示路径；这是明确的移植适配，**不是源文件参数**。没有因此画新火焰/光斑或更换贴图。

## 范围与时序

- 翻滚爆炸：真实弹体落点为球心，保持既有R24。
- 全力尾击：保持既有事件中心与R90球，光刃/前两段不改。
- 电脉：保持ElectroFrame的实际炮口轴、前20处/R25球；光束纵向仍连接原射击区域，不追改枪口位置或伤害。
- 用064相同方法，直接对源几何、粒子和真实贴图的alpha×面积在亮相作12方向R95量测，再统一缩放完整源实例；不能用裁剪包围球代替视觉范围。
- 12方向最弱主体R95对应既有伤害R。FireBall约R～1.218R、FireWave约R～1.132R；暖色源冲击是薄形扩散，投影约R～1.726R。闪光/火星软尾可以超出伤害球；这不是球内每点均匀填满、每像素边界与伤害球相等的证明。保留源造型，不把暖色平面捏造成球壳。
- 主爆发亮相约0.2秒附近；暖色源时间2倍、FireBall与FireWave按源亮相统一压缩。第二次火球延迟仍为0.1秒，不增加独立伤害段。

## 后翻距离

从包内男、女iris_action_fire_roll_*.skeleton的Bip01实际轨道读取，两者一致：起手先前进8.379877；后翻段向后52.465315；动作结束相对起点净后退44.085438，单位为导出原生根运动使用的游戏世界单位。不是依据视频像素估算，也不宣称是米。实际游戏会受地形/原生路径处理/动作打断影响，此处是无障碍动画轨道的标称位移。

## 实际执行的验证

1. 原视频接触表、PIE/ESP脚本/记录解析、NIF/ADDN及纹理逐层核对；证据在本次任务目录。
2. 真正序列化的四份mesh/33子层、27唯一材质、纹理闭包、曲线25维/有限值/32层/241样本边界检查；所有材质声明完整引号，避免065冒号继承解析错误。
3. 火球第二次出生时间最小0.100467秒；隐藏源发射器出生动画生效；源有限池共翻滚659、全力912、电脉275粒子，没有凭空增加发射密度。
4. 94个战斗函数中只改视觉年龄/寿命、配置日志及ShowParts；AdvanceEffects仅注释变动。IrisArsenal.cpp的49个函数完全相同。10份C++/H语法检查、3份Python AST检查通过；这不是C++或HLSL编译。
5. 13个其他曲线块、18个其他视觉记录及全部其他运行文件与基线字节一致；光刃、男女动画、FCS、INI、064/066和旧DLL保持。
6. 独立重复导出24份输出，全部与当前字节一致；未写回项目、未编译。
7. 实际网格/源像素/LUT/图集帧间插值和时钟的CPU动态预览已生成并逐一查看，绿圈只用于R24/R90/R25核对。不是Ogre/GPU或游戏截图。
8. 安装目录所有现有清单哈希仍匹配，旧0.4.22 DLL被067合同正确拒绝，避免旧时钟混用新资源。

CPU结果和完整验证位于：`D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-Iris-SourceEffects067-20261021-181211`。重点文件为`validation067.json`、`reexport067.json`、`*-cpu067-r2.jpg/gif`和`per-file-reports-final.json`。

## 边界与下一步

没有移植Skyrim ENB/折射或beam.nif三个空几何的程序闪电运行时；有限粒子是按源参数确定性导出，未执行完整NiPSys模拟。因此不能称为逐像素1:1，也不能以CPU预览证明游戏亮度、深度和材质加载完全一致。

当前**源码/资源0.4.23（IRIS_THREE_SOURCE_FX_067）待编译**；项目包和游戏现有DLL仍为用户编译的0.4.22/066。`ready=false`是真实状态。本轮未编译C++/HLSL、未部署、未启动/终止游戏。请用户编译`IrisArsenal.sln`的`Release|x64 / v100`，正常退出游戏后运行`UpdateMod.cmd`。日常复制/更新功能没有重构。

所有既有小文件写入前均双备份，根目录为`D:/CodexBackups/Task-Iris-SourceEffects067-20261021-181211`及`E:/AIWorkSpace/_backups/Task-Iris-SourceEffects067-20261021-181211`（后续编辑使用同名前缀的独立后缀）。逐文件报告列出每个实际路径、旧/新SHA256、编码和备份。现有UTF-8/BOM/CRLF或LF保持，中文写后扫描通过。恢复须整套匹配源码、时钟资源和对应DLL，不能只回退其中一项。
