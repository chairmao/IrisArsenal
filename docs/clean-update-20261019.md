# IrisArsenal 全量替换更新（2026-10-19）

现在双击 `E:\KenshiProject\2.Projects\IrisArsenal\UpdateMod.cmd`，执行以下固定流程：

1. 检查游戏已退出，检查用户已编译DLL的x64 PE、059代码合同和源码时间。
2. 从现有源素材与distribution恢复完整package，执行资源/动画/FCS校验并组包。此处不调用C++或HLSL编译器。
3. 核对包内每个文件的SHA256和完整目录清单。目标mod即使没有assets或缺文件也能更新。
4. 将目标目录的**全部内容**（包括旧配置、日志、未知文件、空目录）完整备份到D、E两处，并核对SHA256。
5. 清空且仅清空 `D:\steam\steamapps\common\Kenshi\mods\IrisArsenal` 中的内容；复制完整package并逐文件终验。复制失败时恢复整个旧目录。

不再合并INI、保留旧info或按文件名逐项放行。INI使用 `distribution\IrisArsenal.ini` 中的内容；需要长期保留个人参数时修改该项目模板。新图标随package的icons复制，不再顺带刷新全局data/icons。

## 已修复的更新阻碍

- `test_range_metal041` 以前读取游戏mod里的旧fire_blast/drill_blast文件，缺文件就无法开始修复安装。现在对照项目保存的058历史SHA256，仍核对源粒子/实际范围，不依赖目标目录。
- `test_drive059` 的历史未改资源名单包含旧DLL，导致用户已编译的新DLL被误拒绝。现在只保护未改资源；当前DLL继续独立校验PE、059合同和源码时间。
- 更新器删除逐文件白名单和INI合并逻辑，署名、新资源与其他包内构件统一按清单验证后完整复制。

## 本次实际结果

- 已实际清空并完整复制到上述游戏mod目录，**140个文件**均与项目package逐字节哈希一致。
- DLL：**0.4.16 / IRIS_DRIVE_REBUILD_059**；SHA256：`0c0f908a433ac239cbad26d79ac8530f2abb13f66c4f1aff4cb89fbb1f272b58`。没有代编译。
- 旧目录双备份：
  - `D:\CodexBackups\IrisArsenal-CleanUpdate-20261019-222835-150880-150945a3`
  - `E:\AIWorkSpace\_backups\IrisArsenal-CleanUpdate-20261019-222835-150880-150945a3`
- 修改脚本前的备份：`D:\CodexBackups\Task-Iris-CleanUpdate-20261019-221148-ff950c`，另有E盘副本；多次细修的备份和逐文件报告见项目docs/change-reports。
- 整条资源恢复、源资源校验、动画/FCS校验与组包通过；30项隔离测试中29项通过，1项因Windows不允许创建测试符号链接而跳过。包括缺assets安装、完整覆盖、旧配置/日志双备份、空目录、失败恢复、哈希错误、路径越界、同名大小写冲突和游戏运行阻止。
- 保持原UTF-8与换行（cmd为CRLF，各Python按原格式）；修改文件AST/中文乱码扫描通过。

备份中的 `D\steam\steamapps\common\Kenshi\mods\IrisArsenal` 是完整旧目录；需要回退时，先退出游戏，再用其全部内容替换同名mod目录。不要只取其中DLL混配资源。

当前任务证据：`D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-Iris-CleanUpdate-20261019-221148-ff950c`；部署审计：`E:\KenshiProject\2.Projects\IrisArsenal\docs\update-runs\IrisArsenal-CleanUpdate-20261019-222835-150880-150945a3`。已执行文件部署验收，未启动游戏，未声称动作、GPU或FPS实测。
