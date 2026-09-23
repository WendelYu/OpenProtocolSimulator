# Open Protocol 模拟器 Windows 自动化构建与打包脚本 (PowerShell)
[CmdletBinding()]
param (
    [string]$DistPath = "..\OpenProtocolSimulator-Dist"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host "      Open Protocol 模拟器 Windows 自动化构建与打包 (PowerShell)    " -ForegroundColor Cyan
Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检查 Rust 环境
Write-Host "[1/5] 检查 Rust 编译环境 (cargo)..." -ForegroundColor Yellow
if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
    Write-Error "未找到 cargo 命令！请先从 https://rustup.rs/ 安装 Rust 环境。"
    exit 1
}
$cargoVersion = (cargo --version)
Write-Host "      已就绪: $cargoVersion" -ForegroundColor Green

# 2. 检查 Node.js / npm 环境
Write-Host "`n[2/5] 检查 Web 前端构建环境 (npm)..." -ForegroundColor Yellow
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Error "未找到 npm 命令！模拟器内嵌了 Web 管理控制台，请从 https://nodejs.org/ 安装 Node.js。"
    exit 1
}
$npmVersion = (npm --version)
Write-Host "      已就绪: npm v$npmVersion" -ForegroundColor Green

# 如果前端尚未安装 node_modules，自动安装依赖
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "      未检测到前端依赖，正在执行 npm install..." -ForegroundColor DarkYellow
    Push-Location "frontend"
    npm install
    Pop-Location
}

# 3. 编译 Release 二进制
Write-Host "`n[3/5] 开始编译 Release 二进制 (cargo build --release)..." -ForegroundColor Yellow
Write-Host "      正在构建嵌入式 WebUI 并编译 Rust 内核，请稍候..." -ForegroundColor Gray

cargo build --release
if ($LASTEXITCODE -ne 0) {
    Write-Error "Cargo release 编译失败，请检查编译输出！"
    exit $LASTEXITCODE
}

$exePath = "target\release\open-protocol-device-simulator.exe"
if (-not (Test-Path $exePath)) {
    Write-Error "未找到构建完成的二进制文件: $exePath"
    exit 1
}

# 4. 复制产物到发布目录
Write-Host "`n[4/5] 正在同步打包文件至发布目录..." -ForegroundColor Yellow

$resolvedDist = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot $DistPath))
$distBin = Join-Path $resolvedDist "bin"

if (-not (Test-Path $distBin)) {
    New-Item -ItemType Directory -Path $distBin -Force | Out-Null
    Write-Host "      创建分发目录: $distBin" -ForegroundColor Gray
}

# 复制可执行文件
Write-Host "      - 复制内核程序 -> $distBin\open-protocol-device-simulator.exe" -ForegroundColor Gray
Copy-Item -Path $exePath -Destination (Join-Path $distBin "open-protocol-device-simulator.exe") -Force

# 本地 bin 备份
if (-not (Test-Path "bin")) { New-Item -ItemType Directory -Path "bin" -Force | Out-Null }
Copy-Item -Path $exePath -Destination "bin\open-protocol-device-simulator.exe" -Force

# 复制脚本和文件
$filesToCopy = @("simulator_gui.py", "quick_test_client.py", "启动模拟器.bat")
foreach ($file in $filesToCopy) {
    if (Test-Path $file) {
        Write-Host "      - 复制脚本文件: $file -> $resolvedDist" -ForegroundColor Gray
        Copy-Item -Path $file -Destination $resolvedDist -Force
    }
}

# 配置文件（如果目标已有则不覆盖）
$destConfig = Join-Path $resolvedDist "config.toml"
if (-not (Test-Path $destConfig) -and (Test-Path "config.toml")) {
    Write-Host "      - 复制默认配置文件: config.toml -> $destConfig" -ForegroundColor Gray
    Copy-Item -Path "config.toml" -Destination $destConfig
}

# 5. 完成提示
Write-Host "`n===================================================================" -ForegroundColor Green
Write-Host " [5/5] 打包成功！所有产物已同步至:" -ForegroundColor Green
Write-Host "       $resolvedDist" -ForegroundColor White
Write-Host "===================================================================" -ForegroundColor Green
Write-Host " 您可以直接进入该目录双击【启动模拟器.bat】启动运行！`n"
