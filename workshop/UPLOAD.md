# IrisArsenal工坊发布材料

本次只准备项目运行包，不写真实游戏目录，不编译，不上传。现有DLL内部版本保持0.4.34 / 083。

## 操作

1. 正常退出Kenshi后，双击项目原有UpdateMod.cmd，仍是校验现有包、双备份、清空目标再完整复制。
2. 从Steam启动Kenshi的FCS，打开IrisArsenal，进入Steam Workshop上传界面。标题使用“伊莉丝·锤枪 | Iris Arsenal [RE_Kenshi]”。
3. 封面选择游戏mod目录的preview.jpg；_IrisArsenal.img是同一JPEG，已按本机FCS ModData.GetImagePath()真实返回路径准备。
4. 介绍粘贴WORKSHOP_DESCRIPTION.txt，更新说明粘贴WORKSHOP_CHANGELOG.txt；作者署名由你填写，Steam发布账号由上传器关联，没有虚构作者身份。
5. 元数据维持私人草稿visibility=2／id=0；预览完毕后在上传器选择你要的可见性并发布。没有伪造条目ID。
6. 发布后FCS会写入工坊ID。后续Update组包会读取已安装.info与已有包，保留非零ID、已有可见性和更新时间；两个不同非零ID会明确停止，不能静默选错条目。不要删除所有带ID的.info副本。

## 文件与界限

distribution是发布资料源；stage_package.py在计算完整清单前调用workshop_assets.prepare复制这些资料；原更新脚本完整复制清单，无需更换脚本或重新编译。
本体不混入两个独立种族补丁，它们保存在compatibility，按各自依赖单独发布。来源声明包含未齐备的原始素材再分发授权状态；署名不等于授权，公开发布前应核实源作者许可。
封面由imagegen生成，原图位于本任务IrisArsenal-Cover-Master.png；800×800 JPEG仅做尺寸／格式导出，底部没有招式数量。生成提示词和后续修改要求见本会话；未把演示截图当作Kenshi实机宣传。
保留当前INI供后续性能测试，发布玩家版如需关闭日志，README.txt列出全部六个开关；不改数值、物理、动画或诊断默认值。

RE_Kenshi官方：https://github.com/BFrizzleFoShizzle/RE_Kenshi/releases
本机FCS ModData字段与GetImagePath已实际只读核对；游戏与Steam在线上传效果尚未执行。
