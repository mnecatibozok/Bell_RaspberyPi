#!/bin/bash
# YOLOv8-nano kurulum scripti — Raspberry Pi
echo "=== Zil AI Kurulum ==="
echo "1. ultralytics kuruluyor..."
pip install ultralytics --break-system-packages

echo "2. YOLOv8-nano modeli indiriliyor..."
python3 -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
# Model otomatik olarak ~/.config/Ultralytics/ veya mevcut dizine indirilir
# Kopyala:
cp ~/.config/Ultralytics/yolov8n.pt "$(dirname "$0")/yolov8n.pt" 2>/dev/null || \
  cp yolov8n.pt "$(dirname "$0")/yolov8n.pt" 2>/dev/null || \
  python3 -c "
from ultralytics import YOLO
import shutil, pathlib
m = YOLO('yolov8n.pt')
src = pathlib.Path(m.ckpt_path)
dst = pathlib.Path('$(dirname "$0")') / 'yolov8n.pt'
if src != dst: shutil.copy(src, dst)
print('Model kopyalandı:', dst)
"

echo ""
echo "=== Kurulum tamamlandı ==="
echo "Sunucuyu yeniden başlatın: pkill -f sunucu.py && python3 zunucu/sunucu.py &"
