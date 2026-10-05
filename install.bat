@echo off
setlocal
set "ROOT_DIR=%~dp0"

where py >nul 2>nul
if errorlevel 1 goto :python_command
py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
if errorlevel 1 goto :python_command
py -3 "%ROOT_DIR%system\install\installer.py" %*
exit /b

:python_command
where python >nul 2>nul
if errorlevel 1 goto :missing_python
python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
if errorlevel 1 goto :missing_python
python "%ROOT_DIR%system\install\installer.py" %*
exit /b

:missing_python
echo Python 3.10 or newer is required. 1>&2
exit /b 1
