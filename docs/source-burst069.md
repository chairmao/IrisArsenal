# 源爆炸069：翻滚黑块与钻天破爆发主体

本轮由用户实机1D2311和“不要有太黑色块”要求驱动。用户已编译并部署0.4.24/068：bin、package和游戏DLL SHA256同为 `6cc9c8584de8f289cca72c13c5dd9204c182da67697810267d7100945f5f8afe`。日志前缀0.4.19是旧字符串，不代表实际加载旧DLL。此前STATE“待编译/游戏0.4.23”已过时，下方历史不改写。

## 实际修改

只修改roll_blast和drill_blast的源控制器/私有着色器及曲线。C++/H、DLL、伤害、物理、暂停时钟、事件数、根运动、双翼球心及其他20条效果记录保持原字节。仍为翻滚R24、钻天破固定双翼对称中心R120；没有恢复弹体飞行或额外受击。

- 源SubTex不是“帧数等于FPS”。本机SkyrimSE只读RTTI/vtable反汇编：BSPSysSubTexModifier Update RVA0xD64BF0，FrameCount为归一寿命内步数，首次随机起帧，之后循环；私有069VP按此语义取原图集离散帧。随机分布的确定性种子不与Skyrim逐粒完全相同。
- BSPSysSimpleColorModifier Update RVA0x1323550证实RGB/alpha独立，FadeOut=0时保持中间alpha。补读NiPSysEmitterLifeSpanCtlr、源BSEffect颜色/alpha/UV/增益控制器；同纹理会被多份NIF复用，必须按来源NIF再匹配，不取首个同纹理系统。
- 参考源Effect着色流程，灰度alpha查表后直接作为结果，去掉额外一次寿命alpha乘法。原图集、渐变、混合模式、原发光值保持；没有将普通alpha火球改为加法。
- 用户明确要求不要太黑：仅翻滚pFireBall的冷却色键0..0.20、线性亮度0.02..0.16平滑降低遮挡。此项是公开的移植显示适配，并非声称源NIF就有这项参数；不把黑块涂成不透明橙板。曾试验额外4倍曝光，CPU预览出现白块，已撤回，不进入运行包。
- Stokes源几何按12方向真实UV/alpha/渐变/面积量测，整体尺度约为旧版2.50526倍；不是把微小星火当主体。旧7.188倍全段压缩使主体峰值落在约0.055秒。现在整个Stokes实例共用连续源时钟：源主体峰值约0.391828映射0.20游戏秒，源尾末映射0.52秒，出生/运动/寿命/颜色/几何同步。火相仍从0.56秒起。
- 私有VP支持152个尺寸键，覆盖Warm/Stokes实际150键，保留FireBall24/120、MPS83/140等全量源键。未扩大全局GPU缓冲或修改共享IrisEightShader。

## 来源与不能伪称完成的部分

翻滚：IrisBackJump的8DB/8DA→Skyrim EXPL439C0 `Magic/FireBallExp01.nif`；8DC脚本→8CD→EXPL6051F，同一NIF延迟0.1；另有824暖冲击。原序列图FXFireAnim04Loop与渐变GradFireExplosion继续使用。用户视频198.9..202秒和1D2311逐帧已查看。

钻天破不是两个单层：当前28层来自ALSExp/ALSshock、Stokes ShoutAreaExplosionSmall01、原DragonRend视觉实例、火浪曲面、ADDN64/MPS火焰及星火。各层来源见source-burst069.json及前驱064记录。本轮纠正主体时序/源颜色/粒子语义，不把源文件数量冒充已完整执行原引擎效果。

更新/纠正：分析中曾暂认为Iris8D9 PlasmaBall是遗漏分支；实际MGEF8D6引用master PROJ0B56 ALSPRO，不引用8D9，因此没有添加。ALSPRO是飞矛；RedDragonrendprojectile和MoonProjhorzV1为飞行视觉，不冻结塞入固定球心爆炸。离线试验出现巨大红环，已拒绝。

[MISSING] ALSshock中名称AddOnNode33实际nodeID334。在349个本机mod插件的162个ADDN及已查master中仍无匹配。不能误接原版33。mBegin的Lightning04源可见性false，也不能用常亮闪电猜补。完整程序闪电、折射、受控湍流、ENB/曝光管线仍未执行；因此不能称“完全复刻已达标”。

## 实际验证与限制

已执行源记录追链、本机只读反汇编、相同068输入9输出重复变换、两视角28帧实际序列化资产CPU预览、源时钟连续单调/末尾饱和、所有材质参数闭包及40个独立对象括号/引用检查、150尺寸键与数组容量、运行上限、20其他效果记录及其他曲线逐字检查。242个未授权基线文件哈希保持，包含所有C++/H、DLL、其他运行资产。

相同背景/时点/视角下，翻滚深色遮挡像素1853→148（约92%减少）。这只是CPU光栅结果，不是游戏截图/帧率/GPU实测。预览包含展开、峰值与消散，不能用静态接触图证明完整实机演出；随机浮点哈希与GPU可能不同。范围仍按原源软轮廓适配，R95不保证球内每个像素填满；没有以裁剪包围盒冒充火焰范围。

未编译C++或HLSL，未启动游戏/调试器，未修改存档。HLSL源由游戏下次启动时正常加载，Ogre/GPU最终外观和源后处理差异仍待观察。

## 更新与恢复

已确认游戏退出，现有Update部署器完成完整双备份、清空目标、复制和154文件哈希终验。游戏目录 `D:\steam\steamapps\common\Kenshi\mods\IrisArsenal` 已是资源069，DLL原内部0.4.24及068身份保持。UpdateMod.cmd下次可同步这些包内资源；完整资产重建也已在068后调用source_burst069.apply，避免覆盖回旧特效；本轮未执行完整重建或任何代码编译。

完整旧mod/日志备份：
- `D:\CodexBackups\IrisArsenal-CleanUpdate-20261021-223044-344445-39f3c08e`
- `E:\AIWorkSpace\_backups\IrisArsenal-CleanUpdate-20261021-223044-344445-39f3c08e`

原始工程文件逐项双备份与UTF-8/原BOM、换行记录在任务目录的report-*.json。恢复时先正常退出游戏，将完整备份中的D/steam/.../IrisArsenal内容恢复；恢复工程还需按相应report的Safety.backups恢复作者和包，避免下一次Update覆盖回新版本。

任务证据、候选对比、逐文件报告、完整部署前后清单：`D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-Iris-SourceBurst069-20261021-210037`。

源资源均复用用户本机Skyrim/源模组，作者权属保持；未发布工坊、未新增网上下载素材。源着色逻辑核对参考：https://raw.githubusercontent.com/community-shaders/skyrim-community-shaders/dev/package/Shaders/Effect.hlsl ，字段格式核对：https://raw.githubusercontent.com/niftools/nifxml/develop/nif.xml 。没有复制完整第三方Shader。
