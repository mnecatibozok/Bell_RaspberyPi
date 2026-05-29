#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zil Sistemi — Koridor Kamera Modülü
Raspberry Pi Camera Module 3 + picamera2
- 320x240 MJPEG stream
- YOLOv8-nano ile AI tabanlı insan tespiti (birincil)
- Piksel farkına dayalı hafif hareket algılama (yedek/fallback)
- Hareket logu (günlük JSON dosyası)
- Hareket anında snapshot kaydı (img/YYYYMMDD/)
"""

import io, json, os, threading, time, datetime
from pathlib import Path

# picamera2 sadece Raspberry Pi'de mevcut olur.
try:
    from picamera2 import Picamera2
    _PI_CAM = True
except ImportError:
    _PI_CAM = False

# YOLOv8 (ultralytics) — yoksa piksel-fark yöntemine düşer
try:
    from ultralytics import YOLO as _YOLO
    _YOLO_OK = True
except ImportError:
    _YOLO_OK = False

# ── Sabitler ─────────────────────────────────────────────
CAM_W        = 640
CAM_H        = 480
JPEG_KALITE  = 75
KONTROL_ARA  = 1.0          # YOLOv8 için 1 sn (piksel fark 0.5 sn)
BANNER_SURE  = 15
LOG_DIZIN    = Path(__file__).parent.parent / 'temp'
IMG_DIZIN    = Path(__file__).parent.parent / 'img'
MODEL_YOLU   = Path(__file__).parent / 'yolov8n.pt'

# YOLOv8 güven ve IoU eşiği
YOLO_CONF    = 0.45         # %45 güven altı yok say
YOLO_IOU     = 0.45

# ── Paylaşılan durum ─────────────────────────────────────
_lock          = threading.Lock()
_frame         = None
_hareket_var   = False
_hareket_zaman = None
_bugun_sayisi  = 0
_son_tespit    = None
_esik          = 50          # Piksel fark eşiği VEYA YOLO güven eşiği %
_ders_saati    = False
_her_zaman     = False       # True → ders saati kontrolü yapma, her zaman algıla
_banner_timer  = None
_baslatildi    = False
_ai_aktif      = False       # YOLOv8 başarıyla yüklendiyse True
_ai_model      = None        # YOLO model nesnesi
_son_ai_sonuc  = {}          # Frontend için son AI sonucu

# ── YOLOv8 başlatma ──────────────────────────────────────
def _yolo_yukle():
    global _ai_aktif, _ai_model
    if not _YOLO_OK:
        print('[AI] ultralytics yüklü değil, piksel-fark moduna geçildi.')
        return
    try:
        print('[AI] YOLOv8-nano modeli yükleniyor...')
        _ai_model = _YOLO(str(MODEL_YOLU))
        _ai_aktif = True
        print('[AI] YOLOv8-nano hazır ✓')
    except Exception as e:
        print(f'[AI] Model yüklenemedi: {e} → piksel-fark moduna geçildi.')
        _ai_aktif = False

# ── Yardımcı: piksel farkı ───────────────────────────────
def _piksel_farki(f1: bytes, f2: bytes) -> float:
    try:
        n = min(len(f1), len(f2))
        if n == 0:
            return 0.0
        toplam = sum(abs(a - b) for a, b in zip(f1[:n:3], f2[:n:3]))
        return round(toplam / (n // 3) / 255 * 100, 1)
    except Exception:
        return 0.0

# ── Log ──────────────────────────────────────────────────
def _log_dosyasi() -> Path:
    bugun = datetime.date.today().strftime('%Y-%m-%d')
    return LOG_DIZIN / f'kamera_{bugun}.json'

def _log_yukle() -> list:
    try:
        f = _log_dosyasi()
        if f.exists():
            return json.loads(f.read_text('utf-8'))
    except Exception:
        pass
    return []

def _log_kaydet(kayitlar: list):
    try:
        LOG_DIZIN.mkdir(exist_ok=True)
        _log_dosyasi().write_text(json.dumps(kayitlar, ensure_ascii=False, indent=2), 'utf-8')
    except Exception as e:
        print(f'[KAM] Log kayıt hatası: {e}')

def _hareket_logla(degisim: float, sure: float, ai_bilgi: dict = None):
    kayitlar = _log_yukle()
    simdi    = datetime.datetime.now()
    kayit = {
        'tarih'     : simdi.strftime('%d.%m.%Y'),
        'saat'      : simdi.strftime('%H:%M:%S'),
        'sure'      : round(sure, 1),
        'degisim'   : round(degisim, 1),
        'ders_saati': _ders_saati,
        'ai_tespit' : bool(ai_bilgi),
    }
    if ai_bilgi:
        kayit['ai_kisi_sayisi'] = ai_bilgi.get('kisi_sayisi', 0)
        kayit['ai_guveni']      = ai_bilgi.get('max_guven', 0)
    kayitlar.insert(0, kayit)
    kayitlar = kayitlar[:500]
    _log_kaydet(kayitlar)

# ── Snapshot ─────────────────────────────────────────────
def _snapshot_kaydet(ai_bilgi: dict = None):
    """Frame'i img/YYYYMMDD/ klasörüne kaydeder; alt kısmına bilgi bandı yazar."""
    try:
        with _lock:
            frame = _frame
            ders  = _ders_saati
        if frame is None:
            return
        from PIL import Image, ImageDraw, ImageFont

        simdi = datetime.datetime.now()
        img   = Image.open(io.BytesIO(frame)).convert('RGB')
        w, h  = img.size

        # YOLOv8 tespit kutularını çiz
        if ai_bilgi and ai_bilgi.get('kutular'):
            draw_img = ImageDraw.Draw(img)
            for kutu in ai_bilgi['kutular']:
                x1, y1, x2, y2, conf = kutu
                draw_img.rectangle([(x1,y1),(x2,y2)], outline=(255,50,50), width=2)
                draw_img.text((x1+3, y1+2), f'%{int(conf*100)}', fill=(255,255,50))

        # Alt bilgi bandı
        bant_h = max(30, int(h * 0.12))
        yeni   = Image.new('RGB', (w, h + bant_h), (0, 0, 0))
        yeni.paste(img, (0, 0))
        draw   = ImageDraw.Draw(yeni)
        draw.rectangle([(0, h), (w, h + bant_h)], fill=(160, 0, 0))

        tarih_str = simdi.strftime('%d.%m.%Y')
        saat_str  = simdi.strftime('%H:%M:%S')
        ders_str  = 'DERS SAATİ' if ders else 'DERS DIŞI'
        if ai_bilgi and ai_bilgi.get('kisi_sayisi', 0) > 0:
            ai_str = f"AI: {ai_bilgi['kisi_sayisi']} kişi (%{int(ai_bilgi.get('max_guven',0)*100)})"
        else:
            ai_str = 'AI: Tespit'
        metin = f'{tarih_str}  {saat_str}  |  {ders_str}  |  {ai_str}'

        font = None
        font_boyut = max(14, bant_h - 10)
        for fp in [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
            '/usr/share/fonts/truetype/freefont/FreeSansBold.ttf',
        ]:
            try:
                from PIL import ImageFont as _IF
                font = _IF.truetype(fp, font_boyut)
                break
            except Exception:
                continue
        if font is None:
            from PIL import ImageFont as _IF
            font = _IF.load_default()

        try:
            bbox = draw.textbbox((0,0), metin, font=font)
            tx   = (w - (bbox[2] - bbox[0])) // 2
            ty   = h + (bant_h - (bbox[3] - bbox[1])) // 2
        except AttributeError:
            tx, ty = 8, h + 4

        draw.text((tx, ty), metin, fill=(255, 255, 255), font=font)

        buf = io.BytesIO()
        yeni.save(buf, format='JPEG', quality=85)

        gun_klasor = IMG_DIZIN / simdi.strftime('%Y%m%d')
        gun_klasor.mkdir(parents=True, exist_ok=True)
        dosya_adi  = simdi.strftime('%H%M%S_%f')[:10] + '.jpg'
        (gun_klasor / dosya_adi).write_bytes(buf.getvalue())
        print(f'[KAM] Snapshot kaydedildi: {gun_klasor / dosya_adi}')
    except Exception as e:
        print(f'[KAM] Snapshot kayıt hatası: {e}')

