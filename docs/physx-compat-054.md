# IrisArsenal 0.4.11：PhysX兼容策略054

用户要求：尽可能尝试加载后续运行时，不把完整文件版本定死为2.8.4.6。本轮只修改PhysX初始化与必要的版本/组包/验证记录，不涉及招式、特效、倍率、查询几何和18个Hook。

## 实现与边界

- 原先要求`PhysXCore64.dll`的四段版本完全等于2.8.4.6；现在最低2.8.4.6，同2.8.4 Nx接口族内的后续修订（例如2.8.4.7）可进入尝试路径。第三方安装包9.x版本不等于进程Core的SDK版本。
- 仍只检查已加载的`PhysXCore64.dll`、`PhysXLoader64.dll`和`NxGetPhysicsSDK`，不加载另一份DLL、不创建/释放SDK、不替换接触报告。SDK尚未建立仍是暂态，每个原查询继续核对`scene->getPhysicsSDK()`是否与当前SDK相同。
- 版本资源不可读/损坏、低于最低版本、缺导出或未适配的SDK接口族明确报告原因。不能用未知虚接口调用“没立即崩溃”来证明ABI兼容；因此不增加该类探针或SEH兜底。
- 2.8.5、2.9以及3.x及以上没有在此项目实现新的接口适配，不声称已支持。PhysX3中Nx改Px、查询回调和形体接口均有变化：[NVIDIA官方迁移说明](https://nvidiagameworks.github.io/PhysX/3.3/PhysXGuide/Manual/MigrationFrom28.html)。同2.8.4新修订也是候选，不是对未知二进制兼容性的保证。

## 日志

新增一次性`physx_compatibility contract=IRIS_PHYSX_COMPAT_054`，记录实际四段版本、最低版本、导出存在性、接受/拒绝原因、`revision_mode=baseline/newer_patch_attempt/rejected`；`accepted=1`仅表示准许尝试，明确标记`validation=file_version_and_export_only runtime_verified=0`。模块尚未加载不会永久禁用或每帧刷该日志。

运行身份0.4.11/主合同054；原053伤害队列合同保留。2.5ms预算、32次配置、40ms软目标、FIFO、安全窗口及所有伤害/资源保持。

## 交付与验证

按项目/Skill规定未编译、未链接、未加载新DLL或启动游戏。先执行非编译语法树、真实本机Core文件版本/Loader导出、14组版本/导出边界、旧DLL拒绝和原查询/资产摘要保持检查；结果保存在本会话Task-IrisArsenal-PhysXCompat054的validation文件中。静态条件通过不能证明新修订SDK的实机表现。

项目package只标`ready=false`、版本0.4.11/代码合同054，保留原有DLL真实字节与哈希；游戏仍是已部署0.4.10，没有同步。请编译`E:\KenshiProject\2.Projects\IrisArsenal\IrisArsenal.sln`的 **Release|x64 / v100**，成功并退出游戏后执行`UpdateMod.cmd`；新合同会拒绝旧053 DLL。

双备份根：

- `D:\CodexBackups\IrisArsenal-PhysXCompat054-20261018-181100-563418-16360a`
- `E:\AIWorkSpace\_backups\IrisArsenal-PhysXCompat054-20261018-181100-563418-16360a`

逐文件变更与编码/换行/备份记录：本会话任务目录`reports.json`。未修改的游戏、资产、查询与C++基线见`physx-compat-054-baseline.json`。


## 054更新脚本校验修正

用户已于2026-10-18 18:27编译出0.4.11，旧专项却固定断言“当前编译DLL必须被当作旧版拒绝”，导致正确新DLL被报告为“旧DLL被当作054”。已移除该错误前提，并将用户编译DLL排除于旧资源不可变哈希；其他资产摘要保持。旧合同拒绝/新合同接受仍由现有隔离用例覆盖，真实PE/合同/源码时间门仍在UpdateMod及stage_package入口执行。此修正只改Python验收，无需重新编译C++。

该报错不代表同步成功：确认时项目bin为0.4.11，package和游戏DLL为0.4.10。修正后重新执行UpdateMod.cmd即可继续原有完整更新流程；真实游戏运行仍需新日志确认。
