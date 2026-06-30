import os
import subprocess
import re
from src.qt_compat import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QLineEdit, QComboBox, QScrollArea, 
                            QMessageBox, QStatusBar, QSizePolicy, QPushButton, 
                            QProgressBar, QFrame, Qt, QTimer, QDialog, 
                            QButtonGroup, QRadioButton, QGroupBox, QEvent, QApplication,
                            QIcon, QPixmap, QPen, QColor, QPainter, QFileDialog)
from src.ui.styles import LIGHT_STYLE, DARK_STYLE
from src.ui.components import BookCard
from src.ui.toast import ToastManager
from src.core.database import Database
from src.core.downloader import DownloadWorker
from src.core.installer import InstallerWorker, is_book_installed, get_deb_package_name, get_all_installed_packages
from src.core.translation import tr, set_language, available_languages, on_language_change, remove_language_listener
from src.core.config import load_config, save_config
from src.core.updater import UpdateChecker, UpdateInstaller, AutoUpdateScheduler
from src.core.download_queue import DownloadQueue
from src.core.sync import DatabaseSyncWorker
from src.core.version import __version__ as APP_VERSION
from src.ui.logs_dialog import InstallationLogsDialog
from PyQt5.QtCore import QThread, pyqtSignal

class PackageQueryWorker(QThread):
    packages_loaded = pyqtSignal(set)
    def run(self):
        from src.core.installer import get_all_installed_packages
        self.packages_loaded.emit(get_all_installed_packages())



