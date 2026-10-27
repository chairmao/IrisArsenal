# 083 医疗结算与物理查询安全门分离（源码0.4.34）

## 当前交付身份

用户授权修复已确认的多余医疗queue等待，并补充必要日志。源码为 **0.4.34 / IRIS_MEDICAL_GATE_083**。未编译、未部署、未启动/终止游戏、未修改存档或mod勾选，也未增加Hook/线程/同步对象。用户现有 bin/package/游戏 DLL 三份仍为0.4.33/082，SHA256均为 `c36c9b69469d7e698bbe0c947193c089e091d84e31dd9bf6c0c4309f584811fe`。该身份由本轮真实文件读取与既有082运行日志核对，纠正STATE旧段落“082尚待编译”的历史状态。

依据为本会话只读取证 [原生队列生命周期](D:/CodexWorkSpace/Sessions/20261002-235652-kenshi-crash-407794f2/Task-Iris-NativeQueueLifecycle-20261023-203814-067533/README.md)：原生 updateUT 先移交待处理物理消息，charsUpdateUT Hook到来时后台可以未启动而getter已false。082 id6有291次医疗机会在第一笔前因queue拒绝。局部原生受击链没有逐笔全队列清空门；原生查询确有门。本轮只针对已确认命中的医疗队列移除该额外等待，不扩大到取消查询保护。

## 调用链及边界

```text
原生主循环：physics stopped → physics.updateUT → charsUpdateUT
  Iris SafeHook：原函数 → Idle(世界、physics、AI)
    原互斥内：Tick → 真实查询（原queue门保持）→ 去重并入队稳定身份
    原互斥外：Flush
      每笔：预算 → 世界存在/已初始化/非reset/非load → physics stopped → AI stopped
           → 短锁检查暂停、FIFO取出、epoch
           → 解析caster/victim稳定身份、原生敌我资格
           → getTotalAttackDamageFor、原倍率
           → 单次原生 _NV_hitByMeleeAttack → 原经验/结果
      下一笔重新检查上述状态
```

实现见 [IrisCombat.cpp:1302](E:/KenshiProject/2.Projects/IrisArsenal/IrisCombat.cpp:1302)。医疗不调用 `queuesAreClearMT()`；`gate.queuesClear` 留为-1，明确未读取，不能冒充已清空。新增逐笔 initialized/reset/load检查，用于原生回调重入后阻止下一笔沿用旧世界许可，退出保留未处理FIFO。已开始的原生受击不抢占、不重试。护甲、部位、倍率、敌我、昏迷处理、破防、经验、伤害结果和独立攻击段语义均未改。

碰撞 Contacts/TryCapsuleBatch 的queue门、PhysX模块、三远程地形射线与角色带半径碰撞、所有Hook/动画/资产原字节保持。INI预算仍 **2.5ms /32次**，40ms是等待观察目标，不是超时丢弃或增加单帧预算。

## 必要日志

沿用已有开关，无新增INI项：`EnableLogging=1`、`EnablePerformanceLogging=1`、`EnableCombatDetailLogging=1`、`EnableWindowAuditLogging=1`。项目两份INI原字节保持，当前这些开关已开启。关闭后新统计在已有入口短路，不增加引擎读取或后台日志线程。

- 启动：`medical_gate_ready contract=IRIS_MEDICAL_GATE_083 medical_requires_queues=0 query_queue_gate=retained ...`，带真实配置预算、逐笔状态复查和锁外原生调用标记。
- `audit_window_phase phase=medical` 增加 `medical_native_calls`、`medical_requests_inspected`、`medical_progress_windows_after_queue_pending_observed`；复用现有窗口/进程摘要，按原窗口生命周期清零窗口量并保留进程量。
- 最后一个字段统计：本轮此前 POST_TICK 确实观察到queue=false且本轮完成至少一次原生受击的窗口数。是窗口数，不是伤害次数。数据来自已持原锁的纯值数组，未追加PhysX getter或遍历后台容器。
- `ready_requires_queues=0` 明确医疗ready口径；其他观察阶段的ready仍采用原查询可用性口径。原字段保留；阶段诊断结构合同仍为082，实际医疗政策用083标记。
- `audit_window_trace` 和压力日志保留 `native_calls`、`inspected`、`remaining`、`gate_cause`、耗时和最老等待。`medical_requires_queues=0` 配合医疗queue=-1说明其不参与许可。真实 `physics_running`、`ai_running`、`paused`、`world_invalid` 仍可停止医疗；旧 `reason=world_missing` 兼容分类保留，细分由 `gate_cause=world_invalid` 表达。

入口见 [IrisCombat.cpp:399](E:/KenshiProject/2.Projects/IrisArsenal/IrisCombat.cpp:399)；计数见 [IrisDiagnostics.cpp:60](E:/KenshiProject/2.Projects/IrisArsenal/IrisDiagnostics.cpp:60)。阶段观察并非原子状态，progress关联不能冒称每笔受击瞬间queue仍然false。日志不是FPS/GPU测量。

## 实际执行验证

