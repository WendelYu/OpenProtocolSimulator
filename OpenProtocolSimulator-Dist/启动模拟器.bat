@echo off
setlocal
title Open Protocol Device Simulator

pushd "%~dp0"

echo =========================================================
echo       Open Protocol Device Simulator
echo =========================================================
echo.

:: 1. Check if standalone GUI executable exists
if exist "OpenProtocolSimulator-GUI.exe" (
    echo [1/3] Launching standalone GUI Control Center...
    start "" "OpenProtocolSimulator-GUI.exe"
    goto END
)

:: 2. Check if Python with tkinter is available
where python >nul 2>nul
if %ERRORLEVEL% equ 0 goto TRY_PYTHON

where py >nul 2>nul
if %ERRORLEVEL% equ 0 goto TRY_PY

goto NO_PYTHON

:TRY_PYTHON
echo [2/3] Checking Python GUI environment...
python -c "import tkinter" >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo       Starting GUI Control Center (simulator_gui.py)...
    start "" pythonw simulator_gui.py 2>nul || python simulator_gui.py
    goto END
)
echo [WARN] Python is installed but tkinter GUI module is not available.
goto NO_PYTHON

:TRY_PY
echo [2/3] Checking py GUI environment...
py -c "import tkinter" >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo       Starting GUI Control Center (simulator_gui.py)...
    start "" py -3 simulator_gui.py 2>nul || py simulator_gui.py
    goto END
)
echo [WARN] py launcher is installed but tkinter GUI module is not available.
goto NO_PYTHON

:NO_PYTHON
echo.
echo =========================================================
echo [INFO] Python/GUI not found. Starting backend server...
echo.
echo 1. Web Dashboard: http://localhost:8082
echo 2. How to STOP: Press Ctrl+C in this console window.
echo 3. To get the Desktop GUI with Start/Stop buttons:
echo    Install Python 3 with Tcl/Tk from https://python.org
echo    or download OpenProtocolSimulator-GUI.exe
echo =========================================================
echo.

if exist "bin\open-protocol-device-simulator.exe" (
    start http://localhost:8082
    "bin\open-protocol-device-simulator.exe" --config config.toml
    goto END
)

if exist "open-protocol-device-simulator.exe" (
    start http://localhost:8082
    "open-protocol-device-simulator.exe" --config config.toml
    goto END
)

if exist "target\release\open-protocol-device-simulator.exe" (
    start http://localhost:8082
    "target\release\open-protocol-device-simulator.exe" --config config.toml
    goto END
)

echo.
echo [ERROR] open-protocol-device-simulator.exe was not found!
echo Please download from https://github.com/WendelYu/OpenProtocolSimulator/releases
echo.
pause

:END
popd
endlocal
