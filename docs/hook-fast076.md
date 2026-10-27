# 076：通用Hook在进锁前排除无关调用

源码版本0.4.27，代码合同IRIS_HOOK_FAST_076。用户授权后修改；未编译、未部署、未操作游戏。核对时游戏和用户bin仍为0.4.26/075，保持原文件。原正式1.0快照未改。

## 实际调用链

### 选招

`CharStats::chooseAttack → ChooseHook → originalChoose（恰好一次，四参数原样） → UsesWeapon(stats)`。

UsesWeapon读取SDK当前武器句柄、物品类型与FCS stringID `1-IrisArsenal.mod`。不是本武器，直接返回已经取得的原生结果，不进插件锁。是本武器才进原锁，再核对身份、启用/故障状态、原生站姿/医疗和原生返回类型，进入IrisCombat::Choose；私选无结果仍返回原生。没有扫描背包，没有新增装备缓存，也没有玩家阵营限制。

玩家明确要求不要写死重武器：本轮未加入类别快退，并将旧NativeStandingMeleeAllowed里的SKILL_HEAVY限制改为原生当前类别匹配。类别只用于核对原生返回技巧是否支持当前FCS类别，不能代替装备身份。原生武术/趴地/混合武术结果继续保留。既有双臂与站姿医疗门保留，本轮没有宣称重做了所有武器类别的单/双手医疗规则。

### 身体动画

`AnimationClass::startCombatAnimation/runCombatAnimation → StartHook/RunHook → OwnTechniqueIdentity`。

非空且明确不属于私有技巧：按原始速度与参数调用原函数一次，不进插件锁，也不调用自有攻速/启动记录。属于十招或原型：继续旧Speed加锁计算、原动画调用和启动记录。NULL技巧保留旧路，避免改变原型尚未初始化的旧边界。私有动作的锁没有删除。

### 格挡检查与受击反应

`CombatClass::checkForNeedBlock → MeleeBlockCheckHook → MayNeedTechniqueGuard(self,false)`。

当前近战技巧非本模组时走原生检查；是候选才在原锁内运行ProtectedMeleeMove，核对姿态、世界、Actor、动画进度、配置，再决定是否阻止主动格挡。

`Character::_startStumble → MeleeStumbleHook → MayNeedTechniqueGuard(combat,true)`。

同时看近战当前技巧和角色动画要求中的技巧身份，后者必须保留，否则会遗漏远程霸体。读取动画要求前核对角色有效性；不确定或发生标准异常回原锁内检查。候选在锁内走原ProtectedMeleeMove/ProtectedRangedMove及配置；保护生效仍仅调用既有_getHit(false)，其他情况原受击入口一次。锁外不授予保护、不遍历Actor容器、不访问Ogre场景或PhysX。

### 身份发布

原有SafeHook确认AI/PhysX静止并取得原锁 → Tick → EnsureMoves构造/验证技巧 → PublishTechniqueIdentity → 正式消费者得到指针。诊断原型在Ensure完成初始化/验证后也发布。

快照共11份，每份11指针，原始身份数组共968字节（x64）；每次首次注册只填下一份快照，再用InterlockedExchangePointer发布。读取只做一次原子快照指针读取，然后普通地址比较，不能对11个槽分别做原子RMW。旧快照不覆盖、不释放，技巧沿用当前进程期保留规则，避免读者撞上被改写/回收的表。重复发布同一对象幂等；槽更换或超过11次首次发布明确报错，不能静默覆写。原角色/场景状态读档照常清理，没有新增跨帧角色缓存。

## 性能收益的原因与限制

旧路径里普通角色也会取得共用锁，再检查武器/技巧。新路径让这些明确无关调用绕过锁，减少锁获取、保护检查和自有缓存访问；若与持锁者同时进入，还能减少等待。装备身份检查本身轻量，不是本轮试图省掉的主要工作。

