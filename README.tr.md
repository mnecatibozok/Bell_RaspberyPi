# 🔔 Okul Zil Sistemi

> 🇬🇧 [For English documentation click here → README.md](README.md)

Raspberry Pi üzerinde çalışan, tarayıcı tabanlı bir okul zil yönetim sistemidir. Zilleri programlayın, ses çalın, müzik yönetin, kamera ile varlık tespiti yapın — tüm bunları okul ağındaki herhangi bir telefon veya bilgisayardan web arayüzü üzerinden yapabilirsiniz.

---

## Ne İşe Yarar?

- **Belirlediğiniz saatlerde otomatik zil çalar**
- **Dersler arası MP3 müzik çalar** (dahili müzik çalar ile)
- **USB kamera ve yapay zeka (YOLOv8) ile varlık tespiti yapar** — birisi odaya girdiğinde zil tetikleyebilir
- **Önceden kaydedilmiş sesli anonslar çalar** (deprem ikaz, İstiklal Marşı, öğrenci anonsu vb.)
- **Röle modülü ile amplifikatörü veya zili fiziksel olarak açıp kapatır**
- **Okul ağındaki her cihazdan tarayıcı üzerinden erişilebilir** — uygulama kurulumu gerekmez

---

## Gerekenler

| Malzeme | Detay |
|---|---|
| Raspberry Pi | Model 4B veya 5 önerilir (minimum 2 GB RAM) |
| MicroSD kart | 16 GB veya üzeri, Class 10 |
| Güç adaptörü | Resmi Raspberry Pi adaptörü |
| USB hoparlör veya amplifikatör | 3,5 mm veya USB girişli herhangi bir cihaz |
| USB kamera (isteğe bağlı) | Varlık tespiti için |
| Röle modülü (isteğe bağlı) | Zil veya amplifikatörü fiziksel olarak kontrol etmek için |
| Monitör (sadece ilk kurulum) | Sonrasında monitörsüz de çalışır |

---

## Adım Adım Kurulum

### 1. Adım — Raspberry Pi OS Kurulumu

> **Bunu yeni bir bilgisayara Windows kurmak gibi düşünün.**

1. Başka bir bilgisayarda **Raspberry Pi Imager** programını indirin: https://www.raspberrypi.com/software/
2. MicroSD kartı bir kart okuyucu aracılığıyla o bilgisayara takın.
3. Raspberry Pi Imager'ı açın.
4. **"İşletim Sistemi Seç"** → **"Raspberry Pi OS (64-bit)"** (masaüstü ortamlı olan) seçin.
5. **"Depolama Seç"** → MicroSD kartınızı seçin.
6. **Dişli simgesine** (⚙️) tıklayarak gelişmiş ayarları açın:
   - Bir **hostname** belirleyin (örneğin `zilpi`)
   - Bir **kullanıcı adı ve şifre** belirleyin (bunları bir yere not edin!)
   - **SSH'yi etkinleştirin** (daha sonra uzaktan bağlanmak için)
   - Wi-Fi kullanıyorsanız **Wi-Fi adı ve şifrenizi** girin
7. **"Yaz"**'a tıklayın ve tamamlanmasını bekleyin (~5 dakika).
8. MicroSD kartı Raspberry Pi'ye takın, güç kablosunu bağlayın ve ~2 dakika açılmasını bekleyin.

---

### 2. Adım — Pi'ye Bağlanın ve Güncelleyin

> **Bu işlemi yalnızca bir kez yapmanız yeterlidir.**

Pi'ye monitör ve klavye bağlayın (veya SSH ile bağlanın). Ardından **Terminal** açın ve şunu çalıştırın:

```bash
sudo apt update && sudo apt upgrade -y
```

Bu komut tüm sistem yazılımlarını günceller. 5–10 dakika sürebilir. Çay molası verin. 🍵

Ardından Python 3'ü yükleyin (genellikle zaten yüklüdür):

```bash
sudo apt install python3 python3-pip -y
```

---

### 3. Adım — Zil Sistemi Dosyalarını Pi'ye Kopyalayın

1. Bu sayfanın **Releases** bölümünden **zil-v1-kamera-fix20.zip** dosyasını indirin.
2. Dosyayı Pi'ye kopyalayın. En kolay yol:
   - Bir USB belleğe kopyalayıp USB belleği Pi'ye takın.
   - Ya da ağ üzerinden Pi'nin dosya yöneticisine sürükleyip bırakın.
3. Pi'de **Dosya Yöneticisi**'ni açın, Masaüstü'ne gidin ve `zil` adında yeni bir klasör oluşturun.
4. ZIP dosyasını o klasöre taşıyın, sağ tıklayıp **"Buraya Çıkart"**'ı seçin.

Klasör yapınız şöyle görünmelidir:

```
/home/abc/Desktop/zil/
    zil-programi-v1.html
    zil-baslat.sh
    KURULUM.txt
    zunucu/
        sunucu.py
        ...
    zilsesleri/
        zil.mp3
        siren.mp3
        ...
```

