# 第三方来源与许可边界

公开源码不代表仓库全部文件获得同一新许可证。本次没有为用户代码擅自添加MIT、GPL或其他统一授权。

- tools/third_party/anim_skyrim.py、anim_fo4.py保留其原始说明，附带PyNifly-LICENSE.txt（GPL-3.0）；按其原许可使用。
- native/physx284为未修改的NVIDIA PhysX 2.8.4.6接口头，逐文件来源与原始Git blob见该目录provenance.json；没有上传SDK运行库。
- KenshiLib / RE_Kenshi及OGRE/MyGUI、Boost是外部依赖，各自权利与ABI要求独立。本仓库没有重新授权它们，也未打包Kenshi/Skyrim游戏本体。
- 源项目的Skyrim、soulworker_Iris、Elden Rim、CC0光流纹理和封面来源，见distribution/CREDITS.txt等原说明。按用户最终指示，游戏资源包不随本公开源码仓库上传。

源代码中的原版权与来源声明保持。运行、资源制作和二次发布需分别核实对应组件的许可。
