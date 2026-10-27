# 2026-10-27 3.0最终校验补充：修正退役095测试断言

Owner: Codex

用户新104已通过生产组包，但单项旧测试仍强制095证明合同，误报失败。只删除该退役测试条件，保留validate_dll真实调用及其他检查；当前新DLL完整隔离更新测试21项20通过、1符号链接权限跳过。未改CPP/H、DLL或生产组包器，不需重新编译。总结补充第61项纠错。初次密封副本完整保留为同名-initial；原主目录将封存含测试修正和说明的最终3.0，均有独立哈希与只读标记。

---

# 2026-10-27 正式版3.0最终身份：用户已编译104并完成项目组包

Owner: Codex

用户于封存过程中告知已编译。实际bin与package DLL为0.4.54/IRIS_HOLDER_TIMELINE_104，887808字节，SHA256 1869b6fdbb1f02cc21742cc496f42d2b1585484e149d32b5d293880be42afc80；PDB GUID/age匹配。原update_mod.py --package-only已成功校验组包，不重建素材、不写游戏目录。项目包ready=true；新104仍无游戏日志/实测。

游戏部署仍0.4.53/103，SHA256 29bd1232d73d626660a4f256c4f4e7e6e7c8a904e4ace9671d560ab1aff8c96a，另存runtime-deployed；runtime以用户104完整包为主。3.0只是归档名，内部版本不改。此前本次初核“104未编译/包pending”为用户编译前事实，以下保留历史，不代表最终状态。最终以docs/formal-release-3.0.md、docs/formal3/README.md及归档IDENTITY/SEALED为准。

---

# 2026-10-27 正式版3.0归档与全面模板总结

Owner: Codex

用户要求封存当前版本为正式版3.0并全面总结，额外写入项目。封存名称不改变内部身份：源码0.4.54/104（片尾审计/正式人数门已去除）尚未编译；bin/package/game实际DLL仍0.4.53/103，SHA256 29bd1232d73d626660a4f256c4f4e7e6e7c8a904e4ace9671d560ab1aff8c96a。runtime取已部署103原样，project保留当前104 pending，两套明确区分，不把源码当运行成果。

项目总结入口docs/formal3/README.md，覆盖架构/原生链、18行为Hook及可选深层探针完整源码、58事件与实际FCS/INI、源特效/骨架、空间查询/时钟/生命周期、性能正反例、60项问题与可复用新项目JSON模板；docs/formal-release-3.0.md及根README已加入口。

主归档D:\CodexBackups\IrisArsenal-Formal3.0-20261027-185310-4e0df0；第二盘E:\AIWorkSpace\_backups\IrisArsenal-Formal3.0-20261027-185310-4e0df0，密封结果以SEALED/任务validation为准。历史1.0/2.0不变。未改CPP/H、FCS/配置/素材/更新器；未编译、部署、改存档/加载顺序或工坊。新增文档UTF-8/LF，既有README/STATE写前双备份并保持编码/换行。任务D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-Iris-Formal3-20261027-185310-4e0df0。

---

# 2026-10-27 104：正式持有者无人数上限及片尾事件审计（源码0.4.54待用户编译）

Owner: Codex

用户限定本轮两项：片尾疑似漏发只加诊断；取消正式持有者8人限制。Observe/Discover/Prepare删除8人及retired+slots16个门槛，map/set身份去重和旧Gun延迟回收保持。未改诊断原型人数、查询64、医疗20ms/128、原生资格、伤害、FCS或特效。

AuditActionEnd在End清状态前观察已有快照；记录剩余、到期未消费、kind5标记、横扫采样间隙、原生状态/时间及旧招/新招身份。未知时间不推断漏发，未补发或修改原结束条件。独立EnableActionEndLogging需总日志/性能/明细同时开启；每类前32条及每256次累计，关闭不读快照/遍历/计时/加锁。

运行bin/package/game DLL仍0.4.53/IRIS_INI_DIRECT_103，SHA256 29bd1232d73d626660a4f256c4f4e7e6e7c8a904e4ace9671d560ab1aff8c96a；未编译、未部署。新源码0.4.54/IRIS_HOLDER_TIMELINE_104；包ready=false，原UpdateMod.cmd拒绝旧DLL。需用户编译IrisArsenal.sln / Release|x64 / v100再更新。

任务、逐文件报告、验证与双备份目录名：Task-Iris-EndAudit-Unlimited104-20261027-183516-83ae8c。静态/AST验证结果见任务validation.json，不冒充游戏实测。

---

# 2026-10-27 定时任务：服务时机审查与保守清理（运行仍0.4.53／103）

Owner: Codex

实际bin/package/game三份DLL已由用户编译部署为0.4.53／IRIS_INI_DIRECT_103，SHA256均为29bd1232d73d626660a4f256c4f4e7e6e7c8a904e4ace9671d560ab1aff8c96a。下方103的“待用户编译/仍运行102”为历史。本轮未编译、未部署，不声称有104新运行产物。

按01:50任务先审查两条优化方向。纯近战有效窗口3/4复核：53个非空医疗窗口均有进展，没有积压但缺失Flush的已观察回调；219次查询拒绝为真实创建/销毁消息，查询预算等待0。原生Physics.updateUT先移交消息再进入charsUpdateUT，线程未启动不等于消息已处理。有查询作业的前后UT配对仅3条，queue均false，UT均值0.0991ms，不能据此前移或新增回调来承诺缩短98ms服务间隔。保留20ms/128、所有安全门、FIFO和锁外受击，不恢复101/carry，不引入全局事件串行。

其他战斗开销候选未同时取得足够收益和等价性证据：原生hasAnimation检查AnimationData/骨架/线程状态，getAnimationState检查实体状态集合，不能直接去掉前者；跨帧缓存缺少完整失效证明。低占比清理/迁移不足以支持新的运行维护。没有把原生截肢、物理查询、首次资源创建或可关闭日志IO重新包装为本轮优化；没有证明引擎绝无进一步空间。

因此执行用户允许的fallback：删除IrisCombat.cpp未调用Loaded包装和重复float.h，修正旧预算/轮转/历史身份注释；091历史测试仅在内存回放里恢复旧定义；IrisArsenal.rc只去过时编译状态注释，VERSIONINFO不变。资源完整引用图未找到可删文件，全部保留；虚接口/回调/诊断原型与历史证明不误删。

实际验证：整个战斗翻译单元除上述无调用定义及重复include外所有非注释token相同；128份历史规范化函数对照、80组真实AnimationLength AST边界、18个CPP/头语法单位及Python AST、资源图/有效对象和137份游戏目录文件一致；三处DLL和所有配置均未改。静态证据不冒称游戏/FPS测试。既有诊断继续覆盖查询门、医疗等待、服务间隔及战斗阶段，无新增常驻开销。

本轮是清理，不宣称性能提升。后续若将清理源码打包，需用户在IrisArsenal.sln / Release|x64 / v100重新编译，再退出游戏执行原UpdateMod.cmd；现有源码mtime门保持，不伪造时间绕过旧DLL检查。游戏当前仍使用原103。

依据、非编译验证、逐文件报告及双备份目录名：Task-Iris-ServiceCombat104-20261027-015240-f5c72d
任务产物：D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-Iris-ServiceCombat104-20261027-015240-f5c72d

---

# 2026-10-26 103：INI数值直接读取，普通预算20ms（源码0.4.53待用户编译）

Owner: Codex

用户追加明确要求：不能在代码设置INI调参数值上下限。103最终实现统一IrisIni::Number，移除战斗倍率/权重/距离上限、医疗预算/次数读取范围、日志周期/阈值/采样、远程动作间隔和诊断原型人数的业务数值限制；移除追赶计划对INI的2倍/10ms/256次二次钳制。缺项默认值保持；仅保留数值格式/有限值、布尔/unsigned/float/DWORD实际类型转换、距离-1继承及Min<=Max结构语义。采样0禁抽样不钳为1，也不取模0。当前预算20、次数128、追赶关闭，其余配置值不变。

调用链：四处启动配置入口 -> native/IniValues.h解析 -> 各原字段 -> 原消费者。主线程安全窗口、FIFO、逐笔世界/物理/AI/暂停/身份/资格/原生受击、原循环256扫描不改；不增加线程/Hook/锁。日志周期换算为整数毫秒存入DWORD，只因实际字段类型拒绝无法表示的值，不做业务钳制。

实际bin/package/game DLL仍用户0.4.52/102，SHA256 d6ac6c70e9b89769f2edf633b0657083637e68720c86d092e81ed7e68d1659ec；游戏目录保持原10ms完整部署，不把20写给不支持的旧DLL。最终103合同为IRIS_INI_DIRECT_103，源码0.4.53，package ready=false/pending0.4.53；之前本轮“上限20”准备稿已被追加要求替代，不是当前实现。

用户编译IrisArsenal.sln / Release|x64 / v100，然后正常退出游戏运行原UpdateMod.cmd，20ms及INI直读一起生效。未代编译、未部署新DLL、未启动/终止游戏。备份/逐文件报告/验证：D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-Iris-DamageBudget20ms103-20261026-224258-041874。

---

# 2026-10-26 102：独立弹体速度与极致驱动分段时钟（源码0.4.52待用户编译）

Owner: Codex

用户要求：所有已发Shot独立按游戏秒推进，不再乘动作a.rate；动作/发射节拍继续用原生攻速。火神炮1500、脉冲之焰1000游戏单位/游戏秒，发射预判使用同一速度；两招FCS attack distance/最大飞行距离5000，极致驱动长度10000及角色R9保持。原地形有限射线/角色带半径碰撞、逐事件身份、伤害/安全门未改。

极致驱动源首发3.166539907动作秒，分段映射F(t)=t/2（首发前）、t-1.583269954（首发后）；新首发1.583269954，总长3.916730046。只修改既有男女骨架的时间字段，所有旋转/位移/绑定字节保持；FCS整招anim speed mult仍1，动作/四段伤害/点火节点共映射。ShowParts通过逆映射读取原ion源曲线，新0～1.583秒准星/蓝火特效同步2倍，首发后1倍；不改原特效资源。四段伤害仍间隔0.25动作秒，实际游戏秒仍除角色动作速率。

三份INI已改DamageFlushBudgetMs=10，其余128笔、追赶关闭、FIFO和诊断设置保持；游戏仅INI及对应清单哈希更新。新源码/资产在项目，未编译未部署新DLL/动画/FCS；当前三处DLL仍用户0.4.50/100，SHA256 f53d589fa114476ebab718202f893b8a3b3f32d91e3235eab25928786462c718。package ready=false/pending0.4.52/IRIS_PROJECTILE_TIMELINE_102；原UpdateMod.cmd继续只校验/完整复制，拒绝把旧100配给新时序。

本轮遵守不代编译；用户编译IrisArsenal.sln / Release|x64 / v100后正常退出游戏，执行原UpdateMod.cmd。双备份、逐文件报告与离线验证：D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-Iris-ProjectileDrive102-20261026-215112-232447。

---

# 2026-10-26 100配置调整：统一5ms/128，关闭额外追赶

Owner: Codex

用户授权将distribution、package和游戏三份INI统一为DamageFlushBudgetMs=5、DamageFlushMaxHits=128、EnableDamageBacklogCatchup=0；DamageQueueTargetMs=40及日志开启保持。099代码与备用5ms/64参数仍保留但当前禁用，不新增101尾段/carry，不调整C++、物理、FCS或资源。

DLL保持本轮开始时的现有0.4.50／IRIS_QUERY_GATE_100，三处SHA256均为f53d589fa114476ebab718202f893b8a3b3f32d91e3235eab25928786462c718（已不同于回退时历史b6bdbbfc产物；本轮未修改DLL）。package与游戏清单只更新INI的SHA256。配置在下一次启动读取，无需重新编译；本次未启动游戏，不把5ms当硬帧上限或把成本模型当游戏实测收益。

选择依据：100的10次积压退出均先到数量上限，099为18次次数/3次时间退出；近几轮大批次摊销成本约0.05～0.10ms/次。5ms已是原追赶计划使用的预算；128作为兜底，统一预算避免动态降额及新carry维护。仍需用户下一轮同压力日志验证队列长尾与单窗口峰值的权衡，不能预先承诺FPS提高。

本轮双备份、逐文件报告及验证：D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-Iris-DamageBudget5ms128-20261026-204231-648267-01b010。下方回退100时的旧2.5ms/32、超龄5ms/64描述是历史，不代表当前生效配置。

---

# 2026-10-26 用户要求回退100（源码、构件和游戏目录已恢复）

Owner: Codex

已按101开始前快照逐字节恢复8份100源码/配置/组包文件，删除101有限尾段、carry状态、四项配置及专用诊断；恢复既有099的2.5ms/32普通计划与超龄5ms/64追赶。100精细查询门及“本轮几乎无收益”的中文注释按用户原要求保留；其余近战、远程、敌我、FCS、动作和资源不改。

100历史用户DLL SHA256 b6bdbbfc86b2199ddf85e464762ad33458e52e66a5d73e14bbff76242302d29a，已经恢复bin/Release和package。未代编译或重生成二进制。用户确认正常退出，且核验Kenshi_x64进程已结束后，已恢复游戏DLL、INI和清单。下一次启动加载100；本轮没有启动游戏或冒称游戏内已实测。当前包ready=true/0.4.50/IRIS_QUERY_GATE_100，134份其余资源与100运行快照一致。

原stage_package的源码mtime新旧检查保持，不伪造文件时间或绕过校验；未来源码构建及更新若提示DLL早于源码，用户需编译IrisArsenal.sln / Release|x64 / v100。本次可使用已保存的真实100DLL回退，无需代编译。101新DLL及改动前文件已双备份，原分析记录保留。

回退证据、保留修改汇总、逐文件报告与验证：D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-Iris-Rollback100-20261026-193952-733708-4406e3。以下101待编译及历史状态均保留为审计，不代表当前工程状态。

---

# 2026-10-26 101：原安全回调内的有限伤害尾段（源码0.4.51待用户编译）

Owner: Codex

已核对实际bin/package/game仍为用户0.4.50 / IRIS_QUERY_GATE_100，SHA256 b6bdbbfc86b2199ddf85e464762ad33458e52e66a5d73e14bbff76242302d29a。本轮不改物理查询/动作/特效/FCS，不新增服务点、线程或全局锁，不编译不部署。

依据100最新日志：10次留积压退出均为32/64次数门，未耗尽软预算；推进间隔10样本均值92.01644ms。用户已明确这是当前帧多做结算换排队延迟，不是CPU空转回收。101保留原2.5/5ms总软预算，在原次数出口且还有既有排队工作时一次最多1ms/额外32次（不超过原计划次数及总256，扫描256保持），不重置开始时钟。原生单请求仍不可抢占，不能保证帧硬耗时。

调用：原charsUpdateUT -> 原Idle/Tick/锁外Flush -> 原099计划/逐笔安全/资格/FIFO/医疗/XP -> TryCountTail一次纯值计划/原短锁 -> 同一原循环继续。补处理导致队列降至<=32时，不能反而失去原追赶资格：carry只覆盖入场时已有FIFO请求数，每次原pop递减，追加请求不延长；仍受原年龄门，Clear清零，尾段入场和原pop短锁内核对epoch，禁止读档重入后沿用旧尾段。没有跨帧角色/PhysX指针。

新增EnableDamageCountTail=1、DamageCountTailBudgetMs=1、DamageCountTailMaxHits=32；功能0恢复100调度。EnableDamageCountTailLogging=1受父日志/性能/明细门控制；末尾追加八计数及完整damage_flush子集计时；有界明细记录预算/次数、carry和退出原因。旧追赶明细区分计划与实际，100“几乎无收益但保留”的代码/INI备注保持。

验证：732实际纯策略AST、84映射、45普通小队列及40关闭功能同调用/QPC/顺序、40高压原FIFO前缀、7尾段重入停止、扫描256/失效/时钟/7ms慢单次、实际多窗口/混合成本反例与追加不延长carry、原逐笔消费体token保护、16诊断门与枚举索引、配置兼容/旧100DLL拒绝通过。更新隔离复制20项执行，19通过/1符号链接权限跳过；未修改真实游戏。早期解释器误把--当++，已只修正本任务验证器并重跑，最终依据validation101-final.json及multi-window-validation101.json，不采用早期验证结果作为carry证明。

条件模型及实际AST替身输入显示可缩短部分等待；197请求示例4轮降3轮。这是给定非负成本/资格/引擎间隔输入的离线证据，不是真实医疗/PhysX/并发/FPS测试，不能承诺同幅度游戏提升。工程说明docs/damage-count-tail101.md；完整依据、双备份、逐文件报告及验证在本会话Task-Iris-DamageCountTail101-20261026-181310-788984。

包保留真实0.4.50与旧DLL身份，ready=false/pending_version=0.4.51/pending_contract=IRIS_DAMAGE_COUNT_TAIL_101。用户编译IrisArsenal.sln Release|x64/v100，再正常退出游戏运行原UpdateMod.cmd；未编译时明确拒绝旧100，不伪造新运行产物。

---

# 2026-10-26 100实测更新与下一项分组优化预审

Owner: Codex

真实bin/package/game均已由用户编译部署为0.4.50 / IRIS_QUERY_GATE_100，SHA256 b6bdbbfc86b2199ddf85e464762ad33458e52e66a5d73e14bbff76242302d29a。下方“100待编译/运行099”为历史，不代表当前事实。

100本轮1876次复核/0额外放行；1593次销毁、283次创建主原因。几乎无实际收益，检查本体累计0.417ms，未见明显性能损失（不是严格零开销）。用户要求不回退：功能代码与两项INI=1均保留，并在代码附近及两份项目INI注明。游戏目录本轮未写入。

下一项“扩大远程同窗口分组”先做收益预筛，未接入：按100实际发射参数/终止信息构造8/12/20Hz路径样本，跨旧8项边界扩大至16/24/32组，仅少约0.19%～0.31%探测；同窗口严格包含的空区共享机会0.09%～0.21%。这些是插值候选样本，不是实际查询输入或PhysX重放，只能说明目前缺乏足够收益依据，不能证明算法普遍无效。按用户“先有明确改善依据且流程不变”的前提，本轮不硬接实验运行路径，不发布101或冒称性能优化完成。

本轮只改100测试注释、INI注释/对应哈希和本状态；后续整体token/配置/运行文件验证记录于Task-Iris-WindowEmpty101-20261026-014851-823984。未编译/未部署；既有stage_package按源码mtime检查，后续打包会要求用户重新编译100工程（Release|x64/v100），未绕过检查或回填时间戳。

