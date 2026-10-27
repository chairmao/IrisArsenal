# IrisArsenal 0.1.0 逐文件交付记录

本轮仅新建并迭代IrisArsenal项目。完整逐次记录在docs/change-reports，每份均包含File/Role/Code location/Before/Changes/Reasons/After/Impact/Validation/Safety/Unresolved。

新增文件无需原内容备份；迭代已有文件均先在D:/CodexBackups与E:/AIWorkSpace/_backups建立独立、不可覆盖的备份。文本保持UTF-8及原换行，C++/SLN/VCXPROJ为CRLF；新增一般文本为LF。所有被写文本均严格回读并扫描乱码。

## 每个文件

| 文件（项目内路径） | 职责 | 编码 | 已做检查 |
|---|---|---|---|
| IrisArsenal.cpp | 实际绘制/查询统一入口 | UTF-8/CRLF | 字节回读；文本严格UTF-8和中文乱码扫描 |
| IrisArsenal.rc | DLL版本资源 | UTF-8/LF | 字节回读；文本严格UTF-8和中文乱码扫描 |
| IrisArsenal.sln | 独立Visual Studio入口 | UTF-8/CRLF | 字节回读；文本严格UTF-8和中文乱码扫描 |
| IrisArsenal.vcxproj | v100 Release x64 DLL工程 | UTF-8/CRLF | 字节回读；文本严格UTF-8和中文乱码扫描 |
| PreparePackage.cmd | 用户组包入口 | UTF-8/CRLF | 字节回读；文本严格UTF-8和中文乱码扫描 |
| README.md | 交付边界说明 | UTF-8/LF | 字节回读；文本严格UTF-8和中文乱码扫描 |
| STATE.md | 本项目交付状态 | UTF-8/LF | 字节回读；文本严格UTF-8和中文乱码扫描 |
| docs\asset-provenance.json | 资产和碰撞来源 | UTF-8/LF | 字节回读；文本严格UTF-8和中文乱码扫描 |
| docs\body-retarget.json | 重定向证据 | UTF-8/LF | 字节回读；文本严格UTF-8和中文乱码扫描 |
| docs\cpp-authorization.json | 具体C++授权记录 | UTF-8/LF | 字节回读；文本严格UTF-8和中文乱码扫描 |
| docs\fcs-records.json | FCS身份清单 | UTF-8/LF | 字节回读；文本严格UTF-8和中文乱码扫描 |
| docs\native-races.json | 固定原生人形race集合 | UTF-8/LF | 字节回读；文本严格UTF-8和中文乱码扫描 |
| docs\reference-baseline.json | 只读引用基线 | UTF-8/LF | 字节回读；文本严格UTF-8和中文乱码扫描 |
| docs\reference-observations.json | 历史引用差异 | UTF-8/LF | 字节回读；文本严格UTF-8和中文乱码扫描 |
| docs\source-geometry-preview.png | 普通枪/钻头形体投影 | binary | 字节回读；文本严格UTF-8和中文乱码扫描 |
| docs\source-hashes.json | 源只读身份 | UTF-8/LF | 字节回读；文本严格UTF-8和中文乱码扫描 |
| docs\validation.json | 非编译验收结果 | UTF-8/LF | 字节回读；文本严格UTF-8和中文乱码扫描 |
| package\IrisArsenal\IrisArsenal.ini | 原型配置 | UTF-8/LF | 字节回读；文本严格UTF-8和中文乱码扫描 |
| package\IrisArsenal\IrisArsenal.mod | 隔离FCS武器/技巧/动画 | binary | 字节回读；文本严格UTF-8和中文乱码扫描 |
| package\IrisArsenal\RE_Kenshi.json | RE_Kenshi插件清单 | UTF-8/LF | 字节回读；文本严格UTF-8和中文乱码扫描 |
| package\IrisArsenal\_IrisArsenal.info | 本地mod元信息 | UTF-8/LF | 字节回读；文本严格UTF-8和中文乱码扫描 |
| package\IrisArsenal\assets\drill.csv | 动作/部件/查询合同 | UTF-8/LF | 字节回读；文本严格UTF-8和中文乱码扫描 |
| package\IrisArsenal\assets\iris.hlsl | 前向源发光着色器 | UTF-8/LF | 字节回读；文本严格UTF-8和中文乱码扫描 |
| package\IrisArsenal\assets\iris.material | 源材质适配 | UTF-8/LF | 字节回读；文本严格UTF-8和中文乱码扫描 |
| package\IrisArsenal\assets\iris.program | Ogre程序声明 | UTF-8/LF | 字节回读；文本严格UTF-8和中文乱码扫描 |
| package\IrisArsenal\assets\iris_179f128b96e16ff2.dds | 源武器纹理 | binary | 字节回读；文本严格UTF-8和中文乱码扫描 |
| package\IrisArsenal\assets\iris_22af7ab7d285bd0c.dds | 源武器纹理 | binary | 字节回读；文本严格UTF-8和中文乱码扫描 |
| package\IrisArsenal\assets\iris_2556c812dc7d68e6.dds | 源武器纹理 | binary | 字节回读；文本严格UTF-8和中文乱码扫描 |
| package\IrisArsenal\assets\iris_29343c8126431246.dds | 源武器纹理 | binary | 字节回读；文本严格UTF-8和中文乱码扫描 |
| package\IrisArsenal\assets\iris_5114b0f90ad5da99.dds | 源武器纹理 | binary | 字节回读；文本严格UTF-8和中文乱码扫描 |
| package\IrisArsenal\assets\iris_drill.mesh | 真实三维附加钻头 | binary | 字节回读；文本严格UTF-8和中文乱码扫描 |
| package\IrisArsenal\assets\iris_drill_female.skeleton | 具名身体及持械动画 | binary | 字节回读；文本严格UTF-8和中文乱码扫描 |
| package\IrisArsenal\assets\iris_drill_male.skeleton | 具名身体及持械动画 | binary | 字节回读；文本严格UTF-8和中文乱码扫描 |
| package\IrisArsenal\assets\iris_e43c904a32f784ff.dds | 源武器纹理 | binary | 字节回读；文本严格UTF-8和中文乱码扫描 |
| package\IrisArsenal\assets\iris_edb8fbf0179684de.dds | 源武器纹理 | binary | 字节回读；文本严格UTF-8和中文乱码扫描 |
| package\IrisArsenal\assets\iris_weapon.mesh | 原生Y轴普通武器 | binary | 字节回读；文本严格UTF-8和中文乱码扫描 |
| package\IrisArsenal\assets\iris_weapon_icon.png | 真实武器图标 | binary | 字节回读；文本严格UTF-8和中文乱码扫描 |
| package\IrisArsenal\assets\iris_weapon_proof_female.csv | 独立源WEAPON期望值 | UTF-8/LF | 字节回读；文本严格UTF-8和中文乱码扫描 |
| package\IrisArsenal\assets\iris_weapon_proof_male.csv | 独立源WEAPON期望值 | UTF-8/LF | 字节回读；文本严格UTF-8和中文乱码扫描 |
| package\IrisArsenal\assets\iris_white.dds | 无发光纹理缺省 | binary | 字节回读；文本严格UTF-8和中文乱码扫描 |
| tools\author_prototype.py | 闭环持械生产者 | UTF-8/LF | 字节回读；文本严格UTF-8和中文乱码扫描 |
| tools\kenshi_mod_writer.py | FCS格式编解码 | binary | 字节回读；文本严格UTF-8和中文乱码扫描 |
| tools\nif_geometry.py | 严格刚体NIF读取 | UTF-8/LF | 字节回读；文本严格UTF-8和中文乱码扫描 |
| tools\nif_reader.py | Iris只读NIF解码 | UTF-8/CRLF | 字节回读；文本严格UTF-8和中文乱码扫描 |
| tools\port_math.py | 离线重定向数学 | UTF-8/LF | 字节回读；文本严格UTF-8和中文乱码扫描 |
| tools\safeio.py | 安全写入工具 | UTF-8/LF | 字节回读；文本严格UTF-8和中文乱码扫描 |
| tools\stage_package.py | 仅本项目组包工具 | UTF-8/LF | 字节回读；文本严格UTF-8和中文乱码扫描 |
| tools\third_party\PyNifly-LICENSE.txt | 本地Havok解码依赖 | binary | 字节回读；文本严格UTF-8和中文乱码扫描 |
| tools\third_party\anim_fo4.py | 本地Havok解码依赖 | binary | 字节回读；文本严格UTF-8和中文乱码扫描 |
| tools\third_party\anim_skyrim.py | 本地Havok解码依赖 | binary | 字节回读；文本严格UTF-8和中文乱码扫描 |
| tools\verify_prototype.py | 非编译交叉验收 | UTF-8/LF | 字节回读；文本严格UTF-8和中文乱码扫描 |

