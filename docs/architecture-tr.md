# Mimari Dokümantasyonu

[![English](https://img.shields.io/badge/Language-English-blue?style=flat-square)](architecture.md)

Raf, Pardus ETAP akıllı tahtalarında kararlılık için tasarlanmış katmanlı, asenkron bir mimariye sahiptir. Ağ veya dosya sistemi G/Ç içeren kullanıcıya dönük tüm işlemler arka plandaki `threading.Thread` çalışanlarında (workers) çalışır ve yalnızca `GLib.idle_add` fonksiyonları (callbacks) aracılığıyla UI iş parçacığıyla iletişim kurar.

---

## 1. Katmanlara Genel Bakış

```
┌─────────────────────────────────────────────────┐
│                  UI Katmanı                      │
│  main_window.py · components.py                 │
│  desktop_editor.py · logs_dialog.py             │
│  preferences.py · about.py                      │
├─────────────────────────────────────────────────┤
│               Çekirdek / İş Mantığı              │
│  database.py · downloader.py · installer.py     │
│  updater.py · sync.py · download_queue.py       │
│  config.py · translation.py · cli.py            │
└─────────────────────────────────────────────────┘
```

---

## 2. Çekirdek Modüller

### `database.py` — Kitap Veritabanı

Kitap kataloğunu `database/` dizininden yükler. Hem `fernus_drive.json` hem de `publishers.json` dosyalarını okur ve bunları mevcut kitapların tek bir listesinde birleştirir.
`sync.py` tarafından işlenen uzak senkronizasyonu destekler.

**Önemli sınıf: `Database`**
- `load_books()` — yerel `database/` klasöründen okur ve tüm dosyaları birleştirir
- `get_all_books()` → `list[dict]` — tüm kitap girdilerini döndürür
- `search_books(query)` → `list[dict]` — başlık, yayıncı, açıklama üzerinde tam metin araması

---

### `downloader.py` — İndirme Çalışanı

Kitap paketlerini indiren standart python iş parçacığı tabanlı bir çalışandır:
- **Parçalı akış** (8 KB'lık parçalar) ilerlemeyi takip etmek için
- **Google Drive virüs uyarısı atlatma** — HTML onay sayfalarını algılar ve çıkarılan `confirm` ile `uuid` form token'larıyla yeniden gönderir
- **HTTP Range devam ettirme** — indirme ortasında bağlantı koparsa `Range: bytes=N-` ile yeniden dener (3 otomatik denemeye kadar)
- **İptal Etme** — `cancel()` her parçadan sonra kontrol edilen bir bayrağı (flag) ayarlar
- **Hız hesaplama** — UI'da gösterilen gerçek MB/s

**Geri Çağırmalar (Callbacks):**
- `on_progress_changed(book_id, percent, speed_str)`
- `on_finished(book_id, local_file_path)`
- `on_error(book_id, error_message)`

---

### `download_queue.py` — İndirme Kuyruğu

Yapılandırılabilir eşzamanlılık kontrolüne sahip bir FIFO (ilk giren ilk çıkar) kuyruğu.

**Önemli sınıf: `DownloadQueue`**

| Metot | Açıklama |
|---|---|
| `enqueue(book, local_path)` | Bir iş ekler; zaten kuyrukta veya aktifse `False` döndürür |
| `dequeue(book_id)` | Bekleyen (henüz aktif olmayan) bir işi kaldırır |
| `is_queued(book_id)` | Bekleyenler listesinde bekliyorsa `True` döndürür |
| `is_active(book_id)` | Şu anda indiriliyorsa `True` döndürür |
| `pending_count()` | Başlamayı bekleyen işlerin sayısı |
| `on_download_started(book_id)` | Bir işi aktif olarak işaretlemek için `MainWindow` tarafından çağrılır |
| `on_download_completed(book_id)` | Bir yuvayı serbest bırakır ve bekleyen bir sonraki işi başlatır |

---

### `installer.py` — Paket Kurucu

Kitapları `file_type` özelliklerine göre kurmayı ve kaldırmayı işleyen iş parçacığı tabanlı bir çalışan.

**Önemli sınıf: `InstallerWorker`**

Yapıcı (Constructor): `InstallerWorker(book, file_path, action="install")`

**Desteklenen dosya türleri:**

| `file_type` | Kurma metodu | Kaldırma metodu |
|---|---|---|
| `deb` | `pkexec apt-get install -y ./file.deb` | `pkexec apt-get remove -y <pkg>` |
| `zip` / `fernus` / `appimage` | `/opt/raf/apps/<id>/` dizinine çıkartır/kopyalar + `pkexec` üzerinden genel bir `.desktop` oluşturur | `pkexec` uygulama dizinini + `.desktop` dosyasını siler |
| `flatpak` | `flatpak install --user --noninteractive <ref>` | `flatpak uninstall --user --noninteractive <ref>` |
| `snap` | `pkexec snap install <snap_name>` | `pkexec snap remove <snap_name>` |

`.deb` kurulumları için, tam paket adı `dpkg-deb -f Package` kullanılarak `.deb` dosyasından çıkarılır ve gelecekteki `is_installed` kontrollerini hızlandırmak için `config.json` içinde önbelleğe alınır.

**Geri Çağırmalar (Callbacks):**
- `on_status_changed(book_id, message)`
- `on_finished(book_id, success)`
- `on_output_received(book_id, line)`

---

### `updater.py` — Güncelleme Sistemi

Üç sınıf güncelleme akışının farklı yönlerini işler:

**`UpdateChecker`**
GitHub'dan `update.json` dosyasını çeker, sürüm numaralarını karşılaştırır, yeni sürümlerde callbacks çağırır.

**`UpdateInstaller`**
Bir `.deb` güncelleme dosyasını indirir ve `pkexec apt-get install --reinstall -y` üzerinden kurar.

**`AutoUpdateScheduler`**
6 saatlik aralıklarla arka planda iş parçacığı kontrolleri çalıştırır. Konfigürasyondan `auto_update_policy` okur.

---

### `sync.py` — Uzak Veritabanı Senkronizasyonu

Yerel veritabanı dizinini uzak bir sunucuyla senkronize eder. Yapılandırılan `database_url` bir temel URL'yi gösteriyorsa, eşzamanlı olarak `fernus_drive.json` ve `publishers.json` dosyalarını çeker, doğrular ve yerel `database/` önbellek yoluna kaydeder.

---

### `config.py` — Kalıcı Konfigürasyon

`~/.config/raf/config.json` (veya geliştirici modunda `mock_system/config.json`) dosyasını yönetir.

**Varsayılan konfigürasyon:**
```json
{
  "theme_mode": "system",
  "language": "tr",
  "auto_update_policy": "check",
  "database_url": "",
  "last_update_check": 0.0,
  "package_names": {}
}
```

---

### `translation.py` — Çalışma Zamanı Dil Değiştirme

Yerel dosyaları `src/assets/locales/` dizininden yükler. Callbacks aracılığıyla yeniden başlatmadan çalışma zamanında dil değiştirmeyi destekler.

**Fonksiyonlar:**
- `tr(key, **kwargs)` — `kwargs` ile biçimlendirilmiş `key` için çevrilmiş dizeyi döndürür
- `set_language(lang_code)` — dili değiştirir ve kayıtlı tüm dinleyicilere (listeners) bildirir

---

### `cli.py` — CLI İşleyici

`src.main` betiğine herhangi bir komut satırı argümanı geçirildiğinde çağrılır. 
Simülasyona karşı gerçek paket işlemlerini seçmek için `RAF_DEV` okur.

---

## 3. UI Katmanı

### `main_window.py` — MainWindow (Ana Pencere)

En üst düzey `Adw.ApplicationWindow` şunları yapar:
- `Database`, `DownloadQueue`, `AutoUpdateScheduler` ve `DatabaseSyncWorker` nesnelerine sahiptir
- `active_downloads` ve `active_installations` sözlüklerini yönetir
- Çalışanlar ve UI güncellemeleri arasındaki tüm callbacks fonksiyonlarını `GLib.idle_add` aracılığıyla işler

**Önemli metot grupları:**

| Grup | Metotlar |
|---|---|
| İndirme yaşam döngüsü | `start_download()`, `on_download_progress()`, `on_download_finished()`, `on_download_error()`, `cancel_download()` |
| Kurulum yaşam döngüsü | `start_installation()`, `on_installation_finished()`, `start_uninstallation()`, `on_uninstallation_finished()` |
| Toplu iş (Batch) modu | `toggle_selection_mode()`, `process_local_files()` |
| Yenileme | `refresh_grid()`, `refresh_packages_cache()` |

---

### `components.py` — BookRow

Bir kitap girişini temsil eden `Adw.ActionRow`.

**Önemli öznitelikler:**
- `is_installed: bool` — kurulum durumunu izler
- `downloading: bool` — aktif indirmeyi izler

---

## 4. Dosya Yolu Referansı

| Yol | Amaç |
|---|---|
| `~/.config/raf/config.json` | Kullanıcı konfigürasyonu |
| `~/.cache/raf/downloads/` | İndirme önbelleği |
| `/opt/raf/apps/<id>/` | Sistem genelinde çıkartılmış `.zip`/`.fernus`/`.appimage` kitapları |
| `/usr/share/applications/raf-<id>.desktop` | Bağımsız (standalone) kitaplar için genel masaüstü başlatıcıları |
| `/usr/share/raf/database/` | Ana veritabanı dosyaları (`fernus_drive.json`, `publishers.json`) |
| `mock_system/config.json` | Geliştirici modu konfigürasyonu |
| `mock_system/cache/` | Geliştirici modu indirmeleri |
| `mock_system/installed.json` | Geliştirici modu kurulum durumu |
| `mock_system/update_mock.json` | Geliştirici modu güncelleme meta verisi |
| `~/.config/raf/sideloaded.json` | Kullanıcı tarafından eklenen yerel uygulamalar için veritabanı |
| `~/.local/share/applications/raf-<id>.desktop` | Yerel uygulamalar için kullanıcı tarafından düzenlenen masaüstü başlatıcıları |

---

## 5. Dışarıdan Yükleme (Sideloading) ve Yerel Başlatıcı Düzenleyici

Raf, merkezi uzak veritabanının dışındaki yerel bağımsız uygulama dosyalarının (`.deb`, `.zip`, `.appimage`, `.fernus`) kurulumunu destekler. 

### Dışarıdan Yükleme İş Akışı

1. **Keşif:** Kullanıcı `MainWindow.on_install_local_clicked()` aracılığıyla veya ana pencereye sürükleyip bırakarak yerel dosyaları veya bir dizini seçer.
2. **Ayrıştırma:** `src/core/sideload.py` dosyaları `SUPPORTED_EXTENSIONS` listesine göre doğrular. Tanınmayan dosyalar atlanır.
3. **Veritabanı Enjeksiyonu:** Geçerli yerel uygulamalara benzersiz bir kimlik (`local_<güvenli_dosya_adi>`) verilir ve kullanıcının `~/.config/raf/sideloaded.json` veritabanına eklenir. `Database` sınıfı, Kütüphanem sekmesinde sorunsuz bir şekilde görünmeleri için bu dışarıdan yüklenen uygulamaları ana `fernus_drive.json` listesiyle otomatik olarak birleştirir.
4. **Yürütme:** Dosya yolu `InstallerWorker`'a aktarılır, o da indirilen uzak bir uygulamayla aynı şekilde işler.

### Başlatıcı Özelleştirme

Dışarıdan yüklenen uygulamalar merkezi meta verilerden (yayıncı, doğru başlıklar, simgeler) yoksun olduğundan, Raf yerleşik bir Masaüstü Başlatıcı Düzenleyici (`src/ui/desktop_editor.py`) sağlar.

- Kütüphanem sekmesindeki kurulu yerel uygulamalarda "Başlatıcıyı Düzenle" düğmesinden erişilebilir.
- Düzenleyici, `~/.local/share/applications/` klasörüne kaydederek `sudo` ayrıcalıkları gerektirmeden genel `/usr/share/applications/` başlatıcılarını güvenli bir şekilde geçersiz kılar (override eder).
- `.desktop` INI spesifikasyonunu doğrudan değiştirmek için `Adw.Window` içine sarılmış yerel GTK4/Adwaita düzen widget'larını kullanır.
