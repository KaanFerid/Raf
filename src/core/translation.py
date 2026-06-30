"""
i18n Translation Engine
=======================
Handles localization dictionaries (.json) from the "locales" folder.
Flat format maps sections to keys like 'section.key'.
"""

import json
from pathlib import Path
from src.core.config import load_config, save_config

# Paths to dictionary files (assumes an "assets/locales" folder)
_I18N_DIR = Path(__file__).parent.parent / "assets" / "locales"

# Translation cache
_cache: dict[str, dict] = {}

# Currently active language
_active: str = "en"

# Callbacks to invoke on language change
_listeners: list = []


def _load(lang_code: str) -> dict:
    """
    Loads a language JSON file and flattens it to dot notation.
    """
    # Return from cache if already loaded
    if lang_code in _cache:
        return _cache[lang_code]

    path = _I18N_DIR / f"{lang_code}.json"
    
    # Fallback if file doesn't exist
    if not path.exists():
        print(tr("log.lang_not_found", lang=lang_code, path=path, default=f"[i18n] '{lang_code}' language file not found: {path}"))
        return _cache.get("en", {})

    # Read language file
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception as e:
        print(tr("log.lang_load_error", path=path, error=e, default=f"[i18n] Error loading {path}: {e}"))
        return _cache.get("en", {})

    # Flatten nested dicts to dot notation (e.g. section.key)
    flat: dict[str, str] = {}
    for section, entries in raw.items():
        if section == "_meta" or section == "language_name":
            continue
        if isinstance(entries, dict):
            for key, val in entries.items():
                flat[f"{section}.{key}"] = val
        else:
            flat[section] = str(entries)

    # Cache flattened dict
    _cache[lang_code] = flat
    return flat


def tr(key: str, **kwargs) -> str:
    """
    Returns translated text for a given key, formatting placeholders if kwargs provided.
    """
    data = _load(_active)
    val = data.get(key)

    # Fallback to English if translation is missing in the active language
    if val is None:
        fallback = _load("en")
        val = fallback.get(key, key) # Return key itself if completely missing

    # Format message dynamically if kwargs are passed
    if kwargs:
        try:
            val = val.format(**kwargs)
        except (KeyError, ValueError):
            pass

    return val


def set_language(lang_code: str, save: bool = True) -> bool:
    """
    Switches active language, loads translation dict, and triggers callbacks.
    """
    global _active
    path = _I18N_DIR / f"{lang_code}.json"
    if not path.exists():
        # Fallback to first available language if requested doesn't exist
        available = available_languages()
        if not available:
            return False
        lang_code = "tr" if "tr" in available else list(available.keys())[0]

    _active = lang_code
    _load(lang_code)

    if save:
        config = load_config()
        config["language"] = lang_code
        save_config(config)

    # Notify all listeners to update their UI text
    for cb in _listeners:
        try:
            cb()
        except Exception as e:
            print(tr("log.lang_listener_error", error=e, default=f"[i18n] Listener update error: {e}"))

    return True


def get_language() -> str:
    return _active


def available_languages() -> dict[str, str]:
    """
    Returns map of available languages {"code": "name"}.
    Reads the _meta.language field from all json files.
    """
    langs = {}
    if not _I18N_DIR.exists():
        return langs
        
    # Scan dictionary JSON files
    for f in sorted(_I18N_DIR.glob("*.json")):
        code = f.stem
        try:
            with open(f, "r", encoding="utf-8") as fp:
                raw = json.load(fp)
                meta = raw.get("_meta", {})
                # Support old format where language_name was at root
                name = meta.get("language", raw.get("language_name", code.upper()))
            langs[code] = name
        except Exception:
            langs[code] = code.upper()
            
    # Ensure predictable sort order (tr first if available)
    sorted_keys = sorted(langs.keys())
    if "tr" in langs:
        sorted_keys.remove("tr")
        sorted_keys.insert(0, "tr")
    return {k: langs[k] for k in sorted_keys}


def on_language_change(callback):
    """
    Registers a UI callback to invoke when the language changes.
    """
    if callback not in _listeners:
        _listeners.append(callback)


def remove_language_listener(callback):
    """
    Unregisters a UI callback.
    """
    if callback in _listeners:
        _listeners.remove(callback)


# Initialize the language on module load based on config or system locale
def _init_language():
    config = load_config()
    lang = config.get("language")
    
    if not lang:
        import locale
        try:
            sys_lang, _ = locale.getlocale()
            if sys_lang and sys_lang.startswith("tr"):
                lang = "tr"
            else:
                lang = "en"
        except Exception:
            lang = "tr"
            
    set_language(lang, save=False)

_init_language()


# For backwards compatibility with older files expecting translation_manager
class _TranslationManagerStub:
    def register_listener(self, cb):
        on_language_change(cb)
    def unregister_listener(self, cb):
        remove_language_listener(cb)
    def get_language(self):
        return get_language()
    def get_available_languages(self):
        return available_languages()
    def set_language(self, lang, save=True):
        set_language(lang, save)

translation_manager = _TranslationManagerStub()
