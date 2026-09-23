# Open Protocol 设备模拟器 (独立运行包)

本项目为基于工业标准的 Atlas Copco / Desoutter 拧紧控制器数字孪生模拟器，集成了 Open Protocol (TCP 4545/8080)、REST API 以及 Web 可视化控制台。

---

## 目录结构说明

```
OpenProtocolSimulator-Dist/
├── 启动模拟器.command         # macOS 双击启动脚本 (终端方式)
├── 启动模拟器.bat             # Windows 双击启动脚本 (批处理)
├── OpenProtocolSimulator.app  # macOS 双击启动图标 (App形式)
├── simulator_gui.py          # 跨平台桌面控制中心 (Python Tkinter)
├── config.toml               # 模拟器默认配置文件 (端口、设备信息)
├── simulator.db              # 模拟器状态与协议策略数据库 (已预置全兼容模式)
├── quick_test_client.py      # Python 快捷测试脚本
├── bin/
│   ├── open-protocol-device-simulator       # macOS (ARM64 Apple Silicon) 原生编译程序
│   └── open-protocol-device-simulator.exe   # Windows 64位程序 (放置此处即可在 Windows 上直接运行)
└── README_使用说明.md
```

---

## 一、macOS 系统使用指南

1. **直接启动方式**：
   - 方式 A：双击文件夹中的 **`OpenProtocolSimulator.app`**。
   - 方式 B：双击 **`启动模拟器.command`**。
2. **浏览器 Web 仪表盘**：
   - 服务启动后，浏览器会自动打开 `http://localhost:8082`。

---

## 二、Windows 系统是否支持直接打开使用？

### 核心结论：
- **GUI 控制界面支持**：控制中心界面由 Python 标准库（Tkinter）编写，在 Windows 下**完全兼容**。
- **底层二进制差异**：目前的 `bin/open-protocol-device-simulator` 是在 macOS (Mach-O ARM64) 下编译的，**Windows 无法直接执行 macOS 的机器码**。
- **如何让 Windows 支持直接双击打开？**
  只需将一份 Windows 版的 `open-protocol-device-simulator.exe` 放入 `bin/` 文件夹中，在 Windows 下双击 `启动模拟器.bat` 即可**直接运行**！

### 在 Windows 上获取 `open-protocol-device-simulator.exe` 的三种方法：

#### 方法 1：在任意装有 Rust 的 Windows 电脑上编译（最简单推荐）
1. 复制原项目源码 `open-protocol-device-simulator` 文件夹到 Windows 电脑。
2. 打开 Windows CMD 或 PowerShell：
   ```cmd
   cd open-protocol-device-simulator
   cargo build --release
   ```
3. 编译完成后，在 `target\release\` 目录下会生成 `open-protocol-device-simulator.exe`。
4. 将该 `open-protocol-device-simulator.exe` 复制到本文件夹的 `bin\` 目录即可。

#### 方法 2：利用 GitHub Actions 自动构建 Windows 二进制
如果将代码推送到 GitHub，只需添加一个 Windows 构建工作流（.github/workflows/build-windows.yml），GitHub 会自动在云端编译出 Windows `.exe` 并供下载。

#### 方法 3：通过跨平台交叉编译工具
在具备 Docker 或 MinGW 的 Linux/Mac 上使用 `cargo build --target x86_64-pc-windows-gnu` 编译。
