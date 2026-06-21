import os
import json
import locale
from src.core.config import load_config, save_config

class TranslationManager:
    def __init__(self):
        self._listeners = []
        self._current_lang = "tr"
        self._translations = {}
        
        # Load initially
        self.load_from_config()

    def load_from_config(self):
        config = load_config()
        lang = config.get("language")
        
        if not lang:
            # Detect system locale
            try:
                sys_lang, _ = locale.getdefaultlocale()
                if sys_lang and sys_lang.startswith("tr"):
                    lang = "tr"
                else:
                    lang = "en"
            except Exception:
                lang = "tr"
                
        self.set_language(lang, save=False)

    def set_language(self, lang, save=True):
        if lang not in ["tr", "en"]:
            lang = "tr"
            
        self._current_lang = lang
        self._load_translations()
        
        if save:
            config = load_config()
            config["language"] = lang
            save_config(config)
            
        # Notify all listeners
        for listener in list(self._listeners):
            try:
                listener()
            except Exception:
                pass

    def get_language(self):
        return self._current_lang

    def register_listener(self, callback):
        if callback not in self._listeners:
            self._listeners.append(callback)

    def unregister_listener(self, callback):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _load_translations(self):
        # Locate files relative to this file
        locales_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "assets",
            "locales"
        )
        filepath = os.path.join(locales_dir, f"{self._current_lang}.json")
        
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    self._translations = json.load(f)
            except Exception as e:
                print(f"Error loading translation file: {e}")
                self._translations = {}
        else:
            self._translations = {}

    def tr(self, key, **kwargs):
        parts = key.split('.')
        val = self._translations
        for p in parts:
            if isinstance(val, dict) and p in val:
                val = val[p]
            else:
                return key
        
        # If it is a list (e.g. keywords), return it directly
        if isinstance(val, list):
            return val
            
        if not isinstance(val, str):
            return str(val)
            
        try:
            return val.format(**kwargs)
        except Exception:
            return val

# Global instance
translation_manager = TranslationManager()

def tr(key, **kwargs):
    return translation_manager.tr(key, **kwargs)
