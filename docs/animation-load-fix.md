# IrisArsenal 0.2.0：持械不攻击的加载链修复

根因已确认：FCS动画集30～37的16个文件名缺少`action_`。七招找不到资源，钻头错误地加载已有DrillProof文件而非新动作。日志证据为18:23:57的资源不存在，以及18:28:25的eight_animation_wait；不是DLL没有加载。

修复：身体导出与FCS使用统一文件名；验收从实际FCS字段打开骨架，并验证内部动画身份、长度和所有支持种族引用。16处以外的FCS字段和引用逐项一致。旧缺失路径、存在的旧DrillProof、其他招式错引用、越界路径、缺种族引用共5个故障用例均被拒绝。

已同步游戏目录的IrisArsenal.mod与IrisPackage.json，游戏未运行。DLL、全部C++源码、配置、已制作骨架/材质均保持原字节；无需重编译。需用户重新启动游戏，实际出招与后续战斗效果尚待验证。

本轮完整报告：[animation-load-fix-files.json](E:/KenshiProject/2.Projects/IrisArsenal/docs/animation-load-fix-files.json)。证据与同步收据：[animation-load-fix-validation.json](E:/KenshiProject/2.Projects/IrisArsenal/docs/animation-load-fix-validation.json)。既有文件修改前已分别备份到D:/CodexBackups与E:/AIWorkSpace/_backups；文本保持UTF-8及原换行，无乱码；FCS按二进制格式读写并通过往返。
