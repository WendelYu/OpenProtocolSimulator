# OpenProtocolSimulator

基于工业标准的 **Atlas Copco / Desoutter** 拧紧控制器数字孪生模拟器与测试工具箱。

本项目实现了 **Open Protocol**（开放协议）工业以太网通信规范，集成了高性能异步 TCP 服务端、内嵌 Web 可视化管理面板、桌面级 GUI 控制中心以及全功能的 MID 0900 拧紧曲线波形高频仿真引擎。

[![License](https://img.shields.io/badge/License-MIT%20OR%20Apache--2.0-blue.svg)](https://opensource.org/licenses/MIT)
[![Rust](https://img.shields.io/badge/Rust-1.85%2B-blue.svg)](https://www.rust-lang.org)
[![SvelteKit](https://img.shields.io/badge/SvelteKit-5.x-ff3e00.svg)](https://kit.svelte.dev)
[![Build and Release](https://github.com/WendelYu/OpenProtocolSimulator/actions/workflows/build-and-release.yml/badge.svg)](https://github.com/WendelYu/OpenProtocolSimulator/actions/workflows/build-and-release.yml)

---

## 📌 项目干了啥 (Overview & Core Features)

在汽车制造、精密装配等工业场景中，MES（制造执行系统）、SCADA 与工控上位机需要与扭矩拧紧控制器深度集成。然而，物理控制器设备造价昂贵、产线排期紧张、且难以在实际硬件上安全重现超差（NOK）、通讯中断、丢包超时以及大批量连续拧紧工况。

**OpenProtocolSimulator** 提供了完整的软硬件解耦解决方案：

### 🛠️ 包含的两个核心程序 (The Two Core Programs)

本项目构建并产出了相互配合的 **两个核心程序**，满足不同场景下的调试与测试需求：

| 程序名称 | 技术栈 | 核心职责与功能 |
| :--- | :--- | :--- |
| **1. 模拟器服务端内核**<br>`open-protocol-device-simulator` | Rust (Tokio / Axum) + SvelteKit 5 | **服务端角色**：开放标准 TCP 4545 端口模拟真实控制器，处理上位机的 MID 报文交互；内置 HTTP 8082 网页管理面板与 RESTful API，提供参数集配置、作业流程、异常故障注入及 Web 实时曲线监控。 |
| **2. 可视化控制中心客户端**<br>`OpenProtocolSimulator-GUI` (`simulator_gui.py`) | Python (Tkinter 原生跨平台) | **客户端/调试角色**：作为工业客户端直接连接模拟器（或任何第三方实际拧紧枪），支持一键 MID 0001 握手、MID 0060 拧紧结果订阅、MID 0008/0900 曲线实时波形动态绘制、MID 指令一键调试发送与模拟触发。 |

---

## 🌟 核心特性一览

- 🚀 **全面支持标准 Open Protocol 协议族**：
  - **基础通信**：MID 0001/0002/0003/0004/0005 连接建立、拒绝、保活心跳（MID 9999）
  - **参数集 (PSET)**：MID 0010-0018 参数集选择、上下限公差设定与切换广播
  - **拧紧数据流**：MID 0060/0061/0062 拧紧结果推送与确认（支持 Rev 1-7）
  - **曲线数据流 (Trace Curve)**：**MID 0008/0009/0900** 曲线订阅、退订与高精度多阶段物理采样点推送
  - **作业模式 (Job)**：MID 0030-0035 批次作业流、多工步状态机流转与批次递增递减
  - **多轴同步 (Multi-Spindle)**：MID 0100/0101 多轴状态与合并拧紧结果广播
  - **继电器与设备状态**：MID 0216/0217/0218 继电器功能订阅与工具使能/禁用控制
- 📈 **高仿真多阶段物理曲线生成**：
  - 模拟真实紧固力学过程：旋入阶段 (Free-run) $\rightarrow$ 贴合点 (Snug Point) $\rightarrow$ 屈服弹性变形段 (Tightening) $\rightarrow$ 峰值保持段 (Peak Hold / Shut-off)。
  - 150 个物理连续采样点（2ms 物理间隔，总长 300ms），支持扭矩曲线与角度曲线，完美契合 MID 0900 16-bit 大端二进制报文格式。
- 📊 **Web 端交互式实时曲线监控器 (SvelteKit + Canvas)**：
  - 支持四种专业工程视图：**双轴叠加 (Dual Axis)**、**扭矩-时间 (T-t)**、**角度-时间 (A-t)**、**扭矩-角度 (T-A 特性图)**。
  - 自动高亮识别 **贴合点 (Snug Point)** 与 **峰值点 (Peak Point)**，状态徽章自动判定 OK / NOK。
  - 鼠标悬停十字准星吸附 Tooltip，一键导出 **CSV 表格**、**MID 0900 JSON** 及 **PNG 高清截图**。
- 🧪 **工控异常仿真与故障注入**：
  - 模拟网络丢包、传输延迟（Latency jitter）、偶发断线重连。
  - 支持强制判定合格（OK）或超差（NOK），检验上位机防错拦截逻辑。

---

## 🔄 项目来源与二次开发说明 (Origin & Modifications)

### 项目起源 (Origin)
本项目 Fork 并深度二次开发自开源项目：
- **上游主干仓库**：[Jarrekstar/open-protocol-device-simulator](https://github.com/Jarrekstar/open-protocol-device-simulator)
- **初始原创仓库**：[dustywill/open-protocol-device-simulator](https://github.com/dustywill/open-protocol-device-simulator)

在此向原作者团队在 Rust 基础异步网络架构、状态机模型及 SvelteKit 内嵌框架上的开源贡献致以诚挚敬意！

### 本次做了哪些重大修改与增强 (Major Enhancements)

在原有基础功能之上，本项目进行了多项工业级核心功能的深度重构与自主研发：

1. **MID 0900 曲线订阅与高精度物理波形仿真引擎（核心新增）**：
   - 实现了 `MID 0008` 通用数据订阅与 `MID 0009` 退订机制，打通了曲线通道协议握手。
   - 实现了 `MID 0900` 报文结构与序列化器（ASCII 头部 + 零字符终止符 + 16位大端物理采样序列）。
   - 编写了高保真力学物理波形发生器（`TraceCurveData::generate_curves`），真实拟合螺栓紧固过程中的旋入、贴合爬升、紧固与峰值保持过程。
2. **Web 网页端实时拧紧曲线监控系统（核心新增）**：
   - 后端新增 `LatestCurves` 状态同步、`/curve/latest` 查询端点，并在 `POST /simulate/tightening` 与 `WebSocket (/ws/events)` 广播中全量下发曲线载荷。
   - 前端基于 HTML5 Canvas 自主研发了轻量零依赖、支持 Retina 高清缩放的 `TighteningCurveMonitor` 组件。
   - 提供了工业现场最核心的四种图表视图（包括扭矩-角度特性分析），并内置 CSV、JSON 和 PNG 导出工具。
3. **桌面端 Python 可视化控制中心 (`simulator_gui.py`) 研发**：
   - 采用 Python 原生 Tkinter 开发了开箱即用的跨平台客户端，无需配置复杂依赖即可运行。
   - 实现了对 MID 0900 二进制流的实时解析，内嵌 Canvas 动态绘图引擎，实现曲线动态绘制。
4. **Windows & macOS 一键运行与自动化打包架构优化**：
   - 编写了针对 Windows 环境的自动化构建脚本 `package_windows.bat` 与 `package_windows.ps1`，彻底解决 Windows 下路径空格与批处理编码问题。
   - 制作了 Windows 双击批处理和 macOS `.app` 应用程序图标。
   - 引入 GitHub Actions CI/CD 多平台矩阵编译，自动构建 Windows/macOS/Linux Release 安装包。
5. **协议细节与交互体验完善**：
   - 完善了 MID 0019/0020/0035/0074 协议分支及界面中文本地化优化。

---

## 🚀 如何使用 (Quick Start Guide)

### 方式一：下载已打包好的独立免编译安装包（最快，开箱即用）

进入项目的 **[GitHub Releases 页面](https://github.com/WendelYu/OpenProtocolSimulator/releases)** 直接下载对应系统的发布包：

- **Windows 用户**：下载 `OpenProtocolSimulator-Windows-x86_64.zip`，解压后双击 **`启动模拟器.bat`** 即可直接运行！
- **macOS 用户**：下载 `OpenProtocolSimulator-macOS-ARM64.tar.gz`，解压后双击 **`OpenProtocolSimulator.app`** 或 **`启动模拟器.command`** 即可直接运行！

---

### 方式二：直接使用源码仓库中的 `OpenProtocolSimulator-Dist/` 目录

如果您直接 `git clone` 或在 GitHub 点击 **"Download ZIP"** 下载了整个项目源码，项目根目录下已经预置了 **`OpenProtocolSimulator-Dist/`** 独立运行分发包：

```
OpenProtocolSimulator/
├── OpenProtocolSimulator-Dist/    <--- 预置独立运行包目录
│   ├── 启动模拟器.bat             # Windows 启动脚本
│   ├── 启动模拟器.command         # macOS 启动脚本
│   ├── OpenProtocolSimulator.app  # macOS 双击启动 App
│   ├── simulator_gui.py          # Python 可视化控制中心
│   ├── config.toml               # 配置文件
│   ├── simulator.db              # 预置数据库
│   └── bin/
│       ├── open-protocol-device-simulator       # macOS (Apple Silicon) 二进制
│       └── open-protocol-device-simulator.exe   # Windows 64位二进制 (或从 Releases 放入)
```

- **在 macOS 上**：进入 `OpenProtocolSimulator-Dist` 目录，直接双击 `OpenProtocolSimulator.app` 即可使用。
- **在 Windows 上**：若已有 `bin/open-protocol-device-simulator.exe`（或从 GitHub Releases 下载该 exe 放入 `bin/` 目录），直接双击 `启动模拟器.bat` 即可拉起控制中心。

---

### 方式二：从源码编译构建服务端与前端

#### 前置环境
- **Rust**：1.85+（[rustup.rs](https://rustup.rs/)）
- **Node.js**：20+（用于构建嵌入式 SvelteKit 前端，[nodejs.org](https://nodejs.org/)）
- **Python**：3.9+（可选，用于运行控制中心 GUI 客户端）

#### 1. 编译并运行内核服务程序
```bash
# 1. 克隆代码
git clone https://github.com/WendelYu/OpenProtocolSimulator.git
cd OpenProtocolSimulator

# 2. 安装前端依赖 (仅首次需要)
cd frontend && npm install && cd ..

# 3. 编译并启动服务 (自动编译前端并内嵌到 Rust 二进制中)
cargo run -- --config config.toml
```

服务启动后，终端将输出：
- 🔌 **Open Protocol TCP 服务**：`0.0.0.0:4545`
- 🌐 **Web 管理控制台**：`http://localhost:8082`

打开浏览器访问 `http://localhost:8082`，在【控制中心】点击【模拟拧紧】，即可在下方实时看到动态拧紧曲线！

#### 2. 运行桌面可视化控制中心程序
另开一个终端窗口运行：
```bash
python simulator_gui.py
```
- 点击 **【连接模拟器】**（默认连接 127.0.0.1:4545）
- 点击 **【订阅拧紧 (MID 0060)】** 与 **【订阅曲线 (MID 0008)】**
- 在第三个 Tab【曲线监视】中，即可直观观察上位机接收到的实时曲线波形！

---

### 方式三：Windows 一键自动化打包

如果您在 Windows 上修改了代码，需要重新生成发布包，只需在项目根目录运行：

```cmd
:: 双击运行或在 CMD 中执行：
package_windows.bat
```
脚本将全自动检测环境、构建 Web 前端、生成 Release 二进制，并将所有必要文件自动归档至 `OpenProtocolSimulator-Dist\` 目录下。

---

## 📖 架构与通信协议端口说明

```
┌────────────────────────────────────────────────────────┐
│             工业上位机 / MES / SCADA 系统              │
└──────────────────────────┬─────────────────────────────┘
                           │ Open Protocol (TCP :4545)
                           ▼
┌────────────────────────────────────────────────────────┐
│          OpenProtocolSimulator 内核服务端              │
│  - TCP 协议调度器 (MID 0001, MID 0061, MID 0900)       │
│  - 拧紧状态机 (FSM) & 力学波形仿真器                   │
│  - RESTful API & WebSocket 事件广播 (:8082)            │
└────────────┬─────────────────────────────▲─────────────┘
             │ WebSocket / HTTP            │ TCP Client (:4545)
             ▼                             │
┌──────────────────────────┐  ┌──────────────────────────┐
│  现代 Web 管理控制台     │  │  桌面 GUI 控制中心       │
│  (浏览器 localhost:8082) │  │  (simulator_gui.py)      │
│  - 双轴曲线/特性图分析   │  │  - 实时波形绘制          │
│  - 数据导出 CSV/JSON/PNG │  │  - MID 报文调试测试      │
└──────────────────────────┘  └──────────────────────────┘
```

- **Open Protocol 端口**：`TCP 4545`（可在 `config.toml` 中通过 `listen_address` 修改）
- **Web UI & REST API 端口**：`HTTP 8082`（可通过 `--http-port 8082` 修改）

---

## 📄 开源许可证

本项目基于 [MIT](LICENSE-MIT) 与 [Apache 2.0](LICENSE-APACHE) 双重许可证开源。
欢迎工业自动化、汽车制造及工控通信领域的开发者提交 Issue 与 Pull Request！
