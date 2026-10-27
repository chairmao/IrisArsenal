# IrisArsenal 正式版2.0

2026-10-24按用户要求特别封存。内部版本保留0.4.34 / IRIS_MEDICAL_GATE_083；未重新编译，DLL三处相同，现有PDB身份匹配。SHA256：`5f666e750414e0c3550efadbb3c840deb3ca6900d4755923e84144accb78b21e`。

- 主归档：[正式版2.0](D:/CodexBackups/IrisArsenal-Formal2.0-20261024-005639-412184/RELEASE.md)
- 第二盘：`E:\AIWorkSpace\_backups\IrisArsenal-Formal2.0-20261024-005639-412184`
- 每盘7288文件，258330897字节；7281份实际输入逐项校验，136个runtime文件隔离恢复通过。
- SHA256SUMS.txt：`62f0cc5186ab6cefa2c34b515f3d66db6b03f931c1339d004d84f4929321da35`；SEALED.json：`94219c4ed16661d2c9e8151df16d80590505936b16f9f181d843c3d7a0b1dc28`。文件设只读，后续优化不得覆盖；正式版1.0独立保留。
- 原源码/工程/配置/资源/更新器、实际DLL/PDB、两个独立补丁、发布资料/封面母版、日志及经验均已保存。完整恢复见归档RESTORE.md，依赖边界与原清单两个元数据旧哈希见IDENTITY.json/RELEASE.md。
- 主FCS零RACE，Gameplay与工坊ID3825316881保持。未修改倍率/范围/权重，未更改C++或更新脚本，未操作存档/加载顺序/工坊。

归档当时三处日志均关闭，作为发布基线。随后用户明确本地需开启日志，当前distribution/package/游戏六项开关已另行备份后开启；发布时请在发布副本关闭，不改封存原件。本地配置下次启动读取，无需编译。

下一轮实施细表：[optimization-plan-formal2.md](optimization-plan-formal2.md)。本次只是计划和归档，没有执行战斗优化或FPS/GPU实测。源合同/版本一致不等于精确可复现构建，原外部SDK/全部上游素材不在runtime归档中。

验证及逐文件报告：`D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-Iris-Formal2-20261024-005639-412184`。本地配置和STATE修改前双备份：`D:\CodexBackups\IrisArsenal-Formal2.0-LocalLogs-20261024-005639-412184`、`E:\AIWorkSpace\_backups\IrisArsenal-Formal2.0-LocalLogs-20261024-005639-412184`。
