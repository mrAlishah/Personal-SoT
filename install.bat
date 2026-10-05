@echo off
setlocal
set "ROOT_DIR=%~dp0"

where py >nul 2>nul
if not errorlevel 1 (
  py -3 "%ROOT_DIR%system\install\installer.py" %*
  exit /b
)

where python >nul 2>nul
if not errorlevel 1 (
  python "%ROOT_DIR%system\install\installer.py" %*
  exit /b
)

echo Python 3.10 or newer is required. 1>&2
exit /b 1