---

# 2026-10-26 100：查询精细安全门（源码0.4.50待用户编译）

Owner: Codex

真实bin/package/game为用户0.4.49 / IRIS_DAMAGE_CATCHUP_099，SHA256 e1fbc4762673a11d1ae04eccb90ec69c1adaa012d690ef1a4441f6bd52f0d8ea；下方099待编译为历史。099已实测伤害平均等待39.87ms，碰撞忙1138次/最长任务1370.92ms。本次只细化查询准入，不改医疗、物理形状、FCS或资源。

原门true保持旧路；false时统一QueryAvailable：既有安全主线程阶段内再查world/physics/AI/暂停→八类消息主/后台+门任务实际为空且元数据有效→同SDK公开isWritable→再查上下文/实际空消息→一次同步查询。真实创建/销毁/地形/分组等均不放行，未知保留等待；不flush、不改clear标志、不增线程/Hook/全局锁，不跨帧保存许可或SDK指针。Contacts/TryCapsuleBatch/RunRangedBatch统一接入，新许可不使用球缓存。

EnableQueryGateRefinement=1；0恢复原门。EnableQueryGateLogging=1仍受总日志/性能/明细门控制，关闭无新QPC/计数锁/IO。新增query_gate_refine为准入子计时，不能加到物理或父总量；主原因独占/消息位可重叠，三入口旧拒绝分别计数。普通通过路径不做新检查。

源码0.4.50/IRIS_QUERY_GATE_100，未编译/未部署；用户编译IrisArsenal.sln Release|x64/v100后运行原UpdateMod.cmd。运行中纯快照命中比例与实际延迟/FPS需新DLL日志；不能预先承诺消除1138次拒绝或FPS提升。证据/双备份/逐文件报告见本会话Task-Iris-QueryGate100-20261026-003643-197110。

---

# 2026-10-25 099：超龄医疗积压有界追赶（源码0.4.49待用户编译）

Owner: Codex

当前真实bin/package/game已为用户0.4.48 / IRIS_DRILL_SPHERE_098，SHA256 18820d56ced2c2b9a8ab4138e1a3c9ef8fd1020bd57b0d43c63fd9ef3499a3ba。下方098待编译为历史状态。此次只优化原安全机会内的医疗服务，不改物理/倍率/FCS/资源/特效。

依据：本机原生主循环只在physics停止分支调用charsUpdateUT，随后才启动下一物理阶段。098的279条连续积压7次服务，机会间隔均值126.24ms；不能把其间渲染回调擅自当安全窗口。固定FIFO成本模型在12组无效费用/顺序条件下等待缩短约42%，它不是游戏实测，也不是对任意输入的时延保证。

实现：Configure -> DamageQueueSnapshot原短锁内取老FIFO头时间 -> IrisMedical::SelectService纯值计划 -> 原Flush循环逐笔世界/physics/AI/暂停/身份/资格复查 -> 原生受击/经验。普通/新鲜或<=32队列仍2.5ms/32；仅队列>普通次数且队首等待>=原40ms目标，临时允许请求5ms/64，实际不超过普通额度2倍和10ms/256次/256扫描边界。单次受击不可抢占。没有新安全点/线程/Hook/锁、额外物理查询或跨帧引擎指针；轻负载无新QPC/队列扫描。

INI新增EnableDamageBacklogCatchup（功能，0回旧路）、DamageCatchupBudgetMs=5、DamageCatchupMaxHits=64；EnableDamageCatchupLogging=1仅新增观察，仍需日志/性能/明细父门。摘要damage_catchup_flush是damage_flush子集不可加总，计实际追赶窗口/调用/检查/超过原次数；有界damage_service_plan首8条后每10秒最多1条，既有pressure显示实际与普通额度/最老年龄。

本轮未编译/部署，真实DLL仍098；工作包ready=false/pending0.4.49。用户编译IrisArsenal.sln Release|x64/v100，再运行原UpdateMod.cmd。实际延迟/FPS及提前结算引起资格变化后的费用仍待新DLL实测，不冒称已改善运行性能。产物/证明/验证/逐文件双备份见本会话Task-20261025-213139-389820-Iris-MedicalCatchup099。

---

# 2026-10-25 用户授权098：钻天破前11段随动紧球（源码0.4.48待用户编译）

Owner: Codex

当前基线已核实：用户已编译/部署0.4.47 / IRIS_NATIVE_SECTOR_097，DLL SHA256 eb264cb1de546187e767f730001b3bdab599c8eae7314f018e4b151c4eeb162e，136份游戏清单匹配；下方097“仍为095”的段落是历史，不能代替当前事实。

本轮只将钻天破前11个kind3伤害段从每段8胶囊改成每段1个球；保留11个事件时点/独立cast-event身份、原倍率/原生资格/去重/安全窗口/伤害FIFO。钻头与外环实际19层网格248576顶点，全Z旋转紧球局部中心Z=0.210085988、R=32.9765282；二约束下界32.9765233438，取float向外余量<0.000005。不是角色前进轨迹外接球，也不是AABB对角线；全旋转包络含外环四边形，实际DDS末级mip alpha19>阈值8，不能假定远景角点永远透明。

球心每段取对应姿态；同帧跨段在上帧/当前样本间插值，修正浮动原点差；仅已知两姿态间的估计，不是历史物理世界回放或连续扫掠。非均匀缩放沿用Visual::Draw分解并取最大轴伸缩保证包含；正常统一缩放是紧球，运行时只留有限float余量，不按位移扩大。无新增线程/Hook/锁/SDK裸指针。

实际调用：Emit kind3 -> DrillSphereFrame -> 单球Job -> ResolveJobs -> Contacts(drillSphere) -> OverlapSphere(boundsOnly=true) -> NxScene::overlapSphereShapes(false) -> 既有稳定身份去重/Collect/医疗队列。额外boundsOnly默认false，不改变其余球原INI精度；未修改钻天破终结爆炸、其他九招、FCS、源动画、特效/材质/贴图。旧drill.csv八行只保留格式校验，不再留无用胶囊数组。

诊断：新增drill_sphere_query（sphere子计时，禁止重复加总）、drill_sphere_requests/raw/contacts/cache；首8次+10秒间隔位置/半径/插值日志及异常按段跳过日志。沿用EnableLogging、EnablePerformanceLogging、EnableCombatDetailLogging；关闭时不新增QPC。日志身份修正0.4.48。完整更新脚本复制行为不改，仅要求098新DLL与实际几何对应；旧097明确拒绝。

验证：160组实际C++ AST＋Ogre纯值替身，共39772160顶点包含检查；实际Emit kind3 AST的11个独立移动球、跨事件/浮动原点/非法数据、DDS真实mip、默认精度等价、其他PhysX及医疗/远程/扇形函数token保护、诊断表/非编译语法、旧DLL拒绝和游戏目录哈希全部通过；已查看CPU几何投影。不是MSVC编译、真实PhysX、游戏GPU或FPS测试。

本轮未代编译未部署。源码版本0.4.48 / IRIS_DRILL_SPHERE_098；bin/package/game实际DLL仍为用户0.4.47/097，包ready=false/pending0.4.48。用户下一步编译IrisArsenal.sln Release|x64/v100，然后运行原UpdateMod.cmd。

产物：D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-20261025-200716-308838-Iris-DrillSphere098；说明与验证098.md、validation098-final-r2.json、drill-sphere098-envelope.png、per-file-reports。双备份：D:\CodexBackups\20261025-200716-308838-Iris-DrillSphere098；E:\AIWorkSpace\_backups\20261025-200716-308838-Iris-DrillSphere098。修改前逐文件备份，原UTF-8/BOM/换行/中文保持。

---

# 2026-10-25 用户确认097：原生胶囊与动画增量厚扇形（源码0.4.47待编译）

Owner: Codex

本轮新用户授权任务：原生cullShapes直接裁剪角色AABB，接受额外命中，原完整身份/逐刀去重。每片最多90度，增量区间仅共边，角度随实际动画时钟和同包武器轨道推进；没有固定每帧10度或累计重查旧扇形。静态胶囊及旧手写扩盒路径改为原生overlapCapsuleShapes(false)，零长度为sphere(false)，成功前缀独立消费；旧095扩盒/内核审计/影子路径已退役。

离线真实动画发现快扫首尾最短Slerp会漏掉整圈，已使用新增assets/blade_poses097.csv修正：只读现有男女身体Prop2轨道，SourcePose同换基，实际附件锚定，修正浮动原点，按已过源键重建。原身体动画/特效/FCS/伤害/三远程地形射线与球扫掠/医疗预算保持。无新线程/Hook/锁或跨帧SDK裸指针。

实际bin/package/game仍为用户0.4.46/095 DLL，SHA256 893e90059a05105cb6c432ef1accfab65fa49b58cf3cb3a0305b073ace3ac307。本轮未编译未部署；package ready=false/pending0.4.47/IRIS_NATIVE_SECTOR_097。用户须编译IrisArsenal.sln Release|x64/v100后运行原UpdateMod.cmd，完整复制新轨道。不是恢复已暂停096/旧近似证明目标，不宣称原生接口必快。

验证：2500组/30000点实际平面AST，20组真实男女动画变速回放、42批失败前缀、24组锚点/原点表达式、1100身份三攻击段规格、原医疗FIFO/暂停/代次及6项更新沙盒均通过；最大单片89.973236275度。非编译/真实SDK/游戏/FPS测试。可关闭sector路径、实际结果/等待、异常及耗时/工作量日志已加。

产物：D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-Iris-NativeSector097-20261025-162002-283619；实施说明与验证097.md及per-file-reports。双备份D:/CodexBackups/20261025-NativeSector097、E:/AIWorkSpace/_backups/20261025-NativeSector097。原UTF-8/BOM/各自换行保持，游戏目录原有文件逐字节不变。

---

# 2026-10-25 按用户要求完整撤销096，恢复095

Owner: Codex

用户明确要求回退此次修改。已按任务开始前baseline096快照逐字节恢复095源码、配置与更新组包脚本，移除本轮新增BoundedCylinder/BoundedSphere头文件及对应接入；源码保留原UTF-8、原换行和中文。任务分析和原日志留在会话目录，不进入运行包。

原0.4.46 / IRIS_CONSERVATIVE_PROOF_095已编译DLL来自13:49更新前完整备份，SHA256 893e90059a05105cb6c432ef1accfab65fa49b58cf3cb3a0305b073ace3ac307。已恢复bin/Release、package/IrisArsenal和游戏mods/IrisArsenal三处DLL及095运行INI/清单。没有代编译、启动或终止游戏、改FCS/特效/伤害参数/存档。清理096项目编译中间结果并双备份，防止以后误链接096对象；需要未来编译时使用Release|x64/v100，目前回退无需重编。

备份：D:\CodexBackups\20261025-141443-982412-Iris096-Rollback；E:\AIWorkSpace\_backups\20261025-141443-982412-Iris096-Rollback。回退报告与校验：D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-Iris-Rollback096-20261025-141151。旧优化目标保持暂停，后续不继续优化。以下为本轮修改前完整历史，历史“待编译”不替代当前已恢复DLL事实。

---

# 2026-10-25 06:20定时任务：三条件近似碰撞研究未完成

Owner: Codex

当前实际bin/package/game仍为用户已编译的0.4.46 / IRIS_CONSERVATIVE_PROOF_095；DLL SHA256 893e90059a05105cb6c432ef1accfab65fa49b58cf3cb3a0305b073ace3ac307。135份package清单与部署逐项哈希匹配。下方095“待编译”仅是历史交付状态，已被实际产物核对覆盖；不声称已做源码可复现构建。

本轮用户要求E包含、实际有效体积比≤1.2、计入rho*N请求增长的完整成本严格减少三项联合证明。核查发现旧球对目标AABB在q=4.5/t=1时比值1.261866；胶囊立方扩张的比值大于4/pi；圆柱外接方柱4/pi=1.2732395。它们不符合新1.2上限，不能再当已达标方案。095仅为原映射上的局部省重复工作，没有补齐联合证明。

26-DOP可证明单个名义球/胶囊体积比<1.167，但尚未取得实际目标/复合并集/浮点及完整SDK链成本证明；移动弹体近似首次接触还存在提前爆炸漏原受害人的正常凸胶囊反例。已检索公开算法、核对本机2.8.4接口并执行有理区间证书、实际源码锚点、后果模型、135文件哈希及现有095审计AST验证。不把这些当新算法运行验收。

任务状态：未完成优化，未修改任何.cpp/.h、INI、FCS、资源、构建脚本或DLL，未编译、未部署；没有新增运行监视代码或策略，不需要为本轮重新编译。缺口[MISSING]：覆盖真实查询链的三项联合证明，尤其SDK内部成本与新策略新增工作的可核对界；不能用日志均值或局部操作删除替代。

证据与未完成项：D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-Iris-Collision120-20261025-062010\三条件审查与未完成项.md。原日志、游戏进程、暂停轮询及正式版归档均未操作。下面内容均保留为历史。

---

# 2026-10-25 095可证省重复工作与同输入诊断（源码0.4.46，待用户编译）

Owner: Codex

用户接受有明确条件的计算成本证明＋真实耗时验证，并要求额外受伤人数产生的医疗成本不计碰撞效率；近似/精确名单比例单列。

更新/纠正094节交付状态：真实bin/package/game均已0.4.45/IRIS_CONSERVATIVE_QUERY_094，同SHA256 aa0704f9d12d20343ff9598e51743154875d2a7d8eb8a9fd262ceb42b66b6113。本轮源码0.4.46/IRIS_CONSERVATIVE_PROOF_095未编译未部署，工作清单ready=false，真实DLL版本不伪造。

仅胶囊合批删除无用getType/类型分类，复用原AABB前缀删平行轴重复slab运算，保留094参考开关。普通有效输入H094包含于H095，外扩浮点薄带可多收；异常按项跳过不重查。Sphere/Cylinder/投射物、资格/倍率/FCS/资源、调度64查询/8路径、医疗2.5ms32/FIFO保持。没有新线程/Hook/场景锁或跨帧物理指针。

成本证明分清095对094重复工作删除、094对093的实际成本不能混称。完整输入和权重充分条件见docs/proof-kernel095.md；不能证明任何SDK查询在任意环境必快。EnableConservativeKernelReuse=1，新增同输入精确参考EnableConservativeProofAudit默认0、SampleEvery128；受原诊断父门控制，正常不重查/无新增对照QPC。audit_total_ms单列测试成本，异常批不参与阶段时间比；完整身份逐路径近似/精确/额外/漏项比不冒充最终受伤人数。正式结果不因测试改变，不回退重算。

实际执行的离线AST/容量异常/保护函数、审计统计及更新沙盒结果见Task-Iris-Proof095-20261025-030228验收报告。非编译/真实PhysX/游戏/FPS测试；用户编译IrisArsenal.sln Release|x64/v100后才可测0.4.46真实耗时，退出游戏执行原UpdateMod.cmd。原游戏文件、日志、FCS、正式版2.0均不改。双备份D:/CodexBackups与E:/AIWorkSpace/_backups；原UTF-8无BOM与各文件换行保持。

---

# 2026-10-25 094保守伤害查询（源码0.4.45，待用户编译）

Owner: Codex

用户授权：允许正常数据下多纳入但不漏原命中；异常优先跳过该项、不整批重算；公开API/社区算法/数学包含依据；实际减少工作，不能仅以近似之名增加负载。

真实基线已是用户0.4.44/093，bin/package/game DLL同SHA256 9b7b69c97b5fe4628a7a8a3f9826715a809be7ad93d3deeb79425ca2ef7db748。下节093待编译为历史交付状态。新源码0.4.45/IRIS_CONSERVATIVE_QUERY_094未编译、未部署；工作清单保留真实version0.4.44，ready=false/pending0.4.45。

映射显式位于native/NativeMultiContact.cpp：MapExactSphereToAABBQuery、MapExactCapsuleToAABBQuery（公开SDK accurateCollision=false）；MapExactCapsuleToExpandedAABBTest/ConservativeCapsuleIntersectsAABB（原一次联合广相，Minkowski欧氏球⊆立方体，slab同t区间）；MapExactCylinderToConservativeOBB（原紧凑同向盒外扩浮点余量，去掉形体顶点读取和自有圆柱窄相）。依据本机PhysX2.8.4 NxScene.h、CGAL官方定义、PBRT4e6.1.2，证明与误差边界见docs/conservative-query094.md。

近似合批保留一次查询、动态容量、逐段名单；异常跳过且计数/有界明细，不重算，不运行旧影子，SDK/场景未就绪仍等安全窗。空候选不计算倒数。飞弹停止点仍原一次真实扫掠、环境仍原有限射线；其爆炸AOE近似，避免早停挪动爆心反而漏旧受害人。原CanDamage/逐段去重/医疗2.5ms32 FIFO、64查询/8路径、安全窗口/线程/所有权不变；无新Hook/线程/场景锁。

工作INI新增EnableConservativeDamageQueries=1、EnableConservativeQueryLogging=1，均重启读取；功能默认1独立于日志，诊断缺项0并受日志/性能/明细父门。诊断一次查询一次旧统计锁，非逐形体QPC；新增计数/胶囊近似子阶段及异常日志。新模式忽略旧EnableCapsuleBatchShadow；关闭功能才使用旧精确诊断。未改游戏INI、FCS、资源、正式版2.0或存档。

已执行：24,937映射输入实际C++ AST（24,000随机/37边界/900参数），14合批/回调异常继续/8公开API策略，520独立身份容量；19关键函数逐token保护；原远程实际AST2498批/480包络；64日志门/合计分支；14本地C++语法；更新沙盒20通过1系统链接权限跳过，真实093旧DLL被094合同拒绝；138部署与DLL哈希保持，双备份/编码/换行/中文核验。不是MSVC/真实PhysX/线程/游戏/FPS实测，不能承诺净帧收益；额外人物会增加原生受击，且本轮未减少飞弹扫掠大头成本。

交付：用户编译IrisArsenal.sln / Release|x64 / v100，正常退出游戏执行原UpdateMod.cmd；确认日志0.4.45与IRIS_CONSERVATIVE_QUERY_094后做同压力对照。Task-Iris-Conservative094-20261024-222330有验证结果、逐文件报告、原始基线/保护清单；D:/CodexBackups与E:/AIWorkSpace/_backups同名目录保留每次修改前文件，UTF-8无BOM/原换行保持。本轮不代编译、不自动部署。

---

# 2026-10-24 093查询边界与实例精确省写（源码0.4.44，待用户编译）

Owner: Codex