## 编译与实机边界

源码/资源已准备；没有编译、链接、运行游戏或部署。用户编译IrisArsenal.sln / Release x64 / v100，再用PreparePackage.cmd仅组包。本轮不存在已验证可用的DLL。

依据C:/Users/周凡稀/.agents/skills/code-modification-principles/SKILL.md：“Never attempt to compile, build, link, or regenerate binaries during a conversation.” 本轮仅离线转换网格、骨架与FCS数据，没有调用编译器或构建工具。

实际网格/FCS/骨架、源WEAPON期望值与材质引用验证见validation.json。源Iris输入保持。EphnelSpear.cpp出现与最初基线不同的外部写入，来源未确认；本项目未写该文件，不依赖其实时源码，原基线和差异都保留。

## 外部备份文件

- D:\CodexBackups\IrisArsenal-20261015-190022-861219\E\KenshiProject\2.Projects\IrisArsenal\package\IrisArsenal\assets\iris.material
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-190022-861219\E\KenshiProject\2.Projects\IrisArsenal\package\IrisArsenal\assets\iris.material
- D:\CodexBackups\IrisArsenal-20261015-190022-861219\E\KenshiProject\2.Projects\IrisArsenal\package\IrisArsenal\assets\iris.program
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-190022-861219\E\KenshiProject\2.Projects\IrisArsenal\package\IrisArsenal\assets\iris.program
- D:\CodexBackups\IrisArsenal-20261015-190022-861219\E\KenshiProject\2.Projects\IrisArsenal\package\IrisArsenal\assets\iris.hlsl
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-190022-861219\E\KenshiProject\2.Projects\IrisArsenal\package\IrisArsenal\assets\iris.hlsl
- D:\CodexBackups\IrisArsenal-20261015-190605-744929\E\KenshiProject\2.Projects\IrisArsenal\tools\nif_reader.py
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-190605-744929\E\KenshiProject\2.Projects\IrisArsenal\tools\nif_reader.py
- D:\CodexBackups\IrisArsenal-20261015-190605-744929\E\KenshiProject\2.Projects\IrisArsenal\tools\author_prototype.py
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-190605-744929\E\KenshiProject\2.Projects\IrisArsenal\tools\author_prototype.py
- D:\CodexBackups\IrisArsenal-20261015-190714-539135\E\KenshiProject\2.Projects\IrisArsenal\tools\safeio.py
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-190714-539135\E\KenshiProject\2.Projects\IrisArsenal\tools\safeio.py
- D:\CodexBackups\IrisArsenal-20261015-190751-666219\edit-190751-675569\E\KenshiProject\2.Projects\IrisArsenal\tools\author_prototype.py
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-190751-666219\edit-190751-679014\E\KenshiProject\2.Projects\IrisArsenal\tools\author_prototype.py
- D:\CodexBackups\IrisArsenal-20261015-190751-666219\edit-190751-695518\E\KenshiProject\2.Projects\IrisArsenal\IrisArsenal.cpp
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-190751-666219\edit-190751-697716\E\KenshiProject\2.Projects\IrisArsenal\IrisArsenal.cpp
- D:\CodexBackups\IrisArsenal-20261015-190752-124515\edit-190755-096089\E\KenshiProject\2.Projects\IrisArsenal\package\IrisArsenal\assets\iris.material
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-190752-124515\edit-190755-101257\E\KenshiProject\2.Projects\IrisArsenal\package\IrisArsenal\assets\iris.material
- D:\CodexBackups\IrisArsenal-20261015-190752-124515\edit-190755-106490\E\KenshiProject\2.Projects\IrisArsenal\package\IrisArsenal\assets\iris.program
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-190752-124515\edit-190755-109813\E\KenshiProject\2.Projects\IrisArsenal\package\IrisArsenal\assets\iris.program
- D:\CodexBackups\IrisArsenal-20261015-190752-124515\edit-190755-114950\E\KenshiProject\2.Projects\IrisArsenal\package\IrisArsenal\assets\iris.hlsl
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-190752-124515\edit-190755-118516\E\KenshiProject\2.Projects\IrisArsenal\package\IrisArsenal\assets\iris.hlsl
- D:\CodexBackups\IrisArsenal-20261015-190752-124515\edit-190758-602283\E\KenshiProject\2.Projects\IrisArsenal\docs\body-retarget.json
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-190752-124515\edit-190758-605333\E\KenshiProject\2.Projects\IrisArsenal\docs\body-retarget.json
- D:\CodexBackups\IrisArsenal-20261015-190930-383123\edit-190930-390990\E\KenshiProject\2.Projects\IrisArsenal\tools\port_math.py
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-190930-383123\edit-190930-396217\E\KenshiProject\2.Projects\IrisArsenal\tools\port_math.py
- D:\CodexBackups\IrisArsenal-20261015-190930-383123\edit-190930-414052\E\KenshiProject\2.Projects\IrisArsenal\tools\author_prototype.py
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-190930-383123\edit-190930-417208\E\KenshiProject\2.Projects\IrisArsenal\tools\author_prototype.py
- D:\CodexBackups\IrisArsenal-20261015-190930-777575\edit-190937-182323\E\KenshiProject\2.Projects\IrisArsenal\package\IrisArsenal\assets\iris_drill_male.skeleton
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-190930-777575\edit-190937-185932\E\KenshiProject\2.Projects\IrisArsenal\package\IrisArsenal\assets\iris_drill_male.skeleton
- D:\CodexBackups\IrisArsenal-20261015-190930-777575\edit-190937-610139\E\KenshiProject\2.Projects\IrisArsenal\package\IrisArsenal\assets\iris_drill_female.skeleton
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-190930-777575\edit-190937-613220\E\KenshiProject\2.Projects\IrisArsenal\package\IrisArsenal\assets\iris_drill_female.skeleton
- D:\CodexBackups\IrisArsenal-20261015-190930-777575\edit-190937-626666\E\KenshiProject\2.Projects\IrisArsenal\docs\body-retarget.json
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-190930-777575\edit-190937-628727\E\KenshiProject\2.Projects\IrisArsenal\docs\body-retarget.json
- D:\CodexBackups\IrisArsenal-20261015-191136-526735\edit-191136-528813\E\KenshiProject\2.Projects\IrisArsenal\IrisArsenal.cpp
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-191136-526735\edit-191136-531311\E\KenshiProject\2.Projects\IrisArsenal\IrisArsenal.cpp
- D:\CodexBackups\IrisArsenal-20261015-191136-526735\edit-191136-545988\E\KenshiProject\2.Projects\IrisArsenal\tools\author_prototype.py
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-191136-526735\edit-191136-549699\E\KenshiProject\2.Projects\IrisArsenal\tools\author_prototype.py
- D:\CodexBackups\IrisArsenal-20261015-191136-962866\edit-191146-601186\E\KenshiProject\2.Projects\IrisArsenal\docs\body-retarget.json
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-191136-962866\edit-191146-604762\E\KenshiProject\2.Projects\IrisArsenal\docs\body-retarget.json
- D:\CodexBackups\IrisArsenal-20261015-191136-962866\edit-191146-886800\E\KenshiProject\2.Projects\IrisArsenal\package\IrisArsenal\IrisArsenal.mod
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-191136-962866\edit-191146-888894\E\KenshiProject\2.Projects\IrisArsenal\package\IrisArsenal\IrisArsenal.mod
- D:\CodexBackups\IrisArsenal-20261015-191338-744662\edit-191338-745672\E\KenshiProject\2.Projects\IrisArsenal\IrisArsenal.cpp
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-191338-744662\edit-191338-749914\E\KenshiProject\2.Projects\IrisArsenal\IrisArsenal.cpp
- D:\CodexBackups\IrisArsenal-20261015-191522-862154\edit-191522-875483\E\KenshiProject\2.Projects\IrisArsenal\tools\author_prototype.py
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-191522-862154\edit-191522-882048\E\KenshiProject\2.Projects\IrisArsenal\tools\author_prototype.py
- D:\CodexBackups\IrisArsenal-20261015-191522-862154\edit-191527-376258\E\KenshiProject\2.Projects\IrisArsenal\package\IrisArsenal\assets\iris_drill_male.skeleton
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-191522-862154\edit-191527-380949\E\KenshiProject\2.Projects\IrisArsenal\package\IrisArsenal\assets\iris_drill_male.skeleton
- D:\CodexBackups\IrisArsenal-20261015-191522-862154\edit-191527-876703\E\KenshiProject\2.Projects\IrisArsenal\package\IrisArsenal\assets\iris_drill_female.skeleton
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-191522-862154\edit-191527-881235\E\KenshiProject\2.Projects\IrisArsenal\package\IrisArsenal\assets\iris_drill_female.skeleton
- D:\CodexBackups\IrisArsenal-20261015-191522-862154\edit-191527-892751\E\KenshiProject\2.Projects\IrisArsenal\docs\body-retarget.json
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-191522-862154\edit-191527-895810\E\KenshiProject\2.Projects\IrisArsenal\docs\body-retarget.json
- D:\CodexBackups\IrisArsenal-20261015-191547-414056\edit-191548-028339\E\KenshiProject\2.Projects\IrisArsenal\docs\validation.json
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-191547-414056\edit-191548-032229\E\KenshiProject\2.Projects\IrisArsenal\docs\validation.json
- D:\CodexBackups\IrisArsenal-20261015-191805-604513\edit-191805-609833\E\KenshiProject\2.Projects\IrisArsenal\IrisArsenal.cpp
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-191805-604513\edit-191805-611883\E\KenshiProject\2.Projects\IrisArsenal\IrisArsenal.cpp
- D:\CodexBackups\IrisArsenal-20261015-191805-604513\edit-191805-630019\E\KenshiProject\2.Projects\IrisArsenal\STATE.md
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-191805-604513\edit-191805-632246\E\KenshiProject\2.Projects\IrisArsenal\STATE.md
- D:\CodexBackups\IrisArsenal-20261015-192142-349503\edit-192142-357555\E\KenshiProject\2.Projects\IrisArsenal\IrisArsenal.cpp
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-192142-349503\edit-192142-360908\E\KenshiProject\2.Projects\IrisArsenal\IrisArsenal.cpp
- D:\CodexBackups\IrisArsenal-20261015-195445-805037\edit-195445-811274\E\KenshiProject\2.Projects\IrisArsenal\tools\verify_prototype.py
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-195445-805037\edit-195445-817688\E\KenshiProject\2.Projects\IrisArsenal\tools\verify_prototype.py
- D:\CodexBackups\IrisArsenal-20261015-195445-805037\edit-195445-832259\E\KenshiProject\2.Projects\IrisArsenal\STATE.md
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-195445-805037\edit-195445-835329\E\KenshiProject\2.Projects\IrisArsenal\STATE.md
- D:\CodexBackups\IrisArsenal-20261015-195445-805037\edit-195445-842050\E\KenshiProject\2.Projects\IrisArsenal\README.md
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-195445-805037\edit-195445-845232\E\KenshiProject\2.Projects\IrisArsenal\README.md
- D:\CodexBackups\IrisArsenal-20261015-195446-233138\edit-195446-879469\E\KenshiProject\2.Projects\IrisArsenal\docs\validation.json
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-195446-233138\edit-195446-883716\E\KenshiProject\2.Projects\IrisArsenal\docs\validation.json

