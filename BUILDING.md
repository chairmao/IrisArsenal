# 编译IrisArsenal源码工程

当前源码：0.4.54 / IRIS_HOLDER_TIMELINE_104；正式归档名称3.0。用户已在原环境编译出对应DLL。本仓库包含完整C++工程与原生PhysX头文件，不包含游戏运行资源包、DLL/PDB或商业游戏文件。

## 依赖与目标

- Windows x64，Visual C++ v100工具集及Windows SDK；打开IrisArsenal.sln，选择Release | x64。
- 外部KenshiLib依赖根目录需要Include与Libraries。工程使用KenshiLib.lib、OgreMain_x64.lib、MyGUIEngine_x64.lib；Version.lib来自Windows SDK。不要把KenshiLib的Source/core/Functions_static.cpp重复编入。
- Boost 1.60头与stage/lib中的v100 x64多线程库，保持与原工程ABI一致；thread/system/date_time/chrono等由依赖头自动链接。
- native/physx284保存有来源清单的PhysX 2.8.4.6原始头。它们是编译接口，不附运行库；运行时最低版本/scene-SDK检查仍在插件内。
- 当前已验证环境：依赖目录名KenshiLib_0.5.0，实际导入库0.5.0、Include基线0.5.1。目录名称不能替代库/头/游戏版本核对，相关历史与ABI边界见docs/formal3。

## 目录及路径

原工程默认布局（与当前vcxproj一致）：

```text
KenshiProject/
  1.Dependencies/
    KenshiLib_0.5.0/
      Include/
      Libraries/
    boost_1_60_0/
      boost/
      stage/lib/
  2.Projects/
    IrisArsenal/       # 克隆本仓库到这里
    bin/Release/      # 原工程DLL输出位置
```

若使用其他布局，可以在用户自己的构建命令中覆盖原有全局属性，无需改C++或写死机器路径，例如：

```bat
msbuild IrisArsenal.sln /p:Configuration=Release /p:Platform=x64 /p:DepsDir="C:\KenshiDeps\KenshiLib_0.5.0" /p:BoostDir="C:\KenshiDepsoost_1_60_0"
```

这里只提供用户可运行的命令；上传过程不执行编译，也不宣称在其他机器验证过。

## 配置、运行与工具

vcxproj的两个None项IrisArsenal.ini及RE_Kenshi.json仍保留在package/IrisArsenal，便于IDE查看，和distribution中的模板一起纳入Git。DLL编译不需要动画/模型/贴图/FCS包。

在游戏中使用仍需另外取得匹配的运行资源及RE_Kenshi/KenshiLib；不要将源码仓库当作可直接复制进mods的完整发行包。PrepareAssets/PreparePackage/UpdateMod涉及本地素材或资源闭包，此源码仓库不附这些资源，所以它们不能单独替代资源安装。部分历史测试也依赖本地资源或会话证据，不能声称克隆后全部测试零配置可跑。

原生调用链、十招事件、特效作者方案、性能优化与失败经验、新武器项目规格模板见[项目总结](docs/formal3/README.md)。外部依赖及第三方源码仍遵守各自许可证，见THIRD_PARTY_NOTICES.md。
