# 一键恢复并更新游戏 mod

双击项目根目录的 UpdateMod.cmd。

目标固定为 D:\steam\steamapps\common\Kenshi\mods\IrisArsenal。已从空 package 实际恢复并安装用户编译的 0.3.6，106 个文件终验通过。八招默认权重均为 1。

脚本会核对已编译 DLL 的 x64、版本合同、源码时间，重建普通锤枪/钻头/图标/18个骨架/八招事件/FCS/分层特效/纹理/材质，再静态验收并同步。不会编译 C++ 或 HLSL。源码改后仍需你在 IrisArsenal.sln 手动编译 Release|x64 / v100，再双击更新。

可以删除 package；不要删除 distribution、tools、docs 的源身份记录，也不要删除原始 Skyrim 素材和本地工具依赖。distribution 为独立恢复模板。此更新流程生成产物，直接手改 package 中生成的资源会被作者脚本重新生成；应把长期修改落实到资源作者或模板中。

更新时必须正常退出 Kenshi；检测到游戏进程、DLL过旧、缺素材、校验失败或备份失败就停止。复制失败会回退本次写入，不终止游戏。

游戏目录已有 INI 的数值、注释、编码与换行保留，只追加缺失键；已有 .info 保留，避免更改工坊身份。日志与用户额外文件不删除。首次安装使用 distribution 默认 INI。

覆盖前备份到 D:\CodexBackups 和 E:\AIWorkSpace\_backups；部署逐文件记录在 docs/update-runs。小文件严格双备份，大于20MB的既有目标拒绝自动覆盖。首次空目录安装没有旧文件可备份。

PrepareAssets.cmd 现在也能恢复缺失基础资源，但只生成和验证资产；PreparePackage.cmd 重建并组包，不写游戏。运行依赖是本机已有 Codex 局部 Python、NumPy、Pillow、源素材和只读语法依赖，脚本不下载或安装任何东西。

本次没有修改 C++、战斗参数、mods.cfg 或存档，也没有恢复轮询。验收详见 one-click-update-validation.json，画面/性能仍需游戏测试。
