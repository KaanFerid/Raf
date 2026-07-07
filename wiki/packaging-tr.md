# Paketleme ve Dağıtım Dokümantasyonu

[![English](https://img.shields.io/badge/Language-English-blue?style=flat-square)](packaging.md)

Bu belge, Raf `.deb` paketini derlemek, doğrulamak ve dağıtmak için gereken her şeyi kapsar. Paket, Pardus, Debian ve Ubuntu sistemleri için tamamen Lintian uyumlu olacak şekilde tasarlanmıştır.

---

## 1. Paket Meta Verisi

[`debian/control`](../debian/control) içinde tanımlanmıştır:

```
Package: raf
Architecture: all
Version: (bkz. debian/changelog)
Section: utils
Priority: optional
Depends: python3, python3-gi, gir1.2-gtk-4.0, gir1.2-adw-1, python3-requests, policykit-1
Maintainer: Kaan Ferid Altundaş <kaanferidaltundas@protonmail.com>
Description: Pardus Akilli Tahta Raf Uygulamasi
 Pardus tabanli akilli tahtalarda interaktif kitap raflarinin
 hizlica aranmasi, indirilmesi, kurulmasi ve silinmesini saglar.
```

### Çalışma Zamanı Bağımlılıkları

| Paket | Neden gerekli |
|---|---|
| `python3` | Uygulama çalışma zamanı |
| `python3-gi`, `gir1.2-gtk-4.0`, `gir1.2-adw-1` | GTK4 ve Libadwaita GUI çerçevesi |
| `python3-requests` | HTTP indirmeleri ve Google Drive atlatması |
| `policykit-1` | `.deb` paketlerini kurarken ayrıcalık yükseltme için `pkexec` |

İsteğe bağlı sistem yetenekleri (kesin bağımlılıklar değil):
- `flatpak` — yalnızca Flatpak kitap girdileri için gereklidir
- `snapd` — yalnızca Snap kitap girdileri için gereklidir

---

## 2. Kurulu Dosya Düzeni

`.deb` aracılığıyla kurulduğunda, Raf dosyalarını şuraya yerleştirir:

```
/usr/lib/raf/                     # Uygulama kaynağı
    src/
        main.py
        core/
        ui/
        assets/
/usr/bin/raf                      # Kabuk (shell) başlatıcı betiği
/usr/share/applications/raf.desktop  # Masaüstü girdisi (uygulama başlatıcısı için)
/usr/share/raf/database/          # Ana veritabanı dosyaları (fernus_drive.json, publishers.json)
/usr/share/doc/raf/
    copyright                     # GPL-3.0 telif hakkı beyanı
    changelog.gz                  # Sıkıştırılmış değişiklik günlüğü (changelog)
/usr/share/icons/hicolor/.../raf.png  # Uygulama simgesi
```

`/usr/bin/` içindeki `raf` binary'si basit bir kabuk sarıcısıdır (wrapper):
```bash
#!/bin/sh
exec python3 /usr/lib/raf/src/main.py "$@"
```

---

## 3. Paketi Derleme

### Seçenek A: Kabuk Derleme Betiği (Önerilen)

Gereksinimler: `dpkg-deb`, `md5sum` (Debian/Ubuntu/Pardus'ta standart)

```bash
./scripts/build_deb.sh
```

**Betiğin adım adım yaptığı şey:**

1. Önceki tüm `build/raf-pkg/` hazırlama (staging) dizinini **temizler**
2. **Hazırlama ağacını oluşturur:**
   ```
   build/raf-pkg/
   ├── DEBIAN/
   │   ├── control
   │   ├── md5sums          ← otomatik oluşturulur
   │   └── postinst         ← /usr/bin/raf üzerinde çalıştırılabilir bitleri ayarlar
   └── usr/
       ├── bin/raf
       ├── lib/raf/src/...
       └── share/doc/raf/copyright
   ```
3. **Kaynak dosyalarını** `usr/lib/raf/` içine **kopyalar**
4. **`md5sums` oluşturur:** her veri dosyasının MD5'ini hesaplar (göreceli yollar, `DEBIAN/` olmadan)
5. **Telif hakkını kopyalar:** `debian/copyright` dosyasını `0644` izinleriyle `usr/share/doc/raf/copyright` konumuna yerleştirir
6. **İzinleri ayarlar:** tüm dizinler için `0755`, tüm dosyalar için `0644`, `/usr/bin/raf` için `0755`
7. **`dpkg-deb` çağırır:**
   ```bash
   dpkg-deb --build build/raf-pkg raf_<versiyon>_all.deb
   ```

Eğer `dpkg-deb` bulunamazsa, betik otomatik olarak şuna geri döner:
```bash
python3 scripts/build_deb.py
```

---

### Seçenek B: Saf Python Derleyici

Sistem paketleme araçları gerekmez. Arch Linux, macOS, Windows'ta çalışır.

```bash
python3 scripts/build_deb.py
```

**İçeride nasıl çalışır:**

`.deb` formatı, üç üye içeren bir `ar` arşividir:
```
debian-binary   → "2.0\n"
control.tar.gz  → DEBIAN/control + DEBIAN/md5sums
data.tar.gz     → usr/ dosya ağacı
```

Python derleyicisi:
1. Tüm dosyaları toplamak için kaynak ağacında gezinir
2. `tarfile.open(mode='w:gz', fileobj=BytesIO())` kullanarak `control.tar.gz` dosyasını bellekte oluşturur
3. Dosya okumaları sırasında `hashlib.md5()` ile MD5 sağlama toplamlarını hesaplar
4. Doğru `TarInfo` meta verileriyle (uid/gid=0, mod bitleri) `data.tar.gz` dosyasını oluşturur
5. BSD `ar` formatı özelliklerine göre `struct.pack` kullanarak `ar` arşivi başlıklarını yazar:
   ```
   Sapma(Offset)  Boyut(Size)  Alan(Field)
   0              16           Dosya adı (boşluklarla doldurulmuş)
   16             12           Değiştirme zaman damgası
   28             6            Sahip Kimliği (Owner ID)
   34             6            Grup Kimliği (Group ID)
   40             8            Dosya modu (sekizlik/octal)
   48             10           Bayt cinsinden dosya boyutu
   58             2            Sihirli(Magic): "`\n"
   60             N            Dosya verileri (çift boyuta doldurulmuş)
   ```

Çıktı: Proje kökünde `raf_<versiyon>_all.deb`.

---

## 4. Lintian Uyumluluğu

Paket, `lintian --pedantic` kontrollerini geçecek şekilde tasarlanmıştır:

### MD5 Sağlama Toplamları (`DEBIAN/md5sums`)

`data.tar.gz` içindeki (kurulu dosya ağacı) tüm dosyaların MD5 özetleri listelenmelidir:

```
d41d8cd98f00b204e9800998ecf8427e  usr/lib/raf/src/main.py
...
```

Hem kabuk hem de Python derleme betikleri bunu otomatik olarak hesaplar.

### Telif Hakkı Beyanı

Debian İlkesi §12.5 uyarınca, `usr/share/doc/<pkg>/copyright` konumunda bir `copyright` dosyası bulunmalıdır.

`debian/copyright` konumundaki dosya GPL-3.0'ı beyan eder ve derleme sırasında doğru konuma kopyalanır:
```
usr/share/doc/raf/copyright   (izinler: 0644)
```

### Dosya İzinleri

| Yol | Mod |
|---|---|
| Dizinler | `0755` |
| Düzenli dosyalar | `0644` |
| `/usr/bin/raf` | `0755` (çalıştırılabilir) |

### Paket Mimarisi

Raf derlenmiş C uzantıları (extensions) olmayan saf bir Python uygulaması olduğu için `Architecture: all` doğrudur.

---

## 5. Derlenmiş Bir Paketi Doğrulama

```bash
python3 scripts/inspect_deb.py
```

Bu betik, derlenmiş `.deb` dosyasını kurmadan ayıklar ve inceler. Şunları kontrol eder:

- ✅ Paketin `!<arch>\n` ile başlayan geçerli bir `ar` arşivi olması
- ✅ `debian-binary` içeriğinin `2.0` olması
- ✅ `control.tar.gz` dosyasının `control` ve `md5sums` içermesi
- ✅ `data.tar.gz` dosyasının `usr/share/doc/raf/copyright` içermesi
- ✅ MD5 girdilerinin boş olmaması
- ✅ Paket adı ve sürümünün beklentilerle eşleşmesi

Örnek çıktı:
```
=== Raf Package Inspector ===
Package: raf_1.0.3_all.deb  (46,112 bytes)
✓ Valid ar archive
✓ debian-binary: 2.0
Control files: ['control', 'md5sums']
✓ md5sums present (42 entries)
✓ copyright present at usr/share/doc/raf/copyright
All checks passed.
```

---

## 6. Paketi Kurma

### Doğrudan Kurulum
```bash
sudo apt install ./raf_1.0.3_all.deb
```

### dpkg ile (manuel)
```bash
sudo dpkg -i raf_1.0.3_all.deb
sudo apt-get install -f   # eksik bağımlılıkları çözer
```

### Kaldırma
```bash
sudo apt remove raf
# veya konfigürasyon dosyalarını da kaldırmak için:
sudo apt purge raf
```

---

## 7. Sürüm Yönetimi

Sürüm numarası şuralarda tanımlanır:
- `src/core/version.py` — `__version__ = "1.0.3"` (uygulama ve CLI tarafından kullanılır)
- `debian/changelog` — Sürüm ve tarihi içeren Debian değişiklik günlüğü (changelog) girdisi

Yeni bir sürüm yayınlanırken:
1. `src/core/version.py` dosyasını güncelleyin
2. `debian/changelog` dosyasına standart formatı izleyerek yeni bir girdi ekleyin.
3. Değişiklikleri commit (taahhüt) edin ve GitHub'a push yapın. (Bu, "Build Debian Package" GitHub Eylemini otomatik olarak tetikleyecektir).
4. GitHub'daki **Actions** sekmesine gidin, **Publish Release** iş akışını seçin ve **Run workflow** düğmesine tıklayın. Yeni sürüm etiketini girin (örn. `v1.0.4`).
5. Action, `.deb` dosyasını otomatik olarak derleyecek, resmi bir GitHub Sürümü (Release) oluşturacak ve `.deb` dosyasını varlık olarak ekleyecektir.

---

## 8. GitHub Sürümleri ve Otomatik Güncelleyici

Otomatik güncelleyici, en son sürüm meta verilerini doğrudan GitHub API'sinden çeker:
```
https://api.github.com/repos/KaanFerid/Raf/releases/latest
```

Uygulama, GitHub API yanıtını ayrıştırır:
- **Sürüm:** `tag_name` içinden çıkarılır (örn., `"v1.0.4"` → `"1.0.4"` olur).
- **Değişiklik Günlüğü (Changelog):** Sürüm notlarının (release notes) `body` (gövde) kısmından çıkarılır.
- **İndirme URL'si:** Güncelleyici, `.deb` dosyasını bulmak için sürüm `assets` (varlıklar) dizisini otomatik olarak tarar ve onun `browser_download_url` adresini kullanır.

Uygulama, bu sürüm dizesini sayısal olarak (`.` ile bölerek) yerel `APP_VERSION` ile karşılaştırır. Daha yüksek olan herhangi bir sürüm, kullanıcının politikasına bağlı olarak güncelleme bildirimini veya otomatik kurulumu tetikler. Hiçbir manuel `update.json` bakımı gerekmez!

---

## 9. Bağımsız Uygulamalar, Flatpak ve Snap Paketleme (Gelecek)

Raf'ın kendisi bir `.deb` olarak dağıtılırken, yönetilen kitaplar için **bağımsız Uygulamalar (AppImage, Fernus, ZIP), Flatpak ve Snap paketleri** kurabilir.

Veritabanına bağımsız bir AppImage eklemek için:
**`publishers.json` içindeki AppImage girdisi:**
```json
{
  "id": "my-appimage",
  "title": "Benim AppImage Kitabım",
  "publisher": "Örnek Yayıncı",
  "file_name": "myapp.AppImage",
  "file_type": "appimage",
  "download_url": "https://example.com/myapp.AppImage"
}
```

Veritabanına bir Flatpak veya Snap kitabı eklemek için:

**`books.json` içindeki Flatpak girdisi:**
```json
{
  "id": "org.gnome.Calculator",
  "title": "GNOME Hesap Makinesi",
  "publisher": "GNOME",
  "file_name": "gnome-calculator.flatpak",
  "file_type": "flatpak",
  "flatpak_ref": "org.gnome.Calculator",
  "download_url": ""
}
```

**`books.json` içindeki Snap girdisi:**
```json
{
  "id": "vlc-snap",
  "title": "VLC Medya Oynatıcı",
  "publisher": "VideoLAN",
  "file_name": "vlc.snap",
  "file_type": "snap",
  "snap_name": "vlc",
  "download_url": ""
}
```

> **Not:** Flatpak/Snap girdileri için `download_url` ve `file_name` alanları kullanılmaz — kurucu doğrudan Flatpak/Snap arka plan programları (daemons) ile iletişim kurar. Onları boş dizeler olarak bırakın.