没有删Hook或跳过原生职责，没有把AI/医疗/物理移到后台，没有新线程或全局移动锁，没有玩家专用限制。原生伤害/查询/远程模块保持。收益尚未实测；锁获取墙钟含函数开销，也不等于全部是竞争等待。不能据静态快退次数宣称FPS提升，原有弹体查询热点仍需单独优化。

## 可关闭的长期审计

在项目distribution和package两份INI里增加：

```ini
EnableHookAuditLogging=0
HookAuditSampleEvery=128
```

默认0，避免为观察优化效果让所有普通NPC增加原子计数。要采集时设EnableHookAuditLogging=1，并保持EnableLogging=1、EnablePerformanceLogging=1；启动时读取。每N次进锁回调采样获取锁和受保护段墙钟，普通快退不调用QPC。关闭时审计RAII不做原子计数或QPC，只保留快速开关判断。

开启后五组固定、64字节对齐的原子累计，不取得诊断共用锁、不分配TLS/堆内存、不逐调用写文件。既有摘要窗口新增固定10行audit_hook（五入口×窗口/进程）：calls、fast_returns（未进所审计锁的回调）、locked_callbacks、lock_entries、sampled_callbacks、acquire_wall_ms_sampled、protected_wall_ms_sampled等。累计不跨线程清零；独立原子快照可能包含尚未退出的回调，带inflight_possible标志。窗口是累计差值；最大值明确为process，不伪称窗口最大值或FPS。计时仅采样部分，不能把采样总量称为全量CPU时间。

## 验证

实际结果见[Task-Iris-HookFast076-20261022-200436-77592d/validation-final076.json](D:/CodexWorkSpace/Sessions/20261002-235652-kenshi-crash-407794f2/Task-Iris-HookFast076-20261022-200436-77592d/validation-final076.json)：

- 228组实际Hook AST分支与075原件对照，52个无关路径未进锁；含远程身份遗漏反例、保护异常回原生和失效角色不能读取动画要求。
- 128组选招参数/返回对照，64个非本武器组合无锁；180组九种当前类别矩阵；原732资格案例、1152多持有者条件及2/3/8人分组继续通过。
- 7744次不可变快照发布交错规格观察。属于Python规格和源码结构检查，不是C++原子并发压力测试。
- 审计关闭方法按真实AST执行，不提供QPC/原子函数也通过；不是运行时开销为零的实测证明。
- 10份C++/H语法树及4份Python AST通过。语法器先剥除__fastcall和__declspec(align(64))扩展；不是MSVC语义或链接检查。实际v7.0A SDK声明含所用原子API。
- 20个伤害/物理/远程相关关键函数正文保持，452受保护文件哈希保持；安装目录和用户bin不变。待编译包129项SHA匹配。
- 21项更新隔离测试：20通过、1因Windows符号链接权限不足跳过。实际旧075 DLL被076合同门正确拒绝；没有运行实际更新脚本。

## 构建和启用

本轮不代编译。用户编译 `E:\KenshiProject\2.Projects\IrisArsenal\IrisArsenal.sln`，Release|x64 / v100；正常退出游戏后执行现有UpdateMod.cmd。脚本仍只组包/完整复制，未新增重建流程。包ready=false，pending_version=0.4.27，旧DLL身份保留；只有包含076标记且晚于源码的新用户DLL才能组包为0.4.27。

运行日志一次hook_fast_ready contract=IRIS_HOOK_FAST_076及0.4.27文件版本用于辨认新构建，不能把当前旧DLL当作新优化。未进行MSVC、游戏线程、视觉或FPS测试。

## 双备份与逐文件报告

- `D:\CodexBackups\Task-Iris-HookFast076-20261022-200436-77592d`
- `E:\AIWorkSpace\_backups\Task-Iris-HookFast076-20261022-200436-77592d`

保留完整原路径；每次修改前备份，UTF-8及原CRLF/LF保持，中文/新增乱码检查通过。逐文件报告在本任务reports目录，包含每次修订的before/after SHA与编码。IrisRanged、NativeMultiContact、伤害倍率/范围/权重、FCS、特效、存档和游戏运行目录保持。
