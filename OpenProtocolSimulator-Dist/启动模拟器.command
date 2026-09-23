#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

export PATH="/Library/Frameworks/Python.framework/Versions/Current/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

echo "=================================================="
echo "    正在启动 Open Protocol 设备模拟器控制中心...    "
echo "=================================================="

PYTHON_BIN=""
for py in "/Library/Frameworks/Python.framework/Versions/3.13/bin/python3" \
          "/Library/Frameworks/Python.framework/Versions/Current/bin/python3" \
          "/usr/local/bin/python3" \
          "/usr/bin/python3" \
          "$(command -v python3 2>/dev/null)"; do
    if [ -x "$py" ] && "$py" -c "import tkinter" >/dev/null 2>&1; then
        PYTHON_BIN="$py"
        break
    fi
done

if [ -n "$PYTHON_BIN" ] && [ -f "$DIR/simulator_gui.py" ]; then
    "$PYTHON_BIN" "$DIR/simulator_gui.py"
elif [ -x "$DIR/bin/open-protocol-device-simulator" ] && [ -f "$DIR/config.toml" ]; then
    echo "未检测到支持图形界面的 Python 环境，直接启动服务并打开 Web 仪表盘..."
    "$DIR/bin/open-protocol-device-simulator" --config "$DIR/config.toml" &
    SIM_PID=$!
    sleep 2
    open "http://localhost:8082"
    wait $SIM_PID
else
    echo "错误：未找到模拟器核心文件，请检查目录完整性。"
    read -p "按回车键退出..."
fi
