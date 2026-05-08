@echo off
setlocal
cd /d "%~dp0"

py -3.11 -m pip --version >nul 2>nul
if errorlevel 1 (
  python -m pip --version >nul 2>nul
  if errorlevel 1 goto python_error
  python scripts\build_windows_portable.py
  goto end
)

py -3.11 scripts\build_windows_portable.py
goto end

:python_error
echo Python 3.11+ is required to build the Windows portable package.
echo Install Python from https://www.python.org/downloads/windows/ and retry.
exit /b 1

:end
endlocal
