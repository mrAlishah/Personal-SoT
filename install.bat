@echo off
setlocal
set "ROOT_DIR=%~dp0"

where py >nul 2>nul
if %ERRORLEVEL%==0 (
  py -3 "%ROOT_DIR%system\install\installer.py" %*
  exit /b %ERRORLEVEL%
)

where python >nul 2>nul
if %ERRORLEVEL%==0 (
  python "%ROOT_DIR%system\install\installer.py" %*
  exit /b %ERRORLEVEL%
)

echo Python 3.10 or newer is required. 1>&2
exit /b 1