## 最终清理复核

最后一次C++修改补充收招隐藏失败时的异常隔离；已重新执行非编译资源/隔离验收。对应备份：
- D:\CodexBackups\IrisArsenal-20261015-195741-579458\edit-195741-581911\E\KenshiProject\2.Projects\IrisArsenal\IrisArsenal.cpp
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-195741-579458\edit-195741-584386\E\KenshiProject\2.Projects\IrisArsenal\IrisArsenal.cpp

## 2026-10-15 用户编译失败修复

依据：obj/Release/IrisArsenal.log 中31条错误，归于三个根因；原日志副本与源码基线保存在
D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-IrisArsenal-CompileFix-20261015-201612-172c87。
本轮没有运行任何编译器、链接器、资源生成或部署脚本；不能据静态检查宣称编译/实机通过。

### IrisArsenal.cpp
- File：E:\KenshiProject\2.Projects\IrisArsenal\IrisArsenal.cpp。
- Role / Code location：运行时插件；头文件、Visual::Create、PositionVisual。
- Before：把旧Ogre命名实例重载套入当前接口；调用不存在的SubEntity::setVisible；physHit仅有前置声明。
- Changes / Reasons：使用SDK的createEntity(meshName,groupName)；包含CharMovement.h完整类型；光学四层以公开索引区间0/默认范围切换。依据本机OgreSceneManager.h:1352、OgreSubEntity.h:170/178、CharMovement.h:34；新增索引接口名称均见链接库与运行DLL。
- After / Impact：保留现有资源名、19子网格、光学层时序和无伤害闭环。仅修改自有SubEntity绘制区间，不修改共享网格、材质、原生装备或SDK。
- Validation：新增SDK检查通过；原始源码、缺失完整定义、旧重载、不支持的可见性四个负例均被拒绝；现有网格/骨架/FCS/材质校验通过。编译/链接/渲染未运行。
- Safety：双外部字节备份；UTF-8无BOM、CRLF保持，原中文全部保留且新增注释可读，未见替换字符。
- Unresolved：用户重新生成Release|x64/v100，实机观察四层光学面切换。

