# 075：正式十招多持有者独立起手（源码0.4.26，待用户编译）

## 问题与证据

用户2026-10-22报告多名角色持同一锤枪不会同时攻击。当前INI为MaxActiveActors=1；旧IrisCombat.cpp同时在Choose、PickRanged与Tick里的IrisRanged::Publish统计所有Actor.active/reserved，因而一人的整套动作会阻止其他持有者起手。该配置还被旧源码限制为1..2，单纯改成2仍留下跨角色限制。

实际旧日志D:\steam\steamapps\common\Kenshi\mods\IrisArsenal\logs\IrisArsenal-20261022-183546-955-11676.log中出现3个不同远程持有者，38次起手取证时最大重叠仅1；原生瞄准已就绪时，其他持有者仍在该人动作窗口变为plugin_not_ready。日志是旧版本证据，不能称作075游戏验证。

## 本次修改

- IrisCombat.cpp：删除正式十招近战选择、远程选择、远程就绪发布三处跨角色active/reserved名额门；删除无消费者的maxActors配置变量。各Actor的动画、资源、FCS距离、当前动作及各Slot的busy/pending/request保持。MaxActiveActors不再限制正式十招。
- IrisArsenal.cpp：仅更新源码版本和旧配置诊断说明，去除注释后全部可执行源码行相同。DrillProofOnly=1诊断原型仍按旧MaxActiveActors=1或2运行。
- IrisArsenal.rc：用户下一次编译的PE资源版本更新0.4.26。现有DLL不修改，不伪造构建成功。
- tools/stage_package.py：要求实际DLL含IRIS_MULTI_ACTOR_075，正确用户构建后才可组包ready=true的0.4.26；没有075合同的旧DLL会明确拒绝。
- distribution和package的INI：只追加MaxActiveActors仅用于诊断原型的说明；所有实际配置值、日志开关保持。待构建package清单ready=false，保留原DLL身份和当前文件哈希，并记录pending_version/contract。
- 新test_multi_actor075.py解释实际C++条件；更新已有隔离测试对旧DLL的分类。逐文件详情见本次report-*.json。

## 保持的边界

不新增线程、Hook、锁或PhysX/医疗调用。12个关键函数（包含Flush、ResolveJobs、Emit、AdvanceEffects、End、Clear、Observe、CanDamage、EnsureMoves等）逐函数SHA保持，IrisRanged.cpp/头文件、Native查询实现及141个受保护文件保持。

仍在原主线程安全窗口工作；每窗口64次查询、2.5ms/32次原生医疗FIFO及原伤害事件/逐段去重、暂停/读档清理保持。正式演员登记容量仍为既有8人，远程能力/弹体/视觉池等容量本次未扩大；本修复解决已登记持有者被全局名额强制串行，不宣称无限角色容量或原生AI必定同时起手。原生攻击槽和所有既有资格限制保持。

## 实际执行的验证

1. 解释实际C++条件的1152组矩阵：他人active/reserved不再影响当前角色；自身动画、资源、就绪、暂停、武器与距离仍影响对应入口。
2. 2/3/8人各自通过近战选择前置门、远程选择前置门、就绪发布条件。三个旧源码反例在他人占用时拒绝，当前源码通过。测试只解释起手条件，不执行引擎、完整加权选招或实际动画。
3. 原072资格分支732例继续通过，原生参数和回退行为保持；没有声称重新实测义肢伤势转换。
4. 10份C++/H Tree-sitter语法通过，不代替MSVC类型/链接验证；Python AST、中文/编码及完整待构建清单哈希通过。
5. 原更新器21项隔离测试：20通过，1项符号链接测试因WinError1314系统权限跳过；不写实际游戏目录。
6. 现有用户DLL明确被075合同检查拒绝，bin/package/游戏DLL及当前游戏FCS/INI/清单未修改。未编译、启动/终止游戏、附加调试器或游戏实测，不保证已提升FPS。

## 编译与更新

用户在Visual Studio编译本工程IrisArsenal.sln，Release|x64，v100。编译完成后正常退出Kenshi，再运行UpdateMod.cmd。脚本读取实际新DLL并验证075合同，才会标记0.4.26/ready=true并同步。只运行Update不会编译，不会把现有0.4.25变成多人修复。

下次日志开启时可查一次初始化标记IRIS_MULTI_ACTOR_075，以及audit_resources中的active_peak/reserved_peak。关闭日志不影响多人资格修复。

## 备份、编码与报告

双备份：D:/CodexBackups/Task-Iris-MultiActor075-20261022-184438-8fcaba/和E:/AIWorkSpace/_backups/Task-Iris-MultiActor075-20261022-184438-8fcaba/，按原盘符和相对路径保存。全部小文件修改前均已核验两份备份；C++和既有文本逐文件保留UTF-8/BOM/CRLF或LF，中文乱码扫描通过。每个文件写入后立即保存独立report JSON。

本次完整证据目录：D:/CodexWorkSpace/Sessions/20261002-235652-kenshi-crash-407794f2/Task-Iris-MultiActor075-20261022-184438-8fcaba。validation-source075.json、validation-boundary075.json、update-tests075.log及per-file-reports.json可复核。需要回退时同时恢复本轮源码/版本资源/组包门和package配置清单，避免源码与部署门不一致。当前游戏未部署，本轮无需回退运行DLL。
