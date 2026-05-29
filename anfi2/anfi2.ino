/*
 * Okul Zil Sistemi — Anfi Kontrol Arduino Kodu
 * Tasarim : Mustafa Necati BOZOK
 * Kodlama : Claude (Anthropic) - Mart 2026
 *
 * Baglantilar:
 *   Röle IN pini  → Arduino Digital Pin 7
 *   Röle VCC      → Arduino 5V
 *   Röle GND      → Arduino GND
 *   Buton         → Arduino Digital Pin 4  (diğer ucu GND'ye)
 *
 *   Çift Renkli LED (ortak katot):
 *   Kırmızı anot  → Arduino Digital Pin 12  (220Ω direnç üzerinden)
 *   Yeşil anot    → Arduino Digital Pin 11  (220Ω direnç üzerinden)
 *   Ortak katot   → Arduino GND
 *
 * Seri port: 9600 baud
 * Komutlar : ANFI_AC  → Anfi aç  (röle kapanır, 220V akar)
 *            ANFI_KAP → Anfi kapat (röle açılır, 220V kesilir)
 *            DURUM    → Mevcut durumu sorgula
 */

const int ROLE_PIN    = 7;   // Röle sinyal pini
const int LED_KIRMIZI = 12;  // Çift renkli LED — kırmızı anot (anfi kapalı)
const int LED_YESIL   = 11;  // Çift renkli LED — yeşil anot  (anfi açık)
const int BUTON_PIN   = 4;   // Manuel buton pini (GND'ye bağlı, INPUT_PULLUP)

// Röle mantığı: Optokuplörlü modüllerde LOW = aktif (anfi açık)
// Eğer röleniz HIGH aktifse ROLE_ACIK ve ROLE_KAPALI degerlerini değiştirin
const int ROLE_ACIK   = LOW;  // Röle kapanır → 220V akar  → Anfi açılır
const int ROLE_KAPALI = HIGH;   // Röle açılır  → 220V kesilir → Anfi kapanır

// Buton debounce süresi (ms) — titreşimi önler
const unsigned long DEBOUNCE_MS = 50;

bool anfiDurum    = false;
String komutBuffer = "";

// Buton durum takibi
int  butonSon         = HIGH;   // Pin'den son okunan ham değer
int  butonOnceki      = HIGH;   // Debounce sonrası kararlı değer
unsigned long butonZamani = 0;  // Son değişim zamanı

void anfiAc() {
  digitalWrite(ROLE_PIN, ROLE_ACIK);
  anfiDurum = true;
  Serial.println("OK:ANFI_ACILDI");
}

void anfiKapat() {
  digitalWrite(ROLE_PIN, ROLE_KAPALI);
  anfiDurum = false;
  Serial.println("OK:ANFI_KAPATILDI");
}

void setup() {
  pinMode(ROLE_PIN, OUTPUT);
  
  // Boot titreşimlerini geçmesini bekle
  digitalWrite(ROLE_PIN, ROLE_KAPALI);  // Önce hemen kapat
  delay(500);                            // 500ms bekle
  digitalWrite(ROLE_PIN, ROLE_KAPALI);  // Tekrar kapat (güvenlik için)
  
  pinMode(LED_KIRMIZI, OUTPUT);
  pinMode(LED_YESIL,   OUTPUT);
  pinMode(BUTON_PIN, INPUT_PULLUP);
  // Başlangıçta anfi kapalı → kırmızı yansın
  digitalWrite(LED_KIRMIZI, HIGH);
  digitalWrite(LED_YESIL,   LOW);

  Serial.begin(9600);
  Serial.println("ZIL_ARDUINO_HAZIR");
  Serial.println("Komutlar: ANFI_AC | ANFI_KAP | DURUM");
}

void loop() {

  /* ── 1. Seri porttan gelen komutları işle ─────────────────────── */
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      komutBuffer.trim();
      if (komutBuffer.length() > 0) {
        komutIsle(komutBuffer);
      }
      komutBuffer = "";
    } else {
      komutBuffer += c;
    }
  }

  /* ── 2. Manuel buton kontrolü (debounce ile) ──────────────────── */
  int butonSimdi = digitalRead(BUTON_PIN);

  // Pinден okunan değer değiştiyse debounce zamanlayıcısını sıfırla
  if (butonSimdi != butonSon) {
    butonZamani = millis();
    butonSon = butonSimdi;
  }

  // Debounce süresi geçti ve durum kararlı hale geldi
  if ((millis() - butonZamani) >= DEBOUNCE_MS) {
    // Kararlı durum öncekinden farklıysa işle
    if (butonSimdi != butonOnceki) {
      butonOnceki = butonSimdi;
      // Sadece basma anında (HIGH→LOW) tetikle
      if (butonSimdi == LOW) {
        Serial.println("BUTON:MANUEL_TETIKLEME");
        if (anfiDurum) {
          anfiKapat();
        } else {
          anfiAc();
        }
      }
    }
  }

  /* ── 3. LED renk göstergesi (anfi açık → yeşil, kapalı → kırmızı) ─ */
  digitalWrite(LED_KIRMIZI, anfiDurum ? LOW  : HIGH);
  digitalWrite(LED_YESIL,   anfiDurum ? HIGH : LOW);
}

void komutIsle(String komut) {
  if (komut == "ANFI_AC") {
    anfiAc();

  } else if (komut == "ANFI_KAP") {
    anfiKapat();

  } else if (komut == "DURUM") {
    Serial.print("DURUM:");
    Serial.println(anfiDurum ? "ACIK" : "KAPALI");

  } else {
    Serial.print("HATA:BILINMEYEN_KOMUT:");
    Serial.println(komut);
  }
}
