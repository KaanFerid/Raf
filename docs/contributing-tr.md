# Katkıda Bulunma ve Geliştirici Rehberi

[![English](https://img.shields.io/badge/Language-English-blue?style=flat-square)](contributing.md)

Bu rehber, bir geliştirme ortamının nasıl kurulacağını, kod tabanının nasıl anlaşılacağını, yeni özelliklerin nasıl ekleneceğini ve değişikliklerin nasıl gönderileceğini açıklar.

---

## 1. Geliştirme Ortamını Kurma

### Önkoşullar

- Python 3.9 veya daha yenisi
- Git

### Klonlama ve Çalıştırma

```bash
git clone https://github.com/KaanFerid/Raf.git
cd raf
./run_dev.py
```

`run_dev.py` otomatik olarak şunları yapar:
1. `PyGObject` ve `requests` paketlerinin mevcut olup olmadığını algılar
2. Mevcut değilse, proje dizininde izole bir `.venv` oluşturur
3. `PyGObject` ve `requests` paketlerini `.venv` içine kurar
4. Uygulamayı simülasyon/geliştirici modunda başlatır

> **Betik hiçbir zaman sistem paketlerini değiştirmez.** Tüm bağımlılıklar `.venv` içinde tutulur.

### Manuel Kurulum (pip ile)

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
RAF_DEV=1 python3 -m src.main
```

---

## 2. Geliştirici Modu (`RAF_DEV=1`)

`RAF_DEV=1` ayarı, simülasyon korumalı alanını (sandbox) etkinleştirir. Her sistem düzeyi işlem güvenli bir şekilde simüle edilir:

| Gerçek işlem | Simüle edilen |
|---|---|
| `pkexec apt-get install` | 1.5s gecikme → `mock_system/installed.json` dosyasına yazar |
| `pkexec apt-get remove` | 1s gecikme → `mock_system/installed.json` dosyasından siler |
| `flatpak install` | 1.5s simülasyon |
| `snap install` | 1.5s simülasyon |
| İndirmeler | `mock_system/cache/` dizinine gerçek HTTP indirmesi |
| Güncelleme kontrolü | `mock_system/update_mock.json` okur |
| Konfigürasyon | `mock_system/config.json` okur/yazar |

### Simülasyon (Mock) Dosyaları

| Dosya | Amaç | Örnek içerik |
|---|---|---|
| `mock_system/installed.json` | Hangi kitapların "kurulu" olduğunu izler | `{"book_id_1": true}` |
| `mock_system/update_mock.json` | Simüle edilmiş bir güncellemeyi tetikler | `{"version": "99.0", "download_url": "...", "changelog": "..."}` |
| `mock_system/config.json` | Geliştirici modundaki uygulama ayarları | Üretim konfigürasyonuyla aynı şema |

---

## 3. Proje Düzeni Özeti

```
src/
├── core/         İş mantığı (GTK araçları yok)
├── ui/           Sadece GTK araçları
├── assets/       Statik kaynaklar (JSON, resimler, yerel dizeler)
```

**Kural:** `core` modülleri asla `src/ui/` dizininden bir şey içe aktarmamalıdır. `ui` modülleri `src/core/` dizininden içe aktarma yapabilir.

---

## 4. Veritabanına Yeni Bir Kitap Ekleme

`database/` dizini içindeki dosyaları düzenleyin. 
- Google Drive üzerinde barındırılan kitaplar için `database/fernus_drive.json` dosyasını kullanın.
- Yayıncılardan gelen doğrudan HTTP indirme bağlantıları için `database/publishers.json` dosyasını kullanın.

Her girdi, ana dizi içindeki bir JSON nesnesidir:

### Gerekli minimum alanlar

```json
{
  "id": "essiz-kebab-case-id",
  "title": "Görünen Başlık",
  "publisher": "Yayıncı Adı",
  "file_name": "paket_dosyadi.deb",
  "file_type": "deb",
  "download_url": "https://example.com/paket.deb"
}
```

### İsteğe bağlı alanlar

| Alan | Tür | Ne için kullanılır |
|---|---|---|
| `description` | dize | Aramada gösterilir; arama için kullanılır |
| `flatpak_ref` | dize | `file_type == "flatpak"` olduğunda gereklidir |
| `snap_name` | dize | `file_type == "snap"` olduğunda gereklidir |

### Desteklenen `file_type` değerleri

| Değer | Kurucu | Algılama |
|---|---|---|
| `deb` | `pkexec apt-get install` | `dpkg-query` |
| `zip` | `~/.local/share/raf/apps/` içine çıkar | Dizin mevcut mu kontrolü |
| `fernus` | `zip` ile aynı | Aynı |
| `flatpak` | `flatpak install --user` | `flatpak list --app` |
| `snap` | `pkexec snap install` | `snap list` |

---

## 5. Yerel Dil Dizelerini Ekleme

Kullanıcı tarafından görülebilen tüm dizeler `tr()` çeviri işlevinden geçmelidir. Python dosyalarında kodlanmış (hard-coded) dizeler kabul edilmez.

### Adım 1 — Her iki dil dosyasına da ekleyin

`src/assets/locales/en.json`:
```json
{
  "ui": {
    "my_new_key": "My English text with {placeholder}."
  }
}
```

`src/assets/locales/tr.json`:
```json
{
  "ui": {
    "my_new_key": "Türkçe metin {placeholder} ile."
  }
}
```

### Adım 2 — Kodda kullanım

```python
from src.core.translation import tr

label.set_label(tr("ui.my_new_key", placeholder="değer"))
```

### Anahtar isimlendirme kuralı

| Önek | Bölüm |
|---|---|
| `ui.*` | Ana pencere, iletişim kutuları, kart etiketleri |
| `installer.*` | Paket kurucu durum mesajları |
| `downloader.*` | İndirme çalışanı mesajları |
| `updater.*` | Kendi kendini güncelleme mesajları |
| `cli.*` | CLI paneli metni |

---

## 6. Yeni Bir Çekirdek Çalışan (Core Worker) Ekleme

Arka planda G/Ç (ağ, dosya sistemi) yapan çalışanlar şunları yapmalıdır:

1. `threading.Thread` sınıfını genişletmek
2. Tüm sonuçları `GLib.idle_add` tarafından çağrılan callbacks (geri aramalar) yoluyla iletmek (arka plan iş parçacıklarından doğrudan UI çağrısı yapılmamalıdır)
3. Bir `self._cancelled` bayrağı aracılığıyla iptal etmeyi kabul etmek

Şablon:

```python
import threading
from gi.repository import GLib

class MyWorker(threading.Thread):
    def __init__(self, param):
        super().__init__()
        self.daemon = True
        self._cancelled = False
        self.param = param
        self.on_result_ready = None
        self.on_error = None

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            for chunk in some_operation(self.param):
                if self._cancelled:
                    return
                # parçayı işle ...
            if self.on_result_ready:
                GLib.idle_add(lambda: self.on_result_ready("Tamamlandı"))
        except Exception as e:
            if self.on_error:
                GLib.idle_add(lambda: self.on_error(str(e)))
```

`MainWindow` içinde:
```python
self.worker = MyWorker("girdi")
self.worker.on_result_ready = self.on_result
self.worker.on_error = self.on_error
self.worker.start()
```

---

## 7. Yeni Araçları Temalandırma

Tüm yeni widget'lar Adwaita CSS sınıfları veya GTK yerel stillendirmesi aracılığıyla şekillendirilmelidir.

```python
# Bir widget'a özel bir CSS sınıfı uygula:
my_btn = Gtk.Button(label="Tıkla")
my_btn.add_css_class("suggested-action")
```

---

## 8. Toast Bildirimleri

`MainWindow` erişiminiz olan her yerde bir bildirim gösterin:

```python
# MainWindow veya ona bağlı herhangi bir yöntemden:
self.toast_manager.show_toast(
    message=tr("ui.my_toast_key"),
    toast_type="success",    # "info", "success", "warning", "error"
    duration=3500            # otomatik kapanmadan önceki ms
)
```

Bildirimler engelleyici değildir ve kullanıcı etkileşimini kesintiye uğratmaz.

---

## 9. Test Takımını Çalıştırma

```bash
# Proje kök dizininden tüm testler:
python3 tests/test_updater.py
python3 tests/test_drive.py
```

Testler `RAF_DEV=1` değişkenini örtük olarak kullanır.

### Yeni Bir Test Yazma

```python
import os, sys
os.environ["RAF_DEV"] = "1"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ... test iddiaları (assertions) ...

print("All tests passed.")
```

---

## 10. Taahhüt (Commit) Yönergeleri

- **Geniş zamanlı, emir kipinde** taahhüt mesajları kullanın:  
  ✅ `Add toast notification for install error`  
  ❌ `Added toast notification`

- Bir etiketle ön eklendirin:  
  `feat:` yeni özellik  
  `fix:` hata düzeltmesi  
  `style:` yalnızca kod stili değişiklikleri  
  `refactor:` davranış değişikliği olmayan kod yeniden yapılandırması  
  `docs:` yalnızca belgeleme  
  `test:` test eklemeleri  
  `build:` paketleme/derleme komut dosyaları  

- Taahhütleri odaklanmış tutun — taahhüt başına mantıksal bir değişiklik.

---

## 11. Sürüm Kontrol Listesi

Yeni bir sürümü etiketlemeden önce:

- [ ] `src/core/version.py` dosyasını yeni sürüm dizesiyle güncelleyin
- [ ] `debian/changelog` dosyasına doğru tarih ve sürdürücü (maintainer) ile girdi ekleyin
- [ ] Tüm testleri çalıştırın — `python3 tests/test_updater.py`, `test_drive.py`
- [ ] `.deb` dosyasını derleyin ve inceleyin: `./scripts/build_deb.sh && python3 scripts/inspect_deb.py`
- [ ] GitHub'daki `update.json` dosyasını yeni sürüm + indirme URL'si ile güncelleyin
- [ ] GitHub sürümü (release) oluşturun ve `.deb` dosyasını ekleyin
- [ ] Temiz bir Pardus sanal makinesinde (VM) kurulumu test edin: `sudo apt install ./raf_<versiyon>_all.deb`
