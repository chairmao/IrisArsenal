# 052：清理与可配置长期诊断

源码版本 **0.4.9 / IRIS_LONGTERM_AUDIT_052**，资源修订准备为 **052-CleanupAudit**。本轮未编译、未部署；当前游戏目录仍为 **0.4.8 / IRIS_SEAT_SURFACE_CANNON_050 / 051-SourceFlareMuzzle**。旧日志不能证明新诊断已生效。

## 清理依据与范围

- 删除 `Job.wall` 永远为 false 的字段及不可达分支；删去无消费者的 Blast 参数、重复的旧 QueryMetrics/QuerySummary/queryWork 统计，以及新增模块中未使用的接口。
- 运行包移除 1 个没有消费者的 heavy 网格和 6 张无材质引用的贴图，精确清单及原始 SHA256 在 [retired-runtime-052.json](retired-runtime-052.json)。现有终结事件 kind4 是球心原地爆炸，历史名称 heavy_shell 不代表仍需飞行弹体模型。
- 同步清理效果清单、独占材质、来源元数据和生成器；有效效果由 21 项变为 20 项。剩余实际模型、骨架、纹理像素、Shader、FCS 的字节保持本轮前值；材质只移除已退役且无消费者的一项定义。真实 NIF 材质读取仅用于来源校验，没有重生成模型或纹理。
- 保留有实际消费者的验证数据、显式 DrillProofOnly 诊断动作、导入链所需的第三方读取模块及历史审计文件。文件名旧或暂未在战斗中使用，不足以认定可删除。
- 更新脚本只接受精确退役白名单，删除也参与原有备份/写入/回滚事务；不清理未知文件、日志、存档或个人配置。生成器不会重新导出旧 heavy，完整重建末尾会再次核对引用并精确清理。
- 纠正十招数量、入站保护与出站防御策略、可选诊断分支、加载/同包版本等过期注释。Vulcan* 是历史内部标识，旁注说明了它目前承载所选近战的防御桥接，未为清理改名。

## 启动配置

以下项位于游戏 mod 的 `IrisArsenal.ini` 中的 `[IrisArsenal]`，本轮已加入 distribution 与项目 package 默认配置；更新会保留用户已有值，缺失项补默认。修改后重启游戏生效。

```ini
[IrisArsenal]
EnableLogging=1
EnablePerformanceLogging=1
EnableResourceLogging=1
LogSummarySeconds=60
LogFlushSeconds=2
SlowFrameThresholdMs=8
```

| 配置 | 含义与边界 |
|---|---|
| EnableLogging | 总开关，0 关闭该模块文件输出及新增诊断采样；仍允许 RE_Kenshi 错误出口报告初始化/写盘故障 |
| EnablePerformanceLogging | 0 不采集新增逐帧、物理查询、医疗队列统计；已有动作/错误文本日志由总开关控制 |
| EnableResourceLogging | 独立控制资源读取/初始化/对象创建/材质加载/预热阶段日志和耗时 |
| LogSummarySeconds | 墙钟秒，允许 1～3600，默认60；仅游戏回调到来时检查，暂停期间有回调仍可汇总 |
| LogFlushSeconds | 写盘间隔秒，允许0.1～60，默认2；16KiB缓冲满时提前写，重要故障与资源begin立即写 |
| SlowFrameThresholdMs | 插件安全更新的耗时阈值毫秒，允许0.1～1000，默认8；慢样本至多每秒1条 |

没有日志总行数上限，不截断或自动删除日志。没有后台线程、轮询、计划任务或自动附加调试器。普通日志缓冲写盘，读档/清理/关闭等节点强制提交。磁盘故障最多保留64KiB待写内容，防止诊断自身内存失控，丢弃字节用 dropped_log_bytes 报告；因此不能承诺写盘失败或进程突然结束时零丢失。

## 调用链与统计语义

1. `startPlugin → IrisDiagnostics::Initialize`：读取开关，创建本次运行身份；原生入口仍用 KenshiLib 成员地址解析。18个既有 hook 均保留，没有增加 hook 或物理实体。
2. `SafeHook → BeginFrame → Tick/Combat::Tick → Combat::Flush → Record/EndFrame`：原有安全更新与医疗批次之外只加观测，不改选择、距离、倍率、速度、enemy过滤或原生伤害入口。
3. 查询包装记录球/扫掠/胶囊/圆柱耗时、调用次数、缓存命中、繁忙/预算等待、重试、原始shape/有效contact/初始重叠恢复及溢出。等待不等于查询失败。
4. 医疗记录事件、入队、原生调用结果与出队等待。damage_applied 是原生返回值的归类，不能单独证明实际血量差；伤害仍走原先的近战受击桥接，没有迁移成原生弩弹结算。
5. `Scope` 在配置/资源表读取、资源组初始化、对象创建、材质load、预热等真实调用周围输出 resource_begin/end；记录真实资源名，C++异常展开标 failed=1。begin 未闭合只能证明该阶段证据不完整，不能单独断言游戏崩溃。
6. 周期 `Summary` 同id输出 window 和 process 两套计数/耗时/资源数量，再写 audit_summary_end。读档不重置进程累计；清理摘要在清理完成后输出，当前数量与窗口峰值各有字段。摘要先快照再开启下个窗口，其自身写盘费用计入下个窗口。

