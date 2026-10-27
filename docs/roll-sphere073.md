# 073 火焰翻滚只移除内部深色序列帧火焰

用户明确要求仅去掉深色序列帧贴图层，保留外层球形效果。本次已检查用户截图、源FireBallExp01.nif的真实NiParticleSystem节点和现有序列化资源，目标确定为两份pFireBall，而不是整个火焰效果或其他招式。

## 结果与范围

仅移除翻滚原始层6、10（IrisArsenal/Source069/roll_blast/6及/10），即原FireBallExp01.nif/pFireBall普通alpha混合的深色火团。活动层12→10；配套移除这两层的序列化submesh、曲线和私有材质声明。

外层球体、闪光、小火星全部保留。其余10个submesh原始chunk及37750个曲线值完全相同；保留材质正文、所有共享贴图和Shader原字节相同。没有删除任何png/dds文件，没有换纹理、调整颜色、提亮或重新设计造型。原保守裁剪bounds和2.5秒曲线总长保持，伤害范围/倍率/起爆事件/游戏秒时钟保持。其他招式、C++/H/DLL、动画、FCS和INI不改。

这是按用户明确要求从源复刻中删去指定火团层，不把删除后的效果称作原模组完整火球。

## 作者与更新

新增tools/roll_sphere073.py，先检查源系统/材质/网格/CSV布局，再返回资源修改计划；只拼接保留的原mesh数据块，不调用Ogre导出器、C++/HLSL编译器或图片生成器。tools/author_effects.py在069作者之后执行此步，因此完整重建不会恢复这两层。日常Update仍是原来的组包和全量复制，未增加重建步骤。

stage_package.py仅增加roll_visual_contract=IRIS_ROLL_SPHERE_073清单字段；现有072代码合同门保持。package资源和SHA256已更新，但ready仍为false：当前用户DLL实际为0.4.24，SHA256 c9c026347b5b9a417372146e699643bd90090882e331e2ac7aa43ffecba0471b，未含IRIS_NATIVE_MELEE_072。此前STATE中的6cc9摘要是之前观察，本轮以本次读取为准，不把它当新072产物。

本次资源删层自身没有新增C++修改；上一轮072仍需用户编译IrisArsenal.sln Release|x64/v100，正常退出游戏后运行UpdateMod.cmd。检查时游戏PID37440正在运行，本轮没有同步/修改游戏目录，也没有启动或终止游戏。

## 实际执行的验证

1. 读取真实源NiParticleSystem名称，确认pFireBall；错误源系统元数据会在写入前被拒绝。
2. 已预览并查看两视角、五个时点的前后共20帧CPU图像：内部片状火团移除，外层球体保持。CPU图不是游戏截图，不能代替Ogre/GPU实测。对照图和GIF在本任务目录。
3. 比对实际写入包与已预览候选，五份修改资源/元数据逐字相同；保留10个原submesh块、全部曲线值、其他效果/曲线记录及143个保留材质对象正文相同。
4. 引用闭包通过，没有新增无引用纹理或程序；第二次计划不再输出。3份Python AST通过，129个运行构件哈希符合待编译清单。
5. C++/H、DLL、png/dds、Shader/程序、动画、INI与FCS哈希不变。更新沙盒21项：20通过、1符号链接权限不足跳过；没有写实际游戏目录。

未编译、未游戏测试、未部署，不声称性能或游戏画面已实测。

## 逐文件说明与恢复

- tools/roll_sphere073.py：指定两层的纯数据后处理。
- tools/author_effects.py：在069之后追加073，其他作者顺序不变。
- package/IrisArsenal/assets/iris_fx_roll_blast.mesh：只删除两段submesh，其他数据块原字节保留。
- package/IrisArsenal/assets/effects.csv：翻滚层数12→10及对应两条名称删除，其他记录保持。
- package/IrisArsenal/assets/effect_curves.csv：仅删除这两层曲线行，其他浮点行原样保留。
- package/IrisArsenal/assets/iris_source069.material：只删除对应两个私有材质对象，其余正文保持。
- docs/eight-effects.json：同步活动层与073来源记录；其他效果结构保持。
- tools/stage_package.py：仅记录073资源身份。
- package/IrisArsenal/IrisPackage.json：同步资源哈希，保留072待编译状态。
- STATE.md与本说明：记录实际完成/构建/部署和验证边界。

每项原文件写前双备份，编码/BOM/换行保留，中文回读和乱码扫描。备份根为D:\CodexBackups\Task-Iris-RollSphere073-20261022-014841-7d52bd及E:\AIWorkSpace\_backups\Task-Iris-RollSphere073-20261022-014841-7d52bd，逐文件报告给出完整恢复路径。

任务证据：D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-Iris-RollSphere073-20261022-014841-7d52bd，包括candidate-validation073.json、validation-final073.json、preview-measures073.json、roll-comparison073-pitch18.jpg、roll-comparison073-pitch58.jpg与update-tests073.log。
