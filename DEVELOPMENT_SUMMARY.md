# Etkileşimli Kitap Dükkanı - Geliştirme Özeti

Bu belgede, Pardus tabanlı akıllı tahtalar (ETAP) için geliştirilmiş modern kullanıcı arayüzüne sahip **Etkileşimli Kitap Dükkanı** (eski adıyla KitapMarkt) projesinde tamamlanan tüm aşamalar, eklenen özellikler, mimari yapı ve doğrulama yöntemleri özetlenmiştir.

---

## 👥 Geliştirme Ekibi ve Haklar
* **Geliştirici:** Kaan Ferid Altundaş
* **Lisans:** GPL-3.0 (Detaylar için `debian/copyright` dosyasına bakınız)

---

## 🛠️ Tamamlanan Geliştirme Aşamaları ve Özellikler

### 1. Dosya ve Git Deposu Yapısı
* Proje dizin yapısı tamamen modüler ve temiz bir hale getirilmiştir:
  * `src/core/`: İş mantığı, ağ, güncelleme, indirme ve kurulum işlemleri.
  * `src/ui/`: Kullanıcı arayüzü, Adwaita temaları ve özel arayüz bileşenleri.
  * `src/assets/`: Kitap veritabanı (`books.json`) ve logo/ikon dosyaları.
  * `debian/`: Debian standardizasyon dosyaları (control, copyright, changelog, rules).
  * `docs/`: Mimari ve paketleme detaylarını içeren genişletilmiş kılavuzlar.

### 2. Arayüz Tasarımı & Libadwaita Uyumluluğu
* **Adwaita & Bottles Stili Tasarım:** Modern, göz yormayan, yuvarlatılmış köşeler ve flat tasarım prensiplerine uygun arayüz.
* **Tema Motoru:** Açık (`LIGHT_STYLE`) ve Koyu (`DARK_STYLE`) tema seçenekleri.
* **D-Bus Entegrasyonu:** Sistem teması değiştiğinde (örneğin akıllı tahta koyu moda geçtiğinde) bunu D-Bus portal üzerinden dinleyerek otomatik tema geçişi sağlayan mekanizma.
* **Tercihler Penceresi:** Kullanıcının manuel tema seçmesini veya sistem teması ile senkronize olmasını sağlayan ayarlar penceresi.
* **Özel Publisher Badge Tasarımı:** Şatafatlı logolar yerine yayınevi isimlerinin baş harflerinden oluşan şık, renkli Adwaita avatarları.

### 3. Arama Butonu ve Sembol İyileştirmesi
* **Dinamik Çizilen Arama İkonu:** Unicode arama sembollerinin (`🔍` veya `🔎`) Pardus gibi sistemlerde emoji fontlarının eksik olmasından dolayı kare/bozuk görünmesini engellemek için, `QPainter` ile piksel kalitesinde dynamically çizilen modern bir büyüteç ikonu arama kutusuna eklenmiştir.
* **Klavye Butonu:** Sanal klavye açma butonunun sembolü (`⌨`) yerine arayüzle uyumlu `"Klavye"` metin butonu kullanılarak görsel bütünlük sağlanmıştır.

### 4. Akıllı Tahta Entegrasyonu (Aşama 1)
* **Dokunmatik Ekran Sanal Klavye Tetikleyicisi:** Öğretmenlerin dokunmatik ekranda arama alanına tıkladığında (FocusIn veya MouseButtonPress olayları) sistem sanal klavyesinin (Onboard veya GNOME Caribou) otomatik olarak ekranda belirmesini sağlayan olay filtreleyici (`eventFilter`).
* **Resumption (Kaldığı Yerden İndirme):** Sınıflardaki internet kesintilerine karşı, HTTP `Range` başlığını kullanarak indirmeyi kaldığı yerden başlatan (resumption) ve bağlantı kopmalarında otomatik yeniden deneme (retry) yapan asenkron indirme motoru.

