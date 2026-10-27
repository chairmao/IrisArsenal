# 055逐文件变更索引

每个文件的逐次改动均有独立报告和双备份。详细字段及SHA256见collision-damage-055-files.json；本索引按文件分别列出职责、变化、验证和边界。最终非编译验收通过，任何C++相关条目仍不代表MSVC、PhysX或游戏实测。

## D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-Iris-Formal1-Optimize055-20261018-211300-34f16b\seal_release.py

- Role: 正式版封存脚本
- Code location: copy_tree
- Changes: 排除IDE锁定的.vs缓存；新目录保留失败现场
- Reasons: Browse.VC.opendb共享锁与源码交付无关
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: IDE缓存不归档，其他正式版文件完整保存
- Before: 17cf6e6a38cc3ff15d8962ee439410f8ba04fbb25aa387b978c845a9af50cff5
- After: 47153206185a13fa5a580c0a95c6ca47e671c13bc75eb378890d6c87921a2ad7
- Safety: [{"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\D\\CodexWorkSpace\\Sessions\\20261002-235652-kenshi-crash-407794f2\\Task-Iris-Formal1-Optimize055-20261018-211300-34f16b\\seal_release.py", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\D\\CodexWorkSpace\\Sessions\\20261002-235652-kenshi-crash-407794f2\\Task-Iris-Formal1-Optimize055-20261018-211300-34f16b\\seal_release.py"], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}]

## D:\CodexBackups\Iris-Formal1-Optimize055-20261018-211300-34f16b-Formal1.0-v2\LESSONS.md

- Role: 正式版经验
- Code location: 全文
- Changes: 保存有来源的流程、失误和边界
- Reasons: 用户要求经验与总结纳入正式版
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: 不表示所有源特效逐像素复刻或新优化已实测
- Before: new
- After: d7611e94bc8aea8f4d025f26b75c4f6a88b2ee1f542bd29f68995f9999896506
- Safety: [{"backups": [], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}]

## D:\CodexBackups\Iris-Formal1-Optimize055-20261018-211300-34f16b-Formal1.0-v2\RELEASE.md

- Role: 正式版说明
- Code location: 版本/目录/恢复
- Changes: 记录真实DLL身份、配置差异和安全恢复步骤
- Reasons: 正式版必须可检查和恢复
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: 按用户确认封存，不代表所有工况无问题
- Before: new
- After: 81ba862b1e829a0aa0984fab6bba30e96c583d26943cfd9743d65911e2afeba7
- Safety: [{"backups": [], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}]

## E:\KenshiProject\2.Projects\IrisArsenal\native\NativeMultiContact.h

- Role: 原生查询值接口
- Code location: Diagnostic
- Changes: 新增去重比较/探测/重复/建表和窄相缓冲增长计数；游戏接口不变
- Reasons: 用户21:10任务；已封存正式1.0，依据实际循环复制/线性查找和日志热点
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: C++未编译；未运行游戏或测量FPS
- Before: 12e8acdfc4353c24ef4a4c9451286affc32cbf75d088770c3d92a2e20de4c661
- After: 077f9701e1ff1a28e32068db17bbc7c40f3d138b7571be80e170665d0675896b
- Safety: [{"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\native\\NativeMultiContact.h", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\native\\NativeMultiContact.h"], "encoding": "utf-8", "line_ending": "'\\r\\n'", "mojibake_check": "pass"}]

## E:\KenshiProject\2.Projects\IrisArsenal\native\NativeMultiContact.cpp

- Role: PhysX独立翻译单元
- Code location: IdentityIndex/OverlapCollector/CylinderCollector
- Changes: 小名单线性、大名单完整身份索引；同查询复用圆柱窄相顶点缓冲；扫掠和SDK门不变
- Reasons: 用户21:10任务；已封存正式1.0，依据实际循环复制/线性查找和日志热点
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: C++未编译；未运行游戏或测量FPS
- Before: 3682e7dc3d8ad45e65110a1902e1e913b3d5e1db1cf4d97d69fc8a3f6a48163e
- After: fd0a2910e47ec416c58047af233828d905387cdcd4656574bdb9505161791f27
- Safety: [{"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\native\\NativeMultiContact.cpp", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\native\\NativeMultiContact.cpp"], "encoding": "utf-8", "line_ending": "'\\r\\n'", "mojibake_check": "pass"}]

## E:\KenshiProject\2.Projects\IrisArsenal\IrisDiagnostics.h

- Role: 诊断公共值接口
- Code location: Kind/Counter/WaitStamp
- Changes: 追加独立阶段和采样等待通道，原枚举顺序保持；不引入线程或指针缓存
- Reasons: 用户21:10任务；已封存正式1.0，依据实际循环复制/线性查找和日志热点
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: C++未编译；未运行游戏或测量FPS
- Before: a8aee21c1a8ef28293b97de8784441d9450e2760d8acd903a626a7bab52c7027
- After: 1bb6d74f01893f936558e7223cc910efe461eaebc0d15e1b5afc6b490a09bdbe
- Safety: [{"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\IrisDiagnostics.h", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\IrisDiagnostics.h"], "encoding": "utf-8", "line_ending": "'\\r\\n'", "mojibake_check": "pass"}]

## E:\KenshiProject\2.Projects\IrisArsenal\IrisDiagnostics.cpp

- Role: 固定内存性能审计；当前版本注释
- Code location: Active/Record/ObserveWindow/Summary；头部/版本门说明
- Changes: 可配置碰撞/医疗明细；单独记录墙钟等待归因与医疗四阶段，区分CPU/等待直方图；修正本轮修改文件中的过期054/0.4.11当前身份描述
- Reasons: 用户21:10任务；已封存正式1.0，依据实际循环复制/线性查找和日志热点；避免版本说明与055真实源码矛盾
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: C++未编译；未运行游戏或测量FPS；只改变注释，仍未编译
- Before: ef2892c47739a53f9a2a36bc71419996071913472af2d300c50c8a00a88318c6
- After: af5f5ca06ac30917f6e9ebd7839a65425f437f7aef3dfe14a8cbc863a0d5f64b
- Safety: [{"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\IrisDiagnostics.cpp", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\IrisDiagnostics.cpp"], "encoding": "utf-8", "line_ending": "'\\r\\n'", "mojibake_check": "pass"}, {"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\edit-214803-600041\\E\\KenshiProject\\2.Projects\\IrisArsenal\\IrisDiagnostics.cpp", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\edit-214803-601040\\E\\KenshiProject\\2.Projects\\IrisArsenal\\IrisDiagnostics.cpp"], "encoding": "utf-8", "line_ending": "'\\r\\n'", "mojibake_check": "pass"}]

## E:\KenshiProject\2.Projects\IrisArsenal\IrisCombat.cpp

- Role: 十招与伤害消费者
- Code location: Job/Contacts/ResolveJobs/Flush
- Changes: list splice轮转及容器交换入队；精确胶囊事实缓存；分项医疗与等待；64/2.5ms/32和几何保持
- Reasons: 用户21:10任务；已封存正式1.0，依据实际循环复制/线性查找和日志热点
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: C++未编译；未运行游戏或测量FPS
- Before: ca314624a759735393481688aed577f51a8f4f19430954f71840ec5fd822b656
- After: d8029fe63e4141875113ce02cecc125e5b1962c7dbbc1bc917abe6bcfde2e567
- Safety: [{"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\IrisCombat.cpp", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\IrisCombat.cpp"], "encoding": "utf-8", "line_ending": "'\\r\\n'", "mojibake_check": "pass"}]

## E:\KenshiProject\2.Projects\IrisArsenal\IrisArsenal.cpp

- Role: 原生安全回调入口；当前版本注释
- Code location: Idle；头部/版本门说明
- Changes: 记录既有门的暂停/物理/AI/世界无效状态，原Hook数量与实际转发保持；修正本轮修改文件中的过期054/0.4.11当前身份描述
- Reasons: 用户21:10任务；已封存正式1.0，依据实际循环复制/线性查找和日志热点；避免版本说明与055真实源码矛盾
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: C++未编译；未运行游戏或测量FPS；只改变注释，仍未编译
- Before: c84cb460d6190306289962fce2d1ec015e9b2dff4363a464b9b6ab7254b36ba7
- After: 6ffb006f989491d8127ce1b2558c335a303db83c5ba39ad84f7c36075ee46f3c
- Safety: [{"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\IrisArsenal.cpp", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\IrisArsenal.cpp"], "encoding": "utf-8", "line_ending": "'\\r\\n'", "mojibake_check": "pass"}, {"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\edit-214803-590648\\E\\KenshiProject\\2.Projects\\IrisArsenal\\IrisArsenal.cpp", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\edit-214803-593072\\E\\KenshiProject\\2.Projects\\IrisArsenal\\IrisArsenal.cpp"], "encoding": "utf-8", "line_ending": "'\\r\\n'", "mojibake_check": "pass"}]

## E:\KenshiProject\2.Projects\IrisArsenal\IrisArsenal.rc

- Role: DLL版本资源
- Code location: FILEVERSION/PRODUCTVERSION
- Changes: 优化工作版0.4.12，避免旧正式版DLL冒充055
- Reasons: 用户21:10任务；已封存正式1.0，依据实际循环复制/线性查找和日志热点
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: C++未编译；未运行游戏或测量FPS
- Before: 58e87602a887772f284ace3cf5a2cee42a3f2adc51cb3552d1bf31d5adb913c2
- After: 5d04d1de22b2c064cc688c802d6f022a9f6a5d5f14127e9d4fa4f4ab8b4a030d
- Safety: [{"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\IrisArsenal.rc", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\IrisArsenal.rc"], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}]

## E:\KenshiProject\2.Projects\IrisArsenal\distribution\IrisArsenal.ini

- Role: 配置默认值
- Code location: EnableCombatDetailLogging
- Changes: 新增可关闭的碰撞/医疗明细日志；战斗参数与预算默认保持
- Reasons: 用户21:10任务；已封存正式1.0，依据实际循环复制/线性查找和日志热点
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: C++未编译；未运行游戏或测量FPS
- Before: cd5335d03f1fc4b77ce0feda46db43369084d489948f0f058b5c5cb95ff0ac75
- After: 417763fdb5b41b6bb8b724a190896ddc796e137e8ab73f7199a322898c9fd121
- Safety: [{"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\distribution\\IrisArsenal.ini", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\distribution\\IrisArsenal.ini"], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}]

## E:\KenshiProject\2.Projects\IrisArsenal\tools\stage_package.py

- Role: 组包生产门；当前版本注释
- Code location: BUILD_CONTRACT/validate_dll/main；头部/版本门说明
- Changes: 拒绝旧054 DLL配055源码；真实编译及组包仍由用户执行；修正本轮修改文件中的过期054/0.4.11当前身份描述
- Reasons: 用户21:10任务；已封存正式1.0，依据实际循环复制/线性查找和日志热点；避免版本说明与055真实源码矛盾
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: C++未编译；未运行游戏或测量FPS；只改变注释，仍未编译
- Before: 223cf0b0f38f01bbb7e196035469568c675d0feffec89cfe63307e5139c35b19
- After: 40fefe1ebec53c820ed1d6222ec8611ed31edfffe01b1875172ec0267854d684
- Safety: [{"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\stage_package.py", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\stage_package.py"], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}, {"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\edit-214803-606040\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\stage_package.py", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\edit-214803-608041\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\stage_package.py"], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}]

## E:\KenshiProject\2.Projects\IrisArsenal\package\IrisArsenal\IrisPackage.json

- Role: 包状态
- Code location: ready/code_contract
- Changes: 保留旧DLL，仅标记等待用户编译055
- Reasons: 本任务禁止编译或部署，不能伪装运行产物
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: C++未编译；未运行游戏或测量FPS
- Before: e4f88d29317477e710031e883ac784a536e17caf8a40cbd1026dec77ab38caff
- After: 5715d91699157b8d50d45f2ee381e4b66ecdd834023550e28ba770fd6c79030e
- Safety: [{"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\package\\IrisArsenal\\IrisPackage.json", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\package\\IrisArsenal\\IrisPackage.json"], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}]

## E:\KenshiProject\2.Projects\IrisArsenal\tools\test_balance046.py

- Role: 非编译回归合同
- Code location: 当前版本、入队调用及原枚举前缀
- Changes: 只更新055显式变化；原倍率/FCS/攻速/防御及调度边界模型保持
- Reasons: 055明确替换任务搬运与追加诊断；历史不变量仍逐项校验
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: C++未编译；未运行游戏或测量FPS
- Before: b6fa5892c7947bcf68fec161afd19c57045b612835bc3a89efee30b22615ee63
- After: dd6a6331b31f15bde019e05d1d3f9a3d704fafa8e4fd0556debe30e99a76cc8e
- Safety: [{"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\test_balance046.py", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\test_balance046.py"], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}]

## E:\KenshiProject\2.Projects\IrisArsenal\tools\test_move_parameters045.py

- Role: 非编译回归合同
- Code location: 当前版本、入队调用及原枚举前缀
- Changes: 只更新055显式变化；原倍率/FCS/攻速/防御及调度边界模型保持
- Reasons: 055明确替换任务搬运与追加诊断；历史不变量仍逐项校验
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: C++未编译；未运行游戏或测量FPS
- Before: a3f0bce47efbeda661339ae97d9ef89b08c6f008f1506eab14cbe43d6e40316b
- After: 30aa88382050c568918d6fd200a5d52d00efa9657517f6951ea02c3eb7eea706
- Safety: [{"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\test_move_parameters045.py", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\test_move_parameters045.py"], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}]

## E:\KenshiProject\2.Projects\IrisArsenal\tools\test_melee_reaction044.py

- Role: 非编译回归合同
- Code location: 当前版本、入队调用及原枚举前缀
- Changes: 只更新055显式变化；原倍率/FCS/攻速/防御及调度边界模型保持
- Reasons: 055明确替换任务搬运与追加诊断；历史不变量仍逐项校验
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: C++未编译；未运行游戏或测量FPS
- Before: 7f1d3ca12dc9215e5cff80beb3565ef4f2aa1ca56e099eb7d54d8822813d120f
- After: 9bbc8e4b85b72d5eae10b1d78b8c2733eddd1c051b20bb53d20a03e77a4c73a8
- Safety: [{"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\test_melee_reaction044.py", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\test_melee_reaction044.py"], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}]

## E:\KenshiProject\2.Projects\IrisArsenal\tools\test_release047.py

- Role: 非编译回归合同
- Code location: 当前版本、入队调用及原枚举前缀
- Changes: 只更新055显式变化；原倍率/FCS/攻速/防御及调度边界模型保持
- Reasons: 055明确替换任务搬运与追加诊断；历史不变量仍逐项校验
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: C++未编译；未运行游戏或测量FPS
- Before: b1fbb0011ee30aab06f9d1066f657910a81d36e5a1321204a060c38c00098aa9
- After: bc58b8dd410e181b8e0ae386f46317193d287599bce254bf5abda2c199eec10b
- Safety: [{"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\test_release047.py", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\test_release047.py"], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}]

## E:\KenshiProject\2.Projects\IrisArsenal\tools\test_surface050.py

- Role: 非编译回归合同
- Code location: 当前版本、入队调用及原枚举前缀
- Changes: 只更新055显式变化；原倍率/FCS/攻速/防御及调度边界模型保持
- Reasons: 055明确替换任务搬运与追加诊断；历史不变量仍逐项校验
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: C++未编译；未运行游戏或测量FPS
- Before: 92ea3983c897af05a09ec1b6b989e5b8a5c062028994f44bba67aacc909a14e2
- After: 0e10eb34d80a9ac31cf85a46d3b2cb15886bfa35effaafff24a39d70d613becb
- Safety: [{"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\test_surface050.py", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\test_surface050.py"], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}]

## E:\KenshiProject\2.Projects\IrisArsenal\tools\test_queue_balance053.py

- Role: 非编译回归合同
- Code location: 当前版本、入队调用及原枚举前缀
- Changes: 只更新055显式变化；原倍率/FCS/攻速/防御及调度边界模型保持
- Reasons: 055明确替换任务搬运与追加诊断；历史不变量仍逐项校验
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: C++未编译；未运行游戏或测量FPS
- Before: bb5b628e0db640385991659c90175a2a9770c483aadd8f2081a4c64ce49b9bd7
- After: 76caeec182f53ef2b08d27e59d9327d5daa50d491902f99db755efd17f1f4813
- Safety: [{"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\test_queue_balance053.py", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\test_queue_balance053.py"], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}]

## E:\KenshiProject\2.Projects\IrisArsenal\tools\test_combat_035.py

- Role: 非编译回归合同
- Code location: 任务轮转/入队与总验收
- Changes: 用splice/PushJob明确替代已移除复制实现，仍要求每轮8路径和相同独立事件
- Reasons: 055明确替换任务搬运与追加诊断；历史不变量仍逐项校验
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: C++未编译；未运行游戏或测量FPS
- Before: ad295582bd68e1cae4aa40d1369b9e1fc3710d77066ab8ccdca686319ad2fc0d
- After: ec3aa9ce0684e402777793d3ced3f993a974a2408f3a5b841f68579e625246ab
- Safety: [{"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\test_combat_035.py", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\test_combat_035.py"], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}]

## E:\KenshiProject\2.Projects\IrisArsenal\tools\test_combat_036.py

- Role: 非编译回归合同；历史伤害回归
- Code location: 任务轮转/入队与总验收；消费端资格
- Changes: 用splice/PushJob明确替代已移除复制实现，仍要求每轮8路径和相同独立事件；断言同一短路资格和明确拒绝分支
- Reasons: 055明确替换任务搬运与追加诊断；历史不变量仍逐项校验；计时作用域拆分后旧if字符不再存在，逻辑仍需完整核对
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: C++未编译；未运行游戏或测量FPS；非编译规格不替代运行
- Before: cf4d9cb2b6a18591f090d8741370d1b70064309e772ff54d39a9392668d023b8
- After: c8f15c7d80793b6bc9c34e8dcc438923ea1153e94ce741a15435a6ef2096746e
- Safety: [{"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\test_combat_036.py", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\test_combat_036.py"], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}, {"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\edit-213449-457486\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\test_combat_036.py", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\edit-213449-460488\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\test_combat_036.py"], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}]

## E:\KenshiProject\2.Projects\IrisArsenal\tools\verify_moves.py

- Role: 非编译回归合同
- Code location: 任务轮转/入队与总验收
- Changes: 用splice/PushJob明确替代已移除复制实现，仍要求每轮8路径和相同独立事件
- Reasons: 055明确替换任务搬运与追加诊断；历史不变量仍逐项校验
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: C++未编译；未运行游戏或测量FPS
- Before: cb27f240a5311c9d32f4c503dc175dd2ee17a092f5b02e23a68cff2f75a81283
- After: a93c792ca2e450b3b835918bf2ddee7f49c4c99f8b483c9202669a3cca77bec9
- Safety: [{"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\verify_moves.py", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\verify_moves.py"], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}]

## E:\KenshiProject\2.Projects\IrisArsenal\tools\test_ten_moves042.py

- Role: 非编译回归合同
- Code location: 任务轮转/入队与总验收
- Changes: 用splice/PushJob明确替代已移除复制实现，仍要求每轮8路径和相同独立事件
- Reasons: 055明确替换任务搬运与追加诊断；历史不变量仍逐项校验
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: C++未编译；未运行游戏或测量FPS
- Before: ce31112bc47d2a87dad1663018d72a812168d76ab11426e1ae51f2806fd6431f
- After: 12d52dc46dddc1a1946fb5325d8dbc95e3793aa6c6423c641f367960e0bc57e8
- Safety: [{"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\test_ten_moves042.py", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\test_ten_moves042.py"], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}]

## E:\KenshiProject\2.Projects\IrisArsenal\tools\test_drill_r120.py

- Role: 非编译回归合同
- Code location: 任务轮转/入队与总验收
- Changes: 用splice/PushJob明确替代已移除复制实现，仍要求每轮8路径和相同独立事件
- Reasons: 055明确替换任务搬运与追加诊断；历史不变量仍逐项校验
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: C++未编译；未运行游戏或测量FPS
- Before: c617d785403e49e7a21fd13487ce4449ec8e48baddb9ffe33b80006bf5cc55a4
- After: a76b9b0a248070cde38c0754566089e6b2c9c1f025253aa53f22634ba37421c3
- Safety: [{"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\test_drill_r120.py", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\test_drill_r120.py"], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}]

## E:\KenshiProject\2.Projects\IrisArsenal\tools\historical047.py

- Role: 非编译回归合同
- Code location: assert_047_hash
- Changes: 追加055精确哈希链，未登记变化仍拒绝
- Reasons: 055明确替换任务搬运与追加诊断；历史不变量仍逐项校验
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: C++未编译；未运行游戏或测量FPS
- Before: 5ec433e7643f5e619053d8dd321f763515f08410eb13441bc348499123b73a08
- After: bfd7002f51528ecfc966484d6853d90b56355926f0844dddd9abc2ee6b6c8035
- Safety: [{"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\historical047.py", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\historical047.py"], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}]

## E:\KenshiProject\2.Projects\IrisArsenal\tools\test_physx_compat054.py

- Role: 非编译回归合同；历史兼容回归
- Code location: 版本门不变、查询后缀明确变更；资产摘要
- Changes: 不再假设055查询代码字节等于054；只接受精确登记差异并保留14组版本边界；原INI变化也必须通过精确055迁移链，不宽泛排除配置文件
- Reasons: 055明确替换任务搬运与追加诊断；历史不变量仍逐项校验；新增明细日志键是唯一配置变更，055专项另逐值核对
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: C++未编译；未运行游戏或测量FPS；非编译规格
- Before: 69fe4db5a2b7e7d898b1be3af4e97e2628284350328368ccda04c98bc5a98d35
- After: 945f6277fe8286e7dbb740c9861a838e5c36ae70bcd9e8ca1abb11e7a3529000
- Safety: [{"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\test_physx_compat054.py", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\test_physx_compat054.py"], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}, {"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\edit-213654-700976\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\test_physx_compat054.py", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\edit-213654-703976\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\test_physx_compat054.py"], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}]

## E:\KenshiProject\2.Projects\IrisArsenal\docs\authorized-delta-055.json

- Role: 精确回归迁移；055精确迁移；055最终精确迁移
- Code location: 逐文件/逐函数摘要；INI原始哈希；Flush_parameters045；当前修改文件摘要
- Changes: 只登记055实际变化；登记唯一日志键的旧新字节，不覆盖历史迁移；补充原045归一化医疗全文的精确前后摘要；将最终注释/配置/文档对应到封存的原始字节
- Reasons: 旧不变量需追溯到封存正式版；回归不能忽略整个INI；055只追加计时和拆出等价资格，不应让旧整函数冻结阻止合法变更；保证历史精确回归不因当前注释修订漂移
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: 摘要非行为证明；另有055规格和不变量验收；与配置语义专项一起验证；医疗语义另逐句和模型核对；摘要需结合独立规格而非替代行为验证
- Before: new
- After: c71a66aa6914db5e95c26e765bf44bd4a16862a59d6d4ae769d50895949f8560
- Safety: [{"backups": [], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}, {"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\edit-213654-748496\\E\\KenshiProject\\2.Projects\\IrisArsenal\\docs\\authorized-delta-055.json", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\edit-213654-750504\\E\\KenshiProject\\2.Projects\\IrisArsenal\\docs\\authorized-delta-055.json"], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}, {"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\edit-213858-762612\\E\\KenshiProject\\2.Projects\\IrisArsenal\\docs\\authorized-delta-055.json", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\edit-213858-764612\\E\\KenshiProject\\2.Projects\\IrisArsenal\\docs\\authorized-delta-055.json"], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}, {"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\edit-214806-311943\\E\\KenshiProject\\2.Projects\\IrisArsenal\\docs\\authorized-delta-055.json", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\edit-214806-313945\\E\\KenshiProject\\2.Projects\\IrisArsenal\\docs\\authorized-delta-055.json"], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}]

## E:\KenshiProject\2.Projects\IrisArsenal\docs\collision-damage-055-baseline.json

- Role: 055不变量；055原始不变量
- Code location: 原几何/事件/版本门/资产哈希；原配置值快照
- Changes: 冻结从正式版直接读取的行为和资源边界；追加原正式版INI的逐节逐键值，既有旧哈希不变
- Reasons: 用户要求优化不能改变伤害、范围、特效、权重；允许唯一新增日志开关，原战斗设置必须逐值保持
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: 原始资产不变不代表新C++已实机；摘要仍非运行证明
- Before: new
- After: 54ebb221bef6631b36d064a34cdbbf8d102dca82874bb68d78c42384d4d6014f
- Safety: [{"backups": [], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}, {"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\edit-213654-676328\\E\\KenshiProject\\2.Projects\\IrisArsenal\\docs\\collision-damage-055-baseline.json", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\edit-213654-678327\\E\\KenshiProject\\2.Projects\\IrisArsenal\\docs\\collision-damage-055-baseline.json"], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}]

## E:\KenshiProject\2.Projects\IrisArsenal\tools\test_collision_damage055.py

- Role: 055独立非编译验收；055验证；055验收
- Code location: verify_collision_damage055；禁止共享回调断言；identity_cases；运行配置语义
- Changes: 密集去重、冲突/容量、调度、缓存、等待及真实资产核对；删除无关ready=false字符限制，保留原生回调/几何/容量/事件检查；用实际Hash最后一个乘数解析终项，保留字段顺序和32位溢出模型；逐字节锁所有资产，INI仅允许新增一个诊断键
- Reasons: 不能仅检查源码字符串就声称优化等价或FPS通过；ready=false是既有角色生命周期合法状态，不能凭字符串误判故障；原正则错误多匹配一个括号，尚未执行到密集规格；新日志设置需可交付，但不得偷偷改倍率/范围/权重
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: 这些模型不执行C++/PhysX或编译；模型非C++运行；非C++/PhysX执行；非编译规格
- Before: new
- After: 0dce8e06b6b5004167a3e707e644aafeefed70a30cbbdf941997e4cbbb7ca92c
- Safety: [{"backups": [], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}, {"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\test_collision_damage055.py", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\test_collision_damage055.py"], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}, {"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\edit-213027-274279\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\test_collision_damage055.py", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\edit-213027-277290\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\test_collision_damage055.py"], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}, {"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\edit-213654-685335\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\test_collision_damage055.py", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\edit-213654-687326\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\test_collision_damage055.py"], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}]

## D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-Iris-Formal1-Optimize055-20261018-211300-34f16b\tasklib.py

- Role: 任务安全写入
- Code location: put备份目标
- Changes: 为同任务多次必要修正分别保存新时间戳副本
- Reasons: 不能覆盖任何先前备份
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: 不改变项目运行行为
- Before: 7701cb60e4a10bdbdc01f4eeecd2663a3e4dc42a3b0f532ed5cc4927e1f84ef6
- After: 74d4c347b9aff2bc8a459a12747bafbf3d0df007a761bab7a7a1f5dc6f2aec50
- Safety: [{"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\D\\CodexWorkSpace\\Sessions\\20261002-235652-kenshi-crash-407794f2\\Task-Iris-Formal1-Optimize055-20261018-211300-34f16b\\tasklib.py", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\D\\CodexWorkSpace\\Sessions\\20261002-235652-kenshi-crash-407794f2\\Task-Iris-Formal1-Optimize055-20261018-211300-34f16b\\tasklib.py"], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}]

## E:\KenshiProject\2.Projects\IrisArsenal\tools\test_cannon_quake.py

- Role: 历史物理回归
- Code location: 缓存生命周期
- Changes: 原球缓存检查扩为球和胶囊共同清空
- Reasons: 055新增缓存必须受同一Tick/读档代次约束
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: 非编译验证
- Before: 4efa8926cd97e49fd65b548517c5b5c867a6e1b1472c07ef8fb7207aa6f7d668
- After: 6170259501210be4af5c398e9a5a518ca224a5980f8245cf9b4afa300b7e709a
- Safety: [{"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\edit-213241-578952\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\test_cannon_quake.py", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\edit-213241-582052\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\test_cannon_quake.py"], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}]

## E:\KenshiProject\2.Projects\IrisArsenal\package\IrisArsenal\IrisArsenal.ini

- Role: 待编译运行包配置
- Code location: 日志明细开关
- Changes: 同步EnableCombatDetailLogging默认项到项目包，不同步游戏
- Reasons: 更新管线需默认源与包相同，个人INI仍由更新脚本合并
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: C++未编译；未运行游戏或测量FPS
- Before: cd5335d03f1fc4b77ce0feda46db43369084d489948f0f058b5c5cb95ff0ac75
- After: 417763fdb5b41b6bb8b724a190896ddc796e137e8ab73f7199a322898c9fd121
- Safety: [{"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\edit-213654-663805\\E\\KenshiProject\\2.Projects\\IrisArsenal\\package\\IrisArsenal\\IrisArsenal.ini", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\edit-213654-665362\\E\\KenshiProject\\2.Projects\\IrisArsenal\\package\\IrisArsenal\\IrisArsenal.ini"], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}]

## E:\KenshiProject\2.Projects\IrisArsenal\tools\test_audit052.py

- Role: 052日志回归
- Code location: Active门
- Changes: 要求055明细开关叠加原总开关，不放松全关条件
- Reasons: 新增通道不能绕过EnableLogging/Performance开关
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: 非编译验证
- Before: cdd349ef3a44de59aa2bcc8cc1e9fc7aa5633a2cf1879d6acb788bcd29f18d19
- After: 352b24b84e21612c23c845f73ccc782091d5a4861c16766b7a1a94b11c005d3e
- Safety: [{"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\edit-214026-279023\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\test_audit052.py", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\edit-214026-282027\\E\\KenshiProject\\2.Projects\\IrisArsenal\\tools\\test_audit052.py"], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}]

## E:\KenshiProject\2.Projects\IrisArsenal\docs\collision-damage-055.md

- Role: 055交付说明
- Code location: 实现/配置/证据/边界/编译
- Changes: 记录实际实现与可关闭诊断，不承诺未测FPS
- Reasons: 用户要求优化及日志并保存经验
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: C++/PhysX/游戏待用户编译与测试
- Before: new
- After: 3b3b757b660d7c18cf7c79b9f239b9e0496790fe9687acb0a54cda86ad4546b1
- Safety: [{"backups": [], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}]

## E:\KenshiProject\2.Projects\IrisArsenal\docs\formal-release-1.0.md

- Role: 正式版入口
- Code location: 版本、哈希、恢复索引
- Changes: 在项目中提供可找回的正式版位置
- Reasons: 封存版本不可被后续工作状态混淆
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: 完整边界见归档LESSONS.md
- Before: new
- After: b8efb8e9260736eb4b2a8ef3bed5a825a4cc35bf2b4f0caa68b3d726c0d55b7e
- Safety: [{"backups": [], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}]

## E:\KenshiProject\2.Projects\IrisArsenal\STATE.md

- Role: 项目单写者状态
- Code location: 当前状态前置段
- Changes: 区分封存1.0、优化源码和实际旧DLL
- Reasons: 避免历史未部署文字被当作当前身份
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: 静态验证不等于用户编译或实机
- Before: 89c543738eb54630207067abb4ca51a2adabab666717b226eff221f12022ee60
- After: 89710163fd817dd36342c2192916f90871e3d0d62024fafeccfa4055f8016772
- Safety: [{"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\edit-214605-060465\\E\\KenshiProject\\2.Projects\\IrisArsenal\\STATE.md", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\edit-214605-062968\\E\\KenshiProject\\2.Projects\\IrisArsenal\\STATE.md"], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}]

## E:\KenshiProject\2.Projects\IrisArsenal\README.md

- Role: 项目使用说明
- Code location: 当前版本与配置入口
- Changes: 补充正式版和优化版边界及新日志键
- Reasons: 用户需要不用猜版本和是否部署
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: 没有055实际FPS结论
- Before: e608724cc95d2568c9fbc1600c29809c790802d279a0d2e0abc7d836ea9e007d
- After: 5d9ec723eeaf757a47d7bfa1ae4b4295ed8c64a8f73aec21d9ca075332c80a76
- Safety: [{"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\edit-214605-068973\\E\\KenshiProject\\2.Projects\\IrisArsenal\\README.md", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\edit-214605-069972\\E\\KenshiProject\\2.Projects\\IrisArsenal\\README.md"], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}]

## D:\CodexWorkSpace\ExperienceNotes\Kenshi-Combat-Animation-Porting-Playbook.md

- Role: 长期经验只追加
- Code location: IrisArsenal首版/055补充
- Changes: 追加事实、被淘汰错误和验证限制，历史正文不改
- Reasons: 用户要求以后复刻沿用经验
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: 055仍待用户编译和实机
- Before: 90a4a4a3b177d593e38670801ad2b482c32c4f853a0977d366a5bdc093cac360
- After: 9c3ab2da1a74a5719b9491d06ff77a1698f2005d014a0f779afba01e5e707aff
- Safety: [{"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\edit-214605-074972\\D\\CodexWorkSpace\\ExperienceNotes\\Kenshi-Combat-Animation-Porting-Playbook.md", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\edit-214605-075972\\D\\CodexWorkSpace\\ExperienceNotes\\Kenshi-Combat-Animation-Porting-Playbook.md"], "encoding": "utf-8", "line_ending": "'\\n'", "mojibake_check": "pass"}]

## E:\AIWorkSpace\_notes\code-notes.md

- Role: 共享经验只追加
- Code location: 本次IrisArsenal条目
- Changes: 记录正式版与优化状态，不改历史取证
- Reasons: 共享上下文需有实际证据和未验证边界
- Impact: 仅本轮正式版文档或优化工作树；不改游戏目录，不编译
- Validation: 严格编码/换行/中文回读；Python文件AST；行为验证另见validation.json
- Unresolved: 不能据此宣布055实机稳定
- Before: ff57a19c41a929e52d7c334d8cdb785e61319cc16ee9ea7f596711ca50913347
- After: ace6af45e52c7fc392a9b1d24b059a4fd32382d74057144d4a50ecc180fcba04
- Safety: [{"backups": ["D:\\CodexBackups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\edit-214605-080972\\E\\AIWorkSpace\\_notes\\code-notes.md", "E:\\AIWorkSpace\\_backups\\Iris-Formal1-Optimize055-20261018-211300-34f16b\\edit-214605-082320\\E\\AIWorkSpace\\_notes\\code-notes.md"], "encoding": "utf-8", "line_ending": "'\\r\\n'", "mojibake_check": "pass"}]

