#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Open Protocol Device Simulator - 桌面启动与控制中心
包含：一键启动/停止服务、Web控制台快捷直达、模拟拧紧触发、Open Protocol 报文测试联调、实时日志
"""

import os
import sys
import time
import socket
import signal
import threading
import subprocess
import webbrowser
import json
import urllib.request
import urllib.error
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# 路径计算
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

exe_suffix = ".exe" if sys.platform == "win32" else ""
BIN_PATH = os.path.join(BASE_DIR, "bin", f"open-protocol-device-simulator{exe_suffix}")
if not os.path.exists(BIN_PATH):
    BIN_PATH = os.path.join(BASE_DIR, "target", "release", f"open-protocol-device-simulator{exe_suffix}")
if not os.path.exists(BIN_PATH) and sys.platform == "win32":
    # 尝试无需子目录的直接放置情况
    if os.path.exists(os.path.join(BASE_DIR, f"open-protocol-device-simulator{exe_suffix}")):
        BIN_PATH = os.path.join(BASE_DIR, f"open-protocol-device-simulator{exe_suffix}")

CONFIG_PATH = os.path.join(BASE_DIR, "config.toml")

def check_port_in_use(port, host="127.0.0.1"):
    """检测指定端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex((host, port)) == 0

class OpenProtocolSimulatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Open Protocol 设备模拟器 控制中心")
        self.root.geometry("860x680")
        self.root.minsize(780, 580)
        
        self.process = None
        self.log_reader_thread = None
        self.is_running = False
        self.auto_tightening_running = False
        self.test_socket = None

        # 默认端口设置
        self.tcp_port_var = tk.StringVar(value="4545")
        self.http_port_var = tk.StringVar(value="8081")
        self.webui_port_var = tk.StringVar(value="8082")

        # 检查常用端口状态
        if check_port_in_use(8080):
            self.port_8080_busy = True
        else:
            self.port_8080_busy = False

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self):
        # 顶部标题栏卡片
        header_frame = ttk.Frame(self.root, padding="12 10 12 10")
        header_frame.pack(fill=tk.X)

        title_lbl = ttk.Label(header_frame, text="🔧 Open Protocol 设备模拟器", font=("Helvetica", 17, "bold"))
        title_lbl.pack(side=tk.LEFT)

        sub_lbl = ttk.Label(header_frame, text="Atlas Copco / Desoutter 紧固工具数字孪生仿真系统", font=("Helvetica", 11), foreground="#666")
        sub_lbl.pack(side=tk.LEFT, padx=15, pady=3)

        # 状态指示区
        self.status_badge = tk.Label(header_frame, text="● 未运行", bg="#ff4d4f", fg="white", font=("Helvetica", 11, "bold"), padx=10, pady=3)
        self.status_badge.pack(side=tk.RIGHT)

        # 分割线
        ttk.Separator(self.root, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=2)

        # 主配置与操作区域
        control_frame = ttk.LabelFrame(self.root, text="服务控制与配置", padding="12 8 12 8")
        control_frame.pack(fill=tk.X, padx=12, pady=6)

        cfg_row = ttk.Frame(control_frame)
        cfg_row.pack(fill=tk.X, pady=4)

        ttk.Label(cfg_row, text="Open Protocol TCP 端口:", font=("Helvetica", 10, "bold")).pack(side=tk.LEFT)
        self.tcp_entry = ttk.Entry(cfg_row, textvariable=self.tcp_port_var, width=7)
        self.tcp_entry.pack(side=tk.LEFT, padx=5)

        ttk.Label(cfg_row, text="(常用: 4545 / 8080)", foreground="#888", font=("Helvetica", 9)).pack(side=tk.LEFT, padx=2)

        ttk.Label(cfg_row, text="HTTP API 端口:", font=("Helvetica", 10, "bold")).pack(side=tk.LEFT, padx=(15, 0))
        self.http_entry = ttk.Entry(cfg_row, textvariable=self.http_port_var, width=7)
        self.http_entry.pack(side=tk.LEFT, padx=5)

        ttk.Label(cfg_row, text="WebUI 端口:", font=("Helvetica", 10, "bold")).pack(side=tk.LEFT, padx=(15, 0))
        self.webui_entry = ttk.Entry(cfg_row, textvariable=self.webui_port_var, width=7)
        self.webui_entry.pack(side=tk.LEFT, padx=5)

        # 端口提示信息
        if self.port_8080_busy:
            port_tip = ttk.Label(control_frame, text="💡 提示：检测到本地 8080 端口已被其它程序占用，已自动推荐使用工业标准端口 4545。", foreground="#d46b08", font=("Helvetica", 9))
            port_tip.pack(anchor=tk.W, pady=2)

        # 按钮行
        btn_row = ttk.Frame(control_frame)
        btn_row.pack(fill=tk.X, pady=8)

        self.start_btn = tk.Button(btn_row, text="▶ 启动模拟器", bg="#52c41a", fg="white", font=("Helvetica", 11, "bold"), padx=15, pady=5, command=self.start_simulator)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = tk.Button(btn_row, text="⏹ 停止模拟器", bg="#d9d9d9", fg="#888", font=("Helvetica", 11, "bold"), padx=15, pady=5, state=tk.DISABLED, command=self.stop_simulator)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        self.open_web_btn = tk.Button(btn_row, text="🌐 打开 Web 可视化控制台", bg="#1890ff", fg="white", font=("Helvetica", 11, "bold"), padx=15, pady=5, command=self.open_webui)
        self.open_web_btn.pack(side=tk.LEFT, padx=12)

        # 快速操作栏（模拟拧紧）
        sim_frame = ttk.LabelFrame(self.root, text="快速测试与仿真触发", padding="10 6 10 6")
        sim_frame.pack(fill=tk.X, padx=12, pady=4)

        sim_row = ttk.Frame(sim_frame)
        sim_row.pack(fill=tk.X)

        self.btn_sim_ok = ttk.Button(sim_row, text="⚡ 模拟合格拧紧 (OK: 15N·m)", command=lambda: self.simulate_tightening(ok=True))
        self.btn_sim_ok.pack(side=tk.LEFT, padx=3, pady=4)

        self.btn_sim_nok = ttk.Button(sim_row, text="❌ 模拟超差拧紧 (NOK: 25N·m)", command=lambda: self.simulate_tightening(ok=False))
        self.btn_sim_nok.pack(side=tk.LEFT, padx=3, pady=4)

        self.btn_auto_toggle = ttk.Button(sim_row, text="🔄 开启自动循环", command=self.toggle_auto_tightening)
        self.btn_auto_toggle.pack(side=tk.LEFT, padx=5, pady=4)

        # 工具转向控制
        ttk.Label(sim_row, text="转向:").pack(side=tk.LEFT, padx=(8, 2))
        ttk.Button(sim_row, text="CW (正转)", width=9, command=lambda: self.set_tool_direction("CW")).pack(side=tk.LEFT, padx=2)
        ttk.Button(sim_row, text="CCW (反转)", width=9, command=lambda: self.set_tool_direction("CCW")).pack(side=tk.LEFT, padx=2)

        # 选项卡区域（下半部）
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        # Tab 1: 实时运行日志
        tab_log = ttk.Frame(notebook)
        notebook.add(tab_log, text="📜 运行日志")

        log_toolbar = ttk.Frame(tab_log)
        log_toolbar.pack(fill=tk.X, padx=4, pady=3)

        ttk.Button(log_toolbar, text="清空日志", command=self.clear_logs).pack(side=tk.RIGHT)
        self.autoscroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(log_toolbar, text="自动滚动", variable=self.autoscroll_var).pack(side=tk.RIGHT, padx=10)

        self.log_text = scrolledtext.ScrolledText(tab_log, bg="#1e1e1e", fg="#d4d4d4", insertbackground="white", font=("Menlo", 10))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Tab 2: Open Protocol 报文测试与联调客户端
        tab_client = ttk.Frame(notebook)
        notebook.add(tab_client, text="🛠️ Open Protocol 报文交互调试")

        client_top = ttk.Frame(tab_client, padding="8 6 8 6")
        client_top.pack(fill=tk.X)

        ttk.Label(client_top, text="快捷协议测试报文：", font=("Helvetica", 10, "bold")).pack(anchor=tk.W, pady=2)
        
        test_btn_box = ttk.Frame(client_top)
        test_btn_box.pack(fill=tk.X, pady=4)

        ttk.Button(test_btn_box, text="1. 建立通信 (0001)", command=self.test_send_mid0001).pack(side=tk.LEFT, padx=2)
        ttk.Button(test_btn_box, text="2. 订阅拧紧 (0060)", command=self.test_send_mid0060).pack(side=tk.LEFT, padx=2)
        ttk.Button(test_btn_box, text="3. 订阅扭矩曲线 (0008->0900)", command=self.test_send_mid0008_trace_torque).pack(side=tk.LEFT, padx=2)
        ttk.Button(test_btn_box, text="4. 订阅角度曲线 (0008->0900)", command=self.test_send_mid0008_trace_angle).pack(side=tk.LEFT, padx=2)
        ttk.Button(test_btn_box, text="5. 退订曲线 (0009)", command=self.test_send_mid0009_trace).pack(side=tk.LEFT, padx=2)
        ttk.Button(test_btn_box, text="断开连接", command=self.disconnect_test_client).pack(side=tk.RIGHT, padx=2)

        test_btn_box2 = ttk.Frame(client_top)
        test_btn_box2.pack(fill=tk.X, pady=2)
        ttk.Button(test_btn_box2, text="选参数集1 (0018)", command=self.test_send_mid0018).pack(side=tk.LEFT, padx=2)
        ttk.Button(test_btn_box2, text="校时 (0082)", command=self.test_send_mid0082).pack(side=tk.LEFT, padx=2)
        ttk.Button(test_btn_box2, text="IO状态 (0214)", command=self.test_send_mid0214).pack(side=tk.LEFT, padx=2)
        ttk.Button(test_btn_box2, text="继电器订阅 (0216)", command=self.test_send_mid0216).pack(side=tk.LEFT, padx=2)

        custom_row = ttk.Frame(client_top)
        custom_row.pack(fill=tk.X, pady=6)
        ttk.Label(custom_row, text="自定义报文:").pack(side=tk.LEFT)
        self.custom_mid_entry = ttk.Entry(custom_row, font=("Menlo", 10))
        self.custom_mid_entry.insert(0, "00200001001         ")
        self.custom_mid_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        ttk.Button(custom_row, text="发送报文", command=self.send_custom_mid).pack(side=tk.RIGHT)

        ttk.Label(tab_client, text="报文交互收发记录：", font=("Helvetica", 10, "bold")).pack(anchor=tk.W, padx=12, pady=2)
        self.client_log_text = scrolledtext.ScrolledText(tab_client, bg="#181824", fg="#56b6c2", insertbackground="white", font=("Menlo", 10))
        self.client_log_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # Tab 3: 曲线波形监视与调试中心 (MID 0900 可视化)
        tab_curve = ttk.Frame(notebook)
        notebook.add(tab_curve, text="📈 曲线波形监视器 (MID 0900)")

        curve_top = ttk.Frame(tab_curve, padding="8 6 8 6")
        curve_top.pack(fill=tk.X)

        self.curve_info_lbl = ttk.Label(curve_top, text="等待接收 MID 0900 曲线数据 (请先在报文调试中点击「建立通信」及「订阅扭矩曲线」后触发模拟拧紧)...", font=("Helvetica", 10))
        self.curve_info_lbl.pack(side=tk.LEFT, padx=5)

        ttk.Button(curve_top, text="清空曲线", command=self.clear_curve_canvas).pack(side=tk.RIGHT, padx=5)

        # 曲线绘制 Canvas
        self.curve_canvas = tk.Canvas(tab_curve, bg="#12131a", highlightthickness=0)
        self.curve_canvas.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)
        self.curve_canvas.bind("<Configure>", lambda e: self.redraw_current_curve())
        self.last_curve_data = None

        self.log("[控制中心] 界面已就绪，点击「▶ 启动模拟器」即可启动服务并打开 Web 仪表盘。")

    def log(self, msg):
        """添加日志"""
        def _append():
            timestamp = time.strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"[{timestamp}] {msg}\n")
            if self.autoscroll_var.get():
                self.log_text.see(tk.END)
        self.root.after(0, _append)

    def client_log(self, msg, direction="INFO"):
        """添加报文测试日志"""
        def _append():
            timestamp = time.strftime("%H:%M:%S")
            prefix = ""
            if direction == "SEND":
                prefix = "➡️ [发送] "
            elif direction == "RECV":
                prefix = "⬅️ [接收] "
            elif direction == "ERR":
                prefix = "❌ [错误] "
            else:
                prefix = "ℹ️ [提示] "
            self.client_log_text.insert(tk.END, f"[{timestamp}] {prefix}{msg}\n")
            self.client_log_text.see(tk.END)
        self.root.after(0, _append)

    def clear_logs(self):
        self.log_text.delete("1.0", tk.END)

    def update_config_file(self, tcp_port, http_port, webui_port):
        """生成并写入 config.toml"""
        content = f"""[server]
tcp_port = {tcp_port}
http_port = {http_port}
bind_address = "0.0.0.0"
event_channel_capacity = 100

[webui]
enabled = true
host = "0.0.0.0"
port = {webui_port}

[device]
cell_id = 1
channel_id = 1
controller_name = "OpenProtocolSimulator"
supplier_code = "SIM"

[database]
path = "simulator.db"

[defaults]
auto_tightening_interval_ms = 3000
auto_tightening_duration_ms = 1500
failure_rate = 0.1
"""
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            f.write(content)

    def start_simulator(self):
        """启动模拟器服务"""
        if self.is_running:
            return

        if not os.path.exists(BIN_PATH):
            messagebox.showerror("文件缺失", f"未找到模拟器二进制程序：\n{BIN_PATH}")
            return

        try:
            tcp_p = int(self.tcp_port_var.get())
            http_p = int(self.http_port_var.get())
            webui_p = int(self.webui_port_var.get())
        except ValueError:
            messagebox.showerror("端口错误", "端口号必须为有效数字！")
            return

        # 检查端口占用
        if check_port_in_use(tcp_p):
            messagebox.showerror("端口冲突", f"TCP 端口 {tcp_p} 已被占用，请更改端口（例如 4545 或 9080）后再启动！")
            return
        if check_port_in_use(http_p):
            messagebox.showerror("端口冲突", f"HTTP API 端口 {http_p} 已被占用，请更改端口！")
            return
        if check_port_in_use(webui_p):
            messagebox.showerror("端口冲突", f"WebUI 端口 {webui_p} 已被占用，请更改端口！")
            return

        # 更新配置文件
        self.update_config_file(tcp_p, http_p, webui_p)

        self.log(f"正在启动 Open Protocol 模拟器服务 (TCP: {tcp_p}, HTTP: {http_p}, WebUI: {webui_p})...")

        try:
            # 启动子进程
            self.process = subprocess.Popen(
                [BIN_PATH, "--config", CONFIG_PATH],
                cwd=BASE_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            self.is_running = True

            # 启动日志读取线程
            self.log_reader_thread = threading.Thread(target=self._read_process_output, daemon=True)
            self.log_reader_thread.start()

            # 更新 UI 状态
            self.status_badge.config(text=f"● 运行中 (TCP:{tcp_p})", bg="#52c41a")
            self.start_btn.config(state=tk.DISABLED, bg="#d9d9d9", fg="#888")
            self.stop_btn.config(state=tk.NORMAL, bg="#ff4d4f", fg="white")
            self.tcp_entry.config(state=tk.DISABLED)
            self.http_entry.config(state=tk.DISABLED)
            self.webui_entry.config(state=tk.DISABLED)

            # 延迟 1 秒自动在浏览器打开 Web 控制台
            threading.Thread(target=self._auto_open_webui, args=(webui_p,), daemon=True).start()

        except Exception as e:
            self.log(f"启动失败: {e}")
            messagebox.showerror("启动失败", str(e))
            self.is_running = False

    def _auto_open_webui(self, port):
        time.sleep(1.2)
        url = f"http://localhost:{port}"
        self.log(f"自动唤起系统浏览器访问 Web 控制台: {url}")
        webbrowser.open(url)

    def _read_process_output(self):
        """读取子进程输出"""
        while self.is_running and self.process:
            line = self.process.stdout.readline()
            if not line:
                break
            line_str = line.rstrip()
            if line_str:
                self.log(line_str)

        ret = self.process.poll() if self.process else None
        if self.is_running:
            self.log(f"[提示] 模拟器已退出 (返回值: {ret})")
            self.root.after(0, self._set_stopped_ui)

    def _set_stopped_ui(self):
        self.is_running = False
        self.status_badge.config(text="● 未运行", bg="#ff4d4f")
        self.start_btn.config(state=tk.NORMAL, bg="#52c41a", fg="white")
        self.stop_btn.config(state=tk.DISABLED, bg="#d9d9d9", fg="#888")
        self.tcp_entry.config(state=tk.NORMAL)
        self.http_entry.config(state=tk.NORMAL)
        self.webui_entry.config(state=tk.NORMAL)
        self.auto_tightening_running = False
        self.btn_auto_toggle.config(text="🔄 开启自动循环模拟")

    def stop_simulator(self):
        """停止模拟器服务"""
        if not self.is_running or not self.process:
            return

        self.log("正在停止模拟器服务...")
        try:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
        except Exception as e:
            self.log(f"停止异常: {e}")

        self._set_stopped_ui()
        self.disconnect_test_client()
        self.log("模拟器已完全停止。")

    def open_webui(self):
        """手动打开 Web 控制台"""
        port = self.webui_port_var.get()
        url = f"http://localhost:{port}"
        self.log(f"打开 Web 控制台：{url}")
        webbrowser.open(url)

    def simulate_tightening(self, ok=True):
        """触发单次拧紧"""
        if not self.is_running:
            messagebox.showwarning("提示", "请先启动模拟器服务！")
            return

        http_p = self.http_port_var.get()
        url = f"http://localhost:{http_p}/simulate/tightening"
        payload = {
            "torque": 15.0 if ok else 25.0,
            "angle": 45.0 if ok else 10.0,
            "ok": ok
        }

        def _do():
            try:
                data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=2) as resp:
                    res_body = resp.read().decode("utf-8")
                    self.log(f"触发拧紧模拟成功 [{('OK' if ok else 'NOK')}]: {res_body}")
            except Exception as e:
                self.log(f"触发拧紧失败: {e}")

        threading.Thread(target=_do, daemon=True).start()

    def toggle_auto_tightening(self):
        """开启或停止自动拧紧"""
        if not self.is_running:
            messagebox.showwarning("提示", "请先启动模拟器服务！")
            return

        http_p = self.http_port_var.get()
        if not self.auto_tightening_running:
            url = f"http://localhost:{http_p}/auto-tightening/start"
            target_state = True
            btn_text = "⏹ 停止自动循环模拟"
        else:
            url = f"http://localhost:{http_p}/auto-tightening/stop"
            target_state = False
            btn_text = "🔄 开启自动循环模拟"

        def _do():
            try:
                req = urllib.request.Request(url, data=b"{}", headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=2) as resp:
                    self.auto_tightening_running = target_state
                    self.root.after(0, lambda: self.btn_auto_toggle.config(text=btn_text))
                    self.log(f"自动循环模拟已{'开启' if target_state else '停止'}")
            except Exception as e:
                self.log(f"自动模拟操作失败: {e}")

        threading.Thread(target=_do, daemon=True).start()

    # ---------------- 报文联调客户端 ----------------
    def _ensure_test_connection(self):
        """确保 TCP 测试客户端已连接"""
        if self.test_socket:
            return True

        if not self.is_running:
            self.client_log("模拟器未运行，无法连接测试！", "ERR")
            return False

        try:
            tcp_p = int(self.tcp_port_var.get())
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2.0)
            s.connect(("127.0.0.1", tcp_p))
            self.test_socket = s
            self.client_log(f"成功连接至本地 Open Protocol 服务 127.0.0.1:{tcp_p}")
            
            # 开启后台接收线程
            threading.Thread(target=self._recv_loop, daemon=True).start()
            return True
        except Exception as e:
            self.client_log(f"连接模拟器失败: {e}", "ERR")
            self.test_socket = None
            return False

    def _recv_loop(self):
        """持续接收服务器推送报文（支持 ASCII 报文与包含二进制采样点的 MID 0900 报文）"""
        buf = b""
        while self.test_socket:
            try:
                chunk = self.test_socket.recv(4096)
                if not chunk:
                    break
                buf += chunk

                while len(buf) >= 20:
                    # 检查是否为 MID 0900 曲线报文
                    mid = buf[4:8].decode("ascii", errors="ignore")
                    if mid == "0900":
                        try:
                            msg_len = int(buf[0:4].decode("ascii", errors="ignore"))
                        except ValueError:
                            msg_len = 0

                        if msg_len > 0 and len(buf) >= msg_len:
                            full_msg = buf[:msg_len]
                            buf = buf[msg_len:]
                            self._handle_mid0900_curve(full_msg)
                            continue
                        else:
                            # 长度未完整接收，等待下一个 chunk
                            break

                    # 普通 ASCII 报文（以 \x00 分隔）
                    if b"\x00" in buf:
                        msg_bytes, buf = buf.split(b"\x00", 1)
                        msg_str = msg_bytes.decode("ascii", errors="replace")
                        mid_tag = msg_str[4:8] if len(msg_str) >= 8 else "????"
                        self.client_log(f"[MID {mid_tag}] {msg_str}", "RECV")
                    else:
                        break
            except socket.timeout:
                continue
            except Exception as e:
                break
        self.client_log("测试客户端连接已关闭")
        self.test_socket = None

    def _handle_mid0900_curve(self, raw_bytes):
        """解析并绘制 MID 0900 曲线采样数据"""
        try:
            header_str = raw_bytes[:20].decode("ascii", errors="ignore")
            # 找到 ASCII 与 二进制 分隔符 \x00
            if b"\x00" in raw_bytes[20:]:
                ascii_part, binary_part = raw_bytes[20:].split(b"\x00", 1)
                ascii_str = ascii_part.decode("ascii", errors="ignore")

                res_id = ascii_str[:10].strip()
                timestamp = ascii_str[10:29].strip()
                trace_type_code = ascii_str[32:34].strip() if len(ascii_str) >= 34 else "02"
                trace_name = "扭矩曲线 (Torque)" if trace_type_code == "02" else "角度曲线 (Angle)"
                unit_str = "N·m" if trace_type_code == "02" else "°"

                # 提取二进制采样点 (每点 2 字节大端整数)
                samples = []
                for i in range(0, len(binary_part) - 1, 2):
                    val = int.from_bytes(binary_part[i:i+2], byteorder="big")
                    scale = 100.0 if trace_type_code == "02" else 10.0
                    samples.append(val / scale)

                self.client_log(f"[MID 0900] 接收到 {trace_name}, 采样点数: {len(samples)}, 结果ID: {res_id}", "RECV")

                # 更新界面展示
                curve_info = {
                    "res_id": res_id,
                    "timestamp": timestamp,
                    "trace_name": trace_name,
                    "unit": unit_str,
                    "samples": samples,
                    "max_val": max(samples) if samples else 0.0,
                    "final_val": samples[-1] if samples else 0.0,
                }
                self.root.after(0, self.render_curve_waveform, curve_info)
            else:
                self.client_log("[MID 0900] 报文格式不符合要求（未找到分隔符）", "ERR")
        except Exception as e:
            self.client_log(f"[MID 0900] 解析异常: {e}", "ERR")

    def disconnect_test_client(self):
        if self.test_socket:
            try:
                self.test_socket.close()
            except Exception:
                pass
            self.test_socket = None

    def _send_open_protocol_msg(self, msg_str):
        if not self._ensure_test_connection():
            return

        try:
            raw = msg_str.encode("ascii") + b"\x00"
            self.test_socket.sendall(raw)
            mid = msg_str[4:8] if len(msg_str) >= 8 else "????"
            self.client_log(f"[MID {mid}] {msg_str}", "SEND")
        except Exception as e:
            self.client_log(f"发送失败: {e}", "ERR")
            self.disconnect_test_client()

    def test_send_mid0001(self):
        """MID 0001: Communication Start"""
        # 0020(长度) 0001(MID) 001(Revision) 001(Station)等
        msg = "00200001001         "
        self._send_open_protocol_msg(msg)

    def test_send_mid0060(self):
        """MID 0060: Tightening Result Subscribe"""
        msg = "00200060001         "
        self._send_open_protocol_msg(msg)

    def test_send_mid0014(self):
        """MID 0014: PSET Selected Subscribe"""
        msg = "00200014001         "
        self._send_open_protocol_msg(msg)

    def test_send_mid0008_trace_torque(self):
        """通过 MID 0008 订阅 MID 0900 扭矩曲线 (Torque Trace)"""
        # Table 26: MID(0900) Rev(001) ExtraLength(05) Extra(0001002 - Type 002:Torque)
        msg = "00350008001         0900001050001002"
        self._send_open_protocol_msg(msg)

    def test_send_mid0008_trace_angle(self):
        """通过 MID 0008 订阅 MID 0900 角度曲线 (Angle Trace)"""
        # Table 26: MID(0900) Rev(001) ExtraLength(05) Extra(0001001 - Type 001:Angle)
        msg = "00350008001         0900001050001001"
        self._send_open_protocol_msg(msg)

    def test_send_mid0009_trace(self):
        """通过 MID 0009 退订 MID 0900 曲线"""
        msg = "00300009001         090000100"
        self._send_open_protocol_msg(msg)

    def test_send_mid0018(self):
        """MID 0018: Select PSET 1"""
        # 0023 0018 001 ... PSET 001
        msg = "00230018001         001"
        self._send_open_protocol_msg(msg)

    def clear_curve_canvas(self):
        self.last_curve_data = None
        self.curve_canvas.delete("all")
        self.curve_info_lbl.config(text="波形已清空，等待接收新的 MID 0900 曲线数据...")

    def render_curve_waveform(self, curve_info):
        """在 Canvas 上绘制完整的拧紧曲线波形"""
        self.last_curve_data = curve_info
        samples = curve_info["samples"]
        if not samples:
            return

        trace_name = curve_info["trace_name"]
        unit = curve_info["unit"]
        max_val = curve_info["max_val"]
        final_val = curve_info["final_val"]
        t_stamp = curve_info["timestamp"]
        res_id = curve_info["res_id"]

        info_text = f"📊 [{trace_name}] 结果ID: {res_id} | 峰值: {max_val:.2f} {unit} | 终值: {final_val:.2f} {unit} | 采样数: {len(samples)} 点 | 时间: {t_stamp}"
        self.curve_info_lbl.config(text=info_text)

        self.redraw_current_curve()

    def redraw_current_curve(self):
        """重绘当前曲线（支持窗口缩放自适应）"""
        if not self.last_curve_data:
            return

        samples = self.last_curve_data["samples"]
        if not samples:
            return

        canvas = self.curve_canvas
        canvas.delete("all")

        w = canvas.winfo_width()
        h = canvas.winfo_height()
        if w < 50 or h < 50:
            return

        pad_left = 65
        pad_right = 35
        pad_top = 40
        pad_bottom = 50

        plot_w = w - pad_left - pad_right
        plot_h = h - pad_top - pad_bottom

        # 绘制背景网格
        for y_idx in range(5):
            y = pad_top + (plot_h / 4) * y_idx
            canvas.create_line(pad_left, y, w - pad_right, y, fill="#232634", dash=(2, 4))
        for x_idx in range(7):
            x = pad_left + (plot_w / 6) * x_idx
            canvas.create_line(x, pad_top, x, h - pad_bottom, fill="#232634", dash=(2, 4))

        # 坐标轴
        canvas.create_line(pad_left, pad_top, pad_left, h - pad_bottom, fill="#5c6370", width=2)
        canvas.create_line(pad_left, h - pad_bottom, w - pad_right, h - pad_bottom, fill="#5c6370", width=2)

        max_val = max(max(samples), 0.1)
        # 纵坐标标签
        for y_idx in range(5):
            val = max_val * (4 - y_idx) / 4.0
            y = pad_top + (plot_h / 4) * y_idx
            unit = self.last_curve_data["unit"]
            canvas.create_text(pad_left - 8, y, text=f"{val:.1f}", fill="#828997", anchor=tk.E, font=("Helvetica", 9))

        canvas.create_text(pad_left, pad_top - 18, text=f"数值 ({self.last_curve_data['unit']})", fill="#61afef", font=("Helvetica", 9, "bold"))
        canvas.create_text(w - pad_right, h - pad_bottom + 25, text="采样序列 (时间步长 2ms)", fill="#98c379", font=("Helvetica", 9))

        # 计算并绘制波形连线
        points = []
        n = len(samples)
        for i, val in enumerate(samples):
            x = pad_left + (plot_w * i / max(1, n - 1))
            y = (pad_top + plot_h) - (plot_h * (val / max_val))
            points.append((x, y))

        if len(points) >= 2:
            # 渐变多边形填充（波形阴影）
            poly_points = [points[0][0], h - pad_bottom]
            for px, py in points:
                poly_points.extend([px, py])
            poly_points.extend([points[-1][0], h - pad_bottom])
            canvas.create_polygon(poly_points, fill="#1c283d", outline="")

            # 主波形线条（醒目青/绿色）
            flat_pts = [coord for pt in points for coord in pt]
            line_color = "#00e676" if "Torque" in self.last_curve_data["trace_name"] else "#00b0ff"
            canvas.create_line(flat_pts, fill=line_color, width=3, smooth=True)

            # 标出峰值点
            max_idx = samples.index(max(samples))
            mx, my = points[max_idx]
            canvas.create_oval(mx - 5, my - 5, mx + 5, my + 5, fill="#ff1744", outline="white", width=2)
            canvas.create_text(mx, my - 15, text=f"峰值 {samples[max_idx]:.2f}{self.last_curve_data['unit']}", fill="#ff5252", font=("Helvetica", 10, "bold"))

    def test_send_mid0008(self):
        """MID 0008: Keep Alive"""
        msg = "00200008001         "
        self._send_open_protocol_msg(msg)

    def test_send_mid0082(self):
        """MID 0082: Set Time"""
        now_str = time.strftime("%Y-%m-%d:%H:%M:%S")
        msg = f"00390082001         {now_str}"
        self._send_open_protocol_msg(msg)

    def test_send_mid0214(self):
        """MID 0214: IO Device Status Request (Device 1)"""
        msg = "00210214001         1"
        self._send_open_protocol_msg(msg)

    def test_send_mid0216(self):
        """MID 0216: Relay Function Subscribe (Relay 01, Function 01)"""
        msg = "00240216001         0101"
        self._send_open_protocol_msg(msg)

    def set_tool_direction(self, direction):
        """设置工具转向 (CW / CCW)"""
        if not self.is_running:
            messagebox.showwarning("提示", "请先启动模拟器服务！")
            return

        http_p = self.http_port_var.get()
        url = f"http://localhost:{http_p}/tool/direction"
        payload = {"direction": direction}

        def _do():
            try:
                data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=2) as resp:
                    self.log(f"工具转向已设置为: {direction}")
            except Exception as e:
                self.log(f"设置工具转向失败: {e}")

        threading.Thread(target=_do, daemon=True).start()

    def send_custom_mid(self):
        custom = self.custom_mid_entry.get().strip()
        if not custom:
            return
        if len(custom) < 20:
            custom = custom.ljust(20, " ")
        self._send_open_protocol_msg(custom)

    def on_close(self):
        """关闭窗口时清理资源"""
        if self.is_running:
            if messagebox.askyesno("退出确认", "模拟器仍在运行中，确定要停止并退出吗？"):
                self.stop_simulator()
                self.root.destroy()
        else:
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = OpenProtocolSimulatorApp(root)
    root.mainloop()
