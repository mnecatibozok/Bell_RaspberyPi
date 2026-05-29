#!/bin/bash
# ══════════════════════════════════════════════════
#  Bell System — Server Launcher (Raspberry Pi)
#  Usage: bash bell-start.sh
# ══════════════════════════════════════════════════

BELL_DIR="$(cd "$(dirname "$0")" && pwd)"
PORT=8765
URL="http://localhost:$PORT/zil-programi-v1.html"

echo ""
echo "╔══════════════════════════════════════╗"
echo "║        BELL SYSTEM STARTING          ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Stop old server if running
if pgrep -f "sunucu.py" > /dev/null; then
    echo "► Stopping old server..."
    pkill -f "sunucu.py"
    sleep 1
fi

# Start the server
echo "► Starting server (port $PORT)..."
cd "$BELL_DIR"
python3 zunucu/sunucu.py &
SERVER_PID=$!

# Wait for server to come up
echo "► Waiting for server to be ready..."
for i in $(seq 1 15); do
    sleep 1
    if curl -s "http://localhost:$PORT" > /dev/null 2>&1; then
        echo "► Server ready ✓"
        break
    fi
    if [ $i -eq 15 ]; then
        echo "⚠ Server did not respond within 15 seconds, continuing anyway..."
    fi
done

# Open Chromium in kiosk mode
echo "► Opening browser..."
chromium-browser \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --disable-restore-session-state \
    --no-first-run \
    --check-for-update-interval=31536000 \
    "$URL" &

echo ""
echo "► System running. To stop:"
echo "    pkill -f sunucu.py"
echo "    pkill chromium"
echo ""

# Wait until server exits
wait $SERVER_PID
