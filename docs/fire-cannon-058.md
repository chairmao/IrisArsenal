# 058：火焰视觉2倍速与电脉枪口共线

工作源码为 **0.4.15 / IRIS_FIRE_CANNON_058**。修改前用户已经编译部署0.4.14 / IRIS_RANGED_RAY_057，bin与游戏DLL SHA256均为 `14f3ee85645fe3079ceb67d7657f9f7480864338dec64f5bfc6034e935cefe0e`。058本轮没有编译、部署或游戏实测；正式版1.0归档保持。

## 实现和依据

- 火焰翻滚 `roll_blast` 与全力爆发末击 `full_blast`：原6.5秒源后效以2倍视觉时钟播放，生命周期变为3.25游戏秒，再乘既有攻速/游戏速度关系。源颜色、UV、变形曲线和GPU粒子寿命/速度均使用相同加速年龄，不是只把最后消失时间提前。
- 钻天破末击 `drill_blast`：实际13层中前5层为蓝色电离、后8层为火焰。原蓝相0～0.52秒和0.56秒火相切换点保持；火相使用 `0.56 + (age - 0.56) × 2`，原7.06秒后效变为3.81游戏秒。火焰末端透明度也按源年龄收尾，蓝色不被加速或提前截断。
- 复用当前已校准的 `VoiceFlameWaveProject03.nif` → `MPSFireWaveFlames.nif` 原火浪与粒子、`ALSEXP.nif` 原蓝相、`beam.nif` 原电脉光柱。当前130份非DLL运行资源（模型、贴图、材质、动画、FCS、配置）逐字节保持；没有补造或替换素材。小点火、地震、脉冲爆炸等其他后效不加速。
- 电脉偏轴的直接代码原因：旧光柱/球心使用起手时的 `a.heading`，实际锤枪却随当前原生动作/转向变化。现在 `ElectroFrame` 从 `ActualWeapon` → `SourcePose` 读取当帧枪口和源Z轴，并由 `ShowParts` / `Emit(kind=9)` 共同消费。角色瞄准仍交给原生战斗，不另行设置角色朝向、位置或骨骼；不把光柱单独指向另一条目标连线。
- 几何合同：`muzzle = weapon * (1.807138657, 0, 8.534358047) + origin`；`axis = normalize(weapon.columnZ)`；`center = muzzle + axis * (20 - dot(muzzle - actorRoot, axis))`；`beamReach = dot(center - muzzle, axis) + radius`。伤害球心严格落在枪口轴线上，同时保留相对角色根点的轴向前20，R25保持。球心横向/高度改为实际枪口轴投影，替代旧的缓存方向+单独抬高Y，避免只改显示而留下另一套碰撞坐标。
- 每段成功出手仍保存自己的值快照；已生成范围后效不追踪目标。四次球形命中仍分别在原事件点独立入队，无新增健康事件。倍率、次数、enemy、护甲/部位、经验、防御策略、2.5ms/32 FIFO、64次查询、安全窗口、暂停、读档和后效所有权保持。

## 日志与构建

启动可见 `fire_cannon_ready contract=IRIS_FIRE_CANNON_058 fire_visual_speed=2 drill_blue_speed=1 ...`。前20次电脉成功脉冲记录 `electro_muzzle_axis`，含枪口、轴、球心、半径及光柱长度，不新增逐帧日志。日志头/运行身份改为0.4.15/058，修正遗留056身份字段。

按现有Skill编译边界，本轮没有编译或重新生成DLL。请编译 **IrisArsenal.sln → Release|x64 / v100**，正常退出游戏，再运行 **UpdateMod.cmd**。更新脚本的新058合同与源码时间门会拒绝旧057 DLL；本轮的package标记为ready=false，保留旧DLL原字节，不冒充新效果。

## 实际验证与边界

`tools/test_fire_cannon058.py` 读取真实运行曲线/网格以及男女序列化动作，检查2,328次源曲线状态对应、蓝相保持、8个真实射击姿态、2,000组随机轴/浮动原点、无效方向拒绝、130份运行资源不变、8个核心战斗函数摘要保持。原版偏轴用60°转向负例检出；旧DLL必须被058组包门拒绝。完整回归及语法结果见 `validation-fire-cannon-058.json`，更新/IO沙盒另执行22项。

本任务目录保存真实身体/锤体CPU蒙皮预览与轴线对照、实际源alpha曲线图。这些是离线几何/时序证据，不是游戏截图、GPU/PhysX执行或FPS测量。仍需新DLL编译、运行时Shader及实际原生瞄准/多人战斗验收，不能据此保证游戏表现完全无偏差。

## 备份和逐文件记录

本轮所有旧小文件在写入前双备份，UTF-8/BOM/CRLF或LF保持，中文回读与乱码扫描。具体备份、改动位置、摘要和验证在任务 `reports/`、`original-hashes.json`、`validation.json`，授权函数差异在 `authorized-delta-058.json`。
