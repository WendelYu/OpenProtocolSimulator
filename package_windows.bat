@echo off
setlocal enabledelayedexpansion
title Open Protocol Simulator Windows Packager

pushd "%~dp0"

echo ===================================================================
echo       Open Protocol Simulator Windows Packager
echo ===================================================================
echo.

echo [1/5] Checking Rust compiler (cargo)...
where cargo >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] cargo was not found in PATH!
    echo Please install Rust from https://rustup.rs/ and try again.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('cargo --version') do echo       Found: %%v

echo.
echo [2/5] Checking Node.js / npm environment (npm)...
where npm >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] npm command was not found!
    echo Node.js is required to build the embedded WebUI.
    echo Please install Node.js from https://nodejs.org/ and try again.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('npm --version') do echo       Found: npm v%%v

if not exist "frontend\node_modules\" (
    echo       Installing frontend dependencies (npm install)...
    pushd frontend
    call npm install
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to install frontend dependencies!
        popd
        pause
        exit /b 1
    )
    popd
)

echo.
echo [3/5] Building Release Binary (cargo build --release)...
echo       Building WebUI and compiling Rust binary. Please wait...
cargo build --release
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Cargo build failed! Check errors above.
    pause
    exit /b 1
)

set "RELEASE_EXE=target\release\open-protocol-device-simulator.exe"
if not exist "%RELEASE_EXE%" (
    echo [ERROR] Could not find %RELEASE_EXE%!
    pause
    exit /b 1
)

echo.
echo [4/5] Syncing output files to distribution directories...

set "DIST_DIR=OpenProtocolSimulator-Dist"
if not exist "%DIST_DIR%" mkdir "%DIST_DIR%"
if not exist "%DIST_DIR%\bin" mkdir "%DIST_DIR%\bin"
if not exist "bin" mkdir "bin"

echo       - Copying kernel: open-protocol-device-simulator.exe
copy /y "%RELEASE_EXE%" "%DIST_DIR%\bin\open-protocol-device-simulator.exe" >nul
copy /y "%RELEASE_EXE%" "bin\open-protocol-device-simulator.exe" >nul

echo       - Copying GUI control center: simulator_gui.py
if exist "simulator_gui.py" copy /y "simulator_gui.py" "%DIST_DIR%\" >nul

echo       - Copying test client: quick_test_client.py
if exist "quick_test_client.py" copy /y "quick_test_client.py" "%DIST_DIR%\" >nul

echo       - Copying launcher scripts:
if exist ".bat" copy /y ".bat" "%DIST_DIR%\" >nul

echo       - Copying configuration: config.toml
if not exist "%DIST_DIR%\config.toml" (
    if exist "config.toml" copy /y "config.toml" "%DIST_DIR%\" >nul
)

echo.
echo ===================================================================
echo [5/5] Packaging Completed Successfully!
echo Output Directory: %DIST_DIR%\
echo ===================================================================
echo.
echo You can now go to %DIST_DIR%\ and double-click launcher to run!
echo.
pause

popd
endlocal
