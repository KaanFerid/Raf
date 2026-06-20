# Paketleme ve Standardizasyon Dokümantasyonu

KitapMarkt uygulamasının dağıtımı, debian tabanlı işletim sistemlerine (Pardus, Debian, Ubuntu) uygun olarak standart `.deb` paketi biçiminde yapılır.

## 1. Paket Politikası ve Lintian Uyumluluğu

Debian paket denetleyicisi **Lintian** ve genel debian politikaları doğrultusunda pakete aşağıdaki uyumluluk özellikleri eklenmiştir:

- **MD5 Kontrol Toplamı (`md5sums`)**: Paketin içerisindeki tüm dizin dışı dosyaların MD5 değerleri çıkarılarak `control.tar.gz` altındaki `md5sums` dosyasına kaydedilir. Bu, kurulum esnasında dosyaların bütünlüğünü doğrulamaya yarar.
- **Telif ve Lisans Bilgisi (`copyright`)**: Debian standartlarına göre, her paketin telif hakkı ve lisans bilgileri `usr/share/doc/<paket-adi>/copyright` dosyasında yer almalıdır. Uygulama derlenirken bu dosya `0o644` izinleriyle pakete dahil edilir.

## 2. Derleme Kanalları

Paket derlemesi iki farklı kanal üzerinden yapılabilmektedir:

### Standart Kanal (`build_deb.sh`)
Eğer sisteminizde `dpkg-deb` aracı kuruluysa, bu script:
1. `build/kitapmarkt-pkg` geçici dizinini oluşturur.
2. Kaynak kodları ve dosyaları bu geçici dizine kopyalar.
3. MD5 toplamlarını otomatik hesaplayarak `DEBIAN/md5sums` dosyasını oluşturur.
4. Dosya ve dizin izinlerini (`755` ve `644`) ayarlar.
5. `dpkg-deb --build` komutuyla paketi derler.

### Saf Python Kanalı (`build_deb.py`)
Geliştirici sistemlerinde (örn. Arch Linux veya Windows geliştirme ortamlarında) `dpkg` paketleme araçları yoksa devreye giren bu script:
1. `tarfile` modülü ile `control.tar.gz` ve `data.tar.gz` arşivlerini bellek üzerinde oluşturur.
2. Dosyaları kopyalarken MD5 özetlerini dinamik hesaplar.
3. `ar` arşiv formatının header yapılarını ikili formatta oluşturarak saf Python ile standart `.deb` paketi yazar.
