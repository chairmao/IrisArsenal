@echo off
chcp 65001 >nul
setlocal
rem 使用已有局部Python，不下载依赖，不编译DLL，错误码原样返回。
set "IRIS_PY=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
set "PYTHONDONTWRITEBYTECODE=1"
set "PYTHONIOENCODING=utf-8"
if not exist "%IRIS_PY%" (
 echo 未找到局部Python：%IRIS_PY%
 pause
 exit /b 1
)
rem 只组包已有资源和已编译DLL，再双备份、清空目标并完整复制；不重建资源、不跑历史测试。
echo 全量更新IrisArsenal：旧配置和日志将移入备份，新配置以项目distribution为准。
"%IRIS_PY%" -B -X utf8 "%~dp0tools\update_mod.py"
set "IRIS_RESULT=%ERRORLEVEL%"
if not "%IRIS_RESULT%"=="0" echo 操作失败，请查看上面的原因。没有执行C++编译。
pause
exit /b %IRIS_RESULT%
