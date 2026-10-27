# IrisArsenal 0.2.2：火神/脉冲瞄准与显存复核

实际运行的是用户编译的0.2.1，DLL SHA256 F4BE82FBFCEFC79F8AD1F5FF5630D9E43A574AE7BAC6AB08651C80890CE5BEB5。19:23:32.958日志中，弹体出生(-16333.8,200.301,29543.4)，瞄准却到(-32622.9,236.375,58827.6)。0.2.1未记录目标根/原始骨点，因此不能虚构那次目标的精确胸部坐标。

经实际导出槽/RVA离线核对，Character原生包装直接返回骨点；内部已有节点位置、方向、角色比例。旧Target又加(getPosition-derivedPosition)，重复施加原点。022直接消费原生世界骨点；枪口仍由实际武器附件转换到物理世界，绘制再转回场景。没有关掉地形碰撞、抬高全部弹体、强转角色或制造伤害。

仅vulcan=1、pulse=1，其余0；火神20发/弹体球R4.5/爆炸球R4.5；脉冲3发/每发2倍/爆炸球R9，为火神半径两倍。脉冲小碰撞核心R0.7保持，装饰尾环不作碰撞；三层等离子模型对应源ESP PROJ 0x040008D1与PlasmaBall.nif，恢复既有统一比例后的源可视大小。火神已物理命中的免格挡闪避保持，未把该防御策略扩展给脉冲。

显存：实际19:23:08游戏日志显示同源2048² PNG按两个文件名各加载一次（iris_anim_rgba_...与iris_fx_...），且只开火神也预热全部10类。022复用同一PNG名字/同像素；启用两招只预热gun、bullet、shell、blast、exhaust共5类。PNG按RGBA8完整mip估算旧62,674,300B→新36,787,560B，约减少24.7MiB；估算不含DDS/网格/驱动/游戏其他模组，不是实测GPU占用，也不能解释全部数GB显存或证明泄漏。游戏已退出，无该次GPU历史计数。自有实体/池有界，新增仅递增高水位日志，不能用它代替显存计数。

非编译验收：非零/零世界原点反例、源等离子/火神材质、16份FCS实际骨架引用、8招事件次数/范围、同像素纹理和语法树通过。旧021 DLL组包被022合同拒绝。身体/源HKX/FCS距离/基础0.1武器伤害/医疗队列与enemy过滤未变。MSVC类型/链接、HLSL执行、真实骨点/枪口方向/倒地与坡地命中、显存降幅仍须实机。

按 code-modification-principles/SKILL.md 的“Never attempt to compile, build, link, or regenerate binaries during a conversation.”以及E:/KenshiProject/AGENTS.md“不代编译”要求，本轮没有编译。用户编译 IrisArsenal.sln / Release|x64 / v100 后运行PreparePackage.cmd，再完整同步游戏mod；不能直接用旧DLL配称022。当前仅兼容INI与moves.csv参数及校验清单已同步游戏（游戏无进程），游戏DLL/特效仍021；022完整包ready=false。

安全：改已存在文件前双外部备份，UTF-8/BOM与原换行保持，写后中文/乱码和字节回读通过。逐文件报告见aim-pulse-0.2.2-files.json，直接证据见aim-pulse-0.2.2-evidence.json。没有启动游戏、恢复轮询、附加调试器或修改其他项目。