已核对092真实0.4.43：bin/package/game DLL同SHA256 1651254682d2bc628f1bc7634d6b337c74c93b54f6521668fb11c0a4351e994f。下节“092待编译”为历史交付状态。本轮按用户授权继续优化，未代编译、未部署。

功能：加载时选七组源键相同候选，Draw仍原插值，只有与本实例上次成功提交值逐位相同才省setter；可选缓存随原Visual手动所有权转移、Clear释放、分配失败回原路。附件只复用当前骨骼numChildren标量，原顺序/谓词/256骨骼512子节点保护保持；Ogre Entity枚举受禁用宏控制，OldNode迭代器返回容器与本机DLL不同，已撤销，不加私有偏移/依赖补丁。十招就绪扫描仅独立量测，不跨帧缓存资格/长度/指针。092现场single三个窗口均有收益方向，因此保留single=1，停止半批关闭的AB实验，保留成本监视。

诊断：复用092根树追加7分类，将原SDK提交/执行/finish与报告块分开，不逐形体计时、重放查询或增加Hook/线程/场景锁。直接单射线onHit仍嵌在execute，不能称纯SDK。比较旧物理须把新增query分类exclusive加回；就绪/武器同理，分类迁移不是性能提升。新增开关均可关闭；程序诊断缺项0，本地INI1，功能项独立。医疗2.5ms/32/FIFO、物理64、范围/倍率/过滤/逐段次数、FCS/资源/正式版2.0保持。

232原函数/9文件字节不变；650附件选择边界、1956真实资源分组输出逐位对照、32所有权/分配路径、288树/12新门/16时钟/448策略、2498物理批+560同输入配对、包络/聚组/原生命周期/医疗规格及14语法检查通过。旧物理解释器隔离使用092 Visual，新缓存单独实际AST验；非MSVC/真实PhysX/线程/游戏/FPS测试。Update沙盒20通过1权限跳过；旧DLL被093合同拒绝。

工作包真实version仍0.4.43，ready=false/pending_version0.4.44，新合同IRIS_QUERY_BOUNDARY_093。用户编译IrisArsenal.sln Release|x64/v100后正常退出游戏执行原UpdateMod.cmd。调用链/配置/验证见docs/query-boundary093.md；任务/逐文件报告Task-Iris-QueryBoundary093-20261024-210030；双备份同名D:/CodexBackups及E:/AIWorkSpace/_backups。原UTF-8无BOM及各文件换行保持；未覆盖原日志、存档、模组列表或真实部署。

---

# 2026-10-24 092完整接口归因与空区成本对照（源码0.4.43，待用户编译）

Owner: Codex

用户要求展开“其他战斗处理”到实际接口，并同时处理远程空区24.28ms成本对照、后效及任务消费非物理部分。已核对091真实0.4.42，bin/package/game DLL同SHA256 0da7c141dac6911b11b43cf9ab0b94cf3c0900e88baca4267eeec9c7c7d9f323；下节“091待编译”为历史交付状态。

092全量38分类复用原COMBAT_TICK起止，inclusive/exclusive与root_unwrapped闭合，包含后效/逐弹/残留、任务收集/入队/轮转、可视节点/参数/隐藏、武器姿态/附件/路径；物理、资源生命周期和诊断开销单列。TLS仅借当前栈，无新Hook/线程/引擎getter/锁对象/跨帧指针。根结束合计，慢根首次4条后最多1/10秒。新诊断缺项0，本地工作INI显式1，关闭热路径无新QPC/TLS/统计锁，仍有固定分支/栈成本。

远程复用原时钟记录total/rays/body/probe和输入/命令/省查/失败；显式A/B相邻合格球批交替原single开关，各批只执行一个策略，不额外重放。不是相同输入现场对照；single_off仍保留多条空间省查，整个空区需原EnableRangedEmptyPruning另做两次对照。未有新现场数据，未猜测删除所谓无收益分支。原精确碰撞/医疗2.5ms32 FIFO/物理64/资格/倍率/范围/动作/资源/FCS保持。

240原函数和调用约定、288树/448策略/16原Scope时钟AST、2498原物理批+560同输入single配对、包络/生命周期/医疗规格/14语法检查通过。Update沙盒20通过1权限跳过。没有MSVC/真实TLS线程/PhysX/游戏或FPS测试，不能将插桩重新分项当性能提升。

工作包保留真实0.4.42/旧DLL，ready=false/pending0.4.43，新092合同拒绝旧产物。用户编译IrisArsenal.sln Release|x64/v100后正常退出游戏执行原UpdateMod.cmd；本轮不代编译、不部署、不操作游戏或存档。详见docs/interface-probe092.md及本会话Task-Iris-InterfaceProbe092-20261024-191745。双备份同名D:/CodexBackups和E:/AIWorkSpace/_backups；原编码换行中文保持。

---

# 2026-10-24 091同次动画查找与抽样归因（源码0.4.42，待用户编译）

Owner: Codex

用户要求继续优化并细分大额未归因部分，特别约束不能为极端压力增加轻负载常驻开销。
已核对真实bin/游戏DLL为0.4.41/090同SHA256 ce9636559aaf4e5cd1ccc875f6110ab2f33b9148d95d55b15664b29c3677b28b；下文“090待编译”仅为历史交付状态。
功能仅减少Tick同一次动画状态/长度重复读取，无跨帧缓存。新增work固定栈抽样和native已知探针之间的gap，缺项默认0、本地INI显式1/N32；无新Hook/线程/引擎getter/锁对象/全局扫描。关闭无新QPC/原子/统计锁，未抽中无新QPC。
原生受击、逐段命中、远程/范围/倍率/医疗2.5ms32/FIFO、物理预算64、未设弹体数量门、FCS/特效/真实部署均保持。
109原战斗函数token、80长度边界、1040阶段AST、480Part、1632Hit抽样、64转发、14语法及090全回归通过；Update20通过/1链接特权跳过。无编译/实机/FPS测试。
新工作包ready=false/pending_version0.4.42，保留真实0.4.41内部身份；须用户编译sln Release|x64/v100后Update。配置/统计解释/双备份/逐文件报告见docs/work-trace091.md及D:/CodexWorkSpace/Sessions/20261002-235652-kenshi-crash-407794f2/Task-Iris-WorkTrace091-20261024-165024。

---

# 2026-10-24 090空间分组与解除活动弹体门（源码0.4.41，待用户编译）

Owner: Codex

用户要求继续从远程物理工作优化、调用链清晰/原生安全边界/足额可关日志，并解除弹体上限。已核对真实0.4.40/089：game/package/bin DLL同SHA256 9bd97dd01831c600d174581b0ec9c60c0021ca3fdadf7e1eaa21422fed230370。上节“089待编译”仅为当轮历史交付状态。

当前同安全窗口最多8项按自有完整扫掠包络分组，仅紧凑两组合并；某组有角色不再阻止其他空组省扫掠。未知/包络失败保留原精确；额外宽相含失败别名恢复最坏量预留，shadow不抵扣，64查询硬界保持。独立组宽相为本地显式试验，未保证净收益；单项空时总命令不减少，必须比较宽相+扫掠+队列等待。无新线程/Hook/锁、无跨帧SDK指针，无目标/瞄准/运动/范围/医疗改动。

删除shots>=64和shots+residues+pool>=96活动门；空闲池最多96，额外归还实例销毁，预热共用Return；Draw/入队异常释放临时可视。原任务256、伤害水位和演员容量不扩展。新增空间工作量/分组计时/逐弹自然终止汇总，父门关闭不新读时钟/格式化。EnableRangedSpatialPruning=1、EnableRangedSingleEmptyProbe=1（缺项0）、EnableProjectileWorkLogging=1（缺项0）；游戏INI未直接改。

2498批实际AST、6000包络采样、480聚组、567生命周期、174原函数/完整消费链token、48计时门、14语法单位及医疗规格通过；Update20通过/1链接权限跳过。SDK替身与语法检查不是MSVC/真实PhysX/线程/游戏/FPS测试，未编译/部署；详见docs/spatial-projectiles090.md及本会话Task-Iris-Spatial090-20261024-153055。

工作包ready=false/pending0.4.41，旧DLL身份/hash真实保留，新090合同拒绝旧产物。用户编译IrisArsenal.sln Release|x64/v100，正常退出游戏后原UpdateMod.cmd。正式版2.0、FCS纯净零RACE、现有外置补丁/资源保持。双备份D:/CodexBackups/Task-Iris-Spatial090-20261024-153055和E:/AIWorkSpace/_backups/Task-Iris-Spatial090-20261024-153055，编码/换行/中文保持。

---

# 2026-10-24 089远程实际物理工作省略（源码0.4.40，待用户编译）

Owner: Codex

用户明确要求优先从物理55.1%入手，调用链清晰并保留原生安全边界。实际0.4.39/088已由用户编译部署，game/package/bin DLL同SHA256 cec12ab64c1eec4d236c8c9e3adbeebb166c1a32dc66bae1d78eb584afad1e4f；上节“088待编译”为历史交付状态。

089只处理远程批量球扫掠实际工作：同批相同场景/groups、完整float位参数相同的成功查询以自有名单只读别名复用，失败别名单独原ProjectileAll。联合完整扫掠AABB流式证明无任何角色才省球扫掠；遇角色、身份异常/未知保留原精确SDK，不用getter姿态逐路径剔除以避免PhysX双缓冲歧义。最少3条、空间紧凑、2*N+1预算方试探；无收益只停当前AdvanceEffects，下窗恢复。宽相算真实64预算，偶发多1命令可能影响后续服务机会，须日志一同看等待，不声称每批必加速。

EnableRangedQueryReuse=1、EnableRangedEmptyPruning=1、EnableRangedEmptyShadow=0；显式对照才运行原参考，记录未确认/非空并消费原结果。新查找/宽相计时、实际省查/命令/异常/放弃原因复用EnableCollisionDetailProfiling及原日志/性能/明细父门，无逐形体QPC/IO。原始报告按实际工作计、逻辑contacts各事件独立。无新Hook/线程/场景锁或跨帧SDK裸指针。

三远程地形有限中心射线/角色体积、原生飞行组、完整motion/半径/TOI/墙同距优先、过滤/逐段命中/伤害/FIFO2.5ms32、胶囊088、动画资源/FCS、正式版2.0保持。168既有函数、完整消费链token及实际AST/三维包络/日志门/流式/预算/独立命中/失败反例验证见本会话Task-Iris-RangedWork089-20261024-124808和docs/ranged-work089.md。Update隔离20通过/1链接权限跳过；未编译、未真实PhysX/线程/游戏测试，不能承诺FPS收益。

工作包ready=false/pending0.4.40，现有真实0.4.39 DLL不改写，新089合同拒绝旧DLL。用户编译IrisArsenal.sln Release|x64/v100后正常退出游戏再原UpdateMod.cmd。本轮无自动部署，无游戏进程操作。

双备份D:/CodexBackups/Task-Iris-RangedWork089-20261024-124808及E:/AIWorkSpace/_backups/Task-Iris-RangedWork089-20261024-124808，保留原路径/修订/编码换行与中文。

---

# 2026-10-24 088高压局部预留与远程同窗同步提交（源码0.4.39，待用户编译）

Owner: Codex

用户明确授权两条优化及可关闭调试日志。0.4.38/087已由用户实际编译部署，游戏/package DLL同SHA256 cf04b22e0c45815a906287133e8dee985a3ea5a8a8b6381ec7276c035be1babe；上节旧“待编译”是历史交付状态。

胶囊去掉PlannedJobCost整轮预留死门，改当前count+1局部恢复预留；成功仍按原路径数收费、每作业8条、64硬界。真实合批失败后只在本次ResolveJobs停止继续试批，下一窗恢复；参考失败只推进原成功前缀。失败/显式影子额外预算可能使后续路径留待下窗，不伪称失败也有同帧等价保证。

远程同窗最多8条连续飞弹/队首单路径光炮集中地形射线，球扫掠用NxSceneQuery同步报告；光炮精确OBB/窄相仍原接口（批量OBB缺accurateCollision=true）。报告/SDK对象栈内RAII完成释放，各项独立cast/event/游标、按原顺序消费，未消费预取不跨窗保存。无新增Hook/线程/场景锁，原Tick/Clear/医疗/敌我/几何/范围/倍率/特效保持。

EnableRangedQueryBatching本地1可设0回旧路；新增分阶段/工作计数服从EnableCollisionDetailProfiling及日志/性能/明细父门。创建/释放和unused均可量测，不把SDK批量化声称为已减少远程检测或已获FPS收益。

实际AST 11700预留/2700预取/290回调、7800飞弹顺序/15600胶囊预算规格、91原战斗函数和14语法单位、医疗重入/FIFO/代次、80计时门通过。更新20通过/1链接权限跳过；MSVC/真实PhysX/线程/游戏未执行。详细证据见docs/query-batch088.md及本会话Task-Iris-QueryBatch088-20261024-114303-057567。正式版2.0、FCS、游戏135项静态文件保持。

工作包ready=false/pending0.4.39保留真实0.4.38 DLL，新088合同明确拒绝旧DLL。用户编译IrisArsenal.sln Release|x64/v100，退出游戏后原UpdateMod.cmd；本轮不编译、不部署、不操作游戏进程。

双备份D:/CodexBackups/Task-Iris-QueryBatch088-20261024-114303-057567和E:/AIWorkSpace/_backups/Task-Iris-QueryBatch088-20261024-114303-057567，原路径及逐修订保留。

---

# 2026-10-24 087查询消费优化与分阶段日志（源码0.4.38，待用户编译）

Owner: Codex

用户授权按关闭断肢后方向优化、调用链清晰且日志可关闭。实际0.4.37/086已由用户编译运行；前轮amputate exclusive占伤口86.1%，关闭后1286次原生受击/amputate0，平均受击0.382→0.075ms，是不同战斗对照而非同输入FPS证明。源STATE旧“086待编译”是历史交付状态，不再当当前运行事实。

本轮减少查询内完整身份重复资格判断、同攻击段已接受身份的重复收集、同龄源层重复lo/hi/u计算；16槽冲突完整比较后重算，无分配、无跨帧人物/形体缓存。原SDK查询/范围/完整刀路/排序、64次与每作业8路径、医疗2.5ms/32/FIFO/最终资格和安全门保持，无新线程/Hook。

新增EnableCollisionDetailProfiling：程序缺省0，本地distribution/package1，依赖总日志/性能/明细；12个窗口/进程子阶段和十项工作量计数，无逐形体QPC/IO。SDK回调返回后才提交原诊断锁；关闭不增加QPC/统计锁。真实游戏INI未修改。

38,988次实际AST查询、96组名单、336组float32位置、49完整身份对比、强制槽冲突通过；93原战斗函数/原物理调用与医疗链保持；7重入/FIFO/102目标预算/9代次，14语法单位、更新隔离20通过/1权限跳过。非编译验证不是MSVC/PhysX/线程/游戏测试。详见docs/contact-work087.md和本会话Task-Iris-Contact087-20261024-105216-676167。

现有bin/游戏DLL同SHA256 ec3068111af31d1b14a5c2062a971aa8e6c93219d3fece19ed270ae8003b1688，仍0.4.37。新工作包ready=false/pending0.4.38，只更新新增INI哈希；正式版2.0、FCS和游戏135项静态清单保持。用户编译IrisArsenal.sln Release|x64/v100，退出游戏后原UpdateMod.cmd。新增087合同会明确拒绝旧DLL，不伪装已部署。

双备份D:/CodexBackups/Task-Iris-Contact087-20261024-105216-676167与E:/AIWorkSpace/_backups/Task-Iris-Contact087-20261024-105216-676167，按原完整路径和修订保存。后续根据native_terrain_ray/native_sphere_sweep/capsule_exact/contact_collect等实际耗时决定是否改合批粒度、排序或调度，不靠延后/削减查询掩盖负担。

---

# 2026-10-24 086局部扫掠索引与原生医疗分支（源码0.4.37，待用户编译）

Owner: Codex

用户授权按原生安全调用链优化，并追加只读检查Buffitem与Example。085已由用户实际编译/部署0.4.36；本轮1127次结算，伤口apply子树占87.6%，高伤档贡献83.8%，不能据此认定纯原版缺陷。离线确认原生ragdollMode已有状态/待处理消息去重，amputate有真实肢体分支；两外部DLL实际晚于Iris加载，各自与bin DLL同哈希。没有修改两个工程或加载顺序。

086只将Sweep Collector同形体查找改为本次查询局部索引，少于16仍原线性、冲突完整指针比较、内存失败回原线性，不新查PhysX/不跨帧留SDK指针。同时零计数锁前短路，避免新增零字段空锁。医疗新增六个可关分支探针：amputate/createItem/limb setup/state/collapse/ragdoll，原参数/返回/异常/次数与原线程保持。EnableWoundBranchProfiling程序0、本地distribution/package为1；真实游戏INI未改。2.5ms/32/FIFO、几何/范围/倍率/资格/护甲/经验/动作/特效不改。

73组/10043次实际查找AST对照，320转发、480计时栈、统计/生命周期、24零计数、1024门/972ready及FIFO规格通过。14份语法工具检查存在已说明的成员指针typedef输入排除，不当MSVC类型验证。更新隔离20通过/1链接权限跳过；实际游戏清单哈希全有效，仍0.4.36。工作包ready=false/pending0.4.37，新两合同正确拒绝085 DLL。未编译/部署/实机，无FPS提升结论。

用户编译 IrisArsenal.sln Release|x64/v100，正常退出游戏后UpdateMod.cmd。下一日志核对0.4.37、medical_branch_ready六探针和sweep_shape_index_ready，再判断具体医疗分支是否存在可删冗余；不得把新增子阶段导致apply exclusive下降当优化。详见docs/medical-branches-sweep086.md。

任务证据及双备份同名目录：D:/CodexWorkSpace/Sessions/20261002-235652-kenshi-crash-407794f2/Task-Iris-Medical086-20261024-030412-760704；D:/CodexBackups/Task-Iris-Medical086-20261024-030412-760704；E:/AIWorkSpace/_backups/Task-Iris-Medical086-20261024-030412-760704。正式版2.0、FCS和游戏资源保持。

---

# 2026-10-24 085伤口子树与原生其他受击对照（源码0.4.36，待用户编译）

Owner: Codex

用户本轮授权对照并修改。已确认实际运行0.4.35/084，1133受击中addWound占88.425%，此前“084未编译”仅为历史交付状态。重新核对本机十个真实符号/指令，与084游戏二进制哈希一致；原生近战/弩弹进入同一addWound。加载日志确认fixed/Buffitem.dll，工程有applyDamage减伤/肢体保护Hook；尚未测量它的成本，不能归咎纯原版或另一个mod。