def set_linux_dark_titlebar(window, dark=True):
    """Signals the Linux window manager to draw window decorations in dark or light mode using _GTK_THEME_VARIANT."""
    if os.name != "posix":
        return
    try:
        win_id = window.winId()
        if win_id:
            variant = "dark" if dark else "light"
            subprocess.Popen(
                ["xprop", "-id", str(int(win_id)), "-f", "_GTK_THEME_VARIANT", "8u", "-set", "_GTK_THEME_VARIANT", variant],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
    except Exception:
        pass


class PreferencesDialog(QDialog):
    """Preferences window styled in Adwaita format for theme configuration."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(380, 430)
        self.init_ui()
        
    def init_ui(self):
        self.config = load_config()
        current_mode = self.config.get("theme_mode", "system")
        current_lang = self.config.get("language", "tr")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Appearance setting frame
        self.appearance_group = QGroupBox()
        group_layout = QVBoxLayout(self.appearance_group)
        group_layout.setContentsMargins(15, 12, 15, 12)
        group_layout.setSpacing(8)
        
        self.radio_system = QRadioButton()
        self.radio_light = QRadioButton()
        self.radio_dark = QRadioButton()
        
        if current_mode == "system":
            self.radio_system.setChecked(True)
        elif current_mode == "light":
            self.radio_light.setChecked(True)
        elif current_mode == "dark":
            self.radio_dark.setChecked(True)
            
        group_layout.addWidget(self.radio_system)
        group_layout.addWidget(self.radio_light)
        group_layout.addWidget(self.radio_dark)
        
        layout.addWidget(self.appearance_group)
        
        # Language setting frame
        self.lang_group = QGroupBox()
        lang_layout = QVBoxLayout(self.lang_group)
        lang_layout.setContentsMargins(15, 12, 15, 12)
        lang_layout.setSpacing(8)
        
        self.lang_combo = QComboBox()
        available_langs = available_languages()
        
        selected_index = 0
        for idx, (lang_code, display_name) in enumerate(available_langs.items()):
            self.lang_combo.addItem(display_name, lang_code)
            if lang_code == current_lang:
                selected_index = idx
                
        self.lang_combo.setCurrentIndex(selected_index)
            
        lang_layout.addWidget(self.lang_combo)
        layout.addWidget(self.lang_group)
        
        # Disk Info Box
        self.disk_group = QGroupBox()
        disk_layout = QVBoxLayout(self.disk_group)
        disk_layout.setContentsMargins(15, 12, 15, 12)
        disk_layout.setSpacing(8)
        
        self.disk_label = QLabel()
        self.disk_label.setObjectName("DiskInfoLabel")
        
        self.cache_label = QLabel()
        self.cache_label.setObjectName("CacheInfoLabel")
        
        self.clear_btn = QPushButton()
        self.clear_btn.setProperty("class", "AdwSecondaryBtn")
        self.clear_btn.clicked.connect(self.clear_cache)
        
        disk_layout.addWidget(self.disk_label)
        disk_layout.addWidget(self.cache_label)
        disk_layout.addWidget(self.clear_btn)
        
        layout.addWidget(self.disk_group)
        
        # Actions
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        
        self.cancel_btn = QPushButton()
        self.cancel_btn.setProperty("class", "AdwSecondaryBtn")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.save_btn = QPushButton()
        self.save_btn.setProperty("class", "AdwPrimaryBtn")
        self.save_btn.clicked.connect(self.save_preferences)
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)
        
        # Database URL setting
        self.db_group = QGroupBox()
        db_layout = QVBoxLayout(self.db_group)
        db_layout.setContentsMargins(15, 12, 15, 12)
        db_layout.setSpacing(6)

        self.db_url_hint = QLabel()
        self.db_url_hint.setObjectName("DiskInfoLabel")
        db_layout.addWidget(self.db_url_hint)

        self.db_url_field = QLineEdit()
        self.db_url_field.setObjectName("DatabaseUrlField")
        self.db_url_field.setText(self.config.get("database_url", ""))
        db_layout.addWidget(self.db_url_field)
        layout.addWidget(self.db_group)

        # Auto-update policy setting
        self.update_group = QGroupBox()
        update_layout = QVBoxLayout(self.update_group)
        update_layout.setContentsMargins(15, 12, 15, 12)
        update_layout.setSpacing(8)

        self.radio_update_manual = QRadioButton()
        self.radio_update_check = QRadioButton()
        self.radio_update_auto = QRadioButton()

        current_policy = self.config.get("auto_update_policy", "check")
        if current_policy == "off":
            self.radio_update_manual.setChecked(True)
        elif current_policy == "auto":
            self.radio_update_auto.setChecked(True)
        else:
            self.radio_update_check.setChecked(True)

        update_layout.addWidget(self.radio_update_manual)
        update_layout.addWidget(self.radio_update_check)
        update_layout.addWidget(self.radio_update_auto)
        layout.addWidget(self.update_group)

        # Save/Cancel buttons below new groups
        layout.addLayout(button_layout)
        
        # Localize strings
        self.retranslate_ui()
        
        # Synchronize dialog styling with main window style
        if self.parent():
            self.setStyleSheet(self.parent().styleSheet())
            is_dark = getattr(self.parent(), "current_theme", "light") == "dark"
            set_linux_dark_titlebar(self, is_dark)
            
    def retranslate_ui(self):
        self.setWindowTitle(tr("ui.preferences"))
        self.appearance_group.setTitle(tr("ui.appearance"))
        self.radio_system.setText(tr("ui.system_theme"))
        self.radio_light.setText(tr("ui.light_theme"))
        self.radio_dark.setText(tr("ui.dark_theme"))
        self.lang_group.setTitle(tr("ui.language"))
        self.disk_group.setTitle(tr("ui.system_and_cache"))
        self.clear_btn.setText(tr("ui.clear_cache"))
        self.cancel_btn.setText(tr("ui.cancel"))
        self.save_btn.setText(tr("ui.save"))
        self.disk_label.setText(self.get_disk_info())
        self.cache_label.setText(self.get_cache_size())
        self.db_group.setTitle(tr("ui.database_url"))
        self.db_url_hint.setText(tr("ui.database_url_hint"))
        self.update_group.setTitle(tr("ui.auto_update"))
        self.radio_update_manual.setText(tr("ui.update_policy_manual"))
        self.radio_update_check.setText(tr("ui.update_policy_check"))
        self.radio_update_auto.setText(tr("ui.update_policy_auto"))
        self.adjustSize()

    def get_disk_info(self):
        if os.environ.get("RAF_DEV") == "1":
            path = os.path.abspath(os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "mock_system"
            ))
        else:
            path = os.path.expanduser("~")
            
        try:
            import shutil
            total, used, free = shutil.disk_usage(path)
            free_gb = free / (1024**3)
            total_gb = total / (1024**3)
            return tr("ui.system_free_space", free=f"{free_gb:.1f}", total=f"{total_gb:.1f}")
        except Exception:
            return tr("ui.disk_space_unknown")

    def get_cache_size(self):
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

    def clear_cache(self):
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
                QMessageBox.information(self, tr("ui.success"), tr("ui.cache_clear_success"))
                self.cache_label.setText(self.get_cache_size())
                self.disk_label.setText(self.get_disk_info())
            except Exception as e:
                QMessageBox.warning(self, tr("ui.error"), tr("ui.cache_clear_error", error=str(e)))

    def save_preferences(self):
        if self.radio_system.isChecked():
            mode = "system"
        elif self.radio_light.isChecked():
            mode = "light"
        elif self.radio_dark.isChecked():
            mode = "dark"
            
        self.config["theme_mode"] = mode
        
        # Save active language
        selected_lang = self.lang_combo.currentData()
        self.config["language"] = selected_lang

        # Save database URL
        self.config["database_url"] = self.db_url_field.text().strip()

        # Save auto-update policy
        if self.radio_update_manual.isChecked():
            self.config["auto_update_policy"] = "off"
        elif self.radio_update_auto.isChecked():
            self.config["auto_update_policy"] = "auto"
        else:
            self.config["auto_update_policy"] = "check"

        save_config(self.config)
        
        # Notify dynamic language switch
        set_language(selected_lang)
        
        self.accept()

    def showEvent(self, event):
        super().showEvent(event)
        is_dark = False
        if self.parent() and hasattr(self.parent(), "current_theme"):
            is_dark = self.parent().current_theme == "dark"
        set_linux_dark_titlebar(self, is_dark)


class MainWindow(QMainWindow):
    def __init__(self, startup_files=None):
        super().__init__()
        self.startup_files = startup_files or []
        self.resize(1100, 700)
        self.setMinimumSize(1080, 550)
        
        # Theme configuration variables
        self.current_theme = None
        self.theme_timer = QTimer(self)
        self.theme_timer.timeout.connect(self.check_system_theme_update)
        
        # Search debouncing
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.refresh_grid)
        
        # Core components
        print(tr("log.loading_db"))
        self.db = Database()
        print(tr("log.db_loaded", count=len(self.db.get_all_books())))
        
        # State tracking
        self.active_downloads = {}      # book_id -> DownloadWorker
        self.active_installations = {}  # book_id -> InstallerWorker
        self.logs_dialog = InstallationLogsDialog(self)
        self.card_widgets = {}          # book_id -> BookCard
        self._selection_mode = False    # Batch selection mode active
        self._selected_books = set()    # book_ids selected in batch mode
        
        # Network state
        self.is_offline = False
        self.check_network_status()
        
        self.installed_packages_cache = None
        
        self.init_ui()
        self.update_theme()
        
        # Enable drag and drop for sideloading apps
        self.setAcceptDrops(True)

        # Toast notification manager (must be after init_ui so parent window exists)
        self.toast_manager = ToastManager(self)

        # Download queue (max 2 concurrent downloads)
        self.download_queue = DownloadQueue(max_concurrent=2, parent=self)
        self.download_queue.job_started.connect(self._on_queue_job_started)
        self.download_queue.queue_changed.connect(self._on_queue_changed)
        
        # Auto-update scheduler
        self.auto_update_scheduler = AutoUpdateScheduler(self)
        self.auto_update_scheduler.update_toast_requested.connect(self._on_update_toast)
        self.auto_update_scheduler.auto_install_requested.connect(self.on_update_available)
        self.auto_update_scheduler.start()

        # Remote database sync (auto-sync default to GitHub repo)
        config = load_config()
        db_url = config.get("database_url", "").strip()
        if not db_url:
            db_url = "https://raw.githubusercontent.com/KaanFerid/Raf/main/database/"
            
        if db_url and not self.is_offline:
            self.sync_worker = DatabaseSyncWorker(db_url, self.db.database_dir, parent=self)
            self.sync_worker.sync_finished.connect(self._on_sync_finished)
            self.sync_worker.sync_failed.connect(self._on_sync_failed)
            self.sync_worker.start()
            
        # Start async package query
        self.refresh_packages_cache()
        
        # Periodically refresh installation status of displayed items
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_all_statuses)
        self.refresh_timer.start(15000)
        
        # Register translation change listener
        on_language_change(self.retranslate_ui)
        
        # Process any files passed from CLI (Open With)
        if self.startup_files:
            QTimer.singleShot(500, lambda: self.process_local_files(self.startup_files))

    def closeEvent(self, event):
        # Unregister translation listener to prevent memory leaks
        remove_language_listener(self.retranslate_ui)
        super().closeEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        is_dark = self.current_theme == "dark"
        set_linux_dark_titlebar(self, is_dark)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'drop_overlay') and self.centralWidget():
            self.drop_overlay.setGeometry(0, 0, self.centralWidget().width(), self.centralWidget().height())

    def get_system_theme(self):
        """Checks the system preferred theme using standard D-Bus / desktop portal interface."""
        try:
            res = subprocess.run([
                "dbus-send", "--print-reply", 
                "--dest=org.freedesktop.portal.Desktop", 
                "/org/freedesktop/portal/desktop", 
                "org.freedesktop.portal.Settings.Read", 
                "string:org.freedesktop.appearance", 
                "string:color-scheme"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=1)
            if res.returncode == 0:
                match = re.search(r"uint32\s+(\d+)", res.stdout)
                if match:
                    val = int(match.group(1))
                    if val == 1:
                        return "dark"
                    elif val == 2:
                        return "light"
        except Exception:
            pass

        # Gsettings fallback for GNOME
        try:
            res = subprocess.run([
                "gsettings", "get", 
                "org.gnome.desktop.interface", "color-scheme"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=1)
            if res.returncode == 0:
                val = res.stdout.strip().strip("'")
                if "dark" in val:
                    return "dark"
                else:
                    return "light"
        except Exception:
            pass

        return "light"

    def update_theme(self):
        """Loads preference config and sets light/dark stylesheet layout repainting."""
        config = load_config()
        mode = config.get("theme_mode", "system")
        
        if mode == "system":
            theme = self.get_system_theme()
            if not self.theme_timer.isActive():
                self.theme_timer.start(4000) # check every 4 seconds
        else:
            theme = mode
            self.theme_timer.stop()
            
        if theme == "dark":
            self.setStyleSheet(DARK_STYLE)
            self.current_theme = "dark"
            set_linux_dark_titlebar(self, True)
        else:
            self.setStyleSheet(LIGHT_STYLE)
            self.current_theme = "light"
            set_linux_dark_titlebar(self, False)
            
        # Refresh child widgets style
        for card in self.card_widgets.values():
            card.style().unpolish(card)
            card.style().polish(card)
            card.status_label.style().unpolish(card.status_label)
            card.status_label.style().polish(card.status_label)
            card.primary_btn.style().unpolish(card.primary_btn)
            card.primary_btn.style().polish(card.primary_btn)
            card.secondary_btn.style().unpolish(card.secondary_btn)
            card.secondary_btn.style().polish(card.secondary_btn)

    def check_system_theme_update(self):
        """Automatic system theme monitor callback."""
        config = load_config()
        if config.get("theme_mode", "system") != "system":
            return
            
        theme = self.get_system_theme()
        if theme != self.current_theme:
            self.update_theme()

    def init_ui(self):
        central_widget = QWidget()
        central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Header Area Widget (Adwaita flat header bar)
        header_widget = QWidget()
        header_widget.setObjectName("HeaderWidget")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(16)

        # App branding Title
        self.app_title_label = QLabel()
        self.app_title_label.setObjectName("AppTitleLabel")
        self.app_title_label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        header_layout.addWidget(self.app_title_label)

        # Queue badge (shown when items are queued)
        self.queue_badge = QLabel()
        self.queue_badge.setObjectName("QueueBadge")
        self.queue_badge.setVisible(False)
        header_layout.addWidget(self.queue_badge)

        # Select mode toggle
        self.select_mode_btn = QPushButton()
        self.select_mode_btn.setObjectName("SelectModeBtn")
        self.select_mode_btn.setCheckable(True)
        self.select_mode_btn.clicked.connect(self.toggle_selection_mode)
        header_layout.addWidget(self.select_mode_btn)

        header_layout.addStretch(1)

        # Search Bar input field (Centered)
        self.search_input = QLineEdit()
        self.search_input.setMinimumWidth(150)
        self.search_input.setMaximumWidth(250)
        self.search_input.textChanged.connect(self.on_search_changed)
        self.search_input.installEventFilter(self) # Intercept focus events for keyboard trigger
        # Add custom drawn clean search icon to avoid Unicode rendering issues on Pardus
        self.search_input.addAction(self.create_search_icon(), QLineEdit.LeadingPosition)
        header_layout.addWidget(self.search_input)

        header_layout.addStretch(1)

        # Right segmented control (View Switcher - Adwaita style)
        switcher_container = QWidget()
        switcher_container.setObjectName("ViewSwitcherContainer")
        switcher_container.setMinimumWidth(200)
        switcher_layout = QHBoxLayout(switcher_container)
        switcher_layout.setContentsMargins(0, 0, 0, 0)
        switcher_layout.setSpacing(0)

        self.tab_market_btn = QPushButton()
        self.tab_market_btn.setCheckable(True)
        self.tab_market_btn.setChecked(True)
        self.tab_market_btn.setProperty("class", "ViewSwitcherBtn")
        self.tab_market_btn.setMinimumWidth(80)

        self.tab_library_btn = QPushButton()
        self.tab_library_btn.setCheckable(True)
        self.tab_library_btn.setProperty("class", "ViewSwitcherBtn")
        self.tab_library_btn.setMinimumWidth(110)

        self.tab_group = QButtonGroup(self)
        self.tab_group.addButton(self.tab_market_btn)
        self.tab_group.addButton(self.tab_library_btn)
        self.tab_group.setExclusive(True)
        
        self.tab_market_btn.clicked.connect(self.on_tab_changed)
        self.tab_library_btn.clicked.connect(self.on_tab_changed)

        switcher_layout.addWidget(self.tab_market_btn)
        switcher_layout.addWidget(self.tab_library_btn)
        header_layout.addWidget(switcher_container)

        # Install Local File Button
        self.install_local_btn = QPushButton(tr("ui.install_local_files"))
        self.install_local_btn.setProperty("class", "AdwSecondaryBtn")
        self.install_local_btn.clicked.connect(self.on_install_local_clicked)
        header_layout.addWidget(self.install_local_btn)

        # Settings/Preferences Button
        self.settings_btn = QPushButton()
        self.settings_btn.setProperty("class", "AdwSecondaryBtn")
        self.settings_btn.clicked.connect(self.open_preferences)
        header_layout.addWidget(self.settings_btn)

        # About Button
        self.about_btn = QPushButton()
        self.about_btn.setProperty("class", "AdwSecondaryBtn")
        self.about_btn.clicked.connect(self.show_about_dialog)
        header_layout.addWidget(self.about_btn)

        self.logs_btn = QPushButton()
        self.logs_btn.setProperty("class", "AdwSecondaryBtn")
        self.logs_btn.clicked.connect(self.logs_dialog.show)
        header_layout.addWidget(self.logs_btn)

        main_layout.addWidget(header_widget)

        # 2. Count Label
        self.count_label = QLabel("")
        self.count_label.setObjectName("CountLabel")
        self.count_label.setContentsMargins(20, 8, 20, 8)
        main_layout.addWidget(self.count_label)

        # 3. Content Scroll Area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("ScrollContent")
        
        # List layout for books (Vertical List instead of Grid)
        self.list_layout = QVBoxLayout(self.scroll_content)
        self.list_layout.setContentsMargins(20, 8, 20, 20)
        self.list_layout.setSpacing(10)
        self.list_layout.setAlignment(Qt.AlignTop)
        
        # Empty library / search placeholder state
        self.placeholder_widget = QWidget()
        placeholder_layout = QVBoxLayout(self.placeholder_widget)
        placeholder_layout.setContentsMargins(40, 80, 40, 80)
        placeholder_layout.setAlignment(Qt.AlignCenter)
        
        self.placeholder_label = QLabel()
        self.placeholder_label.setObjectName("PlaceholderLabel")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        placeholder_layout.addWidget(self.placeholder_label)
        
        self.list_layout.addWidget(self.placeholder_widget)
        self.placeholder_widget.hide()
        
        scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(scroll_area, 1)

        # 4. Batch action bar (floats above status bar, hidden by default)
        self.batch_bar = QWidget()
        self.batch_bar.setObjectName("BatchBar")
        self.batch_bar.setVisible(False)
        batch_layout = QHBoxLayout(self.batch_bar)
        batch_layout.setContentsMargins(16, 8, 16, 8)
        batch_layout.setSpacing(10)

        self.batch_count_label = QLabel()
        self.batch_count_label.setObjectName("BatchCountLabel")
        batch_layout.addWidget(self.batch_count_label)
        batch_layout.addStretch(1)

        self.batch_install_btn = QPushButton()
        self.batch_install_btn.setProperty("class", "BatchActionBtn")
        self.batch_install_btn.clicked.connect(self.install_selected)
        batch_layout.addWidget(self.batch_install_btn)

        self.batch_uninstall_btn = QPushButton()
        self.batch_uninstall_btn.setProperty("class", "BatchActionBtn")
        self.batch_uninstall_btn.clicked.connect(self.uninstall_selected)
        batch_layout.addWidget(self.batch_uninstall_btn)

        self.batch_done_btn = QPushButton("✕")
        self.batch_done_btn.setProperty("class", "BatchCancelBtn")
        self.batch_done_btn.clicked.connect(lambda: self.toggle_selection_mode(False))
        batch_layout.addWidget(self.batch_done_btn)

        main_layout.addWidget(self.batch_bar)

        # Drop overlay
        self.drop_overlay = QLabel(central_widget)
        self.drop_overlay.setObjectName("DropOverlay")
        self.drop_overlay.setAlignment(Qt.AlignCenter)
        self.drop_overlay.setStyleSheet("""
            QLabel#DropOverlay {
                background-color: rgba(52, 152, 219, 0.8);
                color: white;
                font-size: 24px;
                font-weight: bold;
                border: 4px dashed white;
                border-radius: 12px;
            }
        """)
        self.drop_overlay.hide()

        # 5. Status Bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        self.offline_badge = QLabel()
        self.offline_badge.setObjectName("OfflineBadge")
        self.offline_badge.setVisible(self.is_offline)
        self.statusBar.addPermanentWidget(self.offline_badge)
        
        # Localize strings initially
        self.retranslate_ui()

    def retranslate_ui(self):
        self.setWindowTitle(tr("ui.app_title"))
        self.app_title_label.setText(tr("ui.app_title"))
        self.tab_market_btn.setText(tr("ui.market"))
        self.tab_library_btn.setText(tr("ui.my_library"))
        self.search_input.setPlaceholderText(tr("ui.search_placeholder"))
        self.settings_btn.setText(tr("ui.preferences"))
        self.about_btn.setText(tr("ui.about_menu"))
        self.logs_btn.setText(tr("ui.logs_menu", default="Logs"))
        self.select_mode_btn.setText(tr("ui.select_mode"))
        self.batch_install_btn.setText(tr("ui.install_selected"))
        self.batch_uninstall_btn.setText(tr("ui.uninstall_selected"))
        self.install_local_btn.setText(tr("ui.install_local_files"))
        self.drop_overlay.setText(tr("ui.drop_files_here"))
        
        self.offline_badge.setText(tr("ui.offline_mode"))
        self.statusBar.showMessage(tr("ui.ready"))
        
        # Refresh dynamic strings in placeholder labels and grid cards
        self.refresh_grid()
        for card in self.card_widgets.values():
            card.retranslate_ui(is_offline=self.is_offline)

    # ------------------------------------------------------------------
    # Title Bar Progress
    # ------------------------------------------------------------------

    def _update_title_progress(self):
        """Updates the window title to show aggregate download progress."""
        active = {bid: w for bid, w in self.active_downloads.items()}
        if not active:
            self.setWindowTitle(tr("ui.app_title"))
            return
        percents = [w.last_percent for w in active.values()]
        avg = sum(percents) // len(percents) if percents else 0
        if len(active) == 1:
            book_id = next(iter(active))
            card = self.card_widgets.get(book_id)
            title_str = card.book['title'] if card else book_id
            self.setWindowTitle(f"[\u25bc {title_str} \u2014 {avg}%] {tr('ui.app_title')}")
        else:
            self.setWindowTitle(f"[\u25bc {len(active)} {tr('ui.downloads')} \u2014 {avg}%] {tr('ui.app_title')}")

    # ------------------------------------------------------------------
    # Download Queue Handlers
    # ------------------------------------------------------------------

    def _on_queue_job_started(self, book_id):
        """Called by the queue when a pending job is promoted to active."""
        job = self.download_queue._last_started
        if job:
            book, local_path = job
            self.download_queue.on_download_started(book_id)
            self.start_download(book, local_path)

    def _on_queue_changed(self, pending_count):
        """Updates the queue badge in the header."""
        if pending_count > 0:
            self.queue_badge.setText(tr("ui.queue_count", count=pending_count))
            self.queue_badge.setVisible(True)
        else:
            self.queue_badge.setVisible(False)

    # ------------------------------------------------------------------
    # Remote Database Sync Handlers
    # ------------------------------------------------------------------

    def _on_sync_finished(self, count):
        """Called when the remote database sync succeeds."""
        self.db.load_books()
        self.refresh_grid()
        self.toast_manager.show_toast(tr("ui.sync_success", count=count), "success")

    def _on_sync_failed(self, error):
        """Called when the remote database sync fails (silent — local cache is used)."""
        print(f"Database sync failed: {error}")

    # ------------------------------------------------------------------
    # Auto-update Scheduler Handlers
    # ------------------------------------------------------------------

    def _on_update_toast(self, version):
        """Shows a toast notification when the auto-update scheduler finds an update."""
        self.toast_manager.show_toast(
            tr("ui.toast_update_available", version=version),
            "info",
            duration=8000
        )

    # ------------------------------------------------------------------
    # Batch Selection Mode
    # ------------------------------------------------------------------

    def toggle_selection_mode(self, active=None):
        """Enters or exits batch selection mode."""
        if active is None:
            active = self.select_mode_btn.isChecked()
        else:
            self.select_mode_btn.setChecked(active)

        self._selection_mode = active
        self._selected_books.clear()

        for card in self.card_widgets.values():
            card.set_selection_mode(active)
            if active:
                card.selection_changed.connect(self._on_card_selection_changed)
            else:
                try:
                    card.selection_changed.disconnect(self._on_card_selection_changed)
                except Exception:
                    pass

        self.batch_bar.setVisible(active)
        self._update_batch_bar()

    def _on_card_selection_changed(self, book_id, is_selected):
        """Tracks selected books for batch operations."""
        if is_selected:
            self._selected_books.add(book_id)
        else:
            self._selected_books.discard(book_id)
        self._update_batch_bar()

    def _update_batch_bar(self):
        """Updates the batch action bar count and button states."""
        count = len(self._selected_books)
        self.batch_count_label.setText(tr("ui.selected_count", count=count))

        books = self.db.get_all_books()
        book_map = {b['id']: b for b in books}

        has_uninstalled = any(
            not self.card_widgets[bid].is_installed
            for bid in self._selected_books
            if bid in self.card_widgets
        )
        has_installed = any(
            self.card_widgets[bid].is_installed
            for bid in self._selected_books
            if bid in self.card_widgets
        )

        self.batch_install_btn.setEnabled(count > 0 and has_uninstalled and not self.is_offline)
        self.batch_uninstall_btn.setEnabled(count > 0 and has_installed)

    def install_selected(self):
        """Queues downloads for all selected uninstalled books."""
        books = self.db.get_all_books()
        book_map = {b['id']: b for b in books}
        queued = 0
        for book_id in list(self._selected_books):
            card = self.card_widgets.get(book_id)
            if card and not card.is_installed and not card.downloading and not card.is_queued:
                book = book_map.get(book_id)
                if book:
                    self._enqueue_book(book)
                    queued += 1
        if queued:
            self.toast_manager.show_toast(
                tr("ui.batch_queued", count=queued), "info"
            )
        self.toggle_selection_mode(False)

    def uninstall_selected(self):
        """Confirms and uninstalls all selected installed books."""
        installed_ids = [
            bid for bid in self._selected_books
            if bid in self.card_widgets and self.card_widgets[bid].is_installed
        ]
        if not installed_ids:
            return
        count = len(installed_ids)
        reply = QMessageBox.question(
            self,
            tr("ui.uninstall_library_title"),
            tr("ui.batch_confirm_uninstall", count=count),
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            books = self.db.get_all_books()
            book_map = {b['id']: b for b in books}
            for book_id in installed_ids:
                book = book_map.get(book_id)
                if book:
                    card = self.card_widgets.get(book_id)
                    if card:
                        card.uninstall_requested.emit(book)
        self.toggle_selection_mode(False)

    def _enqueue_book(self, book):
        """Resolves the local path and adds the book to the download queue."""
        if os.environ.get("RAF_DEV") == "1":
            cache_dir = os.path.abspath(os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "mock_system", "cache"
            ))
        else:
            cache_dir = os.path.expanduser("~/.cache/raf/downloads")
        local_path = os.path.join(cache_dir, book['file_name'])

        if self.download_queue.enqueue(book, local_path):
            card = self.card_widgets.get(book['id'])
            if card:
                card.set_queued(True)
        else:
            self.toast_manager.show_toast(tr("ui.already_queued"), "warning", duration=2500)

    def resizeEvent(self, event):
        """Repositions toast notifications when the window is resized."""
        super().resizeEvent(event)
        if hasattr(self, 'toast_manager'):
            self.toast_manager._reposition_all()


    def check_network_status(self):
        """Checks if the system has an active internet connection."""
        import socket
        try:
            socket.setdefaulttimeout(1.5)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("8.8.8.8", 53))
            s.close()
            self.is_offline = False
        except Exception:
            self.is_offline = True



    def open_preferences(self):
        """Opens user Preferences modal dialog."""
        dialog = PreferencesDialog(self)
        if hasattr(dialog, 'exec'):
            result = dialog.exec()
        else:
            result = dialog.exec_()
        
        if result:
            self.update_theme()
            self.refresh_grid()

    def create_search_icon(self):
        """Creates a clean custom drawn magnifying glass icon to avoid Unicode font rendering bugs on Pardus."""
        pixmap = QPixmap(18, 18)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Color: #8a8a8a (neutral gray matching the placeholder text)
        pen = QPen(QColor("#8a8a8a"))
        pen.setWidth(2)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        
        # Draw a beautiful magnifying glass
        # Circle radius 4.5, centered at (7.5, 7.5) -> top-left at (3, 3)
        painter.drawEllipse(3, 3, 9, 9)
        # Handle line from (10, 10) to (14, 14)
        painter.drawLine(10, 10, 14, 14)
        
        painter.end()
        return QIcon(pixmap)

    def process_local_files(self, file_paths):
        """Processes a list of local files/directories for sideloading installation."""
        if not file_paths:
            return
            
        from src.core.translation import tr
        import os
        from src.qt_compat import QMessageBox
        
        mock_books = []
        file_list_str = ""
        for path in file_paths:
            filename = os.path.basename(path)
            mock_book = {
                "id": f"local_{filename}",
                "title": os.path.splitext(filename)[0],
                "publisher": tr("cli.local_publisher"),
                "file_name": filename,
                "file_type": os.path.splitext(filename)[1].lstrip('.'),
                "is_local": True,
                "absolute_path": path
            }
            mock_books.append((mock_book, path))
            file_list_str += f"• {filename}\n"
            
        prompt_text = tr("ui.confirm_sideload_prompt", count=len(mock_books), files=file_list_str.strip())
        
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setWindowTitle(tr("ui.confirm_sideload_title"))
        msg_box.setText(prompt_text)
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)
        
        if msg_box.exec_() == QMessageBox.Yes:
            for mock_book, path in mock_books:
                self.start_installation(mock_book, path)

    def on_install_local_clicked(self):
        from src.qt_compat import QFileDialog
        from src.core.translation import tr
        
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            tr("ui.select_local_files"),
            "",
            tr("ui.supported_files") + " (*.deb *.zip *.appimage *.fernus)"
        )
        
        if file_paths:
            self.process_local_files(file_paths)

    def dragEnterEvent(self, event):
        """Accept file drops if they contain URLs and show overlay."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.drop_overlay.setGeometry(0, 0, self.centralWidget().width(), self.centralWidget().height())
            self.drop_overlay.raise_()
            self.drop_overlay.show()

    def dragLeaveEvent(self, event):
        """Hide overlay when mouse leaves."""
        self.drop_overlay.hide()
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        """Handle dropped files for sideloading."""
        self.drop_overlay.hide()
        import os
        
        valid_extensions = ('.deb', '.zip', '.appimage', '.fernus')
        dropped_files = []
        
        for url in event.mimeData().urls():
            if url.isLocalFile():
                path = url.toLocalFile()
                if path.lower().endswith(valid_extensions):
                    dropped_files.append(path)
                elif os.path.isdir(path):
                    # Also accept directories like install-local does
                    dropped_files.append(path)

        if dropped_files:
            self.process_local_files(dropped_files)

    def show_about_dialog(self):
        """Displays the About application dialog."""
        msg = QMessageBox(self)
        msg.setWindowTitle(tr("ui.about_title"))
        msg.setText(tr("ui.about_content", version=APP_VERSION))
        
        # Look for the app logo in assets
        import os
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "raf.png")
        if os.path.exists(icon_path):
            msg.setIconPixmap(QPixmap(icon_path).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            msg.setIcon(QMessageBox.Information)
            
        is_dark = self.current_theme == "dark"
        set_linux_dark_titlebar(msg, is_dark)
        
        check_btn = msg.addButton(tr("ui.check_updates"), QMessageBox.ActionRole)
        msg.addButton(QMessageBox.Ok)
        
        if hasattr(msg, 'exec'):
            msg.exec()
        else:
            msg.exec_()
            
        if msg.clickedButton() == check_btn:
            from src.core.updater import UpdateChecker
            self.updater = UpdateChecker()
            self.updater.update_available.connect(self.on_update_available)
            
            def on_no_update():
                QMessageBox.information(self, tr("ui.no_update_title"), tr("ui.no_update_message"))
                
            self.updater.no_update.connect(on_no_update)
            self.updater.start()

    def eventFilter(self, obj, event):
        """Intercepts focus and click events on search input to automatically open OSK."""
        if obj == self.search_input and event.type() in [QEvent.FocusIn, QEvent.MouseButtonPress]:
            self.trigger_virtual_keyboard()
        return super().eventFilter(obj, event)

    def trigger_virtual_keyboard(self):
        """Attempts to display the system-level virtual keyboard using Qt, D-Bus, or Onboard launch."""
        # 1. Standard Qt input method request
        app = QApplication.instance()
        if app:
            app.inputMethod().show()
            
        # 2. Trigger Onboard via D-Bus (Pardus standard)
        try:
            subprocess.Popen([
                "dbus-send", "--type=method_call",
                "--dest=org.onboard.Onboard",
                "/org/onboard/Onboard/Keyboard",
                "org.onboard.Onboard.Keyboard.Show"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
            
        # 3. Trigger GNOME Caribou OSK via D-Bus (GNOME standard)
        try:
            subprocess.Popen([
                "dbus-send", "--type=method_call",
                "--dest=org.gnome.Caribou.Keyboard",
                "/org/gnome/Caribou/Keyboard",
                "org.gnome.Caribou.Keyboard.Show"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
            
        # 4. Fallback: launch onboard if not already active
        try:
            subprocess.Popen(["onboard"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    def on_update_available(self, version, download_url, changelog):
        """Callback triggered when the UpdateChecker thread detects a newer version."""
        reply = QMessageBox.question(
            self,
            tr("ui.new_update_available"),
            tr("ui.update_prompt", version=version, changelog=changelog),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            self.start_app_update(version, download_url)

    def start_app_update(self, version, download_url):
        """Starts downloading the update deb file."""
        if os.environ.get("RAF_DEV") == "1":
            cache_dir = os.path.abspath(os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "mock_system",
                "cache"
            ))
        else:
            cache_dir = os.path.expanduser("~/.cache/raf/downloads")
            
        file_path = os.path.join(cache_dir, f"raf_{version}_update.deb")
        self.statusBar.showMessage(tr("ui.downloading_update"))
        
        # Reuse DownloadWorker for downloading update deb
        self.update_download_worker = DownloadWorker("app_update", download_url, file_path)
        self.update_download_worker.progress_changed.connect(self.on_update_download_progress)
        self.update_download_worker.finished.connect(self.on_update_download_finished)
        self.update_download_worker.error.connect(self.on_update_download_error)
        self.update_download_worker.start()
        
    def on_update_download_progress(self, bid, percent, speed_str):
        pct = percent if percent >= 0 else 50
        self.statusBar.showMessage(tr("ui.downloading_update_percent", percent=pct, speed=speed_str))
        
    def on_update_download_finished(self, bid, file_path):
        self.statusBar.showMessage(tr("ui.update_downloaded_installing"))
        
        # Start installation process
        self.update_installer_worker = UpdateInstaller(file_path)
        self.update_installer_worker.status_changed.connect(lambda msg: self.statusBar.showMessage(msg))
        self.update_installer_worker.finished.connect(self.on_update_install_finished)
        self.update_installer_worker.start()
        
    def on_update_download_error(self, bid, err_msg):
        self.statusBar.showMessage(tr("ui.update_download_error_status"), 5000)
        QMessageBox.warning(self, tr("ui.update_download_error_status"), tr("ui.update_download_failed", error=err_msg))
        
    def on_update_install_finished(self, success):
        if success:
            self.statusBar.showMessage(tr("ui.update_completed_status"), 5000)
            QMessageBox.information(
                self,
                tr("ui.update_successful_title"),
                tr("ui.update_successful_message")
            )
            self.close()
        else:
            self.statusBar.showMessage(tr("ui.update_error_status"), 5000)
            QMessageBox.critical(
                self,
                tr("ui.update_error_title"),
                tr("ui.update_error_message")
            )

    def on_tab_changed(self):
        """Handles switcher tab toggle between Market and Library views."""
        self.refresh_grid()

    def refresh_packages_cache(self):
        self.pkg_worker = PackageQueryWorker()
        self.pkg_worker.packages_loaded.connect(self._on_packages_loaded)
        self.pkg_worker.start()

    def _on_packages_loaded(self, installed_set):
        self.installed_packages_cache = installed_set
        self.refresh_grid()

    def get_filtered_books(self):
        if self.installed_packages_cache is None:
            return []
            
        query = self.search_input.text()
        books = self.db.search_books(query)
            
        # Filter by switcher tab state
        if self.tab_library_btn.isChecked():
            books = [b for b in books if is_book_installed(b, self.installed_packages_cache)]
            
        return books

    def refresh_grid(self):
        """Re-populates the vertical list layout container with filtered items."""
        if self.installed_packages_cache is None:
            return
            
        # Hide and remove all card widgets from list layout
        for card in self.card_widgets.values():
            card.hide()
            self.list_layout.removeWidget(card)

        # Retrieve filtered list
        books = self.get_filtered_books()
        self.count_label.setText(tr("ui.books_listed", count=len(books)))

        for idx, book in enumerate(books):
            book_id = book['id']
            
            installed = is_book_installed(book, self.installed_packages_cache)
            # Retrieve or create widget
            if book_id in self.card_widgets:
                card = self.card_widgets[book_id]
                if book_id not in self.active_downloads and book_id not in self.active_installations:
                    card.update_status(installed, is_offline=self.is_offline)
            else:
                card = BookCard(book, is_installed=installed)
                card.install_requested.connect(self.start_download)
                card.uninstall_requested.connect(self.start_uninstallation)
                card.launch_requested.connect(self.launch_book)
                card.cancel_requested.connect(self.cancel_download)
                self.card_widgets[book_id] = card
                card.update_status(installed, is_offline=self.is_offline)
            
            # Style synchronization
            card.style().unpolish(card)
            card.style().polish(card)
            
            # Position into layout list
            self.list_layout.addWidget(card)
            card.show()
            
        # Move placeholder widget to the bottom of layout list
        self.list_layout.removeWidget(self.placeholder_widget)
        self.list_layout.addWidget(self.placeholder_widget)

        # Toggle empty-state placeholder view
        if len(books) == 0:
            if self.tab_library_btn.isChecked():
                self.placeholder_label.setText(tr("ui.no_installed_books_found"))
            else:
                self.placeholder_label.setText(tr("ui.no_books_found"))
            self.placeholder_widget.show()
        else:
            self.placeholder_widget.hide()

    def refresh_all_statuses(self):
        """Check all books' actual installation state in the background."""
        self.check_network_status()
        self.offline_badge.setVisible(self.is_offline)
        
        self.refresh_packages_cache()

    def on_search_changed(self, text):
        # Restart the debounce timer (300ms) to prevent UI blocking while typing
        self.search_timer.start(300)



    # --- Actions / Core Operations ---

    def start_download(self, book):
        book_id = book['id']
        if book_id in self.active_downloads:
            return

        file_name = book['file_name']
        if os.environ.get("RAF_DEV") == "1":
            cache_dir = os.path.abspath(os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                "mock_system", 
                "cache"
            ))
        else:
            cache_dir = os.path.expanduser("~/.cache/raf/downloads")
        local_file_path = os.path.join(cache_dir, file_name)

        card = self.card_widgets[book_id]
        card.update_status(is_installed=False, downloading=True, percent=0, speed_str=tr("ui.download_preparing"))

        worker = DownloadWorker(book_id, book['download_url'], local_file_path)
        worker.progress_changed.connect(self.on_download_progress)
        worker.finished.connect(self.on_download_finished)
        worker.error.connect(self.on_download_error)
        
        self.active_downloads[book_id] = worker
        self.statusBar.showMessage(tr("ui.downloading_status", title=book['title']))
        worker.start()

    def on_download_progress(self, book_id, percent, speed_str):
        if book_id in self.card_widgets:
            card = self.card_widgets[book_id]
            pct = percent if percent >= 0 else 50
            card.update_status(is_installed=False, downloading=True, percent=pct, speed_str=speed_str)
        self._update_title_progress()

    def on_download_finished(self, book_id, local_file_path):
        worker = self.active_downloads.pop(book_id, None)
        if worker:
            worker.deleteLater()
        self.download_queue.on_download_completed(book_id)
        self._update_title_progress()

        book = self.card_widgets[book_id].book
        self.start_installation(book, local_file_path)

    def on_download_error(self, book_id, err_msg):
        worker = self.active_downloads.pop(book_id, None)
        if worker:
            worker.deleteLater()
        self.download_queue.on_download_completed(book_id)
        self._update_title_progress()

        self.statusBar.showMessage(tr("ui.download_error_status", error=err_msg), 5000)
        
        if book_id in self.card_widgets:
            card = self.card_widgets[book_id]
            card.update_status(is_installed=False)
            
        is_cancelled = (
            err_msg == tr("downloader.download_cancelled") or
            "cancelled" in err_msg.lower()
        )
        if not is_cancelled:
            self.toast_manager.show_toast(tr("ui.toast_download_error", error=err_msg[:60]), "error")

    def cancel_download(self, book):
        book_id = book['id']
        # If queued but not yet downloading, just dequeue it
        if self.download_queue.is_queued(book_id):
            self.download_queue.dequeue(book_id)
            card = self.card_widgets.get(book_id)
            if card:
                card.is_queued = False
                card.update_status(card.is_installed, is_offline=self.is_offline)
            self.statusBar.showMessage(tr("ui.cancelling_download"), 2000)
            return
        # If actively downloading, cancel the worker
        if book_id in self.active_downloads:
            worker = self.active_downloads[book_id]
            worker.cancel()
            self.statusBar.showMessage(tr("ui.cancelling_download"), 3000)

    def start_installation(self, book, local_file_path):
        book_id = book['id']
        if book_id in self.active_installations:
            return

        card = self.card_widgets.get(book_id)
        if card:
            card.status_label.setText(tr("ui.installing_btn"))
            card.status_label.setObjectName("StatusDownloadingLabel")
            card.status_label.style().unpolish(card.status_label)
            card.status_label.style().polish(card.status_label)
            card.primary_btn.setEnabled(False)
            card.primary_btn.setText(tr("ui.installing_btn"))
        
        worker = InstallerWorker(book, local_file_path, action="install")
        worker.status_changed.connect(lambda bid, msg: self.statusBar.showMessage(f"{book['title']}: {msg}"))
        worker.finished.connect(self.on_installation_finished)
        worker.output_received.connect(self.on_install_output)
        worker.auth_failed.connect(lambda bid: self.on_auth_failed(bid, worker))
        
        self.active_installations[book_id] = worker
        self.statusBar.showMessage(tr("ui.installing_status", title=book['title']))
        worker.start()

    def on_install_output(self, book_id, text):
        print(f"[{book_id} install stdout]: {text.strip()}")
        self.logs_dialog.append_log(f"[{book_id}] {text.strip()}")

    def on_installation_finished(self, book_id, success):
        worker = self.active_installations.pop(book_id, None)
        book = worker.book if worker else None
        if worker:
            worker.deleteLater()

        card = self.card_widgets.get(book_id)
        if not book and card:
            book = card.book

        if card:
            card.primary_btn.setEnabled(True)
            installed = is_book_installed(book)
            card.update_status(installed, is_offline=self.is_offline)
        else:
            installed = is_book_installed(book) if book else success
        
        if success and installed:
            self.statusBar.showMessage(tr("ui.install_success_status", title=book['title']), 5000)
            self.toast_manager.show_toast(tr("ui.toast_install_success", title=book['title']), "success")
            
            # Save to database if it was sideloaded
            if book and book.get('is_local'):
                from src.core.database import Database
                self.db.add_sideloaded_book(book)

            if book.get('file_type') == 'deb':
                try:
                    if os.environ.get("RAF_DEV") == "1":
                        cache_dir = os.path.abspath(os.path.join(
                            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                            "mock_system", 
                            "cache"
                        ))
                    else:
                        cache_dir = os.path.expanduser("~/.cache/raf/downloads")
                    local_file_path = os.path.join(cache_dir, book['file_name'])
                    if os.path.exists(local_file_path):
                        os.remove(local_file_path)
                except Exception:
                    pass
            # Trigger refresh to update list layout view
            self.refresh_packages_cache()
        elif getattr(worker, '_auth_failed', False):
            pass # Already handled by on_auth_failed
        else:
            self.statusBar.showMessage(tr("ui.install_error_status", title=book['title']), 5000)
            self.toast_manager.show_toast(tr("ui.toast_install_error", title=book['title']), "error")

    def start_uninstallation(self, book):
        book_id = book['id']
        if book_id in self.active_installations:
            return

        reply = QMessageBox.question(
            self,
            tr("ui.uninstall_library_title"),
            tr("ui.uninstall_library_prompt", title=book['title']),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return

        card = self.card_widgets.get(book_id)
        if card:
            card.primary_btn.setEnabled(False)
            card.secondary_btn.setEnabled(False)
            card.primary_btn.setText(tr("ui.uninstalling_btn"))
        
        worker = InstallerWorker(book, None, action="uninstall")
        worker.status_changed.connect(lambda bid, msg: self.statusBar.showMessage(f"{book['title']}: {msg}"))
        worker.finished.connect(self.on_uninstallation_finished)
        worker.output_received.connect(self.on_install_output)
        worker.auth_failed.connect(lambda bid: self.on_auth_failed(bid, worker))
        
        self.active_installations[book_id] = worker
        self.statusBar.showMessage(tr("ui.uninstalling_status", title=book['title']))
        worker.start()

    def on_uninstallation_finished(self, book_id, success):
        worker = self.active_installations.pop(book_id, None)
        book = worker.book if worker else None
        if worker:
            worker.deleteLater()

        card = self.card_widgets.get(book_id)
        if not book and card:
            book = card.book

        if card:
            card.primary_btn.setEnabled(True)
            card.secondary_btn.setEnabled(True)
            installed = is_book_installed(book)
            card.update_status(installed, is_offline=self.is_offline)
        else:
            installed = is_book_installed(book) if book else not success
        
        if success and not installed:
            self.statusBar.showMessage(tr("ui.uninstall_success_status", title=book['title']), 5000)
            self.toast_manager.show_toast(tr("ui.toast_uninstall_success", title=book['title']), "success")
            
            if book and book.get('is_local'):
                from src.core.database import Database
                self.db.remove_sideloaded_book(book['id'])
                
            self.refresh_packages_cache()
        elif getattr(worker, '_auth_failed', False):
            pass # Already handled by on_auth_failed
        else:
            self.statusBar.showMessage(tr("ui.uninstall_error_status", title=book['title']), 5000)
            self.toast_manager.show_toast(tr("ui.toast_install_error", title=book['title']), "error")

    def on_auth_failed(self, book_id, worker):
        worker._auth_failed = True
        book = worker.book
        title = book['title'] if book else ""
        self.statusBar.showMessage(tr("ui.auth_failed_status", title=title), 5000)
        self.toast_manager.show_toast(tr("ui.toast_auth_failed", title=title), "warning")

    def launch_book(self, book):
        if os.environ.get("RAF_DEV") == "1":
            print(f"[DEVELOPER MODE] Book launched: {book['title']} (File: {book['file_name']})")
            QMessageBox.information(
                self,
                tr("ui.book_launched_sim_title"),
                tr("ui.book_launched_sim_message", title=book['title'], publisher=book['publisher'], filename=book['file_name'])
            )
            return
        
        file_type = book.get('file_type', 'deb')
        
        if file_type == 'deb':
            package_name = get_deb_package_name(book)
            cmd = ["gtk-launch", package_name]
            
            try:
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.statusBar.showMessage(tr("ui.launching_status", title=book['title']), 3000)
            except Exception as e:
                try:
                    subprocess.Popen([package_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self.statusBar.showMessage(tr("ui.launching_status", title=book['title']), 3000)
                except Exception as e2:
                    self.statusBar.showMessage(tr("ui.launch_error_status"), 5000)
                    QMessageBox.warning(
                        self, 
                        tr("ui.app_launch_failed_title"), 
                        tr("ui.app_launch_failed_message", error=str(e2))
                    )
                    
        elif file_type in ['zip', 'fernus']:
            desktop_name = f"raf-{book['id']}"
            cmd = ["gtk-launch", desktop_name]
            
            try:
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.statusBar.showMessage(tr("ui.launching_status", title=book['title']), 3000)
            except Exception as e:
                self.statusBar.showMessage(tr("ui.launch_error_status"), 5000)
                QMessageBox.warning(self, tr("ui.app_launch_failed_title"), tr("ui.book_launch_failed_message", error=str(e)))