### 5. Debian Paket Standardizasyonu ve Kendi Kendini Güncelleme (Aşama 2)
* **Saf Python Debian Derleyici (`build_deb.py`):** `dpkg-deb` paketleme aracı kurulu olmayan sistemlerde bile `ar` ve `tar` formatlarını kullanarak standartlara uygun `.deb` dosyası oluşturan derleyici.
* **Lintian Uyumlaştırması:**
  * Paketteki dosyaların MD5 özetlerinin çıkarılması ve `md5sums` dosyasına kaydedilmesi.
  * Lisans ve Telif haklarının `usr/share/doc/kitapmarkt/copyright` dosyasına `644` izinleriyle yazılması.
* **Uygulama İçi Güncelleme Yöneticisi (Self-Updater):** Yeni sürümleri asenkron kontrol eden, indiren ve `pkexec apt-get install` aracılığıyla yetki yükselterek arka planda kuran mekanizma.
* **Google Drive Virüs Uyarısı Bypassı:** İndirme linklerinde çıkan virüs taraması uyarı sayfalarını otomatik olarak algılayıp bypass eden algoritma.

### 6. Zengin Özellikler & Okul Ortamı Uyumluluğu (Aşama 3)
* **Kategori Filtreleme:** Kitapları İlkokul, Ortaokul, Lise ve Genel olarak sınıflandıran ve arayüzde hap (pill) butonlar olarak gösteren filtreleme çubuğu.
* **Çevrimdışı (Offline) Mod Tespiti:** İnternet bağlantısı koptuğunda arayüzde kırmızı bir `ÇEVRİMDIŞI MOD` uyarısı gösterilir ve indirilmemiş kitapların "Yükle" butonları pasifleştirilerek hata almalar engellenir.
* **Disk Boş Alan Hesaplaması:** Ayarlar penceresinde kurulum dizinindeki boş disk alanının hesaplanarak gösterilmesi.
* **Önbellek Temizleme:** İndirilen `.deb` dosyalarının kapladığı alanı temizleme butonu.

### 7. Uzaktan Yönetim ve CLI Paneli (Aşama 4)
* Uzaktan yönetim için `main.py` dosyasına komut satırı argümanları eklenmiş ve `src/core/cli.py` geliştirilmiştir.
* **Mevcut CLI Komutları:**
  * `./run_arch.py list` -> Tüm kitapları kategorileriyle listeler.
  * `./run_arch.py list-installed` -> Kurulmuş kitap paketlerini gösterir.
  * `./run_arch.py search <terim>` -> Veritabanında kitap araması yapar.
  * `./run_arch.py install <kitap_id>` -> Belirtilen kitabı indirir ve kurar (konsol barı gösterilir).
  * `./run_arch.py uninstall <kitap_id>` -> Kitabı sistemden kaldırır.
  * `./run_arch.py clean` -> İndirme önbelleğini temizler.

---

## 🚀 Çalıştırma ve Test Yöntemleri

### 1. Geliştirici Modunda Çalıştırma (Arch Linux veya test bilgisayarı)
Sisteminizde global paket kurmadan ve root yetkisi gerektirmeden izole ortamda uygulamayı test etmek için:
```bash
./run_arch.py
```

### 2. Normal Modda Çalıştırma (Pardus / Debian Akıllı Tahta)
```bash
python3 -m src.main
```

### 3. Paket Derleme (.deb)
```bash
./build_deb.sh
```

### 4. Otomatik Testleri Çalıştırma
* **UI ve Kategori Testi:**
  ```bash
  python3 scratch/test_ui_features.py
  ```
* **Otomatik Güncelleyici Testi:**
  ```bash
  python3 scratch/test_updater.py
  ```
* **Google Drive Ağ ve Range Testi:**
  ```bash
  python3 scratch/test_drive.py
  ```
* **Oluşturulan Debian Paketinin Yapısal Doğrulanması:**
  ```bash
  python3 scratch/inspect_deb.py
  ```

---

*Bu proje, akıllı tahta donanımları ile tam uyumlu olup en yüksek kararlılık ve performans hedeflenerek tasarlanmıştır.*