新增IrisWoundAudit独立单元，EnableWoundDetailProfiling程序缺省0、本地distribution/package显式1；依赖既有总日志/性能/明细/084探针。根Hook成功后才安装实际医疗/伤口外观/伤害飘字/血液四子探针，桥接域内外同口径、按伤害档位比较；outside_bridge不冒称干净原版。仅固定纯值统计，原参数/次数/返回/异常不变；独立统计锁内无引擎/日志/旧插件锁，TLS故障只关闭诊断，读档只变代数，无新线程。

IrisCombat/Arsenal/Ranged/NativeMultiContact字节不变，原084诊断剥离新增观察后全token一致；2.5ms/32/FIFO、倍率/范围/敌我/护甲/经验/特效不改。14份语法树、实际纯值/分支/转发AST、既有FIFO重入及隔离更新20通过/1权限跳过；不冒称编译、Windows线程或游戏实测。源码/日志身份0.4.36，新085合同拒绝现有084 DLL；包ready=false、pending0.4.36，不部署游戏。用户IrisArsenal.sln Release|x64/v100编译后，退出游戏执行UpdateMod.cmd，再从新日志确定可优化的实际子阶段。

说明docs/wound-profile085.md；证据及即时逐文件报告D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-Iris-Wound085-20261024-020930-624034。逐次双备份D:\CodexBackups\Task-Iris-Wound085-20261024-020930-624034及E:\AIWorkSpace\_backups\Task-Iris-Wound085-20261024-020930-624034。正式版2.0、DLL/FCS/资源和真实游戏INI保持。

---

# 2026-10-24 084优化第一轮诊断（源码0.4.35，待用户编译）

Owner: Codex

用户授权按细表改代码，并强调分析原生的安全/效率是否适用，不照搬。只读重取本机7个函数，确认受击还包含防御/医疗/特效/经验/反应/通知/声音/攻击者反馈；当前主循环直接调用charsUpdateUT一次，未证明额外可用服务机会，所以保留updateDone、2.5ms/32/FIFO和查询安全门。本轮完成计划2～4项诊断，不改倍率/范围/权重/敌我/护甲/部位/经验/碰撞算法。

新增独立IrisNativeAudit单元：EnableNativeHitProfiling和EnableServiceOpportunityLogging程序缺省0，本地distribution/package显式1，旧六项日志仍1。启用且总日志/性能/明细有效才装addWound/addEffect两个诊断Hook；防御/反应复用已有入口。逐笔固定桶区分inclusive/exclusive/未归因余量，异常/失效/嵌套单列；TLS/栈RAII不保存引擎指针、不在原生调用时拿插件锁。服务只观察原回调和队列纯值，不额外Flush，不把状态观察当许可。

101原战斗函数剥离观察后token保持；1024医疗门、972ready、349桶/7分位、192阶段、162就绪/16开关/4短路、64转发AST及7种重入/FIFO规格通过；072的732组与081密集/冲突/异常规格通过。12份C++/H语法，更新隔离20通过/1链接权限跳过；不冒称MSVC/线程/PhysX/GPU执行或FPS改善。

实际三处DLL仍0.4.34/083，未编译/部署；工作包ready=false、pending0.4.35，新084合同正确拒绝旧DLL。用户编译IrisArsenal.sln Release|x64/v100后，退出游戏再UpdateMod.cmd。本轮不写游戏INI/FCS/资源、独立种族补丁、工坊或正式版2.0封存。后续从新日志判断原生慢点和服务机会，再决定实际优化。

说明：docs/native-profile084.md。原生证据/逐文件报告/验证：D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-Iris-NativeProfile084-20261024-011541-440673。逐次双备份：D:/CodexBackups/Task-Iris-NativeProfile084-20261024-011541-440673 与 E:/AIWorkSpace/_backups/Task-Iris-NativeProfile084-20261024-011541-440673。

---

# 2026-10-24 正式版2.0独立封存与下一轮优化细表

Owner: Codex

用户要求将当前mod特别归档为正式版2.0并列出细化优化方案。已先封存原始运行/项目状态，名称正式版2.0；DLL内部仍0.4.34 / IRIS_MEDICAL_GATE_083，三处DLL SHA256 5f666e750414e0c3550efadbb3c840deb3ca6900d4755923e84144accb78b21e，现有PDB身份匹配，未重编。正式版双盘各7288文件；7281份输入全量哈希/源稳定性、136文件隔离恢复及两盘一致性通过，文件设只读，不覆盖正式版1.0。

归档：D:\CodexBackups\IrisArsenal-Formal2.0-20261024-005639-412184；第二盘：E:\AIWorkSpace\_backups\IrisArsenal-Formal2.0-20261024-005639-412184。主FCS24记录/零RACE，Gameplay与工坊ID3825316881保持，两个动画补丁独立保存。归档原游戏内部清单仍有用户FCS保存后的.info/.mod两个旧哈希，外部清单以实际字节验证；package原135项清单有效。源码/版本合同相符不冒称已可复现构建。

用户随后明确本地应开启日志、仅发布时关闭。封存完成后另作双备份，将distribution/package/游戏三处INI的六项日志开关开启并只更新两份清单的INI哈希；其他键与C++/DLL/FCS/资源/更新脚本均保持。正式版2.0原runtime及原project仍是关闭日志状态，不反写封存；当前本地设置重启游戏读取。诊断显示/额外旧查询对照仍关闭，2.5ms/32/FIFO不改。

下一轮细表见docs/optimization-plan-formal2.md：先做原生受击内部归因与既有服务机会测量，再按证据决定调度或重复查询优化；本轮不实施战斗优化、不编译、不新DLL部署、不游戏测试。正式版说明见docs/formal-release-2.0.md；任务证据D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-Iris-Formal2-20261024-005639-412184。本次日志/STATE修改前备份：D:\CodexBackups\IrisArsenal-Formal2.0-LocalLogs-20261024-005639-412184 与 E:\AIWorkSpace\_backups\IrisArsenal-Formal2.0-LocalLogs-20261024-005639-412184。

---

# 2026-10-24 用户工坊标签修正复核与FCS回同步

Owner: Codex

用户已在FCS修正不受Kenshi工坊接受的标签并发布。实际游戏、distribution与package的tags/string均为Gameplay；已发布ID3825316881／visibility=0。原UpdateMod.cmd→update_mod.main→stage_package→workshop_assets→deploy_package调用链符合，既有合并逻辑保留已发布ID／可见性／lastUpdate，没有修改这些脚本。

另发现游戏.mod已经FCS保存：24条记录、零RACE，新增默认字段／保存次数和完整说明头。已将该17976字节文件原样回同步至package主包与distribution基础模板，SHA256 0318fa854a388cfa22527efe64d43bbae8708790d5197dc0686b5f48bbdb2cd8。只改项目源，真实游戏136份静态文件保持；C++／DLL／INI及独立种族补丁未改。package-only与隔离全量迁移实际通过，Gameplay及公开工坊身份保持，无需编译。本轮经验已追加至Kenshi-Combat-Animation-Porting-Playbook。

注意项目INI仍为日志开启的测试配置，游戏已关闭；全量Update会按项目包覆盖该配置，本轮已提示且未改。未实际部署、上传或游戏实测。证据与双备份：D:/CodexWorkSpace/Sessions/20261002-235652-kenshi-crash-407794f2/Task-Iris-WorkshopTagAudit-20261024-004321-568179/validation.json，D:/CodexBackups/Task-Iris-WorkshopTagAudit-20261024-004321-568179 与 E:/AIWorkSpace/_backups/Task-Iris-WorkshopTagAudit-20261024-004321-568179。

---

# 2026-10-23 本体删除全部种族覆盖（不改独立补丁）

Owner: Codex

用户明确要求本体FCS不包含种族动画补丁，并指出EndPoem已有独立补丁。已从package、游戏与distribution基础模板各删除24条RACE，其余FCS记录原字节保持；两生成器禁止回填RACE，验收改为零RACE，发布介绍同步职责。现有EndPoem／IKEMEN独立补丁、C++／DLL／动画／特效／数值和游戏关闭日志的INI均保持。原始0.1.0闭环作者从Ephnel名单建立这些记录，正式作者沿用；不是工坊封面任务新增。此前只回档并未删除，现明确纠正。

实际执行两个生成器并截获输出，含历史RACE输入也得到零RACE；20份实际男女动画引用／内部名称／时长、非RACE字节、受保护文件与135项游戏清单验证通过。移除后种族须由独立补丁接入；现有EndPoem覆盖原24条中的21条，本次未擅自扩充。未编译或游戏实测。FCS旧窗口须重新打开，避免保存旧内容回写。

验证与逐文件报告：D:/CodexWorkSpace/Sessions/20261002-235652-kenshi-crash-407794f2/Task-Iris-RemoveRaceOverrides-20261023-221353-474283/validation.json；双备份：D:/CodexBackups/Task-Iris-RemoveRaceOverrides-20261023-221353-474283 与 E:/AIWorkSpace/_backups/Task-Iris-RemoveRaceOverrides-20261023-221353-474283。

---

# 2026-10-23 工坊首发资料已准备（运行DLL保持用户0.4.34 / 083）

Owner: Codex

用户要求补封面与发布信息，稍后自行执行UpdateMod迁移。封面已按后续要求删除“十式武装”，底部仅“近战 × 远程”。800×800 JPG及相同字节_IrisArsenal.img同时保存在distribution与package；本机FCS真实GetImagePath与XmlSerializer已核对。

新增中英文介绍、更新说明、安装／配置与来源清单；标题不绑定招式数量，不虚构作者或工坊ID。stage_package在原清单计算前调用独立workshop_assets准备静态资料，已有非零ID／可见性／更新时间保留，冲突明确停止；原Update仍为双备份后全量复制，未新增编译或资源重建步骤。当前元数据id=0、visibility=2为私人未发布草稿，上传器说明需用户粘贴TXT。

实际package-only成功；136项完整包哈希、302份受保护代码／DLL／配置／战斗资源保持、8组身份边界、原部署路径隔离清空／完整复制／双备份验证通过；未编译、写真实游戏目录或上传Steam。INI仍为原性能测试设置；README列出六项彻底关日志配置。原源素材未附齐公开再分发授权，CREDITS仅记录来源，不将其误声明为原创或CC0。

发布步骤：[workshop/UPLOAD.md](workshop/UPLOAD.md)。封面母版、提示词、验证与逐文件报告：D:/CodexWorkSpace/Sessions/20261002-235652-kenshi-crash-407794f2/Task-Iris-Workshop-20261023-215209-912666。双备份同名目录位于D:/CodexBackups与E:/AIWorkSpace/_backups。

---

# 2026-10-23 083医疗安全门分离（源码0.4.34，待用户编译）

Owner: Codex

用户授权修正已确认的多余医疗queue等待，并要求必要复核日志。Flush对已有稳定身份的命中请求不再读取/等待queuesAreClearMT；每笔仍检查世界/初始化/reset/load、物理线程、AI、暂停及epoch，原生受击在原插件锁外执行。查询端的queue门、真实PhysX、远程地形射线与角色半径均保持；2.5ms/32配置、FIFO、原敌我/倍率/护甲/部位/经验体保持，没有新增线程/Hook/锁对象。

可关阶段诊断补medical_native_calls、medical_requests_inspected、medical_progress_windows_after_queue_pending_observed；最后一项仅关联本轮此前POST_TICK观察，不冒称原子实时状态。医疗ready不依赖queue，queue=-1表示未读取；原查询ready口径保持。沿用四个既有日志开关，INI未改。

实际1024医疗门AST、972 ready条件、54日志计数AST、7种重入状态/FIFO回放、102目标预算规格、98函数正文/8文件字节边界、10 C++/H语法、081专项及更新隔离20过1链接权限跳过。未编译/未部署/未PhysX或游戏实测，不承诺FPS提升。

纠正下方082“待编译”历史状态：本轮bin/package/游戏三份实际DLL均为用户0.4.33/082，SHA256 c36c9b69469d7e698bbe0c947193c089e091d84e31dd9bf6c0c4309f584811fe，原字节保持。当前源码0.4.34/IRIS_MEDICAL_GATE_083，package ready=false/pending0.4.34，旧DLL正确拒绝083组包门。用户编译IrisArsenal.sln Release|x64/v100，正常退出游戏后UpdateMod.cmd。没有自动编译或操作游戏。

[083实现、日志、双备份与逐文件报告](docs/medical-gate083.md)。本任务证据：D:/CodexWorkSpace/Sessions/20261002-235652-kenshi-crash-407794f2/Task-Iris-MedicalGate083-20261023-205804-0211f9。

---

# 2026-10-23 082安全窗口分项日志与阶段检测（源码0.4.33待用户编译）

Owner: Codex

按用户授权只加可关闭诊断：现有charsUpdateUT Hook原生前后、Tick前后及医疗退出记录纯值状态。新增EnableWindowAuditLogging=1供本轮测试，程序缺省0，需总日志/性能/明细同时为1。四个阶段有相关作业时才读公开getter；医疗只复用原检查读值，短路顺序及原生调用次数保持。旧reason=physics_busy/旧等待归因保留，新增gate_cause区分physics_running/queues_not_clear/ai_running；未知字段-1。不把顺序采样冒称原子状态或工作线程实际运行时长。

固定容量五阶段窗口/进程摘要audit_window_phase；audit_window_trace首次8条/变化至少1秒/持续10秒，记录是否首笔前拒绝、连续医疗拒绝机会、观察跨度与阶段额外探测耗时。复用原主线程Hook及Iris互斥，医疗内不新增引擎getter、线程/Hook/锁对象，原安全门、2.5ms/32 FIFO、原生伤害/几何/资格不改。读档清阶段事实和连续序列，进程累计保留。

实际非编译验证：128组合解释实际安全门AST，20关闭门组合，21受保护函数业务token对照，6连续拒绝/重置规格、40限频规格、10000三态编码往返、10份C++/H语法；081的100300对照条件、4007冲突操作及4097目标/32776检查规格保留通过。不是MSVC/PhysX/线程或游戏实测，未编译、未部署。

源码0.4.33/IRIS_WINDOW_AUDIT_082（含081），实际bin/package/游戏DLL仍用户0.4.31/080，原字节保护。package ready=false/pending0.4.33；须用户编译IrisArsenal.sln Release|x64/v100，退出游戏后UpdateMod.cmd。后续日志需先确认0.4.33及window_audit_ready enabled=1，旧080不能证明新诊断已运行。

[082字段说明、调用链、双备份及逐文件报告](D:/CodexWorkSpace/Sessions/20261002-235652-kenshi-crash-407794f2/Task-Iris-Window082-20261023-200218-57804a/README-082.md)

---

# 2026-10-23 081合批回退策略与异常日志（源码0.4.32待用户编译）

Owner: Codex

按用户本轮清单保留胶囊合批：候选512、潜在检查1024、单条结果256均取消人为上限；内联存储保留，超出按需增长。完整六字段身份去重，单形体身份/几何异常跳过该形体，异常不再触发整批旧查询。形体白名单暂保留四类，其他类型真实支持/性能尚未核实。新增EnableCapsuleBatchShadow=0（默认关闭）；关闭时不运行首8批/新类型/周期旧查询，也不推进周期状态。真正接口不支持/分配失败仍走既有失败恢复，不消费半份结果。

查询返回后按战斗明细开关记录capsule_batch_shape_skipped；首次8条、码变且至少1秒、持续异常每10秒明细，既有摘要累计capsule_batch_skipped_identity/geometry。回调无文件IO。为配套无结果上限，消除单批>2048目标永远无法入队的堵塞：只在伤害队列为空时允许一个完整大批入队，普通规模条件不变；原2.5ms/32 FIFO结算不改。没有新增Hook/线程/锁、跨帧SDK裸指针或伤害规则改动。

已执行非编译验证：100300条实际条件AST、243解析几何场景及4097目标/32776精确检查规格、4007哈希冲突操作、45入队边界与4114次FIFO交付规格、16250轮转规格、25个受保护函数token对照（ResolveJobs只允许上述入队门差异）、10份C++/H语法解析和v100 SEH析构约束检查。109份其他基线代码/配置文件及128份非INI包构件保持；三个DLL SHA仍相同。均不是实际C++/PhysX/游戏线程或FPS实测，未编译、未部署。

源码0.4.32/IRIS_CAPSULE_POLICY_081；实际bin/package/游戏DLL仍0.4.31/080。package ready=false/pending0.4.32，旧DLL不能通过081组包门。用户编译IrisArsenal.sln Release|x64/v100后，正常退出游戏并运行UpdateMod.cmd。双备份、逐文件报告、完整差异和验证结果：

[081调用链、边界与交付报告](D:/CodexWorkSpace/Sessions/20261002-235652-kenshi-crash-407794f2/Task-Iris-Batch081-20261023-191757-b77e10/README-081.md)

---

# 2026-10-23 080保守性能优化（源码0.4.31待用户编译）

Owner: Codex

按用户四方向授权：只在三远程精确t=0环境必然优先时省角色扫掠，其余保留完整位移；当前查询相邻完整身份局部复用资格；可视输入按位完全相同才省custom1..8重复插值/写入，光炮统一查询后一次更新。新增DiagnosticHideEffects=0默认正常，手动全卡GPU采样工具与周期诊断，无新Hook/线程/锁对象，不做未知一般截短或删源层。

原生伤害/敌我/临时敌对、医疗/义肢/家具、原瞄准/炮口/范围、2.5ms/32 FIFO、64查询和读档暂停保持；IrisArsenal.cpp/IrisRanged.cpp与所有动作/特效/FCS/DLL原字节保护。源码0.4.31/IRIS_PERFORMANCE_080未编译，包ready=false/pending0.4.31，旧DLL身份保持。用户编译IrisArsenal.sln Release|x64/v100，正常退出游戏后UpdateMod.cmd；直接旧DLL不能通过080门。

900原生查询AST、4096接触结果对照、1029参数位级条件、6身份字段边界、732近战与296工作状态回归、关闭统计7种组合、10份C++语法/4 Python AST、129包哈希、21隔离Update（20通过/1链接权限跳过）完成；GPU采样器已实际1次运行，仅验证工具通路，不是新DLL游戏A/B。未编译/部署/游戏线程或FPS实测。

详见[080实现、日志、验证与备份](docs/performance080.md)。本任务路径：D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-Iris-Performance080-20261023-015832-78d04f。下方历史状态保留。

---

