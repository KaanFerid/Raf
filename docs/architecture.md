# Mimari Dokümantasyon

KitapMarkt uygulaması, akıllı tahta performansını ve kullanıcı deneyimini optimize etmek amacıyla asenkron çalışan modüler bir mimariye sahiptir.

## 1. Katmanlı Yapı

Uygulama iki temel katmandan oluşur:

### A. İş Mantığı Katmanı (Core)
- **`database.py`**: Yerel JSON tabanlı kitap veritabanını (`books.json`) yönetir, arama ve filtreleme sorgularına yanıt verir.
- **`downloader.py`**: `QThread` tabanlı çalışan `DownloadWorker` sınıfını barındırır. Google Drive virüs uyarısı bypass algoritması, `Range` başlığı ile indirmeyi kaldığı yerden devam ettirme (resumption) ve otomatik yeniden deneme (retry) mekanizmalarına sahiptir.
- **`installer.py`**: İndirilen kitapları paket türüne göre (.deb, .zip, .fernus) kurar. Yetki gerektiren durumlarda `pkexec` kullanır, masaüstü kısayollarını (`.desktop`) kullanıcı dizinine otomatik oluşturur.
- **`updater.py`**: Uygulamanın kendi kendini güncelleyebilmesini sağlar. Geliştirici modunda `update_mock.json` üzerinden, üretim modunda ise uzak sunucudan güncelleme kontrolü yapar.
- **`config.py`**: Kullanıcı tercihlerini (tema seçimi vb.) kalıcı olarak saklar.

### B. Kullanıcı Arayüzü Katmanı (UI)
- **`main_window.py`**: Ana pencereyi, görünüm değiştiricileri (`Market` ve `Kütüphanem`), arama/filtreleme çubuklarını ve hamburger menüyü yönetir.
- **`components.py`**: Adwaita/Bottles stilini taşıyan `PublisherBadge` ve tek sütunlu liste satırı tasarımlarını (`BookRow`) içerir.
- **`styles.py`**: QSS (Qt Style Sheets) kullanarak Açık ve Koyu modern GTK/Adwaita temalarını sunar.

## 2. Asenkron İletişim & Sinyal Mekanizması

Arayüzün donmasını engellemek için tüm ağ ve IO işlemleri Qt'nin `QThread` yapısı ve sinyaller (`Signal`) aracılığıyla gerçekleştirilir:

```
[Main Window (UI Thread)]  <-- Signals --  [DownloadWorker (QThread)]
         |                                           |
         |-- Start / Cancel ------------------------>|
         |                                           |--> requests.Session (chunked download)
```
- **`progress_changed`**: İndirme yüzdesini ve güncel hızı raporlar.
- **`finished`**: İndirme tamamlandığında hedef dosya yolunu döner.
- **`error`**: Hata durumunda arayüze açıklama iletir.
