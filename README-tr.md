# Raf — Etkileşimli Kitap Kütüphanesi

[![English](https://img.shields.io/badge/Language-English-blue?style=flat-square)](README.md)

[![Build Debian Package](https://github.com/KaanFerid/Raf/actions/workflows/build.yml/badge.svg)](https://github.com/KaanFerid/Raf/actions/workflows/build.yml)
[![Release](https://github.com/KaanFerid/Raf/actions/workflows/release.yml/badge.svg)](https://github.com/KaanFerid/Raf/actions/workflows/release.yml)

> **[📖 Raf Wiki Sayfasına Git](wiki/Home-tr.md)** — CLI referansları, mimari diyagramlar ve paketleme rehberleri dahil tüm dokümantasyonu keşfetmek için.

**Raf**, öğretmenlerin ve öğrencilerin tek bir tıklamayla etkileşimli kitap kütüphanelerini aramasını, indirmesini, kurmasını, başlatmasını ve kaldırmasını sağlayan Pardus tabanlı ETAP (akıllı tahta) sistemleri için modern bir masaüstü uygulamasıdır. Global karanlık/aydınlık tema motoruna sahip şık bir Libadwaita tarzı arayüz, bağımlılık içermeyen özel bir i18n çeviri sistemi, sürükle-bırak ve "Birlikte Aç" kurulumları için yerel işletim sistemi entegrasyonu, komut satırı arayüzü ve otomatik güncelleme sistemi sunar.

---

## İçindekiler

1. [Özellikler](#özellikler)
2. [Gereksinimler](#gereksinimler)
3. [Kurulum](#kurulum)
4. [Uygulamayı Çalıştırma](#uygulamayı-çalıştırma)
5. [Komut Satırı Arayüzü (CLI)](#komut-satırı-arayüzü-cli)
6. [GUI Kullanımı](#gui-kullanımı)
7. [Tercihler ve Ayarlar](#tercihler-ve-ayarlar)
8. [.deb Paketi Oluşturma](#deb-paketi-oluşturma)
9. [Geliştirici Modu](#geliştirici-modu)
10. [Proje Yapısı](#proje-yapısı)
11. [Testleri Çalıştırma](#testleri-çalıştırma)
12. [Lisans ve Teşekkür](#lisans-ve-teşekkür)

---

## Özellikler

### Temel Özellikler
- 🔍 **Gerçek zamanlı arama:** En yüksek GUI performansı için 300 ms gecikme (debounce) ile kitap adları, yayıncılar ve açıklamalar içinde anında arama.
- ⬇️ **Devam ettirilebilir indirmeler:** HTTP `Range` başlığı desteği ve Google Drive indirme uyarılarını aşma.
- 📦 **Çok formatlı kurulum** — `.deb`, `.zip`/`.fernus`, `.appimage`, Flatpak, Snap formatlarını destekler.
- 🚀 **Kurulu kitapları başlatma:** Doğrudan uygulama içerisinden kitapları açabilirsiniz.
- 🗑️ **Kaldırma:** Kurulu herhangi bir kütüphaneyi temiz bir şekilde kaldırabilirsiniz.

### Dışarıdan Yükleme ve İşletim Sistemi Entegrasyonu
- 📥 **Sürükle & Bırak** — Kurulum yapmak için dosyaları doğrudan uygulama penceresine sürükleyin.
- 📂 **Birlikte Aç...** — Dosya yöneticinizde paketlere sağ tıklayın ve Raf ile açın.
- 🛡️ **Onay İletişim Kutusu** — Yönetici parolası istemeden önce tüm yerel paketleri gözden geçirme ekranında toplar.

### Performans ve Güvenlik
- 🏎️ **Asenkron Mimari** — Sistem paketi sorguları (`dpkg`) ve kurulumlar arka plan iş parçacıklarında (threads) gerçekleşir, böylece kullanıcı arayüzü asla donmaz.
- 🔐 **Güvenli Alt Süreçler** — Tüm sistem etkileşimleri güvenli dizi (array) yürütmesi kullanır ve kabuk enjeksiyonu (shell injection) açıklarını önler.
- 🛡️ **Kurulum Öncesi Onay** — Sistem kimlik doğrulamasından hemen önce kurulum akışını durdurur ve kullanıcının beklenmedik `pkexec` isteklerini önlemek için kurulacak paketi açıkça görmesini sağlar.
- 📋 **Canlı Log Görüntüleyici** — Kurulum çıktılarını gerçek zamanlı olarak ayıklamak (debug) için özel bir Log (Günlük) iletişim kutusu.

### Kuyruk ve İlerleme
- 📋 **İndirme kuyruğu** — Birden fazla kitap ekleyebilirsiniz; aynı anda en fazla 2 indirme çalışır, diğerleri sırayla bekler.
- 📊 **Başlık çubuğunda ilerleme** — İndirme sırasında pencere başlığında ilerleme durumu gösterilir (ör. `[▼ KitapAdı — %67]`).
- 🔔 **Toast bildirimleri** — Kurulum/kaldırma/güncelleme etkinlikleri için şık, otomatik kapanan bildirimler.

### Bağlantı ve Senkronizasyon
- 📡 **Uzak veritabanı senkronizasyonu** — Uygulama başlangıcında herhangi bir URL'den güncel `books.json` dosyasını getirir.
- 🌐 **Çevrimdışı mod tespiti** — Ağ bağlantısı olmadığında indirmeleri devre dışı bırakır ve bir uyarı gösterir.

### Arayüz ve Temalandırma
- 🎨 **Merkezi Tema Motoru** — Uygulama genelinde (mesaj kutuları ve pop-up'lar dahil) Aydınlık ve Karanlık stiller arasında `QApplication` düzeyinde stil dosyaları kullanarak anında geçiş yapar.
- 🌍 **Özel Bağımlılıksız i18n Motoru** — Düzleştirilmiş (flattened) JSON okuma, `_meta` blokları ile dilleri otomatik keşfetme, İngilizce yedek dil desteği ve uygulamayı yeniden başlatmadan anında UI güncellemesi ile sıfırdan oluşturulmuştur!
- 🔔 **Sistem teması senkronizasyonu** — D-Bus üzerinden masaüstü karanlık/aydınlık tercihini takip eder.

---

## Gereksinimler

### Sistem (Üretim — Pardus/Debian/Ubuntu)

| Bağımlılık | Amaç |
|---|---|
| `python3` (≥ 3.9) | Çalışma zamanı |
| `python3-pyqt5` | Birincil Qt GUI çerçevesi (Pardus ETAP için optimize edilmiştir) |
| `python3-requests` | HTTP indirmeleri |
| `policykit-1` | Yetkili paket işlemleri (`pkexec`) |
| `dpkg` / `apt-get` | `.deb` paketi kurulumu |

### Geliştirici Makinesi (Herhangi bir Linux/macOS)

```text
PyQt5 >= 5.15.0
requests >= 2.25.0
urllib3 >= 1.26.0
```

Kurulum için:
```bash
pip install -r requirements.txt
```

> **Not:** `run_dev.py` sanal ortam (venv) oluşturmayı ve bağımlılık kurulumunu otomatik olarak halleder.

---

## Kurulum

### .deb Paketinden (Pardus İçin Önerilen)

```bash
# Önceden derlenmiş .deb paketini kurun:
sudo apt install ./raf_1.0.3_all.deb
```

Veya `.deb` dosyasına çift tıklayarak yazılım merkezi üzerinden kurabilirsiniz.

Kurulumdan sonra, Raf sistem genelinde şu şekilde kullanılabilir:
```bash
raf           # GUI'yi başlatır
raf list      # CLI komutlarını çalıştırır
```

### Kaynak Koddan

```bash
git clone https://github.com/KaanFerid/Raf.git
cd raf
pip install -r requirements.txt
python3 -m src.main
```

---

## Uygulamayı Çalıştırma

### Üretim Modu (Pardus / Debian)

`.deb` paketlerini kurmak için tam sistem ayrıcalıklarıyla çalışır:

```bash
python3 -m src.main
```

Veya `.deb` paketinden kurulduysa:

```bash
raf
```

### Geliştirici / Simülatör Modu

`run_dev.py` betiği, uygulamayı tamamen korumalı (sandboxed) bir simülasyon ortamında başlatır. Sisteminizde **kalıcı hiçbir değişiklik yapmaz**:

- İndirmeler `mock_system/cache/` klasörüne kaydedilir
- Kurulumlar `mock_system/installed.json` içinde takip edilir
- PolicyKit şifre istekleri atlanır (simüle edilir)

```bash
./run_dev.py
```

Eğer `PyQt5` veya `requests` kurulu değilse, betik başlatılmadan önce otomatik olarak bir `.venv` sanal ortamı oluşturur ve kütüphaneleri kurar.

---

## Komut Satırı Arayüzü (CLI)

Raf, başsız/terminal kullanımı için tam özellikli bir CLI içerir. Tüm komutlar hem üretim hem de geliştirici modunda çalışır.

### Kullanım

```bash
raf <komut> [argümanlar]
# veya geliştirici/kaynak modunda:
./run_dev.py <komut> [argümanlar]
# veya doğrudan:
python3 -m src.main <komut> [argümanlar]
```

### Komutlar

#### `list` — Tüm mevcut kitapları listele
```bash
raf list
```
Veritabanındaki tüm kitapların biçimlendirilmiş bir tablosunu yazdırır.

---

#### `list-installed` — Kurulu kitapları listele
```bash
raf list-installed
```
Sadece sisteme kurulu olan kitapları gösterir.

---

#### `search <terim>` — Kitap veritabanında arama yap
```bash
raf search ankara
```
Kitap adları, yayıncılar ve açıklamalar içinde arama yapar. Büyük/küçük harfe duyarlı değildir.

---

#### `install <kitap_id>` — Kitap indir ve kur
```bash
raf install akademikbasariyayinlarikutuphane
```
Bu komut paketi indirir (gerçek zamanlı ilerleme çubuğu ile) ve `pkexec apt-get install` (`.deb` için) ile kurar veya `.zip` için klasöre çıkartır.

---

#### `uninstall <kitap_id>` — Kitabı kaldır
```bash
raf uninstall akademikbasariyayinlarikutuphane
```
Paketi `.deb` için `pkexec apt-get remove` kullanarak sistemden kaldırır veya `.zip` paketleri için çıkarılan dizini ve `.desktop` başlatıcısını siler.

---

#### `clean` — İndirme önbelleğini temizle
```bash
raf clean
```
Önbelleğe alınmış tüm `.deb` ve `.zip` dosyalarını `~/.cache/raf/downloads/` klasöründen siler. Silinen dosya sayısını raporlar.

---

#### `--help` / `-h` — Yardımı göster
```bash
raf --help
```
Tüm mevcut komutların özetini yazdırır.

---

### CLI Çıkış Kodları

| Kod | Anlamı |
|---|---|
| `0` | Başarılı |
| `1` | Hata (eksik argüman, kitap bulunamadı, indirme başarısız vb.) |

---

## GUI Kullanımı

### Dışarıdan Yükleme (Sürükle & Bırak / Birlikte Aç)
Dosyalara manuel olarak göz atmanıza gerek yok. Desteklenen herhangi bir paketi doğrudan ana pencereye **Sürükleyip Bırakmanız** yeterlidir. Uygulama, dosyalarınızı almaya hazır olduğunu belirten güzel bir mavi bırakma ekranı gösterecektir.
Alternatif olarak, Linux dosya yöneticinizdeki herhangi bir `.deb`, `.zip`, `.appimage` veya `.fernus` dosyasına sağ tıklayıp **Birlikte Aç > Raf**'ı seçebilirsiniz. Her iki yöntem de yönetici ayrıcalıkları istemeden önce ne kurulacağını gözden geçiren şık bir onay penceresi açacaktır.

### Arama
Kitapları gerçek zamanlı filtrelemek için arama çubuğuna yazın. Arama, 300 ms'lik bir geciktirici (debouncer) kullanır ve siz yazarken karmaşık kullanıcı arayüzü düzenlerini yeniden hesaplarken akıllı tahtanızın asla donmamasını veya kare düşürmemesini sağlar.

### İndirme Kuyruğu
Birden fazla kitapta hızlıca Yükle'ye tıkladığınızda veya **Toplu İşlemler → Seçilenleri Yükle**'yi kullandığınızda kitaplar indirme kuyruğuna eklenir. Aynı anda en fazla **2 indirme** çalışır; geri kalanı `Sırada` durumunu gösterir ve yer açıldıkça otomatik olarak başlar.

### Log Görüntüleyici
Uygulama açıkken herhangi bir zamanda başlık çubuğundaki "Loglar" düğmesine tıklayabilirsiniz. Bu işlem, `dpkg`, `apt` ve `unzip` gibi aktif alt süreçlerden gelen canlı çıktıları (`stdout`/`stderr`) izleyen dinamik, karanlık temalı bir terminal görüntüleyici açar.

---

## Tercihler ve Ayarlar

Başlık çubuğundan **Ayarlar**'ı açın. Değişiklikler, **Kaydet**'e tıklandıktan hemen sonra geçerli olur.

### Görünüm
| Seçenek | Açıklama |
|---|---|
| **Sistem Teması (Otomatik)** | D-Bus üzerinden işletim sisteminin karanlık/aydınlık tercihini izler |
| **Aydınlık Tema** | Aydınlık Libadwaita paletini zorlar |
| **Karanlık Tema** | Karanlık Libadwaita paletini zorlar |

Yeni merkezi motor sayesinde, `QApplication.instance().setStyleSheet(...)` ve `RafMessageBox` yoğun olarak kullanılır, bu da her modülün, pencerenin ve toast bildiriminin renklerinin anında doğru bir şekilde değişmesi anlamına gelir.

### Dil
**Türkçe** ve **İngilizce** arasında seçim yapın. Kullanıcı arayüzü, yeniden başlatma gerektirmeden, özel JSON tabanlı `_meta` i18n gözlemci motoru sayesinde anında güncellenir.

---

## .deb Paketi Oluşturma

### Hızlı Derleme

```bash
./scripts/build_deb.sh
```

Bu betik:
1. Geçici bir `build/raf-pkg/` derleme dizini oluşturur
2. Kaynak dosyalarını dizin hiyerarşisi içerisindeki `usr/lib/raf/` hedefine kopyalar
3. `DEBIAN/control` dosyasını yazar
4. Tüm dosyalar için MD5 sağlama toplamlarını hesaplar → `DEBIAN/md5sums`
5. Yeni paketlenmiş uygulamaların en güncel kataloğu içerdiğinden emin olmak için `database/` dizinini kopyalar.

Çıktı: Proje kök dizininde `raf_<versiyon>_all.deb` oluşturulur.

---

## Geliştirici Modu

### Geliştirici Modunda Başlatma

```bash
# GUI modu
./run_dev.py
```

### Güncellemeyi Simüle Etme

`mock_system/update_mock.json` dosyasını düzenleyin:
```json
{
  "version": "99.0.0",
  "download_url": "https://example.com/raf_99.0.0_all.deb",
  "changelog": "Major update with new features."
}
```

Uygulamayı başlatın — güncelleme iletişim kutusu otomatik olarak görünecektir.

---

## Proje Yapısı

```
raf/
├── src/                          # Uygulama kaynak kodu
│   ├── main.py                   # Giriş noktası — GUI veya CLI yönlendirmesi
│   ├── core/
│   │   ├── database.py           # Kitap veritabanı yükleyicisi (yerel JSON + uzak senk.)
│   │   ├── downloader.py         # DownloadWorker — parçalı HTTP indirme iş parçacığı
│   │   ├── download_queue.py     # DownloadQueue — FIFO kuyruğu, eşzamanlılık kontrolü
│   │   ├── installer.py          # InstallerWorker — deb/zip/flatpak/snap kurulumu
│   │   ├── updater.py            # Güncelleme Kontrolcüsü, Kurucusu ve Otomatik Zamanlayıcı
│   │   ├── sync.py               # DatabaseSyncWorker — uzak books.json çekicisi
│   │   ├── config.py             # Kullanıcı ayarları (~/.config/raf/config.json)
│   │   ├── translation.py        # Özel i18n çeviri motoru
│   │   ├── cli.py                # CLI komut yöneticisi
│   │   └── version.py            # Uygulama versiyon numarası
│   ├── ui/
│   │   ├── main_window.py        # Ana Pencere (MainWindow) + Ayarlar (PreferencesDialog)
│   │   ├── components.py         # BookCard, PublisherBadge araçları
│   │   ├── styles.py             # LIGHT_STYLE, DARK_STYLE QSS stil dosyaları
│   │   ├── toast.py              # ToastNotification, ToastManager bildirim sistemi
│   │   └── logs_dialog.py        # Gerçek zamanlı alt süreç günlükleyici
│   └── assets/
│       ├── raf.png               # Uygulama simgesi
│       └── locales/
│           ├── en.json           # İngilizce metinler + _meta verisi
│           └── tr.json           # Türkçe metinler + _meta verisi
│
├── database/                     # .deb ile paketlenen varsayılan JSON katalogları
├── debian/                       # Debian paketleme konfigürasyonları
├── scripts/
│   ├── build_deb.sh              # Derleme betiği (varsa dpkg-deb kullanır)
│   ├── build_deb.py              # Saf Python .deb oluşturucu (dpkg gerekmez)
│   └── inspect_deb.py            # .deb paket yapısı doğrulayıcı
│
├── tests/                        # Kapsamlı birim ve entegrasyon test takımları
├── mock_system/                  # Geliştirici modu kum havuzu
├── docs/                         # Mimari ve API belgeleri
├── run_dev.py                   # Geliştirici çalıştırıcısı (oto-venv + simülasyon)
├── requirements.txt              # Python bağımlılıkları (PyQt5)
└── README.md                     # Bu dosya
```

---

## Testleri Çalıştırma

### Kullanıcı Arayüzü (UI) Özellik Testleri
```bash
python3 tests/test_ui_features.py
```

### Kendi Kendini Güncelleme Testleri
```bash
python3 tests/test_updater.py
```

### Google Drive İndirme Testleri
```bash
python3 tests/test_drive.py
```

---

## Mimariye Genel Bakış

### İş Parçacığı (Threading) Modeli

Tüm ağ giriş/çıkışları ve paket işlemleri, özel olarak Qt sinyalleri aracılığıyla ana UI iş parçacığıyla iletişim kuran arka plan `QThread` işçilerinde çalışır. `PackageQueryWorker`, `dpkg-query` yoklamasının GUI olay döngülerini duraklatmamasını sağlar.

```
[UI İş Parçacığı (MainWindow)]
        │
        ├── PackageQueryWorker (QThread) ──sinyaller──► db_sync_status
        ├── DownloadWorker (QThread) ──sinyaller──► progress_changed, finished, error
        ├── InstallerWorker (QThread) ──sinyaller──► status_changed, finished, output_received
        ├── UpdateChecker (QThread) ──sinyaller──► update_available, no_update
        ├── DatabaseSyncWorker (QThread) ──sinyaller──► sync_finished, sync_failed
        └── AutoUpdateScheduler (QObject + QTimer) ──sinyaller──► update_toast_requested
```

### Konfigürasyon Depolama

Ayarlar `~/.config/raf/config.json` konumunda depolanır.
Çeviriler, iç içe geçmiş anahtarları ayrıştıran yeni düz anahtarlı özel motoru kullanır (örn. `ui.install_button`).

### Kitap Veritabanı Formatı

`database/books.json` yapısı, standart JSON ayrıştırma sınırlamalarını aşmak için doğal olarak genel yorum (comment) düğümlerini destekler.

```json
{
  "_comment": "Özel metniniz burada",
  "books": [
    {
      "id": "essiz-kitap-id",
      "title": "Kitap Adı",
      "publisher": "Yayıncı Adı",
      "file_name": "paket.deb",
      "file_type": "deb",
      "download_url": "https://..."
    }
  ]
}
```

---

## Lisans ve Teşekkür

Bu proje **GPL-3.0** lisansı altındadır. Tam beyan için [`debian/copyright`](debian/copyright) dosyasına bakınız.

**Geliştirici:** Kaan Ferid Altundaş — kaanferidaltundas@protonmail.com

**Teşekkürler:**
- [Icon-Icons.com](https://icon-icons.com/authors/237-nick-frost-and-greg-lapin) üzerinde Nick Frost ve Greg Lapin tarafından tasarlanan kitaplık simgesi