# 2026-10-23 079远程锤枪家具工作状态修复（源码0.4.30待用户编译）

Owner: Codex

用户确认勾选远程后到达研究/耕作家具站立且无进度。原生hasAnythingEquipped先调用hasCrossbowEquipped；旧HasHook将库存能力当作实际手持，收起后仍真。079只在实际getCurrentWeapon身份为本枪时报告持弩/返回私有Gun，空手和其他武器回原生；库存Use/Score能力保留。既有安全Prepare识别原生EQUIP_CROSSBOW完成拔枪阶段，防止修正后冷起手停滞。没有新Hook/锁/线程/工作黑名单，动画、抗打断、伤害/物理、FCS和资源保持。

本机EXE/RTTI/vtable链只读核对；240实际Hook分支+56拔枪条件、旧反例/转发次数、9 C++/H语法、3 Python AST、3精确SDK/库符号、323受保护文件及21更新隔离（20通过/1符号链接权限跳过）完成。未编译/部署/游戏实测。源码0.4.30包含IRIS_EQUIPMENT_STATE_079；当前bin/package/游戏DLL实际已由用户构建为0.4.29/078，纠正下方旧STATE待编译观察；当前仍保留这些DLL原字节。package ready=false/pending0.4.30，用户编译IrisArsenal.sln Release|x64/v100并退出游戏后执行UpdateMod.cmd。

详见[079原生调用链、修复、双备份和验证](docs/noncombat-equipment079.md)。下方历史状态保留。

---

# 2026-10-22 十六既有Hook性能审计078（源码0.4.29待用户编译）

Owner: Codex

按用户要求扩展16入口：原五选招/动作/反应、八远程适配、frame/safe及defence。只插入本地HookAudit/已有锁的可选观察，全部16Hook剥除诊断后的业务token与077备份一致，没有新Hook、线程、锁、装备缓存、原生调用或开火条件。

每128次全回调/进锁各自抽样；固定对齐64位原子累计，每60秒既有摘要输出32行audit_hook，含调用率、回调总墙钟、无所审计锁/进锁分类及锁获取/保护段。总墙钟含原生及嵌套，样本不直接相减/相加当净CPU或FPS。关闭总日志/性能/Hook审计时新增统计无原子/QPC。两份项目INI本次EnableHookAuditLogging=1，采样128和其他配置值保持。

16业务对照、6关闭路径AST、35抽样边界、076/原资格/多人及077全部专项、30关键函数/264受保护文件、10C++语法/3 Python AST、129包哈希、21隔离更新（20过/1权限跳过）完成。未编译/部署/游戏线程或FPS实测。

源码0.4.29包含076预筛+077原生环境组+078诊断；实际用户bin/包/游戏DLL仍0.4.26/075。ready=false且保留旧DLL身份，pending_version=0.4.29；用户编译IrisArsenal.sln Release|x64/v100，正常退出游戏后执行UpdateMod.cmd。详见[078字段、使用、验证和双备份](docs/hook-audit078.md)及[077环境射线修复](docs/native-terrain077.md)。下方为历史状态。

---

# 2026-10-22 三远程环境射线对齐原生077（源码0.4.28待用户编译）

Owner: Codex

用户同一露天建筑原生弩箭可射出，旧075日志794次在枪口处t=0撞BUILDING。重新核对实际EXE：GunClass::shoot 0x43A680和Harpoon单步0x437E30使用0x087FDE47；旧Iris环境全组0xffffffff。RayBlocker改为原生飞行组与调用者组交集，SDK精确射线/最近环境与原零命中规则保持；角色球扫掠/圆柱原组与半径、枪口、瞄准、伤害、安全窗口/预算/失败重试不变，没有新增线程/锁/Hook。

新增077一次运行标记及可关闭形体组/类型/trigger、光炮实际长度诊断；修正impact建筑显示标签，删除诊断节点后的三处战斗业务AST保持。旧日志没有实际shape组别，不能断言具体触发体或宣称原场景游戏已修复。

1152组过滤/3580环境最近规格、3010排序及原连续几何/预算重试通过；20关键函数/266受保护文件、10C++语法/3 Python AST、原资格/多人/076全部分支与21更新隔离（20过/1权限跳过）完成。只读原生二进制/AST/脚本，未编译/部署/游戏测试或FPS测量。

当前用户bin/package/游戏DLL仍0.4.26/075；源码0.4.28含076+077。包ready=false且保留旧version/文件摘要，pending_version=0.4.28；stage新增077合同门。用户编译IrisArsenal.sln Release|x64/v100，正常退出游戏后运行UpdateMod.cmd。详见[077证据、调用链、诊断和双备份](docs/native-terrain077.md)。下方历史状态保留。

---

# 2026-10-22 通用Hook锁前身份过滤076（源码0.4.27待用户编译）

Owner: Codex

正式选招先且仅运行原生一次，再直接检查当前武器实际FCS身份；非本武器不进入插件锁，候选在锁内复核。普通身体动画、无关格挡/受击通过原子发布的不可变私有技巧快照提前转原生；十招/原型NULL旧边界及远程动画要求身份保留。没有玩家限定、新角色缓存、线程或Hook。

按用户最后要求不写死重武器：取消既有SKILL_HEAVY固定类别，改用原生当前FCS类别匹配；现有双手演出医疗/站姿、武术/趴地回退保持。新增EnableHookAuditLogging默认0、HookAuditSampleEvery默认128；需开启日志/性能才能采集五入口原子累计和获取锁/保护段抽样墙钟，既有摘要输出，无逐调用I/O。

228 Hook、128选招、180动态类别、732资格、1152并发分支及7744发布交错规格通过；20关键函数正文/452受保护文件保持、10语法/4 Python AST和21更新隔离（20过/1权限跳过）完成。仅AST/脚本/静态验证，未编译或游戏实测，不能承诺FPS收益。

核对时用户bin/游戏仍0.4.26/075，文件保持；纠正下方075“待编译”为历史状态。当前源码0.4.27/IRIS_HOOK_FAST_076未编译，package ready=false并保留旧DLL身份；用户编译IrisArsenal.sln Release|x64/v100后退出游戏执行UpdateMod.cmd。原正式1.0封存保持。

详见[076调用链、配置、验证及双备份](docs/hook-fast076.md)。下方为历史状态。

---

# 2026-10-22 多持有者独立起手075（源码0.4.26待用户编译）

Owner: Codex

确认旧MaxActiveActors=1被正式近战Choose、远程PickRanged和Publish三处共用，导致日志3持有者起手峰值仅1。075移除正式十招跨角色名额门；当前持有者各按自身/原生状态起手，原8人登记容量、每角色状态、原生医疗回退、64查询、2.5ms/32医疗预算及特效/伤害保持。MaxActiveActors仅保留诊断原型含义。

实际1152组C++条件、2/3/8人同窗口及3旧源码反例、732原生资格、10份C++/H语法、12关键函数和141文件边界、21更新隔离（20通过/1权限跳过）验证完成。未编译或游戏实测，不声称新DLL已生效；当前游戏DLL/FCS/INI/清单保持。

源码版本0.4.26，包ready=false并记录075待编译；stage_package明确拒绝未含IRIS_MULTI_ACTOR_075的旧DLL。用户编译IrisArsenal.sln Release|x64/v100后正常退出游戏，再运行UpdateMod.cmd。无需额外改MaxActiveActors来解除正式招式串行。

详见[075修复、验证与双备份](docs/multi-actor075.md)。下方为历史状态。

---

# 2026-10-22 武器正式基础数值与两个独立动画补丁074已同步

Owner: Codex

武器项目package与游戏FCS均改为切1.44/钝1.2（此前测试值×10）、失血2.5、攻20、防10、室内0，穿甲0.5保持。统一修改平衡生产者与FCS作者并修正旧测试说明；47条其他记录、C++/DLL、伤害事件、特效和动画保持。两处清单FCS摘要已更新。

新建并部署IrisArsenal_IKEMEN_Patch（1种族）及IrisArsenal_EndPoem_Patch（97种族），各自仅追加十套既有动画集引用；ep_ikemen_Animation_Patch_My和End Poem MC_My原文件SHA保持。需用户在启动器勾选新补丁并放在对应原模组、种族及IrisArsenal之后；未改勾选、排序或存档。

实际FCS往返/逐字段、完整作者拦截输出、两处129运行文件哈希、20份男女骨架内部名/时长、两个补丁身份/最小字段/重复生成及三份Python AST通过，136受保护文件保持。未编译、启动游戏或实机测试，无需重编DLL。当前现有DLL已由用户编译为0.4.25并含072合同，下方073待编译描述为历史观察。

详见[074数值、补丁、双备份及验证](docs/weapon-race-patches074.md)。下方历史内容保持。

---

# 2026-10-22 翻滚深色序列帧火团已移除073（仅资源，上轮072仍待编译）

Owner: Codex

按用户最后澄清，只删除翻滚两份源pFireBall深色序列帧层（原层6/10），外球、闪光、小火星和共享贴图保持；活动层12→10。实际保留mesh块、全部曲线/材质正文及其他招式逐字比对通过，双视角20帧CPU前后预览已查看。没有改C++/DLL/Shader/伤害/动画/配置，没有删除贴图文件。作者末尾追加073，重建不会恢复；Update仍只组包和复制。

引用闭包、错误来源拒绝、幂等、3份Python AST、129运行构件哈希及21更新沙盒（20通过/1符号链接权限跳过）已执行，未游戏测试。游戏PID37440运行中，本轮未部署。

重新读取的bin/package/游戏DLL仍0.4.24、SHA256 c9c026347b5b9a41…，未含072合同；此前6cc9摘要为此前观察。源码072/0.4.25尚需用户编译，package保持ready=false；编译IrisArsenal.sln Release|x64/v100后正常退出游戏，运行UpdateMod.cmd同步。详见[073范围、验证与双备份](docs/roll-sphere073.md)。下方为历史状态。

---

# 2026-10-22 原生近战资格/回退072（源码0.4.25，待用户编译）

Owner: Codex

正式十招模式仅在原生站立重武器资格（当前重武器、原生双臂可用、正常姿态且非crippled）通过时私选；原生武术/趴地/其他及模糊混合类别保留。原生空且资格通过仍按专属距离选招；私选失败或故障回退原生。没有新增HP阈值或ImpactPoints。正在播放动作、后效、伤害、防御、远程和资源保持；显式诊断原型分支原字节保持。

732个实际源码AST分支、10份C++/H语法、SDK/链接库符号、函数/运行构件边界及21更新沙盒（20通过/1符号链接权限跳过）已执行。没有编译或游戏测试；初始化一次IRIS_NATIVE_MELEE_072可识别下次用户构建，包ready=false并拒绝旧DLL。

用户bin/package/已部署DLL仍0.4.24，SHA256 6cc9c858…，本轮未部署。须用户编译IrisArsenal.sln Release|x64/v100后正常退出游戏，运行UpdateMod.cmd。[072说明、验证与双备份](docs/native-melee072.md)。下方为历史状态。

---

# 2026-10-21 运行包清理070已同步（DLL0.4.24，视觉069保持）

Owner: Codex

只清理106个无引用材质声明、2个旧GPU入口/函数、2个无引用文件与17个作者死导入；22份开发证明CSV原字节迁到docs/pose-proofs，并同步生产/验证路径。全部C++/H、DLL、有效材质正文、模型/动画/有效像素、FCS、配置、事件/判定与生命周期保持。

全包154→130文件，减少6.13MiB。完整重建末尾按实际引用图清理，日常Update仍是原组包/复制流程。20份男女动画握点重算、有效对象正文/原数据SHA、失败不写入、幂等、全部Python与10份C++语法、21项更新沙盒及130文件部署校验通过。未编译或运行游戏，不能称游戏功能/FPS已实测。无需重编DLL。

保留诊断模式、完整重建旧作者、SDK/许可证/历史证据；一对参数不同的同名准星声明未擅自合并。详见[070清理与备份](docs/cleanup070.md)。下方保留历史。

---

# 2026-10-21 源爆炸069已同步（资源修订，DLL仍为用户编译0.4.24）

Owner: Codex

纠正下方068“待编译/游戏0.4.23”：用户已编译，bin/package/游戏DLL为同一0.4.24、SHA256 6cc9c858…，现有日志证实068。日志硬编码0.4.19前缀不能作版本判断。

本轮只修翻滚/钻天破视觉：源SubTex随机起帧/寿命步数循环、寿命和材质控制器、150尺寸键、独立alpha-LUT和Stokes主体统一源时钟。按用户要求透明化火球极暗冷却尾，不加曝光涂白；不改其他招式、C++/H、DLL、判定/伤害/事件和双翼球心。源ADDN334仍缺，未擅补常亮闪电或飞行层。

实际完成两视角28帧CPU对照（深色遮挡1853→148）、9输出重复、40材质闭包/词法、源时钟/容量和242文件边界。游戏退出后154文件完整同步/哈希通过；无需重编DLL。未编译HLSL、未启动游戏或作GPU验收，不能称完全复刻；详见[069说明](docs/source-burst069.md)。下方为历史。

---

# 2026-10-21 爆炸校准068（源码0.4.24待编译，游戏原0.4.23保持）

Owner: Codex

用户实机反例否定064/067的视觉达标结论。本轮仅三处爆炸素材校准：修正Fade Out Percent为开始点、火球源角速度和24/120/83/140尺寸键，私有VP不改其他招式共享Shader。R24/R120/R90、光刃、双翼球心、066圆环、所有健康/物理判定保持。

按用户后续澄清：翻滚/钻天破终结/全力尾击/火神命中/脉冲独立爆炸生成后统一游戏秒；地震shock与电脉electro_area保留动作攻速，弹体/持续光炮/蓄力附件不改。功能只变Blast的可视rate和Configure一次合同日志，无新线程/Hook或共享IndexData写入。

已实际查看两份新录像逐帧与原演示、三处两视角54帧CPU结果；10份语法、源键/淡出反例、14其他曲线块/19效果记录/其他运行资源逐字、10输出重复变换和150文件包哈希通过。没有C++/HLSL编译或新游戏GPU验证，不宣称实机达标；排序/SubTex/完整NiPSys等缺口见[068说明](docs/burst-calibration068.md)。

包ready=false，现有用户DLL0.4.23及游戏目录原字节保持。请编译IrisArsenal.sln Release|x64/v100后退出游戏运行UpdateMod.cmd。下方保留历史，CPU通过不再视作视觉验收。

---

# 2026-10-21 三招源特效067（源码0.4.23待编译，现有游戏DLL0.4.22）

Owner: Codex

只按实际HKX/PIE/ESP/NIF/ADDN链重建翻滚第二击、全力尾击与电脉视觉。翻滚用439C0/6051F的FireBall+0.1秒源延迟及824；全力用824+3F9ED/七ADDN64火浪；电脉用886 beam+824，成功事件重置效果年龄。光刃、064爆炸、066圆环门、伤害/物理/倍率/权重/线程保持。

包内男女根运动同为后翻52.465315、相对起点净后退44.085438游戏单位。范围保持R24/R90/R25，按真实源alpha/粒子亮相而非裁剪包围标定。CPU动态/12方向范围/24输出重复导出、10份C++语法和逐函数/字节边界检查完成；未作C++/HLSL编译或GPU游戏测试，不宣称像素1:1。

当前用户编译/部署的0.4.22和安装清单已只读核对保持。本轮067 ready=false，新资源不混旧DLL；请编译IrisArsenal.sln Release|x64/v100后退出游戏运行UpdateMod.cmd。[067来源/验证/限制](docs/source-effects-067.md)。下方为历史，不代表当前运行版本。

---

# 2026-10-21 圆环同步066（源码0.4.22待编译，游戏仍0.4.21）

Owner: Codex

用户游戏确认064圆环提前静止出现。现已只读本机Ogre导出实现证实：setIndexDataEndIndex(0)直接返回，旧隐藏无效，不能以声明或符号存在推断语义。

两个可视消费者改为实例custom9；小箍0/四圆环15..18旋转前由顶点程序完全裁剪，到同一旋转时点才显示且共用pose。保留原模型/材质像素/颜色/转速、其他技能/物理/伤害/线程。仅状态变化日志。

本机反汇编、逐帧边界、10份C++语法、材质参数闭包、143个函数对比、实际源纹理CPU前后图和动态预览完成；没有C++/HLSL编译或Ogre/GPU游戏验证。新066 Shader要求配套DLL：包ready=false，旧0.4.21被正确拒绝。当前安装游戏包/DLL完全保持，勿把现有游戏当066。

下一步：用户编译IrisArsenal.sln → Release|x64/v100，正常退出游戏后UpdateMod.cmd。详见[066说明](docs/drill-ring-gate066.md)。下方保留历史。

---

# 2026-10-21 不攻击修复065（资源修订，DLL仍0.4.21）

Owner: Codex

已确认实际运行064 DLL，SHA256 adbb50d9342c6da1e5b1c5cc52941f77fcdd9c27562a91fc34bd22b60c7490bf。钻天破私有源材质的16个未引号冒号名称触发Ogre继承解析错误，预热绑定失败使整个插件停用；不是选招或射程故障。

已修正28个声明及作者输出，材质名/网格/CSV内容仍一致；其他运行构件、C++/H与DLL保持。声明词法、引用闭包、作者循环重生成和基线哈希检查通过，未启动游戏/编译。更正064：CPU/数据验证未覆盖Ogre材质继承词法，不能证明游戏加载成功。详见[065说明](docs/no-attack065.md)。

已在确认游戏退出后运行现有更新入口，147个文件复制/哈希终验通过，游戏目录已同步065材质修复；DLL仍0.4.21且哈希保持。未启动游戏，攻击恢复须下次启动确认。下方保留历史状态，不再将“064待编译”视作当前事实。

---

# 2026-10-21 钻天破源圆环与终结爆炸（064源码0.4.21待用户编译）

Owner: Codex

现有项目/包内DLL经只读核实为0.4.20／063，SHA256 f6d1a2773e21f9c2fb2589aed609ec2e475ad71df6aac01471140769e8c5a3fe，尚无064身份。不得用旧DLL冒充本次源码；本轮未编译、部署或操作游戏。

外围红暗圆环确认是四张错开的透明面（15..18），单层无厚度，整组钻轴跨度约18.23；小金属箍0的厚度约0.692不代表外围环。生产显示从源1.633267999秒切换点开始，0和15..18共用钻头旋转。终结按实际ALS/Stokes/原版DragonRend/FireWave调用链重建为28可视层，固定双翼球心/R120，不增加弹道或伤害段。

