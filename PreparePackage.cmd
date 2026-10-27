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
rem 仅恢复和组包，不写游戏目录。
"%IRIS_PY%" -B -X utf8 "%~dp0tools\update_mod.py" --package-only
set "IRIS_RESULT=%ERRORLEVEL%"
if not "%IRIS_RESULT%"=="0" echo 操作失败，请查看上面的原因。没有执行C++编译。
pause
exit /b %IRIS_RESULT%
