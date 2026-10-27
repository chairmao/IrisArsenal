# IrisArsenal 0.3.1 四招测试与源特效时间层

本轮用户指定：火神/脉冲起手0～360；脉冲弹体R4.5、爆炸R36；整套远程动作后的间隔放入INI并设1；核对脉冲爆炸、启用近战螺旋飞舞/极致驱动并核对表现。此前完整任务授权继续有效，不新增确认。

## 实际参数

| 招式 | FCS起手最小～最大 | 权重 | 弹体半径 | 独立伤害与范围 |
|---|---:|---:|---:|---|
| 极速火神炮 | 0～360 | 1 | 4.5 | 20次，每次0.2倍，球形爆炸R4.5 |
| 脉冲之焰 | 0～360 | 1 | 4.5 | 3次，每次2倍，球形爆炸R36 |
| 螺旋飞舞 | 0～30，保留 | 1 | 无飞弹 | 三次实体武器物理命中，每次1倍；装饰刀光不另加伤害 |
| 极致驱动 | 90～280，保留 | 1 | 无飞弹 | 四次原能量束脉冲，每次1.5倍；长度280，扫掠半径8 |

其余四招权重0。前两招仅勾选游戏“远程”并获得原生射击许可才启用；后两招仍属于近战池，取消远程勾选便于测试。开启名单不是四招无条件交替，仍由原生战斗状态、FCS距离与各池INI权重决定。

[IrisArsenal] RangedActionInterval=1.0：启动读取，0～3600、可用小数，改后重启。它沿用上一版原生弩装填的时间单位，给reloadTimeMin与reloadTimeMax两个相同端点；整套20/3发收尾或中断后才进入间隔，无弹药、不为每枚特效子弹单独装填。原生选敌/视线/走位仍可能让下一次更晚，暂停及变速由原生计时器处理。该键不为近战动作增加插件冷却。

## 源视频与绑定证据

已重读本机已下载Soulworker_Iris_BV1u14y1U74k.mp4：脉冲65～69、螺旋115～118、极致157～162秒；本任务保存三张逐帧联系图。脉冲演示多为向空处开火，不能凭该片段推断落点爆炸颜色，命中资源以ESP引用链为准。

原脉冲PlasmaBall法术0x8D0→MGEF0x8CF→PROJ0x8D1，爆炸引用0x02000BA0。原ESP master槽2为EldenSkyrim.esp，已继续读取本机0-Elden Rim-Base 3.5.9/EldenSkyrim.esp中的对应EXPL（本文件本地form 0x05000BA0）：EDID RimDLC1AurielsBowExpNoEnchant，MODL RimMagic/RimMagicdlc1aurielsskyboltexplosion01.nif。旧版所有弹药共用Iris的explosionwarm0.nif，不能代表该实际命中链。

本次导入真实依赖NIF的四个可渲染层：Flash01、lightRays01SmallCenter、lightRays01BigCenter、Torus03smallSlow；使用原纹理、混合、LUT和三秒序列，按R36校准最大光学包络。它们不增加健康事件。该NIF的NiPSys粒子、朝相机Billboard语义未完整运行，不能称百分之百与Skyrim一致。

PayloadInterpreter的IrisPlasmaShoot/IrisBeam同时施放0x824→MGEF0x812→EXPL0x810，引用ShoutAreaExplosionWarm0.nif。本轮增加四个可导出的枪口伴随层，近枪口短窗口使用完整源曲线的压缩时间映射；极致驱动的蓄力与枪口喷发使用同一资源，是明确的Kenshi视觉适配，不冒充源Papyrus/粒子原封运行。

极致驱动仍读取原beam.nif五层能量管，恢复分层UV、颜色和节点变换；四个原Beam事件保持四个独立物理/医疗窗口，可视在重叠期间只保留同一cast的一束连续洪流，不按四次事件重置UV或叠四层亮度。收招后已发出的束独立渐隐。BSProceduralLightningController原程序闪电仍未执行。

螺旋飞舞保留mco_powerattack3真实身体/Prop2/根轨道和三次HitFrame；按源0.1秒IrisBackfire播放连续尾焰，在实际武器历史位置上生成连续旋转刀光，不额外造斩击伤害。源IrisSteam3涉及大量身体发射器，尚未完整迁入，不能把这项说成已完全吻合演示。

## 分层时间合同与边界

新增tools/fx_timeline.py严格读取本次NIF已用的刚体变换、颜色、透明、UV、发光和衰减曲线，支持线性/二次/TCB/阶跃键组，30Hz采样到effect_curves.csv。四类资源、每层最多241样本、每样本25个有限值；加载后共享，实例只保留年龄，不复制贴图。增量矩阵为H*W(t)*W默认^-1*H^-1，仅用于自有网格的Shader顶点，不写角色/原生武器附件/世界物理体。

按Niftools官方[格式定义](https://raw.githubusercontent.com/niftools/nifxml/develop/nif.xml)核对EffectShaderControlledVariable：0是发光倍率，1～4是衰减，5是透明度，6～9为UV偏移/尺寸。动态网格的保守包围盒覆盖全部源采样，避免扩散后被静止包围盒裁掉。ManualObject刀光使用独立静态VP，避免索取其未提供的Entity custom常量。

维持同一锤枪物品/原生选敌/移动/攻速/身体姿态/伤害队列、enemy及玩家保护、单次医疗和既有格挡政策；火神原物理命中免格挡/闪避，其他招式的原防御合同本轮未改。球形/有限扫掠及各事件去重不变，不以多贴几个火球来制造更多伤害。自有枪口资源加入End/Clear/场景清理和高水位计数。

## 验证与交付

16份实际序列化身体/Prop2、FCS引用/隔离、源事件20/3/3/4、11类FX网格、纹理/混合/LUT、源SHA、25通道曲线/动态包围盒、4个真实C++输入单元/7个语法树和本机SDK声明/符号检查通过。shader只做文本/绑定检查，未编译/未游戏执行。旧030 DLL被031组包合同拒绝是预期保护，不是本次编译失败。

本轮没有编译、组包新DLL、部署、启动/终止游戏或恢复轮询。游戏目录当前为用户0.3.0，0.3.1源码和资产在项目中准备；package ready=false。按code-modification-principles的“Never attempt to compile, build, link, or regenerate binaries during a conversation.”要求，用户编译IrisArsenal.sln / Release|x64 / v100，然后PreparePackage.cmd组包，再整包同步。不能把这些静态检查当作MSVC、HLSL或实机效果成功。

实机重点：远程两招在近/远距离均可选，枪口低位R4.5是否即刻触地；R36三维爆炸对站立/趴地/敌友混合；原生1单位间隔随暂停/变速；取消远程后两近战招式出招；极致蓄力/五层束/4次判定与收尾；螺旋连续持械/尾焰/三击；密集敌人FPS、资源回收、换武器/读档。原030日志出现的ranged_mode_ended早停不能仅凭新距离声称已根治，需新版本测试区分真正原生中断。

安全：既有小文件写前双备份至D:/CodexBackups和E:/AIWorkSpace/_backups，保持UTF-8/BOM/原换行，逐文件写后中文/乱码与字节检查；详见mixed-0.3.1-files.json。本轮未下载依赖，没有修改Skyrim/EldenRim、Ephnel/JCE、游戏文件、mod勾选或存档。
