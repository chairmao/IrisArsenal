# 066：钻头圆环显隐与旋转同步修正（源码0.4.22，待用户编译）

Owner: Codex

## 已证实的旧错误

用户实际观察：红暗圆环先出现并静止，稍后才和钻头一起旋转。064的`setIndexDataEndIndex(0)`并没有隐藏圆环，之前仅凭SDK声明/符号和CPU预览说“已改”是不充分的。

本机`OgreMain_x64.dll`导出只读反汇编：`SubEntity::setIndexDataEndIndex` RVA `0x368610`先`test rdx,rdx`，为0跳至`0x36862a`直接返回；无字段写入。`resetIndexDataStartEndIndex`把两个覆盖值恢复0，`getRenderOperation`在两值相等时保持原始索引。因此“末尾设0就隐藏”的前提在本机不成立，和用户画面完全吻合。未附加游戏、调用DLL或修改引擎。

## 最小修复及调用链

`安全可视更新 → ShowParts / PositionVisual → 当前自有SubEntity custom9 → 配套顶点程序 → 投影裁剪`。

- 首次创建钻头时初始化实例custom9=0。
- 正式消费者仍以同一源时刻`spinBegin=1.633267999`计算钻头旋转角和圆环显隐。小箍0与红/黑圆环15..18在旋转前custom9=0，达到旋转点立即=1。闭环诊断按自身profile.spin使用同一机制。
- 顶点程序关门时把这五个子网格的全部投影顶点设为`(0,0,2,1)`；z>w，三角全部处于远裁剪面外，没有静止圆环或淡入。开门时保留原始worldViewProj投影，圆环和钻头同一个pose，不增加独立旋转时钟。
- 只增加小箍/圆环的两个顶点入口；14个实体钻片和双翼仍走原金属程序。三个原金属顶点/金属片元/圆环片元函数逐字保持。源网格、原贴图、颜色、透明混合和转速不改。
- 不再改IndexData、不改共享材质参数、不改Entity ABI。更新仍在原有安全可视窗口内；跨帧只保存既有自有Visual对象，没有新增游戏对象借用指针、Hook、线程、PhysX或伤害调用。
- 仅门状态变化时记录`drill_ring_gate`或`proof_drill_ring_gate`，包含cast、clip、visible、angle和GPU_verified=0。它证明参数传递，不证明GPU图像。

## 已执行验证

实际本机Ogre PE导出及反汇编、同一19层源网格/原贴图、0.5/1.2/1.62秒及旋转前后边界数值检查、开门后下一帧顶点变化、Shader/材质/实例参数闭包、10份C++/H语法与3份Python AST通过。

94个IrisCombat函数仅Create/Configure/ShowParts变化；49个IrisArsenal函数仅Create/PositionVisual变化，其他函数逐字保持。原三个Shader函数逐字保持；本次基线只改变三份钻头文本资源、两个C++、版本资源及包清单。其他资源/伤害/查询源码和当前安装包哈希保持。

已生成并实际查看真实纹理/网格的CPU前后对照，旧零索引语义会在旋转前绘制静止环，新裁剪逻辑则为空；开门后三帧图案旋转。动态预览也已生成。CPU光栅器没有运行Ogre/HLSL，不能冒充游戏截图或声称实机已修复。

验证证据及CPU图片/GIF：`D:/CodexWorkSpace/Sessions/20261002-235652-kenshi-crash-407794f2/Task-Iris-Ring066-20261021-023649`。

## 编译、更新、恢复

源码版本0.4.22 / `IRIS_DRILL_RING_GATE_066`。按项目与code-modification-principles的不代编译要求，本轮没有编译C++/HLSL，没有部署新资源，没有启动/终止游戏。

现有游戏DLL仍是用户编译0.4.21，SHA256 `adbb50d9342c6da1e5b1c5cc52941f77fcdd9c27562a91fc34bd22b60c7490bf`。包内ready=false；已实测旧DLL被066合同拒绝，避免缺custom9的新资源与旧DLL混用。

请编译`E:/KenshiProject/2.Projects/IrisArsenal/IrisArsenal.sln`，**Release|x64 / v100**；正常退出游戏后运行现有UpdateMod.cmd。脚本仍是组包后备份/清空/复制，本次没有扩展更新行为。

所有小文件改前双备份在`D:/CodexBackups/Task-Iris-Ring066-20261021-023649`和`E:/AIWorkSpace/_backups/Task-Iris-Ring066-20261021-023649`。保留原UTF-8/BOM/换行并扫描中文/乱码。逐文件报告在任务目录；恢复应按同一检查点同时恢复配套C++/版本/作者工具/三份材质文本/包清单，不能只恢复其中一层。
