@echo off
setlocal
cd /d "%~dp0"

:menu
cls
echo ========================================
echo              Codex++ Setup
echo ========================================
echo.
echo [1] Install Codex++
echo [2] Uninstall Codex++
echo [3] Exit
echo.
set /p choice=Please select an option [1-3]:

if "%choice%"=="1" goto install
if "%choice%"=="2" goto uninstall
if "%choice%"=="3" goto end

echo.
echo Invalid choice.
pause
goto menu

:install
echo.
echo Installing Python package...
python -m pip install -e .
if errorlevel 1 goto error
echo.
echo Installing Codex++ shortcut and uninstall entry...
python -m codex_session_delete setup
if errorlevel 1 goto error
echo.
echo Codex++ installed successfully.
echo You can launch it from the Codex++ desktop shortcut.
pause
goto end

:uninstall
echo.
echo Uninstalling Codex++ shortcut and uninstall entry...
python -m codex_session_delete remove
if errorlevel 1 goto error
echo.
echo Codex++ uninstalled successfully.
pause
goto end

:error
echo.
echo Operation failed. Please check the error output above.
pause
exit /b 1

:end
endlocal
