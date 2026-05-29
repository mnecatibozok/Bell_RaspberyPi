#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zil Sistemi — GPIO Röle Modülü
30A Relay Module, Raspberry Pi GPIO 17 pinine bağlı.
LOW  = röle aktif  (anfi açık)
HIGH = röle pasif  (anfi kapalı)

Pi 5 uyumluluğu için lgpio → RPi.GPIO → simülasyon sırasıyla denenir.
"""

import threading

_durum = False   # True = anfi açık
_lock  = threading.Lock()

RELAY_PIN = 17   # BCM numarası (fiziksel pin 11)

# ── GPIO backend tespiti ──────────────────────────────────
_BACKEND = None   # 'lgpio' | 'rpigpio' | None

try:
    import lgpio as _lgpio
    _lgpio_handle = _lgpio.gpiochip_open(0)
    _BACKEND = 'lgpio'
    print('[RELAY] GPIO backend: lgpio (Pi 5 uyumlu)')
except Exception:
    try:
        import RPi.GPIO as _rpigpio
        _rpigpio.setmode(_rpigpio.BCM)
        _rpigpio.setup(RELAY_PIN, _rpigpio.OUT)
        _BACKEND = 'rpigpio'
        print('[RELAY] GPIO backend: RPi.GPIO')
    except Exception as e:
        print(f'[RELAY] GPIO yüklenemedi ({e}) — simülasyon modu.')

# ── Yardımcı: pin yaz ────────────────────────────────────
def _pin_yaz(deger: bool):
    """deger=True → HIGH (kapalı), deger=False → LOW (açık)"""
    if _BACKEND == 'lgpio':
        _lgpio.gpio_write(_lgpio_handle, RELAY_PIN, 1 if deger else 0)
    elif _BACKEND == 'rpigpio':
        _rpigpio.output(RELAY_PIN, _rpigpio.HIGH if deger else _rpigpio.LOW)

# ── API ──────────────────────────────────────────────────
def baslat():
    if _BACKEND is None:
        print('[RELAY] Simülasyon modu — GPIO donanımı yok.')
        return
    try:
        if _BACKEND == 'lgpio':
            _lgpio.gpio_claim_output(_lgpio_handle, RELAY_PIN)
            _lgpio.gpio_write(_lgpio_handle, RELAY_PIN, 1)  # Başlangıçta kapalı
        elif _BACKEND == 'rpigpio':
            # setup zaten __init__'te yapıldı
            _rpigpio.output(RELAY_PIN, _rpigpio.HIGH)
        print(f'[RELAY] GPIO {RELAY_PIN} hazır ✓  (backend: {_BACKEND})')
    except Exception as e:
        print(f'[RELAY] baslat hatası: {e}')

def ac():
    global _durum
    with _lock:
        _durum = True
    try:
        _pin_yaz(False)   # LOW = röle aktif
    except Exception as e:
        print(f'[RELAY] ac hatası: {e}')
    print('[RELAY] Anfi açıldı')

def kapat():
    global _durum
    with _lock:
        _durum = False
    try:
        _pin_yaz(True)    # HIGH = röle pasif
    except Exception as e:
        print(f'[RELAY] kapat hatası: {e}')
    print('[RELAY] Anfi kapatıldı')

def get_durum() -> dict:
    with _lock:
        return {
            'anfi_acik' : _durum,
            'gpio_ok'   : _BACKEND is not None,
            'pin'       : RELAY_PIN,
            'backend'   : _BACKEND or 'simülasyon',
        }

def temizle():
    try:
        if _BACKEND == 'lgpio':
            _lgpio.gpio_write(_lgpio_handle, RELAY_PIN, 1)
            _lgpio.gpiochip_close(_lgpio_handle)
        elif _BACKEND == 'rpigpio':
            _rpigpio.output(RELAY_PIN, _rpigpio.HIGH)
            _rpigpio.cleanup()
        print('[RELAY] GPIO temizlendi')
    except Exception as e:
        print(f'[RELAY] temizle hatası: {e}')
