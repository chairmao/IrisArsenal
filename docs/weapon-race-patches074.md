# 074：正式武器数值与两个独立种族动画补丁

本轮按用户2026-10-22要求修改FCS，并按后续澄清将动画兼容制作成两个新mod。原ep_ikemen_Animation_Patch_My.mod和End Poem MC_My.mod的SHA256保持，不修改模组勾选、排序或存档。

## 武器最终数据

项目package/IrisArsenal/IrisArsenal.mod与游戏mods/IrisArsenal/IrisArsenal.mod已同步，武器StringID仍为1-IrisArsenal.mod。

| 字段 | 之前 | 现在 |
|---|---:|---:|
| cut damage multiplier | 0.144 | 1.44 |
| blunt damage multiplier | 0.12 | 1.20 |
| bleed mult | 1 | 2.5 |
| attack mod | +15 | +20 |
| defence mod | +8 | +10 |
| indoors mod | −8 | 0 |
| armour penetration | 0.5 | 0.5（保持） |

正式基础伤害恢复Falling Sun×1.2，等于本轮修改前测试值的10倍（FCS单精度有正常舍入差）。每招独立倍率、范围、权重、姿态/医疗判断、特效及DLL保持。修正FCS头部与作者中的旧十分之一伤害说明。weapon_balance053.py是唯一平衡来源，author_moves.py完整重建时消费相同七个字段；日常UpdateMod.cmd继续复制当前包，数值不会被旧作者覆盖。

## 独立补丁与加载

- IrisArsenal_IKEMEN_Patch：读取ep_ikemen_Animation_Patch_My中的IKEMEN种族5008011-ep_ikemen.mod，共1个种族。
- IrisArsenal_EndPoem_Patch：严格读取End Poem MC_My里的97个RACE StringID，包含其原已覆盖的机器人与其他人形种族。

两份已分别保存到本工程compatibility目录，并复制到D:/steam/steamapps/common/Kenshi/mods/下各自同名目录。每份只含新增mod与对应info；不复制DLL或动画资源。每个RACE覆盖记录只有animation files新增引用30..39-IrisArsenal.mod，没有任何生命、种族模型、速度、武器或医疗字段。动画文件继续由IrisArsenal原有10套男女资源提供。

使用时在启动器勾选这两个新补丁，放在对应原模组、实际种族模组和IrisArsenal之后。原模组顺序保持。不自动修改data/mods.cfg。之后更新Iris主包不会删除这两个独立目录。需要重新生成补丁时，可使用现有局部Python执行tools/author_race_patches074.py；它只写项目compatibility，不编译或自动部署。源补丁种族数量变化时会明确停止，需重新核对覆盖范围。

## 实际验证及边界

1. 两处武器FCS实际完整解析、逐字段回读和字节往返一致；除武器记录及文件说明外，47条记录原字节保持。
2. 实际执行author_moves.fcs_assets并拦截写入，其全部记录与候选文件逐条一致，证明当前完整FCS生成路径不会撤销本轮修改；未重建动画/特效。
3. 两处完整运行清单各129个文件SHA256逐项通过，清单只更新FCS摘要。数值补丁重复应用不产生变化。
4. 两个新补丁StringID集合分别与原补丁的1/97个RACE完全相同，重复生成字节一致，字段范围仅新增十套引用。显式依赖原补丁与IrisArsenal，引用均指向真实112动画集。
5. 实际读取20份男女序列化骨架，核对内部动画名和时长；不是仅验证文件存在。三份Python AST通过，UTF-8/LF和中文乱码检查通过。
6. 136个C++/H、DLL、特效/模型/动画和原补丁文件SHA256保持。未编译、启动/终止游戏、附加调试器或游戏实测；不能据此保证所有特殊种族的实机握点、体型或动作表现。

## 备份、报告与恢复

修改前所有既有小文件都备份到D:/CodexBackups/Task-Iris-FCS074-20261022-182426-4ee3db/及E:/AIWorkSpace/_backups/Task-Iris-FCS074-20261022-182426-4ee3db/，按原盘符和相对路径保存。原mod二进制中的未修改字符串保持原字节；既有Python/JSON/STATE的UTF-8、BOM与换行分别保持。新文本为UTF-8/LF。

完整候选、验证、覆盖名单及每文件报告位于：D:/CodexWorkSpace/Sessions/20261002-235652-kenshi-crash-407794f2/Task-Iris-FCS074-20261022-182426-4ee3db。逐文件报告report-*.json在每次修改后立即写入，含目的、影响、验证和备份路径。

恢复武器数值时应一并恢复weapon_balance053.py、author_moves.py、两处IrisArsenal.mod及IrisPackage.json，避免生成器和摘要不一致。两个新补丁可在启动器取消勾选；原补丁没有被改动。本轮无需重新编译DLL。
