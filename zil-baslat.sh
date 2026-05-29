#!/bin/bash
# ══════════════════════════════════════════════════
#  Zil Sistemi — Sunucu Başlatıcı (Raspberry Pi)
#  Kullanım: bash zil-baslat.sh
# ══════════════════════════════════════════════════

ZIL_DIR="$(cd "$(dirname "$0")" && pwd)"
PORT=8765
URL="http://localhost:$PORT/zil-programi-v1.html"

echo ""
echo "╔══════════════════════════════════════╗"
echo "║        ZİL SİSTEMİ BAŞLATILIYOR      ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Eski sunucu varsa durdur
if pgrep -f "sunucu.py" > /dev/null; then
    echo "► Eski sunucu durduruluyor..."
    pkill -f "sunucu.py"
    sleep 1
fi

# Sunucuyu başlat
echo "► Sunucu başlatılıyor (port $PORT)..."
cd "$ZIL_DIR"
python3 zunucu/sunucu.py &
SUNUCU_PID=$!

# Sunucunun ayağa kalkmasını bekle
echo "► Sunucu hazırlanıyor..."
for i in $(seq 1 15); do
    sleep 1
    if curl -s "http://localhost:$PORT" > /dev/null 2>&1; then
        echo "► Sunucu hazır ✓"
        break
    fi
    if [ $i -eq 15 ]; then
        echo "⚠ Sunucu 15 saniyede yanıt vermedi, yine de devam ediliyor..."
    fi
done

# Chromium kiosk modunda aç
echo "► Tarayıcı açılıyor..."
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
echo "► Sistem çalışıyor. Kapatmak için:"
echo "    pkill -f sunucu.py"
echo "    pkill chromium"
echo ""

# Sunucu duruncaya kadar bekle
wait $SUNUCU_PID