已执行/查看源视频、动态与侧视CPU预览、10文件语法、实际序列化粒子路径与12方向火焰范围、94函数及基线对比、23份结果重复导出。源码、材质与资源闭包通过；GPU/游戏/MSVC仍待用户，未声称完全复刻或FPS改善。ADDN334在所查Elden插件及原版主文件无匹配，未误接33。详见[064说明](docs/drill-finisher064.md)和[验证](docs/validation-drill064.json)。

下一步：用户编译 IrisArsenal.sln → Release|x64/v100，正常退出游戏运行 UpdateMod.cmd。新时钟资源与064 DLL配套；日常更新脚本仍保持原复制流程。

---

# 2026-10-20 火神双源准星与脉冲原橙色扩散（063源码0.4.20待用户编译）

Owner: Codex

用户已实跑062/0.4.19；历史062“待编译”描述只代表当时状态。本轮0.4.20 / IRIS_SOURCE_MUZZLE_063尚未编译或部署，包内DLL仍是原062字节，ready=false。

火神恢复IrisAnim的anim.nif武器小组与anim1.nif人物大组，源5倍时钟循环旋转，原2.4/2.2秒寿命；不带入源3BA身体。脉冲移除通用准星，按用户后续方向接入IrisPlasmaShoot的824橙色扩散，原曲面/火花/纹理/三次独立时钟。只改两招视觉；实际瞄准、远程许可、Emit、伤害/物理和其他招式不变，不新增Hook/线程/锁。

源旋转241样本、三次源buffer、10文件语法、引用闭包和二次导出同字节通过；已生成并查看男女姿态CPU联系图及动态GIF。CPU不是游戏/GPU实测。具体来源、逐文件报告、备份及验证见[063说明](docs/muzzle063.md)。请用户编译IrisArsenal.sln Release|x64/v100，正常退出游戏后运行UpdateMod.cmd；日常Update流程保持复制，不绑专项检查。

---

# 2026-10-20 远程起手恢复（062源码0.4.19待编译）

Owner: Codex

用户实跑0.4.18/061出现远程不起手。已撤销061额外的“许可前选招/缓存目标相等”限制，以及本轮拟议的招式快照传递；恢复原工作版060的原生许可→选招→播放顺序。原评分、方向和起手参数保持；弹速匹配只用于真正Emit的瞄准值计算。061受伤筛选/直接接触/射程/日志保留，地形射线与角色球/柱、枪口及所有资源不变。

8项专项及10文件语法检查通过，起手控制块与旧版逐项一致；未编译、未部署或游戏验证。旧日志缺原生回调就绪明细，不能声称已确定该次故障唯一原因。新动画阶段诊断仅观察，不加门槛。请编译IrisArsenal.sln Release|x64/v100，退出游戏后运行UpdateMod.cmd。[详细说明](docs/ranged-start-062.md)、[实际验证](docs/validation-ranged-start-062.json)、[逐文件备份](docs/ranged-start-062-changes.json)。下方061提前选招描述已被本次明确撤销。

---

# 2026-10-20 原生资格与远程直接命中修复（061源码完成，待编译）

Owner: Codex

源码0.4.18 / IRIS_COMBAT_POLICY_061。三远程地形仍用中心射线；角色仍用火神/脉冲R4.5球扫掠、光炮R9平端圆柱，炮口/动画/FCS/倍率/范围/权重保持。近远程共用用户指定原生四项资格，不能受伤角色不吞远程弹体；直接物理接触身份并入同段爆炸去重名单。原生预判按实际弹速和攻速匹配；即时光炮无慢弹体提前量；实际飞行上限采用FCS10000，区分无接触消退和碰撞爆炸。事件诊断不再首次N条永久静默，日志仍可配置关闭。

12项专项、16384组资格/4000组排序与10文件Tree-sitter语法检查通过；138个非INI/清单包内文件（包括旧DLL）保持。未编译、部署或游戏实测。当前已部署DLL仍为用户编译的0.4.17/060，下方旧060“游戏0.4.16/059”仅代表当时历史。请编译IrisArsenal.sln Release|x64/v100，再正常退出游戏运行UpdateMod.cmd；日常更新仍不重建资源、不绑定历史源码回归。

原生受阻走位和逐发重做射击许可不在本次改动内，不能承诺所有地形空射已消除。[详细修复与边界](docs/native-combat-061.md)、[验证](docs/validation-native-combat-061.json)、[逐文件报告及双备份](docs/native-combat-061-changes.json)。

---

# 2026-10-20 三远程共享原生瞄准（060源码完成，等待编译）

Owner: Codex

火神炮、脉冲之焰、极致驱动保留当帧实际附件炮口 Muzzle(weapon)+a.origin，并同步给适配Gun；瞄准点统一读取原生 currentAimPos，弹体/光柱的画面与角色碰撞共用同一份方向值。不抬高、平移或锁住炮口，不从头部发射。目标丢失仅在当前动作有效期保留最后原生瞄准值，完成或读档清理。

7项专项检查通过；10个C++/H文件Tree-sitter语法检查通过（非MSVC编译）；15个战斗函数、14个远程函数及139个包内资源/旧DLL摘要保持。没有新增Hook、线程或物理查询。尚未编译、部署或游戏实测；当前游戏DLL仍为原0.4.16/059，本次源码版本为0.4.17/060。先由用户编译 IrisArsenal.sln / Release|x64 / v100，正常退出游戏后运行 UpdateMod.cmd；旧DLL会被060身份检查拒绝。

本次仅统一数据源；原生起手许可到连续发射之间的受阻反馈、重定位走位尚未改动，不能据此声称所有隔地射击问题已解决。实现/验证见 docs/shared-aim-060.md。

---

# 2026-10-19 日常Update已简化并实跑成功

Owner: Codex

UpdateMod不再重建动画/特效，也不运行历史源码回归。只检查用户已编译DLL与已有包的必要构件/文件引用，组包，双备份旧目录，清空并完整复制，终验SHA256。开发完整验收仍可单独运行stage_package.py。Screenshot function:Emit来自此前仍绑定的历史回归，不是复制失败；已从日常更新调用链移除。

已实际调用更新main，并在阻断verify_prototype/rebuild_package模块导入的条件下完成真实部署；140文件与package一致，DLL确认包含aim_mode=target_body瞄准修复。没有代编译或启动游戏。证据：D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-Iris-SimpleUpdate-20261019-230359。以下为历史记录。

---

# 2026-10-19 极致驱动恢复旧版目标瞄准（源码已改，需重新编译）

Owner: Codex

本次仅将Emit(kind8)恢复为与火神炮相同的Target身体瞄准点减实际炮口位置，每次独立脉冲重新计算；光柱和角色柱体共用该方向。肩持动画/准星/蓝火/光流资产、R9、长度10000、四段倍率及其他九招保持。不新增线程、Hook或骨骼/角色转向写入；不再以动画炮轴强制决定弹道，日志增加aim_mode=target_body。

059专项及C++语法检查通过，所有包内资产/旧DLL与游戏DLL保持，旧DLL因早于源码被正确拒绝；package ready=false。版本/资源格式仍0.4.16/059，用户需重新编译IrisArsenal.sln → Release|x64/v100，然后退出游戏运行UpdateMod.cmd；只跑更新脚本不能替代编译。未代编译或游戏实测。

证据和逐文件双备份：D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-Iris-RestoreDriveAim-20261019-225309-cb31f4。以下为历史状态。

---

# 2026-10-19 UpdateMod改为全量清空替换，已实际安装0.4.16

Owner: Codex

UpdateMod现在先准备/校验完整package，再将游戏mod旧目录完整双备份、清空内容、完整复制并逐文件核对；失败恢复整目录。取消逐文件白名单、旧INI合并和旧info保留，配置以distribution/IrisArsenal.ini为准，旧日志进入备份。更新入口不再改写全局图标缓存。

已修复041校验依赖旧游戏资源、059历史断言误拒绝新DLL两个问题。整条源资源/动画/FCS校验和组包通过，30项隔离测试29通过、1项因符号链接创建权限跳过。已实际部署0.4.16 / IRIS_DRIVE_REBUILD_059，140文件与package哈希一致，D/E完整旧目录备份复核一致。未修改C++，未编译，未启动游戏；原UTF-8及换行保持，中文/AST检查通过。

[更新、备份、恢复和验证](docs/clean-update-20261019.md)。源码当前无需重编译；以后正常退出游戏后双击UpdateMod.cmd即可。下方为历史记录，旧白名单/保留INI说明不再适用。

---

# 2026-10-19 更新脚本修复：059 DLL已由用户编译，重新执行UpdateMod即可

Owner: Codex

已核对bin/Release与package的0.4.16 / IRIS_DRIVE_REBUILD_059 DLL及ready=true清单。截图失败原因为同步白名单遗漏CREDITS-drive059.txt；现已精确放行该文件，保留路径/SHA256/双备份/回滚保护，未知署名文件仍拒绝。

旧脚本用真实包复现同一报错且未开始写目标；修复后真实包在隔离mods目录140项完整校验通过，24项更新/IO测试通过。仅修改Python同步脚本、沙盒测试和状态文档；没有修改C++/DLL/资源，也没有写真实游戏目录。无需重新编译，正常退出游戏后重新执行UpdateMod.cmd。

双备份与验证见当前会话Task-Iris-UpdateCredits059-20261019-215332-fa239e。下方“未编译/DLL057”是此前交付时的历史状态，不代表本次已核对的用户编译产物。

---

# 当前：0.4.16 / IRIS_DRIVE_REBUILD_059 极致驱动重做，待用户编译

Owner: Codex

本轮仅极致驱动：PA10站立肩持；真实EXanim1红蓝准星旋转/展开；源枪口蓝光/FireWave；授权CC0纹理三维光流。角色柱体R9，长度10000保持，枪口/轴/物理与可视共用同一快照。其他九招规格、120运行文件和16原医疗/安全函数摘要保持。没有新增Hook、线程、全局移动或运行时骨写入。

完整非编译回归、真实四份动画二次导出一致及22沙盒通过；CPU资产预览已执行。现有bin/package/游戏DLL仍为057/0.4.14；新源码与资源未编译、未部署，package ready=false。新版本请编译 IrisArsenal.sln / Release|x64 / v100，退出游戏后执行UpdateMod.cmd。

证据、来源、限制、备份与逐文件报告见[059说明](docs/drive059-rebuild.md)。不冒称游戏/GPU/FPS实测；正式1.0备份及暂停轮询不动。

---
以下为历史记录：

# 当前：0.4.15 / 058火焰2倍速、电脉枪口共线源码待编译

Owner: Codex

用户已编译部署057/0.4.14，bin与游戏DLL同SHA256 `14f3ee85645fe3079ceb67d7657f9f7480864338dec64f5bfc6034e935cefe0e`。下方旧057“未编译”条目只表示当时交付历史。本轮058只准备源码，DLL保持057，package ready=false；未编译、未部署、未操作游戏。

火焰翻滚/全力末击原火焰8层视觉2倍；钻天破只加速后8层火相，前5层蓝相和0.56切换点保持。源曲线和GPU粒子共用层年龄，寿命相应缩短；伤害/演员时序保持。电脉光柱与四次R25球形事件共用当帧原生枪口轴，轴向前20不变；不写角色位置、朝向或骨骼，不增加线程/锁/Hook。全部原运行资产保持。

实际执行验证和CPU预览见[058说明](docs/fire-cannon-058.md)、[完整验收](docs/validation-fire-cannon-058.json)。新版本需用户编译 IrisArsenal.sln Release|x64/v100，再正常退出游戏执行UpdateMod.cmd。正式1.0备份及暂停的轮询保持，不声称游戏/GPU/FPS实测。

---
以下为历史状态：

# 当前：0.4.14 / 057三远程碰撞分离源码待编译

Owner: Codex

更新/纠正旧条目：用户已编译部署0.4.13/056，bin/package/游戏DLL同SHA256 b8fcd19fb79ec209fe05efc7f73d21b452e8abf670a6c01220fa982dc483fcf7。本轮仅准备057/0.4.14源码；旧DLL不变、package ready=false，尚未编译/部署/游戏实测。

火神/脉冲：有限地形射线 + R4.5角色连续球扫掠，两份结果完整后过滤友军并比较统一TOI，同距墙优先。光炮：环境扫掠改有限射线，R4.5平端圆柱与绘制共同截至墙前。原伤害/范围/倍率/敌我、64查询/16作业预留、2.5ms/32医疗、暂停与后效保持。没有新增线程、锁、Hook、全局组改写或跨帧shape指针。飞弹不足2查询预算只轮转保留pending，失败两份结果都不消费。

完整非编译回归、3010组057顺序规格、056服务顺序、10份C++语法树及22项更新/IO沙盒通过；均不是游戏/PhysX/FPS实测。用户编译 IrisArsenal.sln Release|x64/v100，退出游戏后执行UpdateMod.cmd。详见[057说明](docs/ranged-ray-057.md)、[验证](docs/validation-ranged-ray-057.json)。正式1.0快照保持，不恢复轮询。

---
以下为历史状态：

# 当前：0.4.13 / 056同步合批源码待编译

Owner: Codex

更新/纠正前一状态：用户已编译并部署0.4.12/IRIS_COLLISION_DAMAGE_055，bin与游戏DLL同SHA256 77ba30b05fddd032f03dcb6072d56b5c6477cfa3c50fef76793a1dea397b7009；真实PID37900日志20261018-231436已验证该身份。下面旧“055未编译/仍0.4.11”是交付时历史状态，不再表示当前安装。

本轮按用户授权优化：同Job/同安全窗口静态胶囊2～8路径合批，原生精确窄相、首8批/每256批原查询对照、容量/失败回退；预留原轮路径成本，额外验证只用剩余预算，不改变移动目标原服务帧。移除055零命中胶囊缓存；慢受击增加可配置1ms诊断。没有新线程/Hook/全局物理回调/移动锁。原倍率/范围/权重/护甲/部位/经验/敌我和2.5ms/32 FIFO保持。

项目0.4.13/IRIS_CAPSULE_BATCH_056尚未编译或部署，package ready=false，现有DLL保持0.4.12。正式1.0归档不动。用户编译 IrisArsenal.sln Release|x64/v100后退出游戏执行UpdateMod.cmd；无需重做资源。详见docs/capsule-batch-056.md及validation-capsule-batch-056.json。没有实测FPS提升，不恢复轮询。

---
以下为历史状态：

# 当前：正式版1.0已封存；0.4.12 / 055优化源码待编译

Owner: Codex

2026-10-18 21:10定时任务已按先封存后优化执行。正式版1.0对应实际0.4.11/054，编译/包/游戏DLL同SHA256 57bc5999c31daa6940fac699adf8f665d913bf768f4416b937b20f909ba45778；完整归档 `D:\CodexBackups\Iris-Formal1-Optimize055-20261018-211300-34f16b-Formal1.0-v2`，含经验/恢复/清单。项目包与安装INI语义一致，原文分别保存。

055工作版：完整身份的小名单/哈希去重、list splice免复制轮转、容器交换入队、单Tick精确胶囊缓存、圆柱临时缓冲复用；追加可关闭碰撞/医疗分项和采样等待诊断。64查询、2.5ms/32医疗、40ms软目标、全部范围/伤害/权重/防御保持；没有增加查询延后预算或后台线程。

完整非编译资产/行为回归、055密集规格、语法和22项更新/IO测试已执行，详见docs/validation-collision-damage-055.json及本任务validation.json。不得把Python/语法或旧DLL运行当成055实机。当前游戏和bin的DLL仍0.4.11，package ready=false；新标记IRIS_COLLISION_DAMAGE_055拒绝旧产物。用户编译 IrisArsenal.sln / Release|x64/v100，再退出游戏执行UpdateMod.cmd；本任务未编译、未部署、未操作游戏、未恢复轮询。

[正式版入口](docs/formal-release-1.0.md) · [055实现/日志/限制](docs/collision-damage-055.md)

---
以下为历史状态：

# 当前修正：054更新校验不再假定编译输出为旧DLL

Owner: Codex

用户已编译0.4.11（bin/Release，2026-10-18 18:27:33）；更新在资源验收的“旧DLL被当作054”断言中止，故当时package与游戏DLL仍为0.4.10。根因是test_physx_compat054错误固定本机输出必须为旧版，并把该旧DLL哈希列入资源不变量。现移除这两个不随编译成立的前提，保留所有非DLL资产保护；旧/新代码合同的隔离用例和实际UpdateMod/stage入口PE/合同/源码时间门保持。

只改Python验收和说明，无C++/DLL改动，无需重编译。完整非编译验收、真实0.4.11编译产物的入口检查及旧/新DLL隔离用例执行后，以本次任务validation.json记录为准。未自动部署；用户重跑UpdateMod.cmd，直到“更新成功”才表示同步完成。

---

# 当前准备：0.4.11 / 054 PhysX后续修订尝试

Owner: Codex

用户授权修改PhysX兼容策略；native/NativeMultiContact.cpp取消完整文件版本必须等于2.8.4.6的条件。最低2.8.4.6、同2.8.4 Nx接口族的后续修订允许尝试，核验NxGetPhysicsSDK导出并沿用每次场景同SDK检查；3.x/Px及未适配其他接口族不调用未知虚表。新增一次性physx_compatibility，明确区分候选和运行验证，缺元数据/导出则记录真实原因。

2.5ms预算、32次配置、40ms软目标、全部18 Hook、碰撞查询函数/形体/伤害/视觉与FCS保持。代码合同054、版本0.4.11；资源修订仍053。package仅标待构建ready=false，游戏目录仍为已部署0.4.10，不同步旧DLL伪装修复。按Skill不代编译；用户编译 IrisArsenal.sln → Release|x64/v100 后执行UpdateMod.cmd。

[兼容范围与验证边界](docs/physx-compat-054.md)。非2.8.4.6的真实SDK/游戏尚未测试；不能声称兼容任意更高主版本。旧32配置调优和历史交付如下。

---

# 当前配置调优：0.4.10 / 每批伤害上限32

Owner: Codex

用户2026-10-18要求保持2.5ms预算，将每批原生伤害结算上限12→32。distribution、package和游戏INI已一致设置，40ms等待软目标、FIFO、安全门及其他参数保持；两个清单仅更新INI哈希。现有0.4.10 DLL支持该配置，无需修改C++或编译。053原有12次模型继续覆盖可配置边界，并增加32次用例。新配置需下次启动游戏读取；调整后的群伤延迟与FPS尚未实测。

