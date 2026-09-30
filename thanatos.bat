@echo off
rem Thanatos Universal Windows Launcher
setlocal
set "SCRIPT_DIR=%~dp0"
if exist "%SCRIPT_DIR%venv\Scripts\python.exe" (
    "%SCRIPT_DIR%venv\Scripts\python.exe" "%SCRIPT_DIR%thanatos_cli.py" %*
) else (
    python "%SCRIPT_DIR%thanatos_cli.py" %*
)
endlocal