### tools/verify_prototype.py
- File：E:\KenshiProject\2.Projects\IrisArsenal\tools\verify_prototype.py。
- Role / Code location：离线验收；verify_sdk_contract与main调用处。
- Before：只检查头文件存在，无法识别本次真实构建错误。
- Changes / Reasons：补充完整类型所在头、实体参数、光学层接口声明和链接库/运行DLL符号名称字节的静态检查。
- After / Impact：只读核对本机SDK契约；没有DLL调用、ABI手写、代码编译或资产生成。
- Validation：Python AST与正/负例检查通过；完整离线验收通过。名称检查不等于链接成功。
- Safety：双外部备份；UTF-8无BOM、LF保持，中文检查通过。
- Unresolved：最终编译链接由用户执行。

### STATE.md
- File：E:\KenshiProject\2.Projects\IrisArsenal\STATE.md。
- Role / Code location：项目Owner及构建状态；编译状态段。
- Before：仅记载等待首次编译。
- Changes / Reasons：记录实际用户失败及本次三个根因修复，保留Agent未编译、未部署的边界。
- After / Impact：状态与证据一致，仍为Codex Owner，不接管其他项目。
- Validation：状态与日志、源码、DLL缺失情况相符。
- Safety：双外部备份；UTF-8无BOM、LF保持，中文检查通过。
- Unresolved：新构建结果待用户反馈。

