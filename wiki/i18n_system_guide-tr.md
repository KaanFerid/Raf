# Hafif JSON Yerelleştirme (i18n) Motoru

Bu belge, Python uygulamaları için (özellikle PyQt/PySide, Tkinter veya CustomTkinter gibi GUI framework'leri) tasarlanmış yüksek verimli, sıfır bağımlılıklı bir yerelleştirme sistemini açıklar.

## Genel Bakış
`gettext` (.mo/.po dosyaları) veya Qt Linguist (.qm dosyaları) gibi ağır araçların aksine, bu motor standart JSON dosyalarını kullanır ve **derleme gerektirmez**. Özellikleri:

1. **Düz Nokta Notasyonu (Flat Dot Notation):** İç içe geçmiş JSON nesneleri düzleştirilir (örneğin `map.target_count`), böylece çeviri anahtarlarının okunması kolaylaşır.
2. **Dinamik Biçimlendirme:** Python'un argüman (keyword) formatlamasını destekler (örneğin, `tr("welcome", name="Alice")`).
3. **Otomatik İngilizce Geri Dönüşü (Fallback):** Şu anda aktif olan dilde bir kelime veya cümle eksikse, otomatik olarak varsayılan dile (İngilizce) döner.
4. **Reaktif Kullanıcı Arayüzü (UI) Güncellemeleri:** Gözlemci modeli (`on_language_change`) sunar; böylece GUI bileşenleri, uygulamayı yeniden başlatmaya gerek kalmadan metinlerini anında canlı olarak güncelleyebilir.

---

## 1. Dizin Yapısı

Motor dosyasının hemen yanında `i18n/` adında bir dizin oluşturun. JSON dil dosyalarınızı buraya yerleştirin.

```text
src/
├── i18n_engine.py      # Motor kodu (aşağıda verilmiştir)
└── i18n/
    ├── en.json         # Varsayılan İngilizce sözlük
    └── tr.json         # Türkçe sözlük (veya diğer diller)
```

## 2. Örnek JSON Sözlüğü (`en.json`)

Anahtarları mantıksal olarak düzenleyin. Motor, `_meta` bloğunu yalnızca dil isimleri için kullanır ve çeviri dışı bırakır.

```json
{
  "_meta": {
    "language": "English",
    "code": "en"
  },
  "main": {
    "title": "Uygulamam",
    "welcome": "Tekrar hoş geldin, {user}!",
    "status": "Sistem durumu: {status}"
  },
  "buttons": {
    "save": "Değişiklikleri Kaydet",
    "cancel": "İptal"
  }
}
```

## 3. Kod İçinde Nasıl Kullanılır

### Temel Metin Çevirisi
```python
from i18n_engine import tr, set_language

# Aktif dili ayarla
set_language("en")

# Temel arama
print(tr("buttons.save"))  # Çıktı: Değişiklikleri Kaydet

# Dinamik değişkenlerle arama
print(tr("main.welcome", user="John"))  # Çıktı: Tekrar hoş geldin, John!
```

### Reaktif GUI Kullanımı (Canlı Dil Değiştirme)
Bir GUI uygulamasında, kullanıcı dil ayarını değiştirdiğinde kullanıcı arayüzünün anında güncellenmesini istersiniz.

```python
from i18n_engine import tr, on_language_change

class SettingsWindow:
    def __init__(self):
        self.save_button = Button()
        self.welcome_label = Label()
        
        # Dil değiştiğinde otomatik tetiklenecek geri çağırma fonksiyonunu (callback) kaydet
        on_language_change(self._update_texts)
        
        # İlk metni ayarlamak için bir kez manuel çağır
        self._update_texts()

    def _update_texts(self, *args):
        # Bu fonksiyon tüm arayüz metinlerini günceller.
        # Başka bir yerde set_language() çağrıldığında otomatik olarak çalıştırılır.
        self.save_button.text = tr("buttons.save")
        self.welcome_label.text = tr("main.welcome", user="John")
```

---

## 4. Motor Kodu (`i18n_engine.py`)

Motoru uygulamak için aşağıdaki kodu kopyalayıp projenize yapıştırın.

```python
"""
i18n Çeviri Motoru
=======================
"i18n" klasöründeki yerelleştirme sözlüklerini (.json) işler.
Bölümleri 'bolum.anahtar' gibi anahtarlara eşleyen düz formattır.
"""

import json
from pathlib import Path

# Sözlük dosyalarının yolları (bu dosyanın yanında bir "i18n" klasörü olduğu varsayılır)
_I18N_DIR = Path(__file__).parent / "i18n"

# Çeviri önbelleği
_cache: dict[str, dict] = {}

# Geçerli aktif dil
_active: str = "en"

# Dil değiştiğinde çağrılacak fonksiyonlar (listeners)
_listeners: list = []


def _load(lang_code: str) -> dict:
    """
    Bir dilin JSON dosyasını yükler ve nokta notasyonu ile düzleştirir.
    """
    # Zaten yüklüyse önbellekten (cache) döndür
    if lang_code in _cache:
        return _cache[lang_code]

    path = _I18N_DIR / f"{lang_code}.json"
    
    # Dosya yoksa İngilizce'ye dön
    if not path.exists():
        print(f"[i18n] '{lang_code}' dil dosyası bulunamadı: {path}")
        return _cache.get("en", {})

    # Dil dosyasını oku
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # İç içe geçmiş sözlükleri nokta notasyonuna göre düzleştir (örneğin bolum.anahtar)
    flat: dict[str, str] = {}
    for section, entries in raw.items():
        if section == "_meta":
            continue
        if isinstance(entries, dict):
            for key, val in entries.items():
                flat[f"{section}.{key}"] = val
        else:
            flat[section] = str(entries)

    # Düzleştirilmiş sözlüğü önbelleğe al
    _cache[lang_code] = flat
    return flat


def tr(key: str, **kwargs) -> str:
    """
    Verilen anahtar için çevrilmiş metni döndürür, eğer kwargs verilmişse yer tutucuları biçimlendirir.
    """
    data = _load(_active)
    val = data.get(key)

    # Aktif dilde çeviri eksikse İngilizce'ye dön
    if val is None:
        fallback = _load("en")
        val = fallback.get(key, key) # Tamamen eksikse anahtarın kendisini döndür

    # Eğer kwargs geçilmişse mesajı dinamik olarak biçimlendir
    if kwargs:
        try:
            val = val.format(**kwargs)
        except (KeyError, ValueError):
            pass

    return val


def set_language(lang_code: str) -> bool:
    """
    Aktif dili değiştirir, çeviri sözlüğünü yükler ve callback fonksiyonlarını tetikler.
    """
    global _active
    path = _I18N_DIR / f"{lang_code}.json"
    if not path.exists():
        print(f"[i18n] Dil dosyası bulunamadı: {path}")
        return False

    _active = lang_code
    _load(lang_code)

    # Tüm dinleyicilere (listeners) arayüz metinlerini güncellemelerini bildir
    for cb in _listeners:
        try:
            cb(lang_code)
        except Exception as e:
            print(f"[i18n] Listener güncelleme hatası: {e}")

    return True


def available_languages() -> dict[str, str]:
    """
    Mevcut dillerin haritasını {"kod": "isim"} şeklinde döndürür.
    Tüm json dosyalarındaki _meta.language alanını okur.
    """
    langs = {}
    if not _I18N_DIR.exists():
        return langs
        
    # Sözlük JSON dosyalarını tara
    for f in sorted(_I18N_DIR.glob("*.json")):
        code = f.stem
        try:
            with open(f, "r", encoding="utf-8") as fp:
                meta = json.load(fp).get("_meta", {})
            langs[code] = meta.get("language", code.upper())
        except Exception:
            langs[code] = code.upper()
    return langs


def on_language_change(callback):
    """
    Dil değiştiğinde çalıştırılmak üzere bir UI geri çağırma (callback) işlevi kaydeder.
    """
    if callback not in _listeners:
        _listeners.append(callback)
```