1. 1024组实际C++医疗门AST解释：覆盖世界/物理对象缺失、初始化、reset/load、物理/AI运行、queue真/假、暂停。医疗getter调用数为0；应允许的queue=false路径能通过。
2. 972组实际ready表达式、54组实际日志计数体AST执行，核对未知/未采样队列、0/1/32次进展及窗口计数单位；原20组关闭路径、40限频规格和10000三态编码保留通过。
3. 对原生回调后物理启动、AI启动、暂停、reset、load、未初始化、物理缺失做7种顺序状态回放，每种100个FIFO目标；102目标长调用/预算回放和9个实际epoch表达式通过。这里是带模拟引擎返回的规格回放，不是线程或游戏实测。
4. IrisCombat有98个函数正文token保持，只有Configure日志、快照输出、Flush许可块变化；将许可块复原后，整个医疗消费体逐token等同旧版。10个诊断时钟/开关/等待函数保持；8份Hook/接口/远程/真实物理文件字节保持。
5. 081的100300个可关对照条件、4007冲突索引操作、243解析场景、4097目标/32776检查规格保留通过；不是实际PhysX执行。10份C++/H树语法与3份Python AST通过，不是MSVC类型/链接校验。
6. 更新脚本隔离测试21项：20通过；1项因系统不允许创建测试符号链接跳过。全部写入本任务目录里的模拟mods，未调用真实部署。真实用户082 DLL被083合同门正确拒绝。
7. 检查6154个原有文件字节保持（STATE交付前截面），配置预算2.5ms/32保持，三份DLL哈希保持。完整结果：[validation083.json](D:/CodexWorkSpace/Sessions/20261002-235652-kenshi-crash-407794f2/Task-Iris-MedicalGate083-20261023-205804-0211f9/validation083.json)、[日志/边界结果](D:/CodexWorkSpace/Sessions/20261002-235652-kenshi-crash-407794f2/Task-Iris-MedicalGate083-20261023-205804-0211f9/logging-and-boundary.json)。

验证器初次运行两处问题仅涉及既有 `__declspec` 和构造初始化同名函数的定位，已修正验证器后重新运行全部专项通过；没有用失败运行冒充通过。未执行C++编译、PhysX、游戏线程/场景和FPS测试。其他插件任意重入、引擎内部未公开副作用仍需用户编译后的真实日志核查，不能承诺积压全部消失或特定FPS提升。

## 逐文件报告

- **IrisCombat.cpp**：消费者。Configure添加一次启动身份，Flush移除医疗queue门、逐笔重查世界有效性，快照输出声明无queue依赖。原因是已确认原生阶段语义与291次零进展。查询及实际伤害体保持。AST/98函数对照通过，未游戏验证。
- **IrisDiagnostics.cpp**：诊断。医疗ready独立于queue、增加3个进展累计字段，顺序观察关联明确命名，版本日志改0.4.34。原四重开关、限频和纯值锁内更新保持，未新增引擎getter。972/54/20组实际表达式或路径验证通过。
- **IrisArsenal.rc**：构建文件身份0.4.34，注释说明083和编译状态；未生成DLL。
- **tools/stage_package.py**：只识别用户产物。增加083合同门及真实新包字段；现有DLL正确拒绝。复制/整目录清理流程未变，未运行组包或部署。
- **tools/test_update_mod.py**：已有测试分类，补083缺失的预期拒绝，不生成假PE；隔离20过1权限跳过。
- **tools/test_medical_gate083.py**：新建专项，只解释实际源AST及规格回放，使用本机既有依赖；已运行通过，不编译。
- **package/IrisArsenal/IrisPackage.json**：仅ready=false及pending083，实际version仍保留0.4.33和旧构件哈希，不以源码冒充新DLL。用户编译后由既有Update组包重新生成ready=true。
- **STATE.md**：本次交付状态/实际旧DLL身份/验证及编译步骤置顶，旧历史保留。
- **docs/medical-gate083.md**：本说明；不进入游戏运行包。

各文件详细模板报告和每次修改后的编码/备份检查在 [本任务reports目录](D:/CodexWorkSpace/Sessions/20261002-235652-kenshi-crash-407794f2/Task-Iris-MedicalGate083-20261023-205804-0211f9/reports)。本任务源码/脚本/原状态已先双备份：

- `D:\CodexBackups\Task-Iris-MedicalGate083-20261023-205804-0211f9`
- `E:\AIWorkSpace\_backups\Task-Iris-MedicalGate083-20261023-205804-0211f9`

CPP均保留原UTF-8无BOM/CRLF；RC、Python、JSON、STATE保留原UTF-8无BOM/LF。新文档/测试UTF-8无BOM/LF。每次写入回读并检查中文、替换字符和明显乱码。追加修订的前版本另存各备份目录的具名修订子目录，未覆盖首份备份。

## 用户编译及后续核查

用户在 **IrisArsenal.sln / Release|x64 / v100** 编译；正常退出游戏后运行 **UpdateMod.cmd**，它会识别新083合同并完整复制。未编译就执行Update将明确拒绝旧082，这是防止旧DLL冒充修复，不是已部署成功。

新运行先确认日志 **0.4.34** 和 `medical_gate_ready ...083`。再看medical累计native_calls、剩余/最老等待、time/count/safety yields以及上述queue观察后有进展窗口数。实际queue条件不再出现在医疗拒绝原因中，但查询仍可能因queue暂不可用等待；原生单次长尾和原有预算也仍可能形成积压。不要把新旧不同负载日志直接换算成FPS变化。
