#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR/open-protocol-device-simulator"

echo "=================================================="
echo "    正在启动 Open Protocol 设备模拟器控制中心...    "
echo "=================================================="

# 优先启动图形化桌面控制面板
if [ -f "/usr/local/bin/python3" ]; then
    /usr/local/bin/python3 "$DIR/open-protocol-device-simulator/simulator_gui.py"
elif command -v python3 >/dev/null 2>&1; then
    python3 "$DIR/open-protocol-device-simulator/simulator_gui.py"
else
    echo "未找到 python3，直接启动后端服务并打开 Web 控制台..."
    "$DIR/open-protocol-device-simulator/bin/open-protocol-device-simulator" --config "$DIR/open-protocol-device-simulator/config.toml" &
    SIM_PID=$!
    sleep 2
    open "http://localhost:8082"
    wait $SIM_PID
fi