已只读确认旧上限12的真实运行PID36900使用0.4.10/053，1332次applied、队列峰79、418次超过40ms、最长385.65ms；这不是新32配置的运行证据。历史源码交付记录保留如下，不能再将其中“仍为0.4.9”当作当前部署。

---

# 当前准备：0.4.10 / 053医疗预算与Falling Sun测试武器

Owner: Codex

保留现有碰撞和去重；医疗默认预算2.5ms、等待软目标40ms、次数保险12，均有INI配置；最早入队先处理，超目标不丢弃或超预算补扣。新增压力/让出计数及手动分析明细。武器切/钝按原版Falling Sun×1.2×0.1测试，约0.144/0.12；攻击+15、防御+8、穿甲50%，其他属性/视觉/事件倍率保持。

23组非编译回归、12组新调度规格及22项原同步/IO测试通过；FCS仅原位编辑五数值，128项其他运行资源保持。当前实际安装仍为用户已编译部署的0.4.9/052，本轮未编译部署或实测FPS。请用户编译 **IrisArsenal.sln → Release|x64/v100**，正常退出游戏后执行 **UpdateMod.cmd**。新合同拒绝旧DLL，个人INI值保留，轮询关闭。

[本轮配置、数值、日志与验证边界](docs/queue-balance-053.md) · [逐文件/双备份](docs/queue-balance-053-files.json)

---
以下为历史记录：

# 当前准备：0.4.9 / 052清理与可配置长期日志

Owner: Codex

移除无消费者heavy网格和6张贴图、不可达wall分支/无用参数及旧重复统计，修正过期注释；保留20个有效效果，十招与58次事件、现有伤害/范围/权重/防御策略及18个hook保持。新增独立IrisDiagnostics单元，提供可配置日志总开关、性能与资源阶段开关、汇总/写盘间隔、慢样本阈值；记录实际运行身份、帧/查询/医疗/资源加载耗时、资源数量与峰值，日志无总行数限制。AnalyzeLogs.cmd供手动只读分析，轮询仍关闭。

22组非编译回归、10份C++/头语法检查、13项原同步测试及9项新增回滚/解析测试通过；没有执行编译、游戏或GPU/FPS验收。当前游戏仍为0.4.8/代码050/资源051，本轮未部署。请用户编译 **IrisArsenal.sln → Release|x64 / v100** 后正常退出游戏，执行 **UpdateMod.cmd**；旧DLL会被拒绝，个人INI保留。

[清理、日志配置、调用链、验证边界](docs/cleanup-audit-052.md) · [逐文件与双备份](docs/cleanup-audit-052-files.json)

---
以下为历史记录：

# 已部署：0.4.8 DLL / 051电脉源火焰与火神枪口修复

Owner: Codex

已核对原演示92～96秒、137～140秒和两条真实ESP/NIF/MPS引用链；电脉按源三角面、原UV/LUT/alpha/falloff发亮面积重新标定，整体约为050的1.513倍，原形状/颜色/四层相对关系与275火花保持。枪口原pFireGlow第二颜色区间宽度为0，原引擎保持中间暗色；旧移植误切到高亮终色，且把淡出开始百分比当作时长。已用本机滚5只读Update代码确认并修正该枪口独立Shader，不改其他招式共享粒子。

真实产物CPU前后预览、颜色零区间负例、完整非编译验收与13项更新测试通过。已安全同步7文件，139项核验，DLL仍为用户编译的0.4.8/050代码合同，资源051；无需重新编译。坐姿/动画/FCS/贴图像素/INI/伤害参数未变。更新脚本会保留本轮修复。未启动游戏，GPU/FPS未实测；轮询保持关闭。

[源文件、原引擎分支、前后预览及验证边界](docs/source-effects-051.md) · [实际同步与双备份审计](docs/source-effects-051-delivery.json)

---
以下为历史记录：

# 当前准备：0.4.8 / 050真实表面坐锤与电脉高度修复

Owner: Codex

此前049把源骨骼原点关系当作坐姿验收，未检查实际身体蒙皮；该验收标准错误，已由真实下臀顶面接触检查替换。驱动/电脉共用既有PA6，现按实际男女身体与实体锤面离线校准四份动作，保留双手握点、根运动和骨长。电脉原有扩散层中心在脚底导致大部埋地；050让特效与R25伤害球共用实际枪口高度，前方20、四段倍率保持。

已运行实际网格蒙皮多视角预览、192帧实体表面接触、旧049失败负例、真实源纹理/材质/曲线的CPU像素与地面遮挡对照，以及完整非编译和13项更新脚本测试。未运行GPU或编译，不以CPU预览证明最终游戏画面。游戏目录仍是0.4.7/049，本轮未部署。请编译 **IrisArsenal.sln → Release|x64 / v100**，退出游戏后运行 **UpdateMod.cmd**；新代码合同会拒绝旧DLL。轮询保持关闭。

[原因、修改、真实预览与验证边界](docs/surface-050.md) · [交付审计](docs/surface-050-delivery.json)

---
以下为历史记录：

# 已部署：0.4.7 DLL / 049库存长图标、坐锤接触、电脉源范围

Owner: Codex

已实跑完整UpdateMod并同步：139文件核验/11文件写入，原生当前图标缓存与mod/icons一致。图标UI沿长度排版到493像素；驱动/电脉原PA6坐姿段按源Pelvis与WEAPON接触关系离线校准，双手与抬高枪口保持；电脉补回原275火花/原Glow billboard，范围与光柱统一源标尺。DLL/C++/HLSL/FCS均未改，无需编译；当前INI保留。完整非编译/13项同步与缓存边界测试通过，实际GPU观感待用户确认。未启动游戏、未恢复轮询。

[本轮来源、边界和验证](docs/source-alignment-049.md) · [实际部署核验](docs/source-alignment-049-delivery.json)

---
以下为历史状态：

# 已部署：0.4.7 / 048修复完整更新阻断与旧图标缓存

Owner: Codex

用户确已执行UpdateMod；相同FCS值的字段顺序漂移触发严格摘要门，导致只重建未部署。已修正作者顺序、不放宽门，并完成实际两次FCS重建回归及整条package-only流程。用户确认退出后，完整0.4.7部署成功：138文件核验/17文件写入；DLL匹配用户编译产物；四份新射击动画与枪口1.5倍资源已进游戏。三远程入站保护/电脉源范围特效已随包更新；图标新FCS生效，两份旧缓存双备份后删除，下次原生重建。未启动游戏/未实机测画面或FPS；不需再编译。

[失败原因与实际同步记录](docs/icon-update-repair-048.md)；轮询保持关闭。

---
以下为历史状态：

# 当前准备：0.4.7 / 远程抬枪、受击保护、电脉源范围与原生图标

Owner: Codex

火神/极致驱动以脚底平面标尺抬高实际枪口至1.5倍，离线双手IK、原生root保持；三远程新增当前原生片段入站ImmuneHitReactions，出站格挡/闪避特殊处理仍关闭。补齐原$IrisBeam的CAST824→ShoutAreaExplosionWarm0源范围效果，固定起手朝向，前20/R25与四个健康事件保持。FCS校准原生图标，完整更新后双备份仅本武器旧缓存再原生重建。

完整非编译验收、3200入站边界规格组合、12项隔离同步与缓存安全验证通过；UTF-8/BOM/换行保持。游戏目录与DLL未修改，当前部署0.4.6。0.4.7 / IRIS_HEIGHT_REACTION_CANNON_ICON_047待用户编译Release|x64/v100后退出游戏运行UpdateMod.cmd；ready=false；未实机或测FPS；轮询保持关闭。

[本轮实现与限制](docs/release-047.md) · [验证](docs/validation-0.4.7.json) · [逐文件双备份](docs/release-047-files.json)

---
以下为历史记录：

# 当前准备：0.4.6 / 三远程原链测试与玩家新参数

Owner: Codex

火神/脉冲/光炮均不注册额外防御上下文，消费端再次排除远程；保留原始返回值和blocked/missed统计，未迁移伤害入口。翻滚两段新增破防闪；十招58倍率、7起手区间、权重按用户最新表写入配置。源特效/半径/落点/事件/时钟/入站免疫保持。

游戏INI仅预置本轮明确数值，其他个人键保留；游戏DLL/资源未部署。0.4.6 / IRIS_RANGED_DEFENCE_TEST_046待用户编译Release|x64/v100，退出游戏后UpdateMod.cmd。完整非编译验收、140防御结果策略模型、58段数值/7组距离/10权重核对与12项配置同步测试通过；不把模型检查当实机结论；轮询关闭。

[本轮参数与测试说明](docs/balance-046.md) · [逐文件备份](docs/balance-046-files.json)

---
以下为历史状态：

# 当前准备：0.4.5 / 十招逐段伤害与近战参数配置

Owner: Codex

58次独立倍率（近战31、远程27），7组私有FCS起手距离可覆盖/-1继承；七近战破防闪策略；火神移除额外防御门，三远程不开放该开关，六招特效近战的转格挡/受击免疫分别可配。近战默认行为保持044；纠正脉冲/光炮的近战防御桥接遗漏；几何、落点、源事件/特效/时钟保持绑定。参数表见docs/move-parameters-045.md。

完整非编译检查、400保护组合/48距离继承模型/13项Win32与CRT读取边界及12项隔离同步测试通过；源代码0.4.5/IRIS_MOVE_PARAMETERS_045，042资源合同保持。未编译、未部署、未实机；ready=false。用户Release|x64/v100编译后退出游戏UpdateMod.cmd。以后个人配置修改游戏INI，重启即可；更新保留个人键。轮询保持关闭。


[完整参数表](docs/move-parameters-045.md) · [静态验证](docs/validation-0.4.5.json) · [本轮逐文件双备份](docs/move-parameters-045-files.json)

---
以下为历史状态：

# 当前准备：0.4.4 / 六招近战全部普通受击反应免疫

Owner: Codex

六招近战（翻滚/螺旋飞舞/地震/钻天破/全力爆发/电脉加农）共用043有效原生窗口，免疫小僵直与大踉跄。扩展既有_startStumble钩子，不新增钩子（仍18），不改伤害；保留一次_getHit(false)原生记账。三连击和三招远程保持原生，死亡/昏迷/倒地/失效/加载等仍正常退出，不强播或锁坐标。

完整非编译、980受击流水/75边界、043格挡回归与11同步测试通过。原资产/旧DLL和实际游戏基线未改。0.4.4/IRIS_MELEE_REACTION_044待用户编译，042资产格式保持；ready=false。编译IrisArsenal.sln Release|x64/v100，退出后UpdateMod.cmd。实际C++/游戏/FPS未验收，轮询关闭。

[本轮说明](docs/melee-reaction-044.md) · [验证](docs/melee-reaction-044-validation.json) · [逐文件双备份](docs/melee-reaction-044-files.json)

---
以下为历史状态：

# 当前准备：0.4.3 / 六招近战防御接管保护

Owner: Codex

除破坏之锤三连击外，六招近战仅在有效原生动作内拒绝主动格挡检查；私有技巧motionStops延到归一化1，原生结束门保持。只新增一个SDK地址式钩子，总18；不逐帧回写战斗状态、不重播动画。普通三连击和三招远程、伤害/受击/攻速/事件/原资产保持。原钻天破踉跄保护不扩展。

完整非编译与440组合/14边界专项、11同步测试通过；135原包文件和实际游戏基线哈希未变。0.4.3/IRIS_MELEE_BLOCK_043代码待用户编译，042资产格式保持；ready=false拒绝旧DLL。请编译IrisArsenal.sln Release|x64/v100，退出后UpdateMod.cmd。实际AI/游戏/帧率未验收，轮询关闭。

[本轮说明](docs/melee-block-043.md) · [验证](docs/melee-block-043-validation.json) · [逐文件双备份](docs/melee-block-043-files.json)

---
以下是历史状态：

# 当前准备：0.4.2 / 042-TenMoves

Owner: Codex

全力末击独立full_blast按原R90校准，3.202965102倍；火神原五层枪口补17点源尺寸和三层真实角速度，专用52字节声明，不换贴图。新增近战电脉加农(源坐锤四脉冲，前20/R25/各1倍，FCS0～45)、破坏之锤(用户确认三次纯持械、各1倍，无独立特效，FCS0～25)，INI新增两权重默认1。原八招规格逐值不变，方向/移动仍原生；17钩子、物理/医疗预算保持。

完整非编译和11同步测试通过；20份动作、20FX/12曲线。实际用户游戏0.4.1/125清单哈希匹配，本轮未部署。042 ready=false拒绝旧DLL。用户编译IrisArsenal.sln Release|x64/v100后退出游戏运行UpdateMod.cmd。C++/HLSL/游戏/GPU/FPS未验收，轮询关闭。源NiPSys Drag/完整随机轴仍有限适配；旧drive与新电脉共用源片段的身份事实见本轮说明。

[说明](docs/ten-moves-042.md) · [证据](docs/ten-moves-042-evidence.json) · [逐文件双备份](docs/ten-moves-042-files.json)

---
以下为历史，不代表当前待部署状态：

# 当前准备：0.4.1 / 041-RangeMetal

Owner: Codex

用户要求范围依据代码/素材；录像只确认症状。按实际原火焰粒子/纹理alpha/LUT与网格亮相校准，钻天破火相统一放大2.470154664倍，离线12方向主体95%轮廓至少蓝相3/4；翻滚独立roll_blast放大3.202965102倍匹配原R24。蓝相/全力爆发基准火焰保持字节不变。源深灰002/白镜面逐形状保持，修复暗部底色和环境镜面适配，未伪造新纹理/发光色。

18FX/10曲线；倍率、物理球、动作时序、17钩子保持。完整非编译验收与11更新脚本测试通过，未编译C++/HLSL、未实机/FPS。实际游戏是0.4.0，124文件清单哈希均匹配，未部署。041 package ready=false，旧DLL拒绝混装。请用户编译IrisArsenal.sln Release|x64/v100，退出游戏后UpdateMod.cmd。轮询保持关闭。

[本轮说明](docs/range-metal-041.md) · [来源/范围数据](docs/range-metal-041-evidence.json) · [逐文件/双备份](docs/range-metal-041-files.json)

---
以下为历史状态，不代表当前游戏部署：

# 当前准备：0.4.0 / 040-SourceFire

Owner: Codex

本轮按用户指定先看原演示视频，再查HKX/INI/ESP/ADDN/NIF。FullBust_End真实火焰是VoiceFlameWaveProject03与ADDN64七对象/两MPS；火神枪口NAM1→ADDN09五原层。039通用火球/八象限散布路径已替换。钻天破蓝相/两翼R120单次5倍保持，翻滚共用实源火浪；全力爆发第三刀一次R90球/3倍，前两刀刃线保持；枪口不加伤害。

完整非编译验收及11同步脚本测试通过；未编译/未实机/未测FPS。实际游戏0.3.9清单哈希均匹配，未部署。新package ready=false/拒绝旧DLL；请用户IrisArsenal.sln Release|x64/v100编译后，退出游戏运行UpdateMod.cmd。原湍流/受控力/折射等缺项见说明，不声称1:1或完整体积火焰。轮询保持关闭。

[本轮说明](docs/source-fire-040.md) · [来源/状态](docs/source-fire-040-evidence.json) · [逐文件/双备份](docs/source-fire-040-files.json)

---
以下为历史记录，不代表当前游戏状态：

# 当前准备：0.3.9 透明火焰与重复终结修复

Owner: Codex

用户038真实运行已确认。日志cast13→14、15→16在同一8秒尾帧重放全部12事件且终结重复applied=2；039修正周期认领，不能只把新开始通知当成已回零。蓝相减遮挡，终结/翻滚共享原生火球32帧（256像素/帧）、120火星和三维涡流，去掉49张大火焰卡片。R120、倍率/事件数/其他招式参数保持。

完整静态/序列化/八招周期模型/11更新测试通过，未编译、未实机；实际游戏仍038且清单哈希未变。请编译IrisArsenal.sln Release|x64/v100，退出游戏后UpdateMod.cmd。新包ready=false，旧DLL拒绝门有效；轮询关闭。

[本轮说明](docs/fire-039.md) · [验收](docs/validation-0.3.9.json) · [逐文件/双备份](docs/fire-039-files.json)

---
以下为历史记录：

# 当前准备：0.3.8 / 038-R120 两翼中心直接爆炸

Owner: Codex

用户明确终结没有弹道：已改为原两翼完整几何中心的中点直接引爆，单次球形R120/5倍伤害。115采样中心流与原翼片同源/同钟；原蓝闪→火焰爆炸，原151粒子加98个有限空间覆盖粒子，保守裁剪边界不再缩小显示范围。倍率/敌我门/其余七招战斗参数保持。

非编译完整验收、真实纹理alpha多视角覆盖模型、11项更新测试通过。C++/HLSL未编译，未实机，帧率与最终观感待测。实际三处DLL仍用户037且同字节，游戏037-v2的118清单文件未改；新包ready=false，拒绝旧DLL混装。

下一步：用户编译 `IrisArsenal.sln / Release|x64 / v100`，保持游戏关闭后运行 `UpdateMod.cmd`。轮询关闭。

[本轮说明](docs/drill-r120-0.3.8.md) · [非编译验收](docs/validation-0.3.8.json) · [逐文件双备份](docs/drill-r120-0.3.8-files.json)

---
以下为历史记录，不代表当前待部署状态：

# 当前：0.3.7 / 资源037-v2 终结可见性已修复

Owner: Codex

用户实际037已确认。修复透明尾压缩、源相机闪光、原粒子尺度/alpha、LUT和包围球；无需重编译DLL。非编译验收/11项同步测试通过，实际GPU观感待用户测试。已在游戏关闭后部署资源037-v2，119文件哈希验证，DLL保持原字节037。轮询保持关闭。

[本轮说明](docs/drill-visibility-037-v2.md)

---
以下为历史记录，不代表本轮部署状态：

# IrisArsenal 0.3.7 源翼片与两相终结已准备

Owner: Codex

原EXDrill2严格单骨10形状、AnimObjectA/B开合和源金属；原ALS电离(0～0.52秒)→原SW_FireExplosion六发射器(0.56秒起)，151有限粒子。16FX/8曲线；18骨架/FCS记录不变，终结一次R60/5倍，17钩子不变。

完整非编译和11更新脚本测试通过。未编译、未部署、未启动游戏；实际bin/package DLL与游戏仍用户036。游戏106文件未改，ready=false阻止混包。用户编译Release|x64/v100后退出游戏，运行UpdateMod.cmd。

更正先前ALS缺失：实际在依赖meshes/ALS。说明及双备份见docs/drill-finisher-0.3.7.md。轮询关闭。

