#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "=========================================================="
echo "    🚀 Open Protocol Device Simulator 终端控制台启动器   "
echo "=========================================================="

TCP_PORT=4545
HTTP_PORT=8081
WEBUI_PORT=8082

# 检测 8080 端口
if lsof -i :8080 >/dev/null 2>&1; then
    echo "⚠️  检测到 8080 端口已被系统占用，默认采用标准端口: $TCP_PORT"
else
    # 若 8080 空闲，也可使用 8080
    TCP_PORT=4545
fi

cat << EOT > "$DIR/config.toml"
[server]
tcp_port = $TCP_PORT
http_port = $HTTP_PORT
bind_address = "0.0.0.0"
event_channel_capacity = 100

[webui]
enabled = true
host = "0.0.0.0"
port = $WEBUI_PORT

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
EOT

echo "📡 服务监听端口："
echo "   - Open Protocol TCP 端口: $TCP_PORT"
echo "   - HTTP REST / WebSocket:  http://localhost:$HTTP_PORT"
echo "   - WebUI 仪表盘控制台:      http://localhost:$WEBUI_PORT"
echo ""
echo "正在启动后台服务并唤起浏览器..."

"$DIR/bin/open-protocol-device-simulator" --config "$DIR/config.toml" &
PID=$!

sleep 1.2
if which open >/dev/null 2>&1; then
    open "http://localhost:$WEBUI_PORT"
fi

echo "模拟器正在运行 (PID: $PID)，按 Ctrl+C 退出。"
trap "kill $PID 2>/dev/null; exit 0" INT TERM
wait $PID