### docs/validation.json
- File：E:\KenshiProject\2.Projects\IrisArsenal\docs\validation.json。
- Role / Code location：离线验收产物；local_sdk_compile_regression字段。
- Before：未覆盖上述SDK接口回归。
- Changes / Reasons：写入新的静态接口检查结果，保留compiled_or_linked=false及原有资产校验。
- After / Impact：反映本轮实际执行的检查，不能作为游戏运行证明。
- Validation：JSON回读通过，与实际验收输出一致；6个源输入哈希保持。
- Safety：双外部备份；UTF-8无BOM、LF保持，中文检查通过。
- Unresolved：编译、HLSL和游戏行为待验证。

### docs/reference-observations.json
- File：E:\KenshiProject\2.Projects\IrisArsenal\docs\reference-observations.json。
- Role / Code location：历史参考差异；observed哈希。
- Before：保存上次观测的Ephnel参考源码哈希。
- Changes / Reasons：验收发现参考源码再次发生外部变动，仅记录新哈希；原始baseline未改。
- After / Impact：本项目不以该实时源码为输入，未写入Ephnel或其他项目。
- Validation：当前差异已记录，Iris实际源输入6项严格哈希校验通过。
- Safety：双外部备份；UTF-8无BOM、LF保持，中文检查通过。
- Unresolved：外部修改者未确认。

