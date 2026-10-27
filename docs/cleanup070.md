# 070死代码与冗余资源清理（2026-10-21）

本轮按用户“清理但不影响模组功能”执行，不修改C++/H或DLL。运行版本继续是用户编译0.4.24，视觉069不变，清单增加`IRIS_RUNTIME_CLEANUP_070`。没有执行C++/HLSL编译或启动游戏。

## 实际清理

| 内容 | 数量 | 处理 |
| --- | ---: | --- |
| 无引用旧材质声明 | 106 | 只删完整对象；145份有效声明正文哈希逐项保持，含mesh默认材质 |
| 无引用GPU程序声明 | 2 | IrisEnergyVP/FP，被059源光流取代 |
| 无调用HLSL函数 | 2 | iris_energy_vp/fp；其余函数/结构/参数保留原字节 |
| 不再引用的文件 | 2 | iris_finisher064.material、iris_179f128b96e16ff2.dds，删除前双备份 |
| 运行包中的开发证明CSV | 22 | 原字节迁至docs/pose-proofs，生产端/验证端/两份历史回归更新路径 |
| 资源作者未使用导入 | 17 | AST加载与跨模块引用核查后移除；六个作者的非import AST保持 |

运行包154→130文件（含清单），60,296,067→53,867,731字节，减少6,428,336字节（约6.13MiB）。22份CSV仍在开发目录，保持验证能力，不以删除审计证据充数。

## 判断依据与边界

新增tools/prune_runtime070.py：根集取当前effects.csv、drill.csv、所有包内mesh默认材质、原生FCS filename/string字段、本插件手动创建的Debug和WeaponTrail。继续跟踪材质→GPU程序→HLSL和纹理；内置Basic_Texture_VP/Basic_Coloured_Texture_VP明确是外部程序，不能误删或报成本包缺失。先完成整图检查再写入；缺根、未知外部程序、非法括号即停止。

不能只看最终CSV，因为createEntity在setMaterialName之前会遇到mesh原始默认名；这些材质也保留。不能用“没有普通调用点”判断C++死函数：HybridGun的虚函数、PhysX回调、构造函数及RAII计时对象仍执行。五份C++编译单元审计后没有证据足够的孤立普通函数，未为制造清理数量删除诊断模式或回调。

保留全部22效果记录、25维源曲线、模型、动画、有效纹理像素、FCS、配置、伤害与PhysX代码、事件和生命周期。保留当前构建缓存/IDE设置、第三方SDK、完整资产重建的旧作者和source-cache、许可证以及历史经验/报告。这些是构建/恢复/审计输入，不能因版本号旧就删。

同名IrisArsenal/Eight/d731a679727eca在iris_eight.material与iris_muzzle063.material中depth_write不同。覆盖行为尚未唯一证实，两个原块及顺序均保留；本轮不借清理改准星渲染策略。

## 后续流程

proofs统一由asset_paths070.PROOFS定位。author_prototype/author_moves写入新目录，verify_prototype/verify_moves及035/036历史检查读同一位置。完整重建仍按原顺序执行全部作者，最后在prepare_drill_optics和052退役清理之后调用070，避免重建恢复冗余项。

日常UpdateMod.cmd仍只组包已有完整资源、双备份、清空目标并复制；没有给日常Update增加重建或历史回归步骤。PrepareAssets完整重建未在本轮运行，也未宣称全重建已实测通过；已检查真实生产调用点、依赖模块导入、重复清理与全部有效输入。

## 实际验证

- 20份男女招式动画实际重算骨骼世界变换，与迁移后证明CSV逐帧对照，握点/角度阈值通过；22CSV原字节SHA256与旧包保持。
- 145份有效材质对象正文保持；GPU有效声明正文保持；公共HLSL只有两段无调用函数和对应过时注释被裁剪。
- 124个其余运行构件SHA256保持，全部C++/H/DLL保持，清理后引用闭包和重复执行无变化。
- 引用缺失/未知外部程序时main未调用写入或删除；含字符串/注释括号与未闭合对象的词法边界验证通过。
- 全部Python AST、10份C++/H Tree-sitter语法检查通过；21项原更新沙盒测试通过，包含全量备份、回退和未知文件处理。
- 新包全清单哈希通过，游戏正常退出后同步130文件并逐字节终验。未作游戏GPU/战斗运行测试，不用静态检查承诺FPS或覆盖所有运行故障。

## 同步与恢复

同步状态：True。游戏目录：`D:\steam\steamapps\common\Kenshi\mods\IrisArsenal`。DLL SHA256：`6cc9c8584de8f289cca72c13c5dd9204c182da67697810267d7100945f5f8afe`，无需重新编译DLL。

旧游戏mod完整备份（含日志）：
- `D:\CodexBackups\IrisArsenal-CleanUpdate-20261021-231130-683957-45111654`
- `E:\AIWorkSpace\_backups\IrisArsenal-CleanUpdate-20261021-231130-683957-45111654`

项目小文件删除/修改前也逐项双备份到：`D:/CodexBackups/Task-Iris-Cleanup070-20261021-224528/` 和 `E:/AIWorkSpace/_backups/Task-Iris-Cleanup070-20261021-224528/`，保留原路径，逐文件报告在`D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-Iris-Cleanup070-20261021-224528`的report-*.json。

项目文本原UTF-8/BOM/换行由写入器检测并保持，写后中文/替换字符检查完成；二进制文件原字节备份。恢复需退出游戏后从完整旧mod备份恢复；若恢复工程，则按逐文件报告Safety.backups恢复作者/路径与资产，避免下一次Update再次同步清理包。历史源模组文件及正式1.0快照未改。
