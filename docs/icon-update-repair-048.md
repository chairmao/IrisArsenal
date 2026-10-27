# 048：修复UpdateMod完整重建失败，已部署0.4.7

用户确实在2026-10-18 04:02执行过UpdateMod.cmd。文件与报告证明：04:02:15已编译带047合同的新DLL；04:02:41撤销ready并开始资源重建，04:03:32完成资源；随后实际校验复现AssertionError: package:IrisArsenal.mod，尚未进入游戏部署。

根因：author_prototype.field会删除旧键再追加。047准备包直接最后更新相机浮点字段，而author_moves.fcs_assets完整重建先更新相机、后更新伤害，把相同数值的字段重新排序。仅本武器字段顺序不同、各值相同、其他47记录及头部完全相同，但严格字节摘要应当阻止未确认差异。048修复生产者顺序，不放宽摘要门、不重编译、不改变数值。

更正上一轮验证范围：准备包通过不能代表UpdateMod完整重建后通过；这次补上真实FCS生产者两次连续运行和原047已验收摘要一致的回归。完整运行update_mod.py --package-only后：资源重建、全套非编译检查、两次FCS重建与用户DLL组包均通过。

经用户确认已退出游戏，使用同一部署函数完成完整同步：

- 游戏目录D:/steam/steamapps/common/Kenshi/mods/IrisArsenal实际版本0.4.7。
- DLL与用户已编译产物SHA256一致，带IRIS_HEIGHT_REACTION_CANNON_ICON_047。
- 火神/极致驱动四份男女身体动画均不同于旧游戏版本，并与项目的新枪口高度动画逐字节一致。
- 新电脉范围资源、13条曲线及三远程入站保护配置随整包安装；不把只换DLL当作更新。
- 138个安装文件校验，实际写入17文件；用户现有INI键由更新器保留、只补缺键。安装清单的每一个摘要与实际文件匹配。
- 图标FCS已实际同步auto=true、H=0.059155464、V=-0.05018258、zoom=2.29；原两份10月15日旧PNG在D:/CodexBackups与E:/AIWorkSpace/_backups双备份后删除，下次游戏原生生成。
- 不自动启动游戏；未运行游戏GPU/实机画面或FPS测试。无需用户再次编译DLL。

代码仅修改Python作者顺序、验收挂接并新增FCS重建回归；无C++/头文件修改。UTF-8/no BOM与原LF保持，中文/乱码扫描通过。项目源代码/数据和部署文件均按文件单独双备份。

部署证据：D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-IrisArsenal-IconHotfix-048-20261018-041013-4cfd72\deployment-result.json；逐文件部署报告：D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-IrisArsenal-IconHotfix-048-20261018-041013-4cfd72\deployment-audit\IrisArsenal-Update-20261018-042101-806001-e45bc3f0；缓存报告在同任务目录cache-file-report-1/2.json。项目代码逐文件报告也在同任务目录report-*.json。

