# Etkileşimli Kitap Kütüphanesi

Pardus tabanlı akıllı tahtalar (ETAP) için geliştirilmiş, modern kullanıcı arayüzüne sahip interaktif kitap kütüphanesi istemcisidir. 

Bu istemci, öğretmenlerin ve öğrencilerin akıllı tahtalarda interaktif kitap kütüphanelerini kolayca aramasını, indirmesini, kurmasını, çalıştırmasını ve kaldırmasını sağlar.

---

## 🚀 Başlangıç

Proje, hem Pardus akıllı tahta ortamında (üretim/production) hem de kişisel geliştirici bilgisayarlarında (simülasyon/developer) çalışabilecek şekilde tasarlanmıştır.

### 💻 Geliştirici / Simülatör Modu (Arch Linux vb.)

Sisteminizde hiçbir kalıcı değişiklik yapmadan, global kütüphaneler kurmadan veya sisteme paket eklemeden uygulamayı güvenli bir şekilde denemek için geliştirici çalıştırıcısını kullanabilirsiniz. Bu script, gerekli bağımlılıklar (PySide6, requests) sisteminizde yoksa proje dizininde izole bir sanal ortam (`.venv`) oluşturarak uygulamayı başlatır:

```bash
# Simülatör modunda güvenli çalıştırmak için:
./run_arch.py
```

### 🏫 Üretim Modu (Pardus / Debian Akıllı Tahta)

Uygulamanın gerçek sistem paketlerini (`.deb`) kurup silebildiği yetkili modda çalıştırmak için:

```bash
python3 -m src.main
```

---

## 📦 Debian Paketi Derleme & Standardizasyon

Etkileşimli Kitap Kütüphanesi, Debian ve Lintian standartlarına (Lisans/Copyright ve MD5 kontrol toplamı uyumluluğu) tam uyumlu bir paket derleme yapısına sahiptir.

### Derleme Adımları

Proje dizininde aşağıdaki scripti çalıştırarak debian paketini derleyebilirsiniz. Derleme tamamlandığında ana dizinde `etkilesimli-kitap-kutuphanesi_1.0.0_all.deb` paketi oluşacaktır:

```bash
./scripts/build_deb.sh
```

> [!NOTE]
> Sisteminizde standart paketleme aracı olan `dpkg-deb` yüklü değilse, derleme scripti otomatik olarak saf Python tabanlı paket derleyiciyi (`scripts/build_deb.py`) devreye sokar.

### Derlenen Paketi Doğrulama

Oluşturulan `.deb` paketinin Debian politikalarına uyumluluğunu, `md5sums` ve `copyright` dosyalarının varlığını incelemek için:

```bash
# Paket yapısını doğrulamak için:
python3 scripts/inspect_deb.py
```

---

## 🛠 Proje Yapısı

Dizin yapısı modüler ve temiz bir mimari sunar:

- `src/`: Uygulama kaynak kodları.
  - `src/main.py`: Uygulama ana giriş noktası.
  - `src/qt_compat.py`: PySide6, PyQt6 ve PyQt5 arasında otomatik uyumluluk katmanı.
  - `src/core/`: Arka plan iş mantığı (database, downloader, installer, config, updater).
  - `src/ui/`: Arayüz tasarımları (Libadwaita / Bottles stili modern pencereler ve temalar).
  - `src/assets/`: Uygulama görselleri, logolar ve kitap veritabanı (`books.json`).
- `debian/`: Standart debian paket yapılandırma dosyaları (`control`, `rules`, `changelog`, `copyright`).
- `docs/`: Mimari ve paketleme detaylarını içeren genişletilmiş dokümantasyon dizini.
- `scripts/`: Derleme, paketleme, veritabanı ayrıştırma ve diğer otomatikleştirme scriptleri.
- `tests/`: UI, updater ve ağ bağlantısı için otomatik birim/entegrasyon testleri.
- `mock_system/`: Geliştirici modunda indirmeleri ve kurulumları simüle etmek için kullanılan yerel önbellek dizini.

---

## ℹ️ Lisans

Bu proje **GPL-3.0** lisansı altında lisanslanmıştır. Detaylar için `debian/copyright` dosyasına bakabilirsiniz.
