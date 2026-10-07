@echo off
setlocal
set "ROOT_DIR=%~dp0"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

where py >nul 2>nul
if not errorlevel 1 (
  py -3 "%ROOT_DIR%system\install\install.py" %*
  exit /b
)

where python >nul 2>nul
if not errorlevel 1 (
  python "%ROOT_DIR%system\install\install.py" %*
  exit /b
)

echo Python 3 is required. 1>&2
exit /b 1
