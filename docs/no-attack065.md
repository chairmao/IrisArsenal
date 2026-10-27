# 065：钻天破材质语法使全部攻击停用的修复

Owner: Codex

## 已确认原因

用户已编译并部署DLL **0.4.21 / IRIS_DRILL_FINISHER_064**，SHA256 `adbb50d9342c6da1e5b1c5cc52941f77fcdd9c27562a91fc34bd22b60c7490bf`。不是旧DLL或更新失败。

`IrisArsenal-20261021-020700-100-3608.log:250–256`：`drill_blast`预热失败，随后`plugin_disabled: effect material binding rejected`。`kenshi.log`中同一材质文件的16处声明报告`base object named "1"/"0"/... not found in script definition`。源NIF层名含冒号而导出声明未引用，Ogre将冒号解析为继承运算符，未创建期望的材质。`IrisCombat.cpp Visual::Create`绑定回读失败，经现有异常路径停用插件，因此全部私有招式不能起手。

## 本次改动

- `tools/finisher_sources064.py`：只修正apply中声明名称的引号，保留NIF原层名。后续重建不会再次输出歧义语法。
- `package/IrisArsenal/assets/iris_finisher064.material`：28个定义完整引用；除声明引号外逐字符一致。网格、CSV引用名保持原值。
- `package/IrisArsenal/IrisPackage.json`：重算资源哈希；DLL仍是用户编译的0.4.21，没有伪造新编译版本。

未改C++/Hook、选招条件、倍率/范围/伤害、瞄准、物理查询、时序、Shader、贴图或线程。无需重新编译。保持原异常保护，不通过移除材质检查掩盖错误。

## 实际验证及边界

已执行SDK词法token规则声明检查：旧16处歧义，新0处；28个定义/实际网格二进制/效果表引用逐项一致；22个效果记录引用闭包及纹理/程序文件存在检查通过；真实作者循环在内存重生成与修复文件完全一致；其他运行构件与全部C++/H/DLL基线哈希保持；用户DLL合同/PE/x64/源码时间检查通过。

更正064交付的验证范围：此前数据闭包和CPU预览没有覆盖Ogre材质脚本的继承词法，不能证明材质在游戏中成功创建。本次同样不将静态检查称为Ogre/GPU或战斗实测；未启动游戏。

其他063共享材质`IrisArsenal/Eight/d731a679727eca`存在预先重复定义，原日志未将其报告为本次停用原因；相关两文件保持原样，没有扩大到其他招式。

## 安全与恢复

修改前双备份：`D:/CodexBackups/Task-Iris-NoAttack065-20261021-021516`、`E:/AIWorkSpace/_backups/Task-Iris-NoAttack065-20261021-021516`。保留UTF-8、原BOM和换行，中文及乱码扫描通过。完整逐文件报告、日志证据和验证在会话Task-Iris-NoAttack065-20261021-021516目录。

正常退出游戏后现有UpdateMod.cmd可同步修复；无需编译DLL。若已同步，在下次启动时重新创建材质；当前进程因运行错误停用的插件不能通过热替换文件自行恢复。
