import os
import subprocess
import shutil
from gi.repository import Gtk, Adw
from src.core.translation import tr, set_language, available_languages
from src.core.config import load_config, save_config

def get_disk_info():
    if os.environ.get("RAF_DEV") == "1":
        path = os.path.abspath(os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "mock_system"
        ))
    else:
        path = os.path.expanduser("~")
        
    try:
        total, used, free = shutil.disk_usage(path)
        free_gb = free / (1024**3)
        total_gb = total / (1024**3)
        return tr("ui.system_free_space", free=f"{free_gb:.1f}", total=f"{total_gb:.1f}")
    except Exception:
        return tr("ui.disk_space_unknown")

def get_cache_size():
    if os.environ.get("RAF_DEV") == "1":
        cache_dir = os.path.abspath(os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "mock_system",
            "cache"
        ))
    else:
        cache_dir = os.path.expanduser("~/.cache/raf/downloads")
        
    if not os.path.exists(cache_dir):
        return tr("ui.cache_size_zero")
        
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(cache_dir):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        size_mb = total_size / (1024 * 1024)
        return tr("ui.download_cache_size", size=f"{size_mb:.1f}")
    except Exception:
        return tr("ui.cache_size_unknown")


class PreferencesWindow(Adw.PreferencesWindow):
    def __init__(self, parent=None):
        super().__init__(transient_for=parent)
        self.set_title(tr("ui.preferences"))
        self.set_default_size(450, 500)
        self.set_decorated(False)
        
        self.config = load_config()
        self.init_ui()
        
    def init_ui(self):
        page = Adw.PreferencesPage()
        self.add(page)
        
        # --- Appearance Group ---
        appearance_group = Adw.PreferencesGroup(title=tr("ui.appearance"))
        page.add(appearance_group)
        
        self.theme_combo = Adw.ComboRow(title=tr("ui.appearance"))
        theme_model = Gtk.StringList.new([tr("ui.system_theme"), tr("ui.light_theme"), tr("ui.dark_theme")])
        self.theme_combo.set_model(theme_model)
        
        mode = self.config.get("theme_mode", "system")
        if mode == "system": self.theme_combo.set_selected(0)
        elif mode == "light": self.theme_combo.set_selected(1)
        elif mode == "dark": self.theme_combo.set_selected(2)
        
        self.theme_combo.connect("notify::selected", self.on_theme_changed)
        appearance_group.add(self.theme_combo)
        
        # --- Language Group ---
        lang_group = Adw.PreferencesGroup(title=tr("ui.language"))
        page.add(lang_group)
        
        self.lang_combo = Adw.ComboRow(title=tr("ui.language"))
        self.langs = list(available_languages().items())
        lang_model = Gtk.StringList.new([name for code, name in self.langs])
        self.lang_combo.set_model(lang_model)
        
        current_lang = self.config.get("language", "tr")
        for i, (code, name) in enumerate(self.langs):
            if code == current_lang:
                self.lang_combo.set_selected(i)
                break
                
        self.lang_combo.connect("notify::selected", self.on_language_changed)
        lang_group.add(self.lang_combo)
        
        # --- Storage Group ---
        storage_group = Adw.PreferencesGroup(title=tr("ui.system_and_cache"))
        page.add(storage_group)
        
        self.disk_row = Adw.ActionRow(title=get_disk_info())
        storage_group.add(self.disk_row)
        
        self.cache_row = Adw.ActionRow(title=get_cache_size())
        clear_btn = Gtk.Button(label=tr("ui.clear_cache"), valign=Gtk.Align.CENTER)
        clear_btn.add_css_class("destructive-action")
        clear_btn.connect("clicked", self.clear_cache)
        self.cache_row.add_suffix(clear_btn)
        storage_group.add(self.cache_row)
        
        # --- Update Policy Group ---
        update_group = Adw.PreferencesGroup(title=tr("ui.auto_update"))
        page.add(update_group)
        
        self.update_combo = Adw.ComboRow(title=tr("ui.auto_update"))
        update_model = Gtk.StringList.new([tr("ui.update_policy_manual"), tr("ui.update_policy_check"), tr("ui.update_policy_auto")])
        self.update_combo.set_model(update_model)
        
        policy = self.config.get("auto_update_policy", "check")
        if policy == "off": self.update_combo.set_selected(0)
        elif policy == "check": self.update_combo.set_selected(1)
        elif policy == "auto": self.update_combo.set_selected(2)
        
        self.update_combo.connect("notify::selected", self.on_update_changed)
        update_group.add(self.update_combo)

        # --- Database Group ---
        db_group = Adw.PreferencesGroup(title=tr("ui.database_url"))
        page.add(db_group)
        
        self.db_entry = Adw.EntryRow(title=tr("ui.database_url_hint"))
        self.db_entry.set_text(self.config.get("database_url", ""))
        self.db_entry.connect("changed", self.on_db_changed)
        db_group.add(self.db_entry)

    def on_theme_changed(self, combo, pspec):
        idx = combo.get_selected()
        modes = ["system", "light", "dark"]
        self.config["theme_mode"] = modes[idx]
        save_config(self.config)
        
        manager = Adw.StyleManager.get_default()
        if modes[idx] == "system": manager.set_color_scheme(Adw.ColorScheme.DEFAULT)
        elif modes[idx] == "light": manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
        elif modes[idx] == "dark": manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)

    def on_language_changed(self, combo, pspec):
        idx = combo.get_selected()
        lang_code = self.langs[idx][0]
        self.config["language"] = lang_code
        save_config(self.config)
        set_language(lang_code)

    def on_update_changed(self, combo, pspec):
        idx = combo.get_selected()
        policies = ["off", "check", "auto"]
        self.config["auto_update_policy"] = policies[idx]
        save_config(self.config)

    def on_db_changed(self, entry):
        self.config["database_url"] = entry.get_text().strip()
        save_config(self.config)

    def clear_cache(self, btn):
        if os.environ.get("RAF_DEV") == "1":
            cache_dir = os.path.abspath(os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "mock_system",
                "cache"
            ))
        else:
            cache_dir = os.path.expanduser("~/.cache/raf/downloads")
            
        if os.path.exists(cache_dir):
            try:
                for f in os.listdir(cache_dir):
                    file_path = os.path.join(cache_dir, f)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                
                from src.ui.desktop_editor import show_message
                show_message(self, tr("ui.success"), tr("ui.cache_clear_success"))
                self.cache_row.set_title(get_cache_size())
                self.disk_row.set_title(get_disk_info())
            except Exception as e:
                from src.ui.desktop_editor import show_message
                show_message(self, tr("ui.error"), tr("ui.cache_clear_error", error=str(e)), type="error")