### docs/file-changes.md
- File：E:\KenshiProject\2.Projects\IrisArsenal\docs\file-changes.md。
- Role / Code location：本逐文件报告；新增编译修复节。
- Before：只有原型交付记录。
- Changes / Reasons：追加真实错误根因、文件范围、验证及备份索引，保留历史。
- After / Impact：供用户追溯此次修复，不影响运行包。
- Validation：UTF-8严格回读及中文/替换字符检查。
- Safety：双外部备份；UTF-8无BOM、LF保持。
- Unresolved：本报告不证明编译或实机通过。

### docs/delivery.json
- File：E:\KenshiProject\2.Projects\IrisArsenal\docs\delivery.json。
- Role / Code location：交付哈希清单及编译状态。
- Before：源码/检查/状态文件哈希为修复前。
- Changes / Reasons：刷新本轮文件哈希，记录用户上次构建失败、本次等待重编译，compiled=false/deployed=false保持。
- After / Impact：审计清单对应当前文件，不组包、不部署。
- Validation：清单每项重新计算SHA-256，包内全部资产与修复前相同。
- Safety：双外部备份；UTF-8无BOM、LF保持；备份详见同目录change-reports下本轮JSON。
- Unresolved：需要用户重新生成DLL。

本轮已创建备份（本报告和交付清单自身备份另见即时change-reports）：
- D:\CodexBackups\IrisArsenal-20261015-201612-706680\edit-201612-712219\E\KenshiProject\2.Projects\IrisArsenal\IrisArsenal.cpp
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-201612-706680\edit-201612-715632\E\KenshiProject\2.Projects\IrisArsenal\IrisArsenal.cpp
- D:\CodexBackups\IrisArsenal-20261015-201612-706680\edit-201612-721232\E\KenshiProject\2.Projects\IrisArsenal\tools\verify_prototype.py
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-201612-706680\edit-201612-725331\E\KenshiProject\2.Projects\IrisArsenal\tools\verify_prototype.py
- D:\CodexBackups\IrisArsenal-20261015-201612-706680\edit-201612-737793\E\KenshiProject\2.Projects\IrisArsenal\STATE.md
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-201612-706680\edit-201612-739932\E\KenshiProject\2.Projects\IrisArsenal\STATE.md
- D:\CodexBackups\IrisArsenal-20261015-201645-533265\edit-201646-332753\E\KenshiProject\2.Projects\IrisArsenal\docs\reference-observations.json
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-201645-533265\edit-201646-336201\E\KenshiProject\2.Projects\IrisArsenal\docs\reference-observations.json
- D:\CodexBackups\IrisArsenal-20261015-201645-533265\edit-201646-343083\E\KenshiProject\2.Projects\IrisArsenal\docs\validation.json
- E:\AIWorkSpace\_backups\IrisArsenal-20261015-201645-533265\edit-201646-346338\E\KenshiProject\2.Projects\IrisArsenal\docs\validation.json

## 2026-10-15 0.1.1首次运行纠错

详见[运行证据和逐文件报告](0.1.1-runtime-fix.md)。已确认首次无伤害查询拒绝导致整插件停用；本轮隔离查询、补齐19层材质绑定并默认关闭线框。新DLL未编译/未部署，当前package标记ready=false。源网格/骨架/DDS/FCS二进制未变。

## 2026-10-15 最新碰撞模板审查（0.1.2）

[碰撞接入模板](Collision-Template.md)明确诊断与正式消费者的边界；[逐文件审查记录](0.1.2-template-review.md)记录当前路径恢复/point读取/版本更改。本轮未导入ALL_HITS/SDK/健康，未编译部署。

## 钻头材质修订（2026-10-16）

[源证据及逐文件报告](0.1.2-drill-optics.md)：同像素PNG兼容转存、源金属镜面与橙红能量/弧光透明恢复；C++、模型、动画、碰撞和DLL保持。当前资源合同IRIS_DRILL_OPTICS_V1，未编译HLSL、未部署/实机。