> ⚠️ **Önemli:** Yukarıdaki yollardaki `abc` kullanıcı adı bir örnektir. Bunu 1. Adımda belirlediğiniz kendi kullanıcı adınızla değiştirin (örneğin `pi`, `admin` veya ne koydunuzu).

---

### 4. Adım — (İsteğe Bağlı) Yapay Zeka Kamera Özelliğini Kurun

> USB kameranız yoksa veya varlık tespitine ihtiyacınız yoksa bu adımı atlayın.

Terminal açıp şunu çalıştırın:

```bash
cd /home/abc/Desktop/zil
bash zunucu/ai_kur.sh
```

Bu komut YOLOv8-nano yapay zeka modelini (~6 MB) indirir ve gerekli bağımlılıkları kurar. Yavaş bir bağlantıda 10–15 dakika sürebilir.

---

### 5. Adım — Sistemi Başlatın

**A Seçeneği — Çift tıklama (en kolay):**

Masaüstündeki `Zil-Baslat.desktop` dosyasına çift tıklayın.
"Bu dosyayı çalıştırmak istiyor musunuz?" diye sorarsa **"Çalıştır"**'a tıklayın.

**B Seçeneği — Terminal:**

```bash
bash /home/abc/Desktop/zil/zil-baslat.sh
```

Sistem başladığında tarayıcı penceresi otomatik olarak açılır ve Zil Sistemi arayüzü görüntülenir.

---

### 6. Adım — Başka Bir Cihazdan Arayüzü Açın

Sistem çalışır hale gelince, **aynı Wi-Fi ağındaki herhangi bir telefon, tablet veya bilgisayardan** kontrol edebilirsiniz.

1. Pi'nin IP adresini öğrenin: Pi'de Terminal açıp şunu yazın:
   ```bash
   hostname -I
   ```
   `192.168.1.42` gibi bir şey göreceksiniz.

2. Telefonunuzda veya başka bir bilgisayarda tarayıcıyı açıp şu adrese gidin:
   ```
   http://192.168.1.42:8765/zil-programi-v1.html
   ```
   (`192.168.1.42` yerine Pi'nizin gerçek IP adresini yazın.)

---

### 7. Adım — (İsteğe Bağlı) Açılışta Otomatik Başlat

Pi her açıldığında zil sistemi otomatik başlasın mı?

Terminal açıp şu iki komutu çalıştırın:

```bash
mkdir -p /home/abc/.config/autostart
cp /home/abc/Desktop/zil/zil-autostart.desktop /home/abc/.config/autostart/zil.desktop
```

Artık Pi her açıldığında Zil Sistemi otomatik olarak başlar. Klavyeye gerek kalmaz.

---

## Kendi Zil Seslerinizi Eklemek

`.mp3` formatındaki ses dosyalarınızı `zil` klasörü içindeki `zilsesleri/` klasörüne kopyalamanız yeterlidir. Sistem bir sonraki başlatmada bunları otomatik olarak algılar.

> Desteklenen format: **MP3**. Dosya adında boşluk bırakmayın — bunun yerine alt çizgi kullanın (örneğin `okul_zili.mp3`).

---

## Arka Plan Müziği Eklemek

`zil` klasörü içinde `mp3` adında bir klasör oluşturun, içine çalma listesi klasörleri ekleyin:

```
zil/
  mp3/
    sabah/
      sarki1.mp3
      sarki2.mp3
    teneffus/
      sarki3.mp3
```

Sistem bu klasörleri tarayarak Müzik Çalar panelinde kullanılabilir hale getirir.

---

## Sistemi Durdurmak

Sunucuyu durdurmak için Terminal'e şunu yazın:

```bash
pkill -f sunucu.py
```

Tarayıcıyı da kapatmak için:

```bash
pkill chromium
```

---

## Sık Karşılaşılan Sorunlar

**Tarayıcı otomatik açılmıyor**
→ Chromium'u elle açın ve `http://localhost:8765/zil-programi-v1.html` adresine gidin.

**Ses çıkmıyor**
→ Hoparlörün bağlı olduğundan ve Pi'nin ses çıkışının doğru cihaza ayarlandığından emin olun. Terminal'de `alsamixer` komutunu çalıştırın ve sesin kapalı olmadığını kontrol edin.

**Kamera görüntüsü gelmiyor**
→ Sunucu başlamadan önce USB kameranın takılı olduğundan emin olun. Terminal'de `ls /dev/video*` yazın — `/dev/video0` görünmelidir.

**Açılışta otomatik başlamıyor**
→ `zil-autostart.desktop` dosyasındaki yolların gerçek kullanıcı adınız ve klasör konumunuzla eşleştiğini kontrol edin.

**Kullanıcı adını değiştirdim, yollar bozuldu**
→ `zil-baslat.sh`, `bell-start.sh` ve `zil-autostart.desktop` dosyalarını bir metin editöründe açın, `abc` yazan yerleri kendi kullanıcı adınızla değiştirin.

---

## Dil Desteği

Arayüzün sağ üst köşesindeki **TR / EN** düğmesiyle Türkçe ve İngilizce arasında geçiş yapabilirsiniz.

---

## Lisans

Bu proje eğitim amaçlı geliştirilmiştir. Okulunuz için özgürce uyarlayabilirsiniz.
