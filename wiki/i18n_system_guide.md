# Lightweight JSON Localization (i18n) Engine

This document explains a highly efficient, zero-dependency localization system designed for Python applications (especially GUI frameworks like PyQt/PySide, Tkinter, or CustomTkinter).

## Overview
Unlike heavy tools such as `gettext` (.mo/.po files) or Qt Linguist (.qm files), this engine uses standard JSON files and requires **no compilation**. It features:

1. **Flat Dot Notation:** Nested JSON objects are flattened (e.g. `map.target_count`), making translation keys easy to read.
2. **Dynamic Formatting:** Supports Python's keyword formatting (e.g., `tr("welcome", name="Alice")`).
3. **Automatic English Fallback:** If a string is missing in the currently active language, it falls back to the default language (English).
4. **Reactive UI Updates:** Provides an Observer pattern (`on_language_change`) so GUI widgets can update their text live without requiring an app restart.

---

## 1. Directory Structure

Create a directory named `i18n/` next to the engine script. Place your JSON language files inside it.

```text
src/
├── i18n_engine.py      # The engine code (provided below)
└── i18n/
    ├── en.json         # Default English dictionary
    └── tr.json         # Turkish dictionary (or any other languages)
```

## 2. Example JSON Dictionary (`en.json`)

Organize keys logically. The engine ignores the `_meta` block, using it only for language names.

```json
{
  "_meta": {
    "language": "English",
    "code": "en"
  },
  "main": {
    "title": "My Application",
    "welcome": "Welcome back, {user}!",
    "status": "System is {status}"
  },
  "buttons": {
    "save": "Save Changes",
    "cancel": "Cancel"
  }
}
```

## 3. How to use it in code

### Basic String Translation
```python
from i18n_engine import tr, set_language

# Set active language
set_language("en")

# Basic lookup
print(tr("buttons.save"))  # Output: Save Changes

# Lookup with dynamic variables
print(tr("main.welcome", user="John"))  # Output: Welcome back, John!
```

### Reactive GUI Usage (Live Language Switching)
In a GUI application, you want the UI to update immediately when the user changes the language setting.

```python
from i18n_engine import tr, on_language_change

class SettingsWindow:
    def __init__(self):
        self.save_button = Button()
        self.welcome_label = Label()
        
        # Register the callback to automatically trigger on language change
        on_language_change(self._update_texts)
        
        # Call it once manually to set initial text
        self._update_texts()

    def _update_texts(self, *args):
        # This function updates all UI text.
        # It is fired automatically whenever set_language() is called elsewhere.
        self.save_button.text = tr("buttons.save")
        self.welcome_label.text = tr("main.welcome", user="John")
```

---

## 4. The Engine Code (`i18n_engine.py`)

Copy and paste the following code into your project to implement the engine.

```python
"""
i18n Translation Engine
=======================
Handles localization dictionaries (.json) from the "i18n" folder.
Flat format maps sections to keys like 'section.key'.
"""

import json
from pathlib import Path

# Paths to dictionary files (assumes an "i18n" folder next to this file)
_I18N_DIR = Path(__file__).parent / "i18n"

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
        print(f"[i18n] '{lang_code}' language file not found: {path}")
        return _cache.get("en", {})

    # Read language file
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # Flatten nested dicts to dot notation (e.g. section.key)
    flat: dict[str, str] = {}
    for section, entries in raw.items():
        if section == "_meta":
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


def set_language(lang_code: str) -> bool:
    """
    Switches active language, loads translation dict, and triggers callbacks.
    """
    global _active
    path = _I18N_DIR / f"{lang_code}.json"
    if not path.exists():
        print(f"[i18n] Language file not found: {path}")
        return False

    _active = lang_code
    _load(lang_code)

    # Notify all listeners to update their UI text
    for cb in _listeners:
        try:
            cb(lang_code)
        except Exception as e:
            print(f"[i18n] Listener update error: {e}")

    return True


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
                meta = json.load(fp).get("_meta", {})
            langs[code] = meta.get("language", code.upper())
        except Exception:
            langs[code] = code.upper()
    return langs


def on_language_change(callback):
    """
    Registers a UI callback to invoke when the language changes.
    """
    if callback not in _listeners:
        _listeners.append(callback)
```
