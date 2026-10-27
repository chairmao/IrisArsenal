# 072 原生近战资格和回退

源码0.4.25，待用户编译。当前用户bin/package/游戏DLL仍为0.4.24、SHA256 6cc9c8584de8f289cca72c13c5dd9204c182da67697810267d7100945f5f8afe。本轮未编译或部署。

## 最终行为

ChooseHook仍先且仅调用一次原生chooseAttack，range/reach/last/stationary原样传递。正式十招模式仅在专用锤枪、原生当前类别SKILL_HEAVY、角色有效、原生双臂可用、PS_NORMAL且非原生crippled状态时私选。伤势、缺肢/义肢和腿伤状态由原生医疗维护，不加HP阈值，不将任一臂可用当作重武器资格，不将这条双臂规则套用到其他武器。

原生返回武术、趴地或非重武器技巧时保留。技巧同时标记武术和重武器时，无法从最终指针区分入选分支，保守保留原生。原生为空时，只要上述身体资格通过，仍可进入原来的专属距离/权重选择，避免普通招式够不到就封掉钻天破等较远招式。私有选择失败或插件故障均返回已取得的原生值；原生也为空则保持空。

只检查新起手；正在播放动作、抗打断、后效、伤害队列和并发预约/主线程释放逻辑保持。显式DrillProofOnly诊断分支仍是原字节的严格原型规则，以上回退针对正式十招模式。

本轮未将scoreTechnique套到现有单左臂零伤害占位技巧，避免占位记录冒充完整身体资格。没有增加ImpactPoints或伤害段，没有改公共技巧池。此修复补伤势/姿态资格和回退，专属技能的距离/权重仍按玩家配置，不整体搬用普通技巧的技能/负重/上招评分。

## 线程及日志

沿用原生选招回调和ChooseHook既有互斥域，只读原生流程已使用的医疗状态、姿态和技巧类别。不创建线程/锁，不在选招中更新医疗、创建资源或查询物理，不跨帧新增保存角色/技巧指针。初始化一次IRIS_NATIVE_MELEE_072合同日志随原日志开关，没有新增逐帧输出。

## 逐文件变更

| 文件 | 变化 |
|---|---|
| IrisArsenal.cpp | NativeStandingMeleeAllowed资格门；ChooseHook正式模式回退；ReadAssets一次合同日志；源码说明0.4.25 |
| IrisArsenal.rc | 文件/产品版本0.4.25，只有用户编译后才会产生新DLL |
| tools/stage_package.py | 新增072合同校验及清单字段，版本0.4.25；日常Update仍只组包、清空和复制 |
| tools/test_update_mod.py | 真实用户DLL测试同时覆盖旧DLL明确拒绝、后续用户新DLL正常校验，不伪造PE |
| tools/test_native_melee072.py | 解释实际修改函数的C++语法树，执行原生状态替身的分支矩阵 |
| package/IrisArsenal/IrisPackage.json | ready=false，标记源码已改、旧DLL仍0.4.24，禁止混装 |
| STATE.md | 追加本轮真实源码/产物/验证状态，历史保持 |
| 本说明 | 记录范围、证据、限制、编译和恢复 |

## 已实际执行的验证

- 732个实际C++源码AST分支案例：720个双臂/五种姿态/残疾标志/当前类别/原生返回种类矩阵，另覆盖停用、故障、未就绪、私选失败、空角色保护及原生空时距离0/18/50/80的私选入口。原生调用一次及四参数原样传递均有断言。
- 10份C++/H语法、3份Python AST及四个所用SDK入口在链接库/运行DLL的符号存在性通过。它们不能代替MSVC类型和链接验证。
- 更新脚本21项沙盒回归：20通过、1项系统未允许创建测试符号链接而跳过。真实游戏目录未操作。
- 函数逐字边界：只改ReadAssets/ChooseHook，新添一个资格函数；其余47函数和显式诊断分支原字节保持。IrisCombat、IrisRanged、NativeMultiContact、配置/FCS/动画/特效保持。
- 132份既有运行构件/用户bin DLL/安装DLL及安装清单SHA保持。实际旧DLL被072组包门拒绝。

矩阵以原生已经计算好的状态为输入，未模拟医疗系统伤势变化本身。正常、伤臂、缺肢、正常义肢及腿伤趴地的实际流转仍待用户编译后的游戏验证。本轮未运行/终止游戏、附加调试器或编译，不声称游戏已测或FPS提高。

## 编译和恢复

用户编译 E:\KenshiProject\2.Projects\IrisArsenal\IrisArsenal.sln，Release|x64 / v100；正常退出游戏后运行现有UpdateMod.cmd。新DLL应为0.4.25并包含IRIS_NATIVE_MELEE_072。更新脚本没有增加编译或历史重建步骤。

双备份根目录：D:\CodexBackups\Task-Iris-NativeMelee072-20261022-013135-2cf1e5 与 E:\AIWorkSpace\_backups\Task-Iris-NativeMelee072-20261022-013135-2cf1e5。每个原文件在唯一edit子目录按原盘符/路径保存；恢复时按逐文件报告取回原字节。本轮前的用户DLL和游戏包始终保持。

逐文件报告及验证：D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-Iris-NativeMelee072-20261022-013135-2cf1e5，包含 report-*.json、validation-source072.json、validation-boundary072.json、update-tests072.log。此前原生离线调用链在相邻 Task-Iris-RollNative071-20261022-004723/native-selection071.md。
