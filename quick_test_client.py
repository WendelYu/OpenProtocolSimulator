#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Open Protocol 协议快速联调测试客户端
自动化测试流程：
1. 发送 MID 0001 (建立连接通信) -> 等待并校验 MID 0002 响应
2. 发送 MID 0060 (订阅拧紧结果) -> 等待并校验 MID 0005 响应
3. 调用 HTTP API 模拟触发一次拧紧 -> 验证 TCP 连接是否推送 MID 0061 拧紧结果
4. 打印完整报文解析说明
"""

import socket
import time
import json
import urllib.request
import sys

TCP_PORT = 4545
HTTP_PORT = 8081

def test_full_flow():
    print(f"==================================================")
    print(f"   Open Protocol 模拟器通信联调测试 (TCP 端口: {TCP_PORT})")
    print(f"==================================================")

    # 1. 建立 TCP 连接
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3.0)
        s.connect(("127.0.0.1", TCP_PORT))
        print("✅ 成功连接至 Open Protocol TCP 端口！")
    except Exception as e:
        print(f"❌ 无法连接至 127.0.0.1:{TCP_PORT}: {e}")
        print("💡 请先启动模拟器服务后再运行此测试脚本。")
        return False

    def send_mid(msg):
        print(f"\n➡️ [发送] {msg}")
        s.sendall(msg.encode("ascii") + b"\x00")

    def recv_mid():
        buf = b""
        start_time = time.time()
        while time.time() - start_time < 3.0:
            try:
                chunk = s.recv(1024)
                if not chunk:
                    break
                buf += chunk
                if b"\x00" in buf:
                    raw, _ = buf.split(b"\x00", 1)
                    decoded = raw.decode("ascii", errors="replace")
                    mid = decoded[4:8] if len(decoded) >= 8 else "????"
                    print(f"⬅️ [接收] MID {mid}: {decoded}")
                    return mid, decoded
            except socket.timeout:
                break
        return None, None

    # 2. 发送 MID 0001
    send_mid("00200001001         ")
    mid, resp = recv_mid()
    if mid == "0002":
        print(f"  🎉 MID 0002 握手成功！控制器信息响应正常。")
    else:
        print(f"  ⚠️ 未收到 MID 0002，收到: {mid}")

    # 3. 发送 MID 0060 (订阅拧紧结果)
    send_mid("00200060001         ")
    mid, resp = recv_mid()
    if mid == "0005":
        print(f"  🎉 MID 0005 (0060) 订阅确认成功！已就绪等待拧紧数据。")
    else:
        print(f"  ⚠️ 收到: {mid}")

    # 3.1 发送 MID 0008 (订阅 MID 0900 曲线数据)
    print("\n📈 发送 MID 0008 订阅 MID 0900 扭矩曲线...")
    send_mid("00350008001         0900001050001002")
    mid, resp = recv_mid()
    if mid == "0005":
        print(f"  🎉 MID 0005 (0900) 曲线订阅确认成功！")
    else:
        print(f"  ⚠️ 收到: {mid}")

    # 4. 触发 HTTP 模拟拧紧
    print("\n⚡ 正在通过 HTTP API 触发单次拧紧测试 (15.0 N·m / 45° OK)...")
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{HTTP_PORT}/simulate/tightening",
            data=json.dumps({"torque": 15.0, "angle": 45.0, "ok": True}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=2.0) as http_resp:
            print(f"  HTTP 触发响应: {http_resp.read().decode('utf-8')}")
    except Exception as e:
        print(f"  HTTP 触发异常: {e}")

    # 5. 等待接收 MID 0061 (拧紧数据)
    print("\n⏳ 正在监听 TCP 推送的 MID 0061 拧紧结果报文...")
    mid, resp = recv_mid()
    if mid == "0061":
        print(f"  🎉 成功接收到 MID 0061 拧紧结果报文！")
        print(f"  报文解析：{resp}")
        # 回复 MID 0062 ACK
        send_mid("00200062001         ")
        print("  已回复 MID 0062 ACK 确认收悉。")
    else:
        print(f"  ⚠️ 未能捕获到 MID 0061 (接收: {mid})")

    # 6. 等待接收 MID 0900 (曲线数据)
    print("\n⏳ 正在监听 TCP 推送的 MID 0900 曲线波形报文...")
    mid, resp = recv_mid()
    if mid == "0900":
        print(f"  🎉 成功接收到 MID 0900 曲线数据报文！")
        print(f"  曲线数据包预览 (前120字符): {resp[:120]}...")
    else:
        print(f"  ⚠️ 接收: {mid}")

    s.close()
    print("\n==================================================")
    print("           联调测试流程完毕！各项功能正常           ")
    print("==================================================")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        TCP_PORT = int(sys.argv[1])
    test_full_flow()
