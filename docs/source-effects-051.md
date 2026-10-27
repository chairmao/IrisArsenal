# 051：电脉加农的源范围火焰、火神炮的源枪口火焰

## 实际状态

2026-10-18已同步到 `D:\steam\steamapps\common\Kenshi\mods\IrisArsenal`：139项核验，7个文件写入（6资源＋manifest）。DLL仍为用户编译的0.4.8，代码合同仍为050；资源修订 `051-SourceFlareMuzzle`。不需重编译DLL。未启动游戏或执行Shader编译，下一次游戏正常加载源Shader；没有恢复轮询。

## 原模组究竟是不是截图那样

电脉原演示137～140秒显示短促的橙色放射爆发，带扩散纹理、火花和光柱，并不是持续燃烧的一片地面火海。其 `$IrisBeam` 同时CAST886/824/826：886是beam.nif，824沿MGEF812→EXPL810指向 `SW/Iris/ShoutAreaExplosionWarm0.nif`；826是MarkedForDeath效果，本轮不把它臆造成额外火焰。当前三层源曲面/原Glow billboard/275真实火花来自824，源颜色、UV、寿命均在。

先前用alpha/RGB控制值筛选后直接取整片几何外缘133.3143当作发亮主体半径，但DarkSwirls/VaporTile的大片几何边缘在贴图中很弱。这把真正的发亮部分缩小了。051在原三角面每面64个确定性重心采样，读取真实纹理/LUT/顶点alpha和视角falloff，按发亮面积能量计算12个视角的95%主体范围；可见面积峰值约0.4秒，参考尺度88.1001。整套源效果因此统一放大1.513213821倍；没有逐层乱摆、加任意粒子、改色或换贴图。同一比例用于光柱横截面，保持原层间关系。伤害仍为前20、R25，球心仍是050真实枪口高度，伤害次数/倍率不变。

火神原链为IrisShoot1→PROJ85D.NAM1→`RimMagic/SW_MagMuzzle.nif`→AddOnNode9→`MPS/MPSFireBoltImpact01.nif`。确有pFireGlow光晕层，但原演示92～96秒是火焰核心、火星、两层余烬和光晕的组合，长期伸缩的实心亮球不是正确的移植结果。

这次不只依据图形格式字段推断：只读本机 `SkyrimSE.exe` 的RTTI与BSPSysSimpleColorModifier::Update（vtable25）确认了两个分支。第二颜色区间长度为0时直接保持中间色；pFireGlow的原区间为[0,0.3,0,0]。旧移植用max(.001,宽度)强行插到第三色，把中间RGB[0.25882,0.10196,0.07059]错误换成[0.90196,0.62745,0.32941]。另一个原分支在FadeOutPercent=0.15后开始淡出，0表示关闭；旧公式在0.85后才开始。051只修正IrisMuzzleVP的这些语义；原五层、20发出生点、尺寸17采样、每粒角速度、纹理及RGB源值完全保留。插件没有增加任何原生地址、偏移或调用；反汇编地址只用于离线取证。

原引擎文件sha256、确切分支位置、ESP字段、NIF引用和预览依赖均记录于[证据](source-effects-051-evidence.json)。格式字段参考[NifTools原始规范](https://raw.githubusercontent.com/niftools/nifxml/develop/nif.xml)，NiPSysModifier::Update槽位参考[CommonLibSSE-NG声明](https://raw.githubusercontent.com/CharmedBaryon/CommonLibSSE-NG/main/include/RE/N/NiPSysModifier.h)；行为结论以本机实际Update分支为依据。

## 主动验证

先做了一轮真实CPU预览，只修淡出后仍是球，因此没有宣称修复；继续查到零宽颜色区间的确切原生分支并修正后再次预览，光晕不再盖住火焰形状。两份最终比较都读取实际序列化网格、真实纹理/图集/LUT、寿命和时钟，使用明亮底色。预览为CPU光栅化，不是游戏截图、GPU结果或FPS测量。旧例已冻结为真正050 buffer/曲线，游戏升级后仍可复现。

![枪口旧新CPU比较](previews051/muzzle-before-after.jpg)

![电脉旧新CPU比较](previews051/electro-before-after.jpg)

- 051独立测试核对原生零宽区间、fadeOut=0、原RGB/alpha边界、实际网格整体相似变换、151帧原曲线、原20发和全部不变文件。最终图像摘要/输入摘要逐项核对。
- 完整非编译验收通过；13项隔离同步/备份/回滚/配置/白名单测试通过。050坐姿192帧与049旧姿势负例继续通过，十招58次事件/20身体动画/21效果保持。
- 游戏关闭后安全同步并逐文件核对实际安装的138个运行文件＋manifest；DLL和用户INI摘要保持。没有改存档、勾选、原mod素材、其他项目或游戏进程。
- CPU预览验证了本轮像素合成和几何结果，不能代替实际GPU、环境深度、后处理或运行性能测试。完整NiPSys拖曳/湍流/程序闪电、IrisSteam2/3序列仍不宣称已经完整移植。原光晕存在，源火焰也包含相机朝向粒子，不能把原始所有粒子卡片都称为移植错误。

## 文件、备份与编码

`tools/electro_coverage051.py`为可见主体测量；`electro_area.py`为原效果统一量尺；`muzzle_detail.py`修正枪口独立Shader生成；`preview_source051.py`/`test_source_effects051.py`记录实际预览与边界。`stage_package.py`仅更新资源修订名；历史测试只接受`authorized-delta-051.json`的精确迁移。C++/H/RC/FCS/动画/纹理像素/个人INI均未改。

修改前均双备份，保留UTF-8/BOM及原CRLF/LF，写后严格回读和中文乱码检查。实际游戏双备份为 `D:\CodexBackups\IrisArsenal-Update-20261018-124857-916538-2cec7499` 与 `E:\AIWorkSpace\_backups\IrisArsenal-Update-20261018-124857-916538-2cec7499`；项目逐文件备份、编码和报告见[交付审计](source-effects-051-delivery.json)。

以后执行项目 `UpdateMod.cmd` 会从作者工具重建并同步051，无需重新编译本轮DLL。旧050/049报告保持为历史，不能用它们证明051已经实机测试。
