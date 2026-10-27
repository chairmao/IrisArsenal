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
rem 补全基础文件后生成当前资源，不编译、不部署。
"%IRIS_PY%" -B -X utf8 "%~dp0tools\rebuild_package.py"
if errorlevel 1 exit /b 1
"%IRIS_PY%" -B -X utf8 "%~dp0tools\verify_moves.py"
set "IRIS_RESULT=%ERRORLEVEL%"
if not "%IRIS_RESULT%"=="0" echo 操作失败，请查看上面的原因。没有执行C++编译。
pause
exit /b %IRIS_RESULT%