---
以下为历史观察：

# 2026-10-17 一键恢复/更新已交付

Owner: Codex

package 与游戏 IrisArsenal 目录均被删空；新增 UpdateMod.cmd + tools/rebuild_package.py + tools/update_mod.py，并修复两个旧入口。独立 distribution 模板保证从空包恢复。修正旧共享纹理测试对已去重PNG的依赖，改为直接核验原DDS像素。

用户已编译的0.3.6（IRIS_EIGHT_036，560640B）已实际通过 UpdateMod.cmd 部署至游戏 mod，106 文件终验成功。11 个同步/失败回退测试和完整资源非编译验收通过；C++与HLSL未由agent编译，游戏未启动，实机仍待测试。双备份与逐文件报告见docs/one-click-update-validation.json及docs/update-runs。游戏原目录为空，本次无旧游戏文件备份。轮询保持关闭。

---
以下历史状态只代表各次记录时的观察：

# IrisArsenal 0.3.6 透明终结、升腾火焰与重武器

本轮：去掉钻天破误绘的不透明折射球壳，终结保留8透明层；翻滚新增独立完整火焰/点火，地震与翻滚火焰提高竖向；修正源尾焰局部时钟，补回全力爆发charge3五层。地震/钻天破/全力爆发已物理命中的伤害破格挡闪避，护甲原生；所有伤害isEnemy双门，INI DamageUnconsciousTargets=1默认允许昏迷敌人，0排除。锤枪与私有技巧统一重武器。

**036源码/资产静态通过，未编译/未部署/未实机；实际用户035运行已确认。** 请用户编译IrisArsenal.sln Release|x64/v100，再PreparePackage.cmd整包。原ALS资源/EXDrill2/完整NiPSys等仍有缺失，详见八招对照，不宣称完整还原。游戏文件未改，轮询仍停止。

[本轮说明及八招对照](docs/effects-0.3.6.md) · [验证](docs/validation-0.3.6.json) · [逐文件备份](docs/effects-0.3.6-files.json)。以下为历史状态，其当时“未编译”不代表现在的实际用户部署。

---

# IrisArsenal 0.3.5 伤害队列与命中修正

火神弹速800（2.5倍）、脉冲440（2倍）；修复坏物理路径堵住所有后续伤害的FIFO问题，刀/钻使用真实胶囊体积查询，全力爆发改为源三段有效窗口持续检测且每敌人每段一次。钻天破本招免疫小/大受击反应，医疗/死亡/昏迷仍原生；修复Ogre不支持的replace混合。地震仍是球R36，火焰最大水平半径36。

钻天破终结已改为本源九层蓝白冲击→火焰余波，R60/5倍保持；原ALSExp/ALSshockExp依赖本机缺失，不能称完全原版移植。**035源码/资源静态通过，未编译/未部署/未实机；游戏仍034。** 请手动编译IrisArsenal.sln的Release|x64/v100，再PreparePackage.cmd完整组包。ready=false与旧DLL拒绝门有效，日志轮询未恢复。

[本轮完整说明](docs/combat-fix-0.3.5.md) · [验证](docs/validation-0.3.5.json) · [逐文件与备份](docs/combat-fix-0.3.5-files.json)。下方全部为历史状态。

---

Owner: Codex

# IrisArsenal 0.3.4 九点光学/碰撞修正

源码与资产034：八招权重全1；地震六层水平火环匹配R36，离线落锤IK使锤头距脚底约0.6；光炮R4.5，源五层能量管加三维金环/细电弧、激发蓝离子光；脉冲圆盘法向Y→Z；自有三远程飞弹忽略盟友/玩家阻挡，环境与中立仍可阻挡。火神与脉冲同用胸部世界骨点；同位撞地差异根因未确认，新增阻挡身份诊断。

**034静态通过，未编译/未部署/未实机；游戏实际033已确认。** 用户编译IrisArsenal.sln **Release|x64 / v100**→PreparePackage.cmd→整包同步。光环/电弧/离子为参考约束重建，未宣称完整原NiPSys。游戏/源素材未改，日志轮询未恢复。

[本轮说明](docs/optics-0.3.4.md) · [验证](docs/validation-0.3.4.json) · [逐文件/双备份](docs/optics-0.3.4-files.json)。下方历史状态保留，旧版本实机状态以各条目时间为准。

---

Owner: Codex

# IrisArsenal 0.3.3 光学修正与10000远程测试

当前源码/资产033：准星改为对照原录像重绘的平面红蓝环/刻线；地震改用3:35～3:37火焰变体源六层网格/4秒曲线，仍四波R36伤害；脉冲四层爆炸增加独立显示增益。三招远程FCS 0～10000、私有GunData一致，光炮R9/最长10000由同一FCS数据决定。五招继续权重1；原间隔1、倍率、enemy过滤、球AOE优化与医疗软预算保持。

已确认旧360范围门可以导致远处无动作；旧日志无空等距离，不能唯一归因，新增有界ranged_gate区分范围/就绪/原生许可。**033未编译/未部署/未实机；实际游戏032**。用户编译IrisArsenal.sln **Release|x64 / v100**→PreparePackage.cmd完整组包。准星为录像重建，原NIF未确认；完整Skyrim粒子系统仍未移植。

[本轮说明](docs/fire-reticle-0.3.3.md) · [验证](docs/validation-0.3.3.json) · [逐文件与备份](docs/fire-reticle-0.3.3-files.json)。下方为历史资料。

---

Owner: Codex

# IrisArsenal 0.3.2 三远程与两近战测试

已在项目内启用：远程vulcan/pulse/drive均FCS 0～360，近战spiral 0～30、earthquake 0～45，五招权重1，其他0。极致驱动改为R9、最大长360的连续平端柱体光炮；地震改用真实巨人践踏源烟尘，两层有限粒子，四波独立球形R36伤害。AOE增加同帧完整球事实缓存/人物形体去重，仍各事件独立结算、enemy与玩家保护、医疗软预算。

**源码/资产032已完成静态检查，未编译、未部署、未实机**。游戏DLL仍030。请编译`IrisArsenal.sln`的 **Release|x64 / v100**，再运行`PreparePackage.cmd`完整组包；旧DLL与新资产不可混装。勾选游戏“远程”测三招，取消后测两招近战，整套远程间隔`RangedActionInterval=1.0`。光炮的程序闪电和完整Skyrim粒子系统未全部移植；实际FPS提升尚未测量。

[本轮设计和参数](docs/cannon-quake-0.3.2.md) · [验证](docs/validation-0.3.2.json) · [逐文件报告/备份](docs/cannon-quake-0.3.2-files.json)。以下为历史记录。

---

# IrisArsenal 项目状态

Owner: Codex

## 当前：0.3.1 四招测试与源特效（2026-10-16）

用户本轮五点已写入源码/资产：远程两招FCS 0～360，脉冲弹体R4.5/爆炸R36；INI RangedActionInterval=1.0控制整套远程动作后原生间隔。四招权重均1：远程vulcan/pulse、近战spiral/drive，其余0。原身体/事件倍率保持。

已按原ESP追到EldenRim真实脉冲命中四层，新增分层颜色/UV/扩散曲线、枪口辅助、极致连续洪流与螺旋连续刀光。NiPSys/程序闪电/身体Steam3仍未完整移植，不宣称完全复刻。静态检查通过；源码031/FXv4未编译/未部署，旧030 DLL被组包拒绝，包ready=false。游戏实际已由用户更新到030，本轮游戏文件未变。

用户编译IrisArsenal.sln **Release|x64 / v100**→PreparePackage.cmd→整包同步。不要只复制DLL或把新FXv4放进旧030。详细参数、源链、验证和风险见[本轮说明](docs/mixed-0.3.1.md)与[验证](docs/validation-0.3.1.json)。近战测试可取消游戏“远程”勾选，依旧遵守FCS距离（spiral 0～30，drive 90～280）。以下为历史资料。

---

# IrisArsenal 项目状态

Owner: Codex

## 当前：0.3.0 同锤枪原生远近切换（2026-10-16）

Owner: Codex。用户选择同一件锤枪切换远近，延续完整任务授权，无需另询源码权限。火神/脉冲只由游戏远程开关和原生射击许可启动；合法GunClass能力适配，不变更物品类型/存档。原生AI/视线/计时保留，FCS播整套20/3发，结束后native reload min/max均2，无弹药/弩装填动画；两招离开近战池。

新增IrisRanged.cpp/.h并接入真实vcxproj，030合同/4单元/16钩子。022世界瞄准/源特效/纹理共享与两招R4.5/R9保持。当前权重仍仅两招1，其他0，故取消远程后当前测试配置不出招。源码静态/语法/SDK符号/原生离线证据通过；真实GOAP/拔枪/姿态/间隔/读档清理仍未实机。

当前用户已编译并同步022，真实DLL SHA256 87232387965b502261ac025c02efa21c88564db8bbdb29254c90aa3670bc1ebe，三处一致。030未编译/组包/部署，包ready=false；旧022被组包拒绝。用户编译IrisArsenal.sln Release|x64/v100→PreparePackage.cmd→完整同步。没有启动/终止游戏或恢复轮询，详见docs/ranged-0.3.0*与本任务原生证据。以下均为历史状态。

---

## 当前：0.2.2 火神/脉冲世界瞄准与资源（2026-10-16）

Owner: Codex。用户完整授权仍有效；最新要求脉冲爆炸半径是火神两倍，已设R9（火神R4.5）。仅vulcan/pulse权重1，其他0。

0.2.1确已编译部署并运行；真实日志出现origin约(-16334,200,29543)而aim约(-32623,236,58828)，重复原点。022直接读原生世界骨点，分招记录目标根/骨点/枪口/方向；脉冲恢复PlasmaBall三层源尺寸；同像素2048贴图复用名，只预热启用的5类，约24.7MiB PNG/mip估算节省，未实测GPU/泄漏。新增自有实例有界高水位。

022代码/资产静态验收通过，未编译、未实机、未整包部署；旧021组包会被拒绝，包ready=false。游戏无进程时仅同步兼容INI/moves.csv及清单，游戏DLL仍用户021。用户编译IrisArsenal.sln Release|x64/v100→PreparePackage.cmd→完整同步。细节/逐文件双备份见docs/aim-pulse-0.2.2*。旧段落均为历史状态。

---

## 当前：0.2.1 火神炮六项修正（2026-10-16）

Owner仍Codex，用户完整授权本任务，无需重复询问。0.2.0 PID34456实际跑通动作与事件，用户报告黑球/黑雾/朝地射击；旧Target=root+2、材质忽略源混合/LUT/顶点标志、火神借用了错误PlasmaBall已在代码/数据确认。

0.2.1源码/资源已修：源Fireball四层（从本机BSA只读同字节缓存）、9类FX/10含钻头预热类型、源混合/LUT/falloff、骨点瞄准和出生可视；仅火神已物理命中的伤害经三重身份单次TLS免格挡闪避，原生护甲/部位及其他招式防御保持。基础武器cut/blunt0.1，vulcan20发球R4.5；仅vulcan权重1，其他0。FCS火神35～180未改。

项目合同IRIS_EIGHT_021，包ready=false。当前游戏仍用户0.2.0 DLL，只同步3份兼容参数及校验清单，新材质/FX v3/瞄准与破防未部署。必须用户IrisArsenal.sln Release|x64 v100编译→PreparePackage.cmd→完整包同步。agent没有编译或启动游戏，没有恢复轮询。

16动画/9网格/27混合参数、半径包络、FCS引用反例、SDK声明/链接符号与语法树通过，不能等同MSVC/HLSL/实机已通过。备份及逐文件证据见docs/vulcan-fix-0.2.1*.json。下面是历史交付，当前身份以上述为准。

---

## 当前：0.2.0 FCS动画加载修复（2026-10-16 18:37）

用户授权无需重复询问。真实0.2.0运行PID34848，18:23:17加载七钩子成功；18:23:57引擎报iris_<招式>骨架不存在，18:28:25插件等待动画。实际八招导出iris_action_<招式>；旧drill存在但只含DrillProof，八招全不可用。

已修正动画作者与8个FCS动画集的16个引用。验证沿FCS→实际文件→内部动画名/长度→种族引用；5个故障例均拒绝，16份身体/事件/资源/语法静态检查通过。仅项目脚本/FCS/文档与游戏FCS/校验清单改动，没有C++/DLL修改或agent编译。游戏DLL仍用户0.2.0，SHA256 b31c8dd4655b86b7d9908c0be6076904b7b58781a5c19de2af5df4afccbb988c。

已部署游戏IrisArsenal.mod和IrisPackage.json，部署时游戏未运行。需用户重新启动确认出招；未自动启动游戏、未恢复轮询。双备份与详细证据见docs/animation-load-fix-validation.json。下述交付状态为历史记录，不能代替本节当前身份。

---

## 当前：0.2.0 八招源码/资源（2026-10-16）

用户授权本任务全部必要代码/资产/工程修改，无需重复询问。合同IRIS_EIGHT_020。八招身体/持械/root、FCS私有技巧、INI权重、源特效、物理事件与原生医疗队列已接入；火神20发、钻头展开80ms。源平移锁约束已按实际位消费。

C++/HLSL未编译、未部署、未游戏测试；不能据静态通过宣布最终完成。完整NiPSys/程序闪电/全部控制器/EXDrill2蒙皮尚未完成；新OverlapSphere需真实SDK/场景实机验收。当前保留原生格挡与闪避，未增加额外破防。

已通过16份骨架/握点/源hash、8招次数/FCS隔离、8个新源网格/纹理、真实代理覆盖与Tree-sitter语法检查；不等于MSVC类型/链接/GPU通过。用户编译IrisArsenal.sln / Release|x64 / v100后运行PreparePackage.cmd，旧DLL不能配新资源，清单ready=false。

本轮只写IrisArsenal，复制本机官方SDK头到局部；语法依赖只在任务tools/syntax。没有恢复轮询或操作游戏进程。下一步是用户编译后的逐招实机验证，依据真实日志/录像收敛。

---
以下为历史状态，不代表当前版本：

# IrisArsenal 项目状态

Owner: Codex

## 当前补充：钻头光学资源修订（2026-10-16）

仍为0.1.2 C++源码，未改动；资产合同IRIS_DRILL_OPTICS_V1。用户视频640B05及对应0.1.1 PID27532日志显示循环可运行，但为黑剪影/白矩形。日志明确anim.dds加载失败；源实体镜面/发光和4张弧光alpha未被旧简化材质正确处理。

资源已恢复源镜面强度、光泽、发光与透明；BC7 anim纹理转同像素PNG；法线与真实转动产生金属高光，天空/地面/太阳用本机既有参数近似原ENB。19层源绑定独立记录；没有更改网格/骨架/动作/碰撞/C++/DLL/普通武器参数，没有新增粒子或伤害。

离线验收通过，C++/HLSL未编译；本次未组包/部署。读取的bin/package/游戏DLL仍为用户0.1.1，旧版时间与部署记录只作为历史，不当新画面证明。须完成既有0.1.2编译并整包更新后实机观察。详见docs/drill-optics.json、docs/0.1.2-drill-optics.md。

当前源码：0.1.2；最新碰撞模板审查完成，未编译/未部署。实际已编译/部署的DLL在本轮观察为0.1.1。
用户编译：IrisArsenal.sln / Release|x64 / v100；成功后PreparePackage.cmd。

## 2026-10-15 最新碰撞经验审查（0.1.2）

已读取Playbook的0.6.12～0.6.14补充、Ephnel 0.6.13恢复及0.6.14审计说明，仅只读参考该项目。当前Probe是无伤害首非自身阻挡诊断，正式版本需要的多接触消费者未确定，因此不导入ALL_HITS/正式SDK/健康/长期统计。

发现0.1.1的querySuppressed使一次C++查询异常停止角色诊断直到读档，与最新逐路径恢复要求冲突。0.1.2删除该状态，当前诊断失败后下一安全更新继续；日志限频不限制尝试，初始重叠不读point，坏比例记录原位型。正式接入规范见docs/Collision-Template.md。

本轮只读核对发现用户已在21:21编译/同步0.1.1（新合同IRIS_011_BOUND_DRILL_QUERY_ISOLATED），此前“仍为0.1.0”属于上一轮观察。当前0.1.2源码合同IRIS_012_DIAGNOSTIC_PATH_RETRY未编译/未部署，bin/package/游戏DLL保持用户0.1.1字节。package标记ready=false，必须重新编译后组包。

0.1.2非编译校验通过；动画/纹理/材质/FCS/模型/胶囊尺寸和时间轴不变。没有新游戏测试、性能收益或多目标伤害覆盖结论；轮询保持关闭。


## 历史：0.1.1源码交付时状态（以下不代表当前DLL）

版本：0.1.1修正源码与文本合同；等待用户重新编译及实机复核。
目标：正常武器→钻头展开旋转→收回；只有此一招，无伤害、无终结发射。
具体C++授权：用户已授权IrisArsenal.cpp的闭环/查询/清理/日志；本轮修复同一范围的运行故障。

实际0.1.0测试：游戏PID37108（2026-10-15 20:23:21启动），部署DLL SHA256 4d885dd6ebdcdeff5075beacd44fb22600e64721651197d1c71a6ec3a3d0fbb9；项目、package与部署包在本轮开始时逐字节一致。20:31:20.086第一次动作在clip=1.46867、554次查询后因native sweep fraction invalid永久停用。原值未记录，不能猜测为距离单位或某种PhysX条件。

0.1.1：无效返回值仅拒绝当前诊断并记录raw_fraction；查询C++异常只停止该演员诊断，原生动作/可视/后续选招继续。自有钻头19层按真实源mesh材质逐层重绑回读，drill.csv v2保存顺序；DebugDraw默认0。仍无强制移动、健康/踉跄/全局PhysX回调。

用户编译：IrisArsenal.sln / Release|x64 / v100。产物../bin/Release/IrisArsenal.dll；成功后PreparePackage.cmd要求0.1.1合同再组包。
编译状态：0.1.0由用户编译过；0.1.1按项目/Skill规则未由agent编译。现有bin和package DLL均为旧0.1.0，不可直接部署。
游戏状态：本轮没有部署、未操作正在运行的游戏、未改勾选/存档/其他项目，未恢复轮询。
验证：docs/validation.json；源NIF/19层mesh/配置顺序一致，文本/网格/骨架/FCS静态检查通过。画面、旋转、连续施放仍待实机。详见docs/0.1.1-runtime-fix.md。

共享_collab/STATE.md仍属于SpareLimbBonus历史任务；本项目独立Owner，不接管其他项目。
