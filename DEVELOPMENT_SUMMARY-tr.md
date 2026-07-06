# Raf — Geliştirme Özeti

[![English](https://img.shields.io/badge/Language-English-blue?style=flat-square)](DEVELOPMENT_SUMMARY.md)

Bu belge, tamamlanan her geliştirme aşamasının kronolojik bir dökümünü, temel tasarım kararlarının arkasındaki mantığı ve uygulamanın yeteneklerinin tam bir referansını sunar. Projenin nasıl geliştiğini anlaması gereken sürdürücüler ve katkıda bulunanlar için tasarlanmıştır.

---

## 👥 Proje Bilgileri

| Alan | Değer |
|---|---|
| **Geliştirici** | Kaan Ferid Altundaş |
| **İletişim** | kaanferidaltundas@protonmail.com |
| **Lisans** | GPL-3.0 (bkz. `debian/copyright`) |
| **Hedef Platform** | Pardus ETAP Akıllı Tahtalar (Debian tabanlı) |
| **Dil** | Python 3.9+ |
| **GUI Çerçevesi** | PySide6 / PyQt6 / PyQt5 (otomatik algılama) |

---

## 🛠️ Aşama Aşama Geliştirme Geçmişi

### Aşama 1 — Proje Temeli ve Mimari

**Hedef:** Sıfırdan temiz, sürdürülebilir bir proje yapısı oluşturmak.

- Proje standart bir açık kaynak Python düzenine göre yeniden düzenlendi:
  - `src/core/` — kullanıcı arayüzünden (UI) tamamen ayrılmış iş mantığı (business logic)
  - `src/ui/` — tüm Qt araçları ve stil dosyaları
  - `src/assets/` — kitap veritabanı ve simge varlıkları
  - `debian/` — Debian paketleme konfigürasyonu
  - `docs/` — teknik dokümantasyon
  - `scripts/` — paketleme ve yardımcı araç otomasyonu
  - `tests/` — otomatik test takımı
  - `mock_system/` — korumalı (sandboxed) geliştirici ortamı
- PyQt6 geriye dönük uyumluluğu için `enum` düzeltmeleri dahil olmak üzere PySide6, PyQt6 ve PyQt5 üzerinde tek bir birleşik içe aktarma arayüzü sağlamak amacıyla `qt_compat.py` oluşturuldu.
- `books.json` dosyasını yüklemek ve sunmak için ilk `Database` sınıfı yazıldı.
- `progress_changed`, `finished` ve `error` sinyalleri ile `DownloadWorker` (QThread) oluşturuldu.

---

### Aşama 2 — GUI Tasarımı: Libadwaita / Adwaita Stili

**Hedef:** Pardus/GNOME masaüstü standartlarına uygun görsel olarak modern bir arayüz oluşturmak.

- GTK Libadwaita'nın düz, yuvarlatılmış köşeli estetiğini taklit eden tam `LIGHT_STYLE` ve `DARK_STYLE` QSS stil sayfaları `styles.py` içinde tasarlandı ve uygulandı.
- `BookCard` widget'ı şu öğeleri içeren yatay bir satır düzeniyle oluşturuldu:
  - `PublisherBadge` — yayıncı adının ilk harfine dayalı deterministik bir palet kullanan, özel `QPainter` ile çizilmiş renkli baş harf avatarı.
  - İlerleme çubuğu (indirme başlayana kadar gizli).
  - Hız ve durum etiketleri.
  - CSS hedeflemesi için dinamik `class` özelliği geçişli birincil ve ikincil eylem düğmeleri.
- Ortalanmış arama, solda marka logosu, sağda görünüm değiştirme sekmeleri (Market / Kütüphanem), Ayarlar ve Hakkında düğmeleri içeren başlık çubuğu oluşturuldu.
- Tema seçici radyo düğmeleri ve dil açılır kutusu içeren `PreferencesDialog` (Ayarlar İletişim Kutusu) uygulandı.
- Pencere yöneticisinin başlık çubuğu dekorasyonunu seçilen temayla eşitlemek için `xprop` kullanan `set_linux_dark_titlebar()` eklendi.

---

### Aşama 3 — İndirme Motoru ve Akıllı Tahta Entegrasyonu

**Hedef:** İndirmeleri akıllı tahta ağ koşullarında güvenilir hale getirmek.

- 8 KB parçalı (chunk) HTTP akış indirmesi uygulandı.
- **Google Drive virüs uyarısı atlatma** eklendi: Yanıtın bir HTML onay sayfası olduğunu (ilk 2 KB içinde `<form` bulunmasıyla) algılar, `id`, `confirm` ve `uuid` token'larını düzenli ifadelerle (regex) çıkarır ve `drive.usercontent.google.com/download` adresine doğru POST isteğini yeniden gönderir.
- **HTTP Range (Aralık) devam ettirme** eklendi: Kısmi indirmeden sonra bağlantı koparsa, indirmeyi `Range: bytes=<alınan_bayt>-` başlığı ile yeniden dener; hata vermeden önce en fazla 3 otomatik deneme yapar.
- **Ekran klavyesi (OSK) tetikleyicisi** entegre edildi: Arama `QLineEdit`'indeki bir `eventFilter`, odaklanma (focus) olaylarını algılar ve dokunmatik ortamlar için `onboard` (veya `florence`) klavyesini başlatır.
- Başlık çubuğu indirme ilerlemesi için `DownloadWorker` sınıfına `last_percent` özniteliği eklendi.
- Şu işlemleri kapsayan `InstallerWorker` QThread oluşturuldu:
  - `pkexec apt-get install -y ./file.deb` üzerinden `.deb` paketleri.
  - `.zip`/`.fernus` paketleri: `~/.local/share/raf/apps/<id>/` konumuna çıkartır ve `.desktop` başlatıcı oluşturur.
  - Geliştirici modunda simüle edilmiş yükleme/kaldırma (1,5 sn / 1 sn yapay gecikmeler).
- İş parçacığının zarif (graceful) bir şekilde sonlandırılması ile `cancel_download()` uygulandı.

---

### Aşama 4 — Debian Paketi ve Kendi Kendini Güncelleme

**Hedef:** Raf'ı kendi kendini güncelleme mekanizmasına sahip Lintian uyumlu bir `.deb` paketi olarak dağıtmak.

- `scripts/build_deb.sh` oluşturuldu — `dpkg-deb` kullanan standart derleme yolu.
- `scripts/build_deb.py` oluşturuldu — Sistem araçlarına ihtiyaç duymadan, yalnızca `tarfile`, `hashlib` ve `struct` kullanarak `ar` arşiv formatını (doğru `control.tar.gz` ve `data.tar.gz` ile birlikte) tamamen Python'da oluşturan `.deb` derleyici.
- Lintian uyumluluğu sağlandı:
  - `DEBIAN/md5sums` — Paketlenmiş tüm veri dosyalarının MD5 sağlama toplamları.
  - `usr/share/doc/raf/copyright` — Katı `0o644` izinleriyle GPL-3.0 beyanı.
  - Dosya izni yaptırımları (dizinler `0755`, dosyalar `0644`, çalıştırılabilir dosyalar `0755`).
- `UpdateChecker` (QThread) oluşturuldu — GitHub'dan `update.json` dosyasını çeker, sürüm numaralarını karşılaştırır ve `update_available(versiyon, url, değişiklik_notları)` sinyalini yayar.
- `UpdateInstaller` (QThread) oluşturuldu — Güncelleme `.deb` dosyasını indirir ve `pkexec apt-get install --reinstall -y` ile kurar.
- Güncelleme akışı, değişiklik notlarını zengin metin (rich-text) biçiminde sunan bir onay iletişim kutusu gösteren `MainWindow.on_update_available()` fonksiyonuna bağlandı.

---

### Aşama 5 — CLI Paneli

**Hedef:** Sistem yöneticileri için başsız (headless) / terminal kullanımını etkinleştirmek.

- Altı komutu ( `list`, `list-installed`, `search`, `install`, `uninstall`, `clean`) işleyen `src/core/cli.py` oluşturuldu.
- `src/main.py`, herhangi bir argüman mevcut olduğunda CLI moduna yönlendirecek şekilde değiştirildi.
- CLI, `DownloadWorker` ve `InstallerWorker` sınıflarını doğrudan yeniden kullanmak için başsız bir Qt bağlamı (`QT_QPA_PLATFORM=offscreen`) kullanır.
- Kullanım özeti için `--help` / `-h` / `help` argümanı eklendi.
- İndirmeler sırasında terminalde gerçek zamanlı bir ASCII ilerleme çubuğu uygulandı.
- Tüm CLI dizeleri, GUI ile aynı `tr()` sistemi üzerinden tamamen yerelleştirildi (lokalize edildi).

---

### Aşama 6 — Arayüz Cilalama ve Tema Düzeltmeleri

**Hedef:** Görsel regresyonları (bozulmaları) düzeltmek ve kullanıcı deneyimini iyileştirmek.

- PyQt5 karanlık tema uyumluluğu düzeltildi — `DARK_STYLE` QSS artık her üç Qt arka ucunda (backend) da aynı şekilde çalışıyor.
- `PreferencesDialog` içindeki tema seçimi daireleri düzeltildi — Güvenilir çapraz arka uç (cross-backend) oluşturma (rendering) için saf CSS daireleri yerine QSS'de `QRadioButton` özel `indicator` kuralları getirildi.
- Karanlık modda dil seçicideki beyaz çubuklar düzeltildi — `DARK_STYLE` içinde `QComboBox` açılır `QListView` arka planı yamandı.
- `PreferencesDialog` penceresinin her zaman ana pencerenin aktif stil sayfasını (stylesheet) miras alması sağlandı.
- Metin kırpılmasını önlemek için `PreferencesDialog` düğmeleri `retranslate_ui()` üzerinde `adjustSize()` ile dinamik olarak boyutlandırıldı.
- Kullanılmayan yerel dil anahtarları (locale keys) kaldırıldı (`primary_keywords`, `middle_keywords`, `high_keywords` ve kategoriyle ilgili tüm dizeler dahil olmak üzere yaklaşık 15 yetim anahtar temizlendi).
- `translation.py` dosyasında kullanımdan kaldırılmış (deprecated) `locale.getdefaultlocale()`, `locale.getlocale()` ile değiştirildi.
- Tüm çekirdek modüllerdeki tüm yalın (bare) `except:` ifadeleri `except Exception:` ile değiştirildi.

---

### Aşama 7 — Büyük Özellik Genişletmesi

**Hedef:** Uygulamayı zengin özelliklere sahip tam bir v1.x ürününe dönüştürmek.

Yedi yeni özellik tasarlandı, uygulandı ve entegre edildi:

#### 7.1 İndirme Kuyruğu (`src/core/download_queue.py`)

- `DownloadQueue` — Yapılandırılabilir maksimum eşzamanlılığa (varsayılan: 2) sahip `QObject` tabanlı bir FIFO (ilk giren ilk çıkar) kuyruğu.
- Aynı kitabın birden fazla kez kuyruğa eklenmesini engeller (`book_id` ile kontrol edilir).
- `job_started`, `job_finished`, `queue_changed` sinyallerini yayar.
- `MainWindow`, başlık çubuğu rozetini güncellemek için `queue_changed` sinyaline yanıt verir.
- Kuyruğa alınmış (henüz indirilmeyen) bir karttaki İptal düğmesine tıklamak `DownloadQueue.dequeue()` öğesini çağırır — indirme başlatılmadan anında kaldırma.

#### 7.2 Toast Bildirimleri ve Uyarılar (`src/ui/toast.py`, `src/ui/dialogs.py`)

- `ToastNotification` — `QPropertyAnimation` ile yavaşça beliren (fade-in) çerçevesiz bir bindirme (overlay) `QWidget`.
- `ToastManager` — Aktif bildirimleri sağ alt köşede istifler, kapatıldıklarında ve pencere yeniden boyutlandırıldığında konumlarını günceller.
- Farklı renklere sahip dört tür: `info` (mavi), `success` (yeşil), `warning` (kehribar), `error` (kırmızı).
- Bildirimlerin gösterildiği durumlar: kurulum başarılı/hata, kaldırma başarılı/hata, indirme hatası, güncelleme mevcut, veritabanı senkronizasyonu başarılı.
- **Kurulum Öncesi Onayı:** `pkexec` aracılığıyla ayrıcalıkları yükseltmeden önce kullanıcılardan onay isteyen araya giren (intercepting) bir modal (zorunlu) istem eklendi. Bu istem, bir indirme tamamlandıktan hemen sonra ancak `start_installation` yürütülmeden önce görünür ve yanlışlıkla çıkabilecek kök (root) kimlik doğrulama isteklerini önler.

#### 7.3 Başlık Çubuğu İlerlemesi

- `MainWindow._update_title_progress()` her `progress_changed` sinyalinde ve indirme bitiminde/hatasında çağrılır.
- Tek indirme: `[▼ Ankara Kitabı — %67] Raf`
- Çoklu indirmeler: `[▼ 3 indirme — ort %45] Raf`
- Hiçbir aktif indirme kalmadığında başlık `Raf` olarak sıfırlanır.

#### 7.4 Toplu İşlemler

- Başlık çubuğunda **Seçim modu** geçiş düğmesi (`SelectModeBtn`).
- `BookCard.set_selection_mode(active)` bir `☐`/`☑` onay kutusu düğmesini gösterir/gizler.
- `BookCard.selection_changed` sinyali `(kitap_id, secili_mi)` bilgisini `MainWindow`'a iletir.
- Durum çubuğunun üstünde toplu işlem çubuğu görünür: seçili öğe sayısı etiketi, Seçilenleri Kur düğmesi, Seçilenleri Kaldır düğmesi ve ✕ çıkış düğmesi.
- `install_selected()` — İndirme kuyruğu aracılığıyla seçilen ancak kurulmamış tüm kitapları kuyruğa ekler.
- `uninstall_selected()` — Bir onay iletişim kutusu gösterir ve ardından seçilen her kartta `uninstall_requested` sinyalini tetikler.

#### 7.5 Uzak Veritabanı Senkronizasyonu (`src/core/sync.py`)

- `DatabaseSyncWorker` — Başlangıçta uzak bir `books.json` URL'sini çeken QThread.
- Yerel önbelleğe yazmadan önce JSON yapısını doğrular.
- `_on_sync_finished()`, `Database` sınıfını yeniden yükler ve kitap ızgarasını (grid) yeniler.
- Başarısızlıkta tamamen sessizdir — yerel önbellek her zaman yedek olarak kullanılır.
- URL, `PreferencesDialog` (Ayarlar) içinde "Kitap Veritabanı URL'si" altında yapılandırılır.

#### 7.6 Flatpak ve Snap Desteği (`src/core/installer.py`)

- `InstallerWorker` artık iki yeni `file_type` (dosya türü) değerini işliyor:
  - `"flatpak"` → `flatpak install --user --noninteractive <flatpak_ref>`
  - `"snap"` → `pkexec snap install <snap_adi>`
- Kaldırma yolları: `flatpak uninstall --user`, `pkexec snap remove`
- Tespit yardımcıları: `get_all_installed_flatpaks()`, `get_all_installed_snaps()`
- Erişilebilirlik kontrolleri: `flatpak`/`snap` binary dosyası PATH ortam değişkeninde değilse, yerelleştirilmiş bir hata mesajı yayar.
- `is_book_installed()`, dosya türüne (`file_type`) göre uygun tespit ediciye (detector) yönlendirir.
- Tüm Flatpak/Snap durum mesajları için yerel dizeler eklendi (İngilizce + Türkçe).

#### 7.7 Otomatik Güncelleme Zamanlayıcı (`src/core/updater.py`)

- `AutoUpdateScheduler`, 6 saatlik aralıklarla bir `QTimer` içinde çalışır.
- `config.json` içinde `"auto_update_policy"` altında saklanan üç kullanıcı tarafından yapılandırılabilir politika:
  - `"off"` (Kapalı) — Arka planda hiçbir kontrol yapılmaz.
  - `"check"` (Kontrol Et) — 24 saatte en fazla bir kez kontrol eder; güncelleme bulunursa bir toast bildirimi gösterir.
  - `"auto"` (Otomatik) — 24 saatte en fazla bir kez kontrol eder; güncelleme bulunursa kurulumu sessizce tetikler.
- Yapılandırmada saklanan `last_update_check` (son güncelleme kontrolü) zaman damgası, gereksiz ağ isteklerini önler.
- Politika, `PreferencesDialog` (Ayarlar) içinde "Otomatik Güncellemeler" altında yapılandırılabilir.

---

### Aşama 8 — Tam Yerelleştirme ve UX (Kullanıcı Deneyimi) Cilalama

**Hedef:** Tüm kullanıcıya dönük dizelerin %100 çevrilebilir olduğundan emin olmak ve kalıcı iletişim kutusu (modal) hatalarını düzeltmek.

- Kod içine gömülü (hardcoded) dizeleri `tr(...)` ile değiştirmek için tüm kaynak dosyaların kapsamlı bir taraması tamamlandı.
- Arka plan bash komut dosyasının doğru UI dilinde rapor vermesi için kurulum günlüğü izleri (`installer.py`) tamamen yerelleştirildi.
- Bağımsız simgeler ve biçimlendirme yer tutucuları uygun olduğunda yerelleştirilebilir bloklara sarıldı.
- Zorunlu `AboutDialog` (Hakkında) içindeki "Günlükler"e tıklamanın arka planda tıklanamaz bir `LogsDialog` oluşturduğu bir etkileşim engelleyici hata düzeltildi (Hakkında penceresi artık önce kapatılıyor).
- Bağımlılıklar eksikse otomatik olarak bir PyQt5 sanal ortamı sağlayan birleşik bir `run_dev.py` oluşturmak için `run_arch.py` ve `run_dev.py` birleştirildi.

---

## 📁 Eksiksiz Dosya Envanteri

### Kaynak Dosyalar

| Dosya | Görev |
|---|---|
| `src/main.py` | Giriş noktası — GUI veya CLI yönlendirmesi |
| `src/qt_compat.py` | Qt arka uç soyutlama katmanı |
| `src/core/database.py` | JSON kitap kataloğu yükleyici |
| `src/core/downloader.py` | HTTP indirme QThread'i |
| `src/core/download_queue.py` | Eşzamanlılık kontrollü FIFO indirme kuyruğu |
| `src/core/installer.py` | deb/zip/flatpak/snap için paket kurma/kaldırma |
| `src/core/updater.py` | Güncelleme denetleyicisi, kurucu, otomatik güncelleme zamanlayıcı |
| `src/core/sync.py` | Uzak veritabanı senkronizasyon çalışanı |
| `src/core/config.py` | Konfigürasyon kalıcılığı |
| `src/core/translation.py` | Çalışma zamanı i18n motoru |
| `src/core/cli.py` | CLI komut işleyici |
| `src/core/version.py` | Uygulama versiyon sabiti |
| `src/ui/main_window.py` | Ana Pencere + Tercihler (Ayarlar) |
| `src/ui/components.py` | BookCard (Kitap Kartı) + PublisherBadge (Yayıncı Rozeti) |
| `src/ui/styles.py` | LIGHT_STYLE (Aydınlık) ve DARK_STYLE (Karanlık) QSS |
| `src/ui/toast.py` | Toast bildirim bindirme sistemi |
| `src/assets/books.json` | Yerleşik kitap veritabanı |
| `src/assets/raf.png` | Uygulama simgesi |
| `src/assets/locales/en.json` | İngilizce dil dizeleri |
| `src/assets/locales/tr.json` | Türkçe dil dizeleri |

### Derleme ve Paketleme

| Dosya | Görev |
|---|---|
| `scripts/build_deb.sh` | `dpkg-deb` kullanan kabuk (shell) derleme betiği |
| `scripts/build_deb.py` | Saf Python `.deb` oluşturucu (sistem aracı gerektirmez) |
| `scripts/inspect_deb.py` | Paket yapısı doğrulayıcı |
| `debian/control` | Paket meta verisi |
| `debian/changelog` | Versiyon geçmişi |
| `debian/copyright` | GPL-3.0 lisans beyanı |
| `debian/rules` | Debhelper derleme kuralları |
| `debian/compat` | Debhelper uyumluluk seviyesi |
| `MANIFEST.in` | setuptools manifest dahil etmeleri |
| `setup.py` | Python paketleme konfigürasyonu |
| `requirements.txt` | Python bağımlılık listesi |

### Geliştirici Araçları

| Dosya | Görev |
|---|---|
| `run_dev.py` | Geliştirici çalıştırıcı: oto-venv + simülasyon modu |
| `mock_system/` | Korumalı yükleme/indirme ortamı |

### Testler

| Dosya | Neyi test eder |
|---|---|
| `tests/test_ui_features.py` | Widget oluşturma, arama, durum güncellemeleri |
| `tests/test_updater.py` | Güncelleme kontrol akışı |
| `tests/test_drive.py` | Google Drive indirme uyarı atlatması |

---

## 🚀 Hızlı Başvuru — Çalıştırma ve Derleme

### GUI'yi Başlat (Geliştirici Modu)
```bash
./run_dev.py
```

### GUI'yi Başlat (Üretim Modu)
```bash
python3 -m src.main
# veya kurulu ise:
raf
```

### CLI Komutları
```bash
raf list
raf list-installed
raf search <terim>
raf install <kitap_id>
raf uninstall <kitap_id>
raf clean
raf --help
```

### .deb Paketi Derleme
```bash
./scripts/build_deb.sh         # Standart (dpkg-deb gerektirir)
python3 scripts/build_deb.py   # Saf Python (dpkg gerekmez)
python3 scripts/inspect_deb.py # Derlenen paketi doğrula
```

### Testleri Çalıştırma
```bash
python3 tests/test_ui_features.py
python3 tests/test_updater.py
python3 tests/test_drive.py
```

---

## 🔧 Temel Tasarım Kararları

### Neden `asyncio` yerine `QThread` çalışanları (workers)?

Qt'nin kendi iş parçacığı modeli, sinyal/yuva (signal/slot) sistemi ile temiz bir şekilde bütünleşir. `asyncio`, bir olay döngüsü köprüsü (`qasync`) gerektirir ve zaten Qt'ye bağlı olan bir proje için karmaşıklık katar. `QThread` + sinyaller basit, iyi anlaşılan bir kalıp sunar.

### Neden üç Qt arka ucu?

Pardus ETAP tahtaları, Debian depolarında `python3-pyqt5` ile birlikte gönderilir. Geliştirici makineleri genellikle `PySide6` tercih eder. Tüm üçünü `qt_compat.py` aracılığıyla desteklemek, aynı kod tabanının değişiklik yapılmadan her yerde çalışmasını sağlar.

### Neden SQLite yerine yerel JSON veritabanı?

Kitap kataloğu küçüktür (< 100 girdi), çalışma zamanında salt okunurdur (read-only) ve bir şema taşıma (migration) sistemi olmadan `.deb` içine dahil edilmesi gerekir. JSON'u düzenlemek, farklılıkları (diff) bulmak ve dağıtmak daha basittir. Uzak senkronizasyon özelliği, çevrimiçi bir sorgu API'sine olan ihtiyacı ortadan kaldırır.

### Neden `sudo` yerine `pkexec`?

`pkexec`, modern GNOME/Pardus masaüstlerinde ayrıcalık yükseltme (privilege escalation) için PolicyKit standardıdır. Terminal parola istemi yerine işletim sistemi kimlik doğrulama iletişim kutusunu sunar, bu da akıllı tahta kullanıcı deneyimiyle tutarlıdır.

### Neden saf Python `.deb` oluşturucu?

ETAP geliştiricileri genellikle `dpkg-deb` uygulamasının bulunmadığı Arch Linux veya macOS üzerinde çalışır. Saf Python oluşturucu, Debian sistem araçları yüklenmeden projenin herhangi bir yerde derlenmesine olanak tanır.
