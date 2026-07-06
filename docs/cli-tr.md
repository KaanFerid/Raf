# CLI Referansı

[![English](https://img.shields.io/badge/Language-English-blue?style=flat-square)](cli.md)

Raf komut satırı arayüzü (CLI) için eksiksiz referans. CLI tüm mantığı GUI ile paylaşır — aynı kurucu, indirici ve veritabanı modülleri kullanılır.

---

## Çağırma

```bash
# .deb üzerinden kurulduysa:
raf <komut> [argümanlar]

# Kaynaktan (geliştirici modu — sistem değişiklikleri yapılmaz):
./run_dev.py <komut> [argümanlar]

# Kaynaktan (üretim modu):
python3 -m src.main <komut> [argümanlar]
```

---

## Genel Seçenekler

| Bayrak | Açıklama |
|---|---|
| `--help`, `-h`, `help` | Komut özetini yazdırır ve çıkar |

---

## Komutlar

---

### `list` — Mevcut tüm kitapları listele

**Kullanım:**
```bash
raf list
```

**Açıklama:**
Veritabanındaki tüm kitapları biçimlendirilmiş bir tablo olarak yazdırır. Sütunlar sabit genişliklere hizalanmıştır.

**Çıktı:**
```
Total 42 books available:
ID                                  | Title                                         | Publisher
--------------------------------------------------------------------------------------------------------------
akademikbasariyayinlarikutuphane    | Akademik Başarı Yayınları Kütüphanesi         | Akademik Başarı Yay.
ankarakutuphane                     | Ankara İl Milli Eğitim Kütüphanesi            | Ankara İl MEM
...
```

**Çıkış kodu:** `0`

---

### `list-installed` — Kurulu kitapları listele

**Kullanım:**
```bash
raf list-installed
```

**Açıklama:**
Tüm kurulu kitaplar için sistemi sorgular ve yalnızca mevcut olanları gösterir. `.deb` paketleri için `dpkg-query`, Flatpak için `flatpak list` ve Snap için `snap list` kullanır.

**Çıktı:**
```
Total 3 installed books available:
ID                                  | Title                                         | Type
--------------------------------------------------------------------------------------------------------------
ankarakutuphane                     | Ankara İl Milli Eğitim Kütüphanesi            | deb
```

**Çıkış kodu:** `0`

---

### `search <terim>` — Kitapları ara

**Kullanım:**
```bash
raf search <terim>
raf search "birden fazla kelime"
```

**Açıklama:**
Kitap adlarını, yayıncı adlarını ve açıklamaları (büyük/küçük harf duyarsız) arar ve eşleşen sonuçları yazdırır.

**Argümanlar:**
| Argüman | Gerekli | Açıklama |
|---|---|---|
| `terim` | Evet | Arama dizesi. Birden fazla kelime içeren terimleri tırnak içine alın. |

**Örnek:**
```bash
raf search ankara
# Çıktı:
Search results (2 items):
ID                                  | Title                                         | Publisher
ankarakutuphane                     | Ankara İl Milli Eğitim Kütüphanesi            | Ankara İl MEM
...
```

**Çıkış kodu:** `0` (başarı, sıfır sonuç dahil), `1` (terim argümanı eksik)

---

### `install <kitap_id>` — Bir kitabı indir ve kur

**Kullanım:**
```bash
raf install <kitap_id>
```

**Açıklama:**
Kitap paketini indirir ve kurar. `kitap_id`, `books.json` içindeki `id` alanı ile tam olarak eşleşmelidir. ID'leri bulmak için `raf list` kullanın.

**Argümanlar:**
| Argüman | Gerekli | Açıklama |
|---|---|---|
| `kitap_id` | Evet | `raf list` çıktısındaki tam kitap ID'si |

**Süreç:**
1. Veritabanındaki kitabı arar — bulunamazsa hata ile çıkar
2. Zaten kurulu olup olmadığını kontrol eder — öyleyse bilgi mesajı ile çıkar
3. Paket dosyasını indirir, gerçek zamanlı bir ilerleme çubuğu gösterir:
   ```
   Downloading: [========================================] %100 (2.34 MB/s)
   ```
4. `pkexec apt-get install -y ./file.deb` (veya `flatpak`/`snap` karşılıkları) aracılığıyla kurar
5. Başarı veya başarısızlığı bildirir

**Örnek:**
```bash
raf install akademikbasariyayinlarikutuphane
```

**Çıkış kodları:**
| Kod | Anlamı |
|---|---|
| `0` | Başarıyla kuruldu |
| `1` | Kitap bulunamadı / indirme hatası / kurulum başarısız / zaten kurulu |

**Notlar:**
- `pkexec` ve PolicyKit gerektirir — işletim sistemi yönetici kimlik bilgilerini isteyecektir
- Geliştirici modunda (`RAF_DEV=1`), kurulum sistem değişiklikleri olmadan simüle edilir
- İndirmeler `~/.cache/raf/downloads/` (veya geliştirici modunda `mock_system/cache/`) dizininde önbelleğe alınır
- İndirme kesintiye uğrarsa, sonraki çalıştırma `Range` başlıklarını kullanarak kaldığı yerden devam etmeye çalışacaktır

---

### `install-local <yol>` — Yerel dosya veya dizini kur

**Kullanım:**
```bash
raf install-local <dosya_veya_dizin_yolu>
```

**Açıklama:**
Yerel uygulama dosyalarını (.deb, .appimage, .zip, .fernus) indirmeden kurar. Eğer bir dizin belirtilirse, o dizindeki desteklenen tüm dosyaları kurmaya çalışır. Tanınmayan dosyalar uyarı ile atlanır.

**Argümanlar:**
| Argüman | Gerekli | Açıklama |
|---|---|---|
| `yol` | Evet | Dosya veya dizine giden mutlak veya göreceli yol |

**Örnek:**
```bash
raf install-local ~/Downloads/myapp.deb
raf install-local /media/usb/apps/
```

**Çıktı:**
```
Warning: The following unsupported files were skipped:
- notes.txt
Installing: myapp
 Status: Extracting files...
 Status: Installing system package (authorization may be requested)...
Success: 'myapp' successfully installed.
```

**Çıkış kodu:** Başarı durumunda `0`, hata durumunda `1`.

---

### `uninstall <kitap_id>` — Bir kitabı kaldır

**Kullanım:**
```bash
raf uninstall <kitap_id>
```

**Açıklama:**
Belirtilen kitabı sistemden kaldırır. Komut, ilerlemeden önce kitabın gerçekten kurulu olup olmadığını kontrol eder.

**Argümanlar:**
| Argüman | Gerekli | Açıklama |
|---|---|---|
| `kitap_id` | Evet | `raf list-installed` çıktısındaki tam kitap ID'si |

**Örnek:**
```bash
raf uninstall akademikbasariyayinlarikutuphane
```

**Süreç:**
1. Kitabı arar — veritabanında değilse hata ile çıkar
2. Kurulu olup olmadığını kontrol eder — kurulu değilse bilgi mesajı ile çıkar
3. `.deb` için `pkexec apt-get remove -y <package>` ile kaldırır
4. `.zip`/`.fernus` kitapları için: uygulama dizinini ve `.desktop` başlatıcısını siler
5. Sonucu bildirir

**Çıkış kodları:**
| Kod | Anlamı |
|---|---|
| `0` | Başarıyla kaldırıldı |
| `1` | Kitap bulunamadı / kurulu değil / kaldırma başarısız |

---

### `clean` — İndirme önbelleğini temizle

**Kullanım:**
```bash
raf clean
```

**Açıklama:**
`~/.cache/raf/downloads/` (veya geliştirici modunda `mock_system/cache/`) dizinindeki tüm dosyaları siler. Kurulumlardan sonra disk alanı açmak için kullanışlıdır.

**Çıktı:**
```
Success: Download cache cleared. 5 files deleted.
# veya zaten boşsa:
Cache folder is empty or does not exist.
```

**Çıkış kodu:** `0`

---

## Ortam Değişkenleri

| Değişken | Değerler | Etki |
|---|---|---|
| `RAF_DEV` | `1` | Geliştirici/simülasyon modunu etkinleştirir |

---

## Örnekler

```bash
# Her şeyi listele
raf list

# "matematik" ile ilgili tüm kitapları bul
raf search matematik

# Belirli bir kitabı kur
raf install ankarakutuphane

# Nelerin kurulu olduğunu kontrol et
raf list-installed

# Bir kitabı kaldır
raf uninstall ankarakutuphane

# İndirme önbellek alanını temizle
raf clean

# Yukarıdakilerin tümünü geliştirici modunda çalıştır (sistem değişiklikleri olmadan)
RAF_DEV=1 raf list
RAF_DEV=1 raf install ankarakutuphane
```

---

## Hata Mesajları

| Mesaj | Neden |
|---|---|
| `Error: Book with ID '{id}' not found.` | Kitap ID'sinde yazım hatası — doğrulamak için `raf list` çalıştırın |
| `Error: Search term not specified.` | `raf search` terim olmadan çalıştırıldı |
| `Error: Book ID to install not specified.` | `raf install` ID olmadan çalıştırıldı |
| `Error: Book ID to uninstall not specified.` | `raf uninstall` ID olmadan çalıştırıldı |
| `Info: '{title}' is already installed.` | Kitap zaten sistemde mevcut |
| `Info: '{title}' is already not installed.` | Olmayan bir kitabı kaldırmaya çalıştı |
| `Download error: {error}` | Ağ arızası, geçersiz URL veya disk dolu |
| `Error: Installation cannot proceed because the download failed.` | İndirme hatasından sonra kurulum iptal edildi |

---

## GUI'den Farklılıklar

| Davranış | GUI | CLI |
|---|---|---|
| İndirme kuyruğu | FIFO, maksimum 2 eşzamanlı | Sıralı, her seferinde bir tane |
| İlerleme | Kartta animasyonlu ilerleme çubuğu | ASCII metin ilerleme çubuğu |
| PolicyKit iletişim kutusu | Grafik işletim sistemi iletişim kutusu | Aynı grafik işletim sistemi iletişim kutusu |
| Dil | Tercihler'de yapılandırılır | Sistem yerel ayarlarını takip eder |
| Tema | Aydınlık/Karanlık | N/A |
| Çevrimdışı algılama | Kullanıcı arayüzünde afiş | İndirme denemesinde hata mesajı |