每份日志头包含：DLL版本、代码合同、安装清单中的资源修订、实际游戏EXE路径和文件版本、PID、进程创建FILETIME、配置及64位计数标记；文件名含时间/毫秒/PID。不同运行不得合并基线。

资源数量包含角色/活跃/预留、投射物、后效、闲置复用对象、已附着对象、查询任务、待结算医疗、已预热资源和延迟回收枪对象，另有窗口与进程峰值。fresh_visuals/pool_reuses/visual_dispose_attempts 观察创建、复用与销毁尝试；销毁尝试不是GPU释放成功证明，异常仍需结合既有清理错误日志。

### 耗时阅读注意

- QPC记录的是 **CPU侧调用经过时间**，包括调用中的等待，未测GPU执行、显存字节、游戏FPS或线程纯CPU占用；不能用 audit_slow_safe_frame 直接换算整机FPS。
- 除 damage_queue_age 外，直方图样本为每个安全帧该通道的合计，包含零工作和暂停帧；启动加载发生在安全帧外时仍有 calls/总耗时/max_call_ms，不能把没有直方图样本解读成0耗时。
- damage_queue_age 是每条医疗请求的墙钟等待，字段为 wait_ms_total/max_wait_ms、sample_basis=request_wall_latency、CPU_side=0，可能包含暂停/预算等待，不可混加为执行开销。
- p50/p95/p99 是16桶的毫秒**上界**，不是精确分位；最后无界桶返回-1，histogram_samples=0时的0也不能当作真实零。
- safe_tick/combat_tick/查询/资源/医疗存在嵌套，耗时不能直接相加。资源阶段独立开关，perf关闭时资源日志仍可开启。
- 每窗口与进程累计分别输出；不能把多条process累计相加。长期趋势需要比较相邻累计差、窗口值和相同运行身份。

## 手动分析

日志目录：`D:\steam\steamapps\common\Kenshi\mods\IrisArsenal\logs`。

双击项目根目录 **AnalyzeLogs.cmd**，或把某个日志路径作为参数传给它；只读逐行分析原日志，无行数截断、无轮询、无日志修改。输出JSON包含身份、最新完整摘要、最近8个资源数量快照、未闭合/失败的资源阶段及已匹配的禁用/清理错误。

分析器要求两套scope及摘要footer齐全，半份摘要不参与结果；未匹配的普通警告仍需查原始日志。这是手动审计工具，不是自动故障定论或泄漏检测器。已对旧0.4.8日志实跑，正确显示不存在052身份和摘要，没有冒称新日志已经工作。

## 验证与交付

- 22组现有专项回归与052静态/独立统计模型通过，10份C++/头文件语法树无错误，项目Python均通过AST解析。
- 原更新链13项隔离测试、新增9项日志解析/精确退役/回滚/个人开关保持测试通过；不调用编译器，不生成运行二进制。
- 完整重建的元数据来源以实际源NIF只读核对；剩余运行资产与当前部署清单逐文件对比；游戏目录文件未改。
- 跳过会重生成FCS的test_icon_rebuild048；FCS与图标现存字节直接比对保持。历史回归只对052明确授权差异采用精确摘要链，其余源行为/材质/Shader校验保留。
- **未执行MSVC编译、C++运行、实际游戏、GPU、FPS或长时间实机验证**。语法/模型不能证明这些行为已通过。

下一步由用户编译 `IrisArsenal.sln → Release|x64 / v100`，正常退出游戏后执行 **UpdateMod.cmd**。脚本会拒绝旧DLL，重新恢复/校验资源并同包同步。验证新日志头显示 `IRIS_LONGTERM_AUDIT_052` 后，才能用它判断实际运行。

逐文件报告及原始双备份见 [cleanup-audit-052-files.json](cleanup-audit-052-files.json)。既有文件保留UTF-8/BOM/换行，新增文本UTF-8；没有改写历史审计结论。