# ── Kamera thread (picamera2) ─────────────────────────────
def _kamera_thread():
    global _frame
    print('[KAM] Kamera başlatılıyor (picamera2)...')
    try:
        cam    = Picamera2()
        config = cam.create_video_configuration(
            main={'size': (CAM_W, CAM_H), 'format': 'RGB888'},
            encode='main',
        )
        cam.configure(config)
        cam.start()
        print(f'[KAM] Kamera hazır: {CAM_W}×{CAM_H}')
        from PIL import Image
        while True:
            arr = cam.capture_array()
            img = Image.fromarray(arr[:, :, ::-1]).transpose(Image.FLIP_LEFT_RIGHT)
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=JPEG_KALITE)
            with _lock:
                _frame = buf.getvalue()
            time.sleep(0.04)
    except Exception as e:
        print(f'[KAM] Kamera hatası: {e}')
        _placeholder_thread()

def _placeholder_thread():
    global _frame
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print('[KAM] Pillow yüklü değil.')
        return
    while True:
        img  = Image.new('RGB', (CAM_W, CAM_H), (15, 15, 30))
        draw = ImageDraw.Draw(img)
        t    = datetime.datetime.now().strftime('%H:%M:%S')
        draw.rectangle([0, 0, CAM_W-1, CAM_H-1], outline=(50, 80, 120))
        draw.text((CAM_W//2 - 50, CAM_H//2 - 10), f'KAM YOK  {t}', fill=(80, 120, 180))
        buf  = io.BytesIO()
        img.save(buf, format='JPEG', quality=60)
        with _lock:
            _frame = buf.getvalue()
        time.sleep(1)

# ── AI hareket thread (YOLOv8) ────────────────────────────
def _ai_hareket_thread():
    """YOLOv8-nano ile her saniyede insan tespiti yapar."""
    global _hareket_var, _hareket_zaman, _bugun_sayisi, _son_tespit
    global _banner_timer, _son_ai_sonuc
    hareket_aktif    = False
    hareket_baslangic = None
    son_ai_bilgi     = {}

    while True:
        time.sleep(KONTROL_ARA)

        if not _her_zaman and not _ders_saati:
            if hareket_aktif:
                hareket_aktif = False
                hareket_baslangic = None
                with _lock:
                    _hareket_var = False
            _son_ai_sonuc = {'kisi_sayisi': 0, 'max_guven': 0, 'kutular': []}
            continue

        with _lock:
            mevcut = _frame
        if mevcut is None:
            continue

        simdi     = datetime.datetime.now()
        tespit_var = False
        ai_bilgi  = {}

        try:
            from PIL import Image as _PImg
            img_pil = _PImg.open(io.BytesIO(mevcut))
            sonuclar = _ai_model.predict(
                source=img_pil,
                classes=[0],        # 0 = person (COCO)
                conf=YOLO_CONF,
                iou=YOLO_IOU,
                verbose=False,
            )
            kutular     = []
            max_guven   = 0.0
            kisi_sayisi = 0
            for r in sonuclar:
                for box in r.boxes:
                    conf = float(box.conf[0])
                    x1, y1, x2, y2 = [int(v) for v in box.xyxy[0]]
                    kutular.append((x1, y1, x2, y2, conf))
                    if conf > max_guven:
                        max_guven = conf
                    kisi_sayisi += 1
            tespit_var = kisi_sayisi > 0
            ai_bilgi   = {'kisi_sayisi': kisi_sayisi, 'max_guven': round(max_guven,2), 'kutular': kutular}
            _son_ai_sonuc = ai_bilgi
        except Exception as e:
            print(f'[AI] Tahmin hatası: {e}')
            continue

        if tespit_var:
            if not hareket_aktif:
                hareket_aktif     = True
                hareket_baslangic = simdi
                son_ai_bilgi      = ai_bilgi
                with _lock:
                    _hareket_var   = True
                    _hareket_zaman = simdi.strftime('%H:%M')
                    _son_tespit    = simdi.strftime('%H:%M')
                    _bugun_sayisi += 1
                threading.Thread(target=_snapshot_kaydet, args=(ai_bilgi,), daemon=True).start()
                if _banner_timer:
                    _banner_timer.cancel()
                _banner_timer = threading.Timer(BANNER_SURE, _banner_kapat)
                _banner_timer.daemon = True
                _banner_timer.start()
        else:
            if hareket_aktif:
                hareket_aktif = False
                sure = (simdi - hareket_baslangic).total_seconds() if hareket_baslangic else 0
                _hareket_logla(0, sure, son_ai_bilgi)
                hareket_baslangic = None
                son_ai_bilgi      = {}

# ── Piksel-fark yedek thread ──────────────────────────────
def _hareket_thread():
    """YOLOv8 yoksa piksel karşılaştırması ile hareket algılar."""
    global _hareket_var, _hareket_zaman, _bugun_sayisi, _son_tespit, _banner_timer
    onceki_frame     = None
    hareket_aktif    = False
    hareket_baslangic = None

    while True:
        time.sleep(0.5)
        with _lock:
            mevcut = _frame

        if mevcut is None or onceki_frame is None:
            onceki_frame = mevcut
            continue

        if not _her_zaman and not _ders_saati:
            if hareket_aktif:
                hareket_aktif = False
                hareket_baslangic = None
                with _lock:
                    _hareket_var = False
            onceki_frame = mevcut
            continue

        degisim      = _piksel_farki(onceki_frame, mevcut)
        onceki_frame = mevcut
        simdi        = datetime.datetime.now()

        if degisim >= _esik:
            if not hareket_aktif:
                hareket_aktif     = True
                hareket_baslangic = simdi
                with _lock:
                    _hareket_var   = True
                    _hareket_zaman = simdi.strftime('%H:%M')
                    _son_tespit    = simdi.strftime('%H:%M')
                    _bugun_sayisi += 1
                threading.Thread(target=_snapshot_kaydet, daemon=True).start()
                if _banner_timer:
                    _banner_timer.cancel()
                _banner_timer = threading.Timer(BANNER_SURE, _banner_kapat)
                _banner_timer.daemon = True
                _banner_timer.start()
        else:
            if hareket_aktif:
                hareket_aktif = False
                sure = (simdi - hareket_baslangic).total_seconds() if hareket_baslangic else 0
                _hareket_logla(degisim, sure)
                hareket_baslangic = None

def _banner_kapat():
    global _hareket_var
    with _lock:
        _hareket_var = False

# ── Genel API ─────────────────────────────────────────────
def baslat():
    global _baslatildi
    if _baslatildi:
        return
    _baslatildi = True
    LOG_DIZIN.mkdir(exist_ok=True)
    IMG_DIZIN.mkdir(exist_ok=True)

    # Kamera thread
    if _PI_CAM:
        t = threading.Thread(target=_kamera_thread, daemon=True)
    else:
        print('[KAM] picamera2 bulunamadı, placeholder modu.')
        t = threading.Thread(target=_placeholder_thread, daemon=True)
    t.start()

    # AI veya yedek hareket thread
    _yolo_yukle()
    if _ai_aktif:
        th = threading.Thread(target=_ai_hareket_thread, daemon=True)
        print('[AI] YOLOv8-nano hareket algılama başlatıldı.')
    else:
        th = threading.Thread(target=_hareket_thread, daemon=True)
        print('[KAM] Piksel-fark hareket algılama başlatıldı.')
    th.start()

def get_frame() -> bytes | None:
    with _lock:
        return _frame

def get_durum(ders_saati_aktif: bool = False) -> dict:
    global _ders_saati
    _ders_saati = ders_saati_aktif
    with _lock:
        d = {
            'hareket_var' : _hareket_var,
            'son_tespit'  : _son_tespit or '—',
            'bugun_sayisi': _bugun_sayisi,
            'ders_saati'  : _ders_saati,
            'esik'        : _esik,
            'bagli'       : _frame is not None,
            'ai_aktif'    : _ai_aktif,
            'her_zaman'   : _her_zaman,
        }
    d.update(_son_ai_sonuc)
    return d

def get_log() -> dict:
    kayitlar = _log_yukle()
    return {
        'kayitlar'    : kayitlar,
        'esik'        : _esik,
        'bugun_sayisi': len(kayitlar),
        'ders_sayisi' : sum(1 for k in kayitlar if k.get('ders_saati')),
        'ai_aktif'    : _ai_aktif,
    }

def temizle_log():
    try:
        f = _log_dosyasi()
        if f.exists():
            f.unlink()
    except Exception:
        pass

def set_esik(yeni_esik: int):
    global _esik, YOLO_CONF
    _esik     = max(5, min(95, int(yeni_esik)))
    YOLO_CONF = _esik / 100

def set_mod(her_zaman: bool):
    global _her_zaman
    _her_zaman = bool(her_zaman)
    print(f'[KAM] Mod güncellendi: {"her zaman" if _her_zaman else "sadece ders saati"}')  # AI modunda güven eşiği olarak kullan
