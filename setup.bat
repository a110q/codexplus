@echo off
setlocal
cd /d "%~dp0"

set "VENV_DIR=%~dp0.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"

:menu
cls
echo ========================================
echo              Codex++ Setup
echo ========================================
echo.
echo [1] Install Codex++
echo [2] Uninstall Codex++
echo [3] Update Codex++
echo [4] Exit
echo.
set /p choice=Please select an option [1-4]:

if "%choice%"=="1" goto install
if "%choice%"=="2" goto uninstall
if "%choice%"=="3" goto update
if "%choice%"=="4" goto end

echo.
echo Invalid choice.
pause
goto menu

:install
echo.
call :ensure_venv
if errorlevel 1 goto error
echo Installing Codex++ into venv...
"%VENV_PY%" -m pip install -e .
if errorlevel 1 goto error
echo.
echo Installing Codex++ shortcut and uninstall entry...
"%VENV_PY%" -m codex_session_delete setup
if errorlevel 1 goto error
echo.
echo Codex++ installed successfully.
echo You can launch it from the Codex++ desktop shortcut.
pause
goto end

:uninstall
echo.
if exist "%VENV_PY%" (
    set "RUNPY=%VENV_PY%"
) else (
    echo Codex++ venv not found, falling back to system python.
    set "RUNPY=python"
)
echo Uninstalling Codex++ shortcut and uninstall entry...
"%RUNPY%" -m codex_session_delete remove
if errorlevel 1 goto error
echo.
echo Codex++ uninstalled successfully.
pause
goto end

:update
echo.
call :ensure_venv
if errorlevel 1 goto error
echo Updating Codex++ from GitHub Release...
"%VENV_PY%" -m codex_session_delete update
if errorlevel 1 goto error
echo.
echo Codex++ update finished.
pause
goto end

:ensure_venv
if exist "%VENV_PY%" exit /b 0
echo.
echo Creating Python virtual environment at "%VENV_DIR%"...
python -m venv "%VENV_DIR%"
if errorlevel 1 (
    echo Failed to create venv. Make sure Python 3.11+ is installed and available on PATH.
    exit /b 1
)
echo Upgrading pip / setuptools / wheel inside venv...
"%VENV_PY%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 exit /b 1
exit /b 0

:error
echo.
echo Operation failed. Please check the error output above.
pause
exit /b 1

:end
endlocal
