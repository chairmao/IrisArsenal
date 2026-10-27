@echo off
chcp 65001 >nul
"C:\Users\周凡稀\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B -X utf8 "%~dp0tools\read_audit052.py" %*
pause
