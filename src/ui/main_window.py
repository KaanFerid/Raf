import os
import subprocess
import re
from src.qt_compat import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QLineEdit, QComboBox, QScrollArea, 
                            QMessageBox, QStatusBar, QSizePolicy, QPushButton, 
                            QProgressBar, QFrame, Qt, QTimer, QMenu, QDialog, 
                            QButtonGroup, QRadioButton, QGroupBox, QEvent, QApplication,
                            QIcon, QPixmap, QPen, QColor, QPainter)
from src.ui.styles import LIGHT_STYLE, DARK_STYLE
from src.ui.components import BookCard
from src.core.database import Database
from src.core.downloader import DownloadWorker
from src.core.installer import InstallerWorker, is_book_installed, get_deb_package_name, get_all_installed_packages
from src.core.config import load_config, save_config
from src.core.updater import UpdateChecker, UpdateInstaller

class PreferencesDialog(QDialog):
    """Preferences window styled in Adwaita format for theme configuration."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tercihler")
        self.setFixedSize(380, 360)
        self.init_ui()
        
    def init_ui(self):
        self.config = load_config()
        current_mode = self.config.get("theme_mode", "system")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Appearance setting frame
        group_box = QGroupBox("Görünüm")
        group_layout = QVBoxLayout(group_box)
        group_layout.setContentsMargins(15, 12, 15, 12)
        group_layout.setSpacing(8)
        
        self.radio_system = QRadioButton("Sistem Teması (Otomatik)")
        self.radio_light = QRadioButton("Açık Tema")
        self.radio_dark = QRadioButton("Koyu Tema")
        
        if current_mode == "system":
            self.radio_system.setChecked(True)
        elif current_mode == "light":
            self.radio_light.setChecked(True)
        elif current_mode == "dark":
            self.radio_dark.setChecked(True)
            
        group_layout.addWidget(self.radio_system)
        group_layout.addWidget(self.radio_light)
        group_layout.addWidget(self.radio_dark)
        
        layout.addWidget(group_box)
        
        # Disk Info Box
        disk_box = QGroupBox("Sistem ve Önbellek")
        disk_layout = QVBoxLayout(disk_box)
        disk_layout.setContentsMargins(15, 12, 15, 12)
        disk_layout.setSpacing(8)
        
        self.disk_label = QLabel(self.get_disk_info())
        self.disk_label.setStyleSheet("color: #8a8a8a; font-size: 12px;")
        
        self.cache_label = QLabel(self.get_cache_size())
        self.cache_label.setStyleSheet("color: #8a8a8a; font-size: 12px;")
        
        self.clear_btn = QPushButton("Önbelleği Temizle")
        self.clear_btn.setProperty("class", "AdwSecondaryBtn")
        self.clear_btn.clicked.connect(self.clear_cache)
        
        disk_layout.addWidget(self.disk_label)
        disk_layout.addWidget(self.cache_label)
        disk_layout.addWidget(self.clear_btn)
        
        layout.addWidget(disk_box)
        
        # Actions
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.setProperty("class", "AdwSecondaryBtn")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Kaydet")
        save_btn.setProperty("class", "AdwPrimaryBtn")
        save_btn.clicked.connect(self.save_preferences)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
        # Synchronize dialog styling with main window style
        if self.parent():
            self.setStyleSheet(self.parent().styleSheet())
            
    def get_disk_info(self):
        if os.environ.get("ETKILESIMLI_KITAP_KUTUPHANESI_DEV") == "1":
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
            return f"Sistem Boş Alanı: {free_gb:.1f} GB / {total_gb:.1f} GB"
        except Exception:
            return "Disk Alanı: Bilinmiyor"

    def get_cache_size(self):
        if os.environ.get("ETKILESIMLI_KITAP_KUTUPHANESI_DEV") == "1":
            cache_dir = os.path.abspath(os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "mock_system",
                "cache"
            ))
        else:
            cache_dir = os.path.expanduser("~/.cache/etkilesimli-kitap-kutuphanesi/downloads")
            
        if not os.path.exists(cache_dir):
            return "Önbellek Boyutu: 0.0 MB"
            
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(cache_dir):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)
            size_mb = total_size / (1024 * 1024)
            return f"İndirme Önbelleği: {size_mb:.1f} MB"
        except Exception:
            return "Önbellek Boyutu: Bilinmiyor"

    def clear_cache(self):
        if os.environ.get("ETKILESIMLI_KITAP_KUTUPHANESI_DEV") == "1":
            cache_dir = os.path.abspath(os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "mock_system",
                "cache"
            ))
        else:
            cache_dir = os.path.expanduser("~/.cache/etkilesimli-kitap-kutuphanesi/downloads")
            
        if os.path.exists(cache_dir):
            try:
                for f in os.listdir(cache_dir):
                    file_path = os.path.join(cache_dir, f)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                QMessageBox.information(self, "Başarılı", "İndirme önbelleği başarıyla temizlendi.")
                self.cache_label.setText(self.get_cache_size())
                self.disk_label.setText(self.get_disk_info())
            except Exception as e:
                QMessageBox.warning(self, "Hata", f"Önbellek temizlenirken hata oluştu:\n{e}")

    def save_preferences(self):
        if self.radio_system.isChecked():
            mode = "system"
        elif self.radio_light.isChecked():
            mode = "light"
        elif self.radio_dark.isChecked():
            mode = "dark"
            
        self.config["theme_mode"] = mode
        save_config(self.config)
        self.accept()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Etkileşimli Kitap Kütüphanesi")
        self.resize(850, 650)
        self.setMinimumSize(700, 500)
        
        # Theme configuration variables
        self.current_theme = None
        self.theme_timer = QTimer(self)
        self.theme_timer.timeout.connect(self.check_system_theme_update)
        
        # Core components
        print("Kitap veritabanı yükleniyor...")
        self.db = Database()
        print(f"Veritabanı yüklendi. Toplam {len(self.db.get_all_books())} kitap mevcut.")
        
        # State tracking
        self.active_downloads = {}      # book_id -> DownloadWorker
        self.active_installations = {}  # book_id -> InstallerWorker
        self.card_widgets = {}          # book_id -> BookCard
        
        # Network & Category state
        self.is_offline = False
        self.active_category = "Tümü"
        self.check_network_status()
        
        self.init_ui()
        self.update_theme()
        
        # Check for updates in the background on startup
        self.update_checker = UpdateChecker()
        self.update_checker.update_available.connect(self.on_update_available)
        self.update_checker.start()
        
        # Periodically refresh installation status of displayed items
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_all_statuses)
        self.refresh_timer.start(5000) # every 5 seconds

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

        # Gsettings fallback for pure GNOME environment
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
        else:
            self.setStyleSheet(LIGHT_STYLE)
            self.current_theme = "light"
            
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
        app_title = QLabel("Etkileşimli Kitap Kütüphanesi")
        app_title.setObjectName("AppTitleLabel")
        header_layout.addWidget(app_title)

        header_layout.addStretch(1)

        # Center segmented control (View Switcher - Adwaita style)
        switcher_container = QWidget()
        switcher_container.setObjectName("ViewSwitcherContainer")
        switcher_layout = QHBoxLayout(switcher_container)
        switcher_layout.setContentsMargins(0, 0, 0, 0)
        switcher_layout.setSpacing(0)

        self.tab_market_btn = QPushButton("Market")
        self.tab_market_btn.setCheckable(True)
        self.tab_market_btn.setChecked(True)
        self.tab_market_btn.setProperty("class", "ViewSwitcherBtn")

        self.tab_library_btn = QPushButton("Kütüphanem")
        self.tab_library_btn.setCheckable(True)
        self.tab_library_btn.setProperty("class", "ViewSwitcherBtn")

        self.tab_group = QButtonGroup(self)
        self.tab_group.addButton(self.tab_market_btn)
        self.tab_group.addButton(self.tab_library_btn)
        self.tab_group.setExclusive(True)
        
        self.tab_market_btn.clicked.connect(self.on_tab_changed)
        self.tab_library_btn.clicked.connect(self.on_tab_changed)

        switcher_layout.addWidget(self.tab_market_btn)
        switcher_layout.addWidget(self.tab_library_btn)
        header_layout.addWidget(switcher_container)

        header_layout.addStretch(1)

        # Search Bar input field
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Ara...")
        self.search_input.setFixedWidth(180)
        self.search_input.textChanged.connect(self.on_search_changed)
        self.search_input.installEventFilter(self) # Intercept focus events for keyboard trigger
        # Add custom drawn clean search icon to avoid Unicode rendering issues on Pardus
        self.search_input.addAction(self.create_search_icon(), QLineEdit.LeadingPosition)
        header_layout.addWidget(self.search_input)

        # (Virtual Keyboard manual button removed to clean up the layout as requested)

        # Publisher Filter Combo Box
        self.publisher_combo = QComboBox()
        self.publisher_combo.addItem("Tüm Yayıncılar")
        publishers = sorted(list(set(b['publisher'] for b in self.db.get_all_books())))
        for pub in publishers:
            self.publisher_combo.addItem(pub)
        self.publisher_combo.currentTextChanged.connect(self.on_filter_changed)
        header_layout.addWidget(self.publisher_combo)

        # Hamburger Menu Button
        self.menu_btn = QPushButton("☰")
        self.menu_btn.setObjectName("MenuButton")
        self.menu_btn.setFixedWidth(36)
        self.menu_btn.setProperty("class", "AdwSecondaryBtn")
        self.menu_btn.clicked.connect(self.show_hamburger_menu)
        header_layout.addWidget(self.menu_btn)

        main_layout.addWidget(header_widget)

        # 1b. Category Filter Bar (Adwaita/Bottles style horizontal pills)
        category_widget = QWidget()
        category_widget.setObjectName("CategoryFilterWidget")
        category_layout = QHBoxLayout(category_widget)
        category_layout.setContentsMargins(20, 8, 20, 8)
        category_layout.setSpacing(8)
        
        category_label = QLabel("Kategori:")
        category_label.setStyleSheet("font-weight: bold; color: #8a8a8a; font-size: 12px;")
        category_layout.addWidget(category_label)
        
        self.cat_buttons = {}
        categories = ["Tümü", "İlkokul", "Ortaokul", "Lise", "Genel"]
        self.cat_group = QButtonGroup(self)
        self.cat_group.setExclusive(True)
        
        for cat in categories:
            btn = QPushButton(cat)
            btn.setCheckable(True)
            btn.setProperty("class", "CategoryFilterBtn")
            if cat == self.active_category:
                btn.setChecked(True)
            btn.clicked.connect(self.on_category_changed)
            self.cat_group.addButton(btn)
            category_layout.addWidget(btn)
            self.cat_buttons[cat] = btn
            
        category_layout.addStretch(1)
        main_layout.addWidget(category_widget)

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
        
        self.placeholder_label = QLabel("Kütüphaneniz boş.\nMarket sekmesinden kitap inceleyip yükleyebilirsiniz.")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setStyleSheet("color: #8a8a8a; font-size: 15px; font-weight: 500;")
        placeholder_layout.addWidget(self.placeholder_label)
        
        self.list_layout.addWidget(self.placeholder_widget)
        self.placeholder_widget.hide()
        
        scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(scroll_area, 1)

        # 4. Status Bar
        self.statusBar = QStatusBar()
        self.statusBar.setStyleSheet("background-color: transparent; color: #8a8a8a; border-top: 1px solid transparent;")
        self.setStatusBar(self.statusBar)
        
        self.offline_badge = QLabel("  ÇEVRİMDIŞI MOD  ")
        self.offline_badge.setStyleSheet("background-color: #c01c28; color: #ffffff; font-weight: bold; border-radius: 4px; font-size: 11px;")
        self.offline_badge.setVisible(self.is_offline)
        self.statusBar.addPermanentWidget(self.offline_badge)
        
        self.statusBar.showMessage("Hazır")

        # Load initial view list
        self.refresh_grid()

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

    def on_category_changed(self):
        btn = self.sender()
        if btn and btn.isChecked():
            self.active_category = btn.text()
            self.refresh_grid()

    def show_hamburger_menu(self):
        """Displays hamburger menu dropdown."""
        menu = QMenu(self)
        menu.setStyleSheet(self.styleSheet())
        
        pref_action = menu.addAction("Tercihler...")
        pref_action.triggered.connect(self.open_preferences)
        
        about_action = menu.addAction("Hakkında")
        about_action.triggered.connect(self.show_about_dialog)
        
        menu.exec(self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomLeft()))

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

    def show_about_dialog(self):
        """Displays the About application dialog."""
        QMessageBox.about(
            self,
            "Etkileşimli Kitap Kütüphanesi Hakkında",
            "<h3>Etkileşimli Kitap Kütüphanesi v1.0.0</h3>"
            "<p>Pardus Akıllı Tahtalar için Kitap ve Uygulama Marketi.</p>"
            "<p>© 2026 Kaan Ferid Altundaş</p>"
        )

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
        except:
            pass
            
        # 3. Trigger GNOME Caribou OSK via D-Bus (GNOME standard)
        try:
            subprocess.Popen([
                "dbus-send", "--type=method_call",
                "--dest=org.gnome.Caribou.Keyboard",
                "/org/gnome/Caribou/Keyboard",
                "org.gnome.Caribou.Keyboard.Show"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass
            
        # 4. Fallback: launch onboard if not already active
        try:
            subprocess.Popen(["onboard"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass

    def on_update_available(self, version, download_url, changelog):
        """Callback triggered when the UpdateChecker thread detects a newer version."""
        reply = QMessageBox.question(
            self,
            "Yeni Güncelleme Mevcut",
            f"<h3>Etkileşimli Kitap Kütüphanesi v{version} sürümü hazır!</h3>"
            f"<p><b>Yenilikler:</b><br/>{changelog}</p>"
            f"<p>Uygulamayı şimdi güncellemek ister misiniz?</p>",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            self.start_app_update(version, download_url)

    def start_app_update(self, version, download_url):
        """Starts downloading the update deb file."""
        if os.environ.get("ETKILESIMLI_KITAP_KUTUPHANESI_DEV") == "1":
            cache_dir = os.path.abspath(os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "mock_system",
                "cache"
            ))
        else:
            cache_dir = os.path.expanduser("~/.cache/etkilesimli-kitap-kutuphanesi/downloads")
            
        file_path = os.path.join(cache_dir, f"etkilesimli-kitap-kutuphanesi_{version}_update.deb")
        self.statusBar.showMessage("Güncelleme indiriliyor...")
        
        # Reuse DownloadWorker for downloading update deb
        self.update_download_worker = DownloadWorker("app_update", download_url, file_path)
        self.update_download_worker.progress_changed.connect(self.on_update_download_progress)
        self.update_download_worker.finished.connect(self.on_update_download_finished)
        self.update_download_worker.error.connect(self.on_update_download_error)
        self.update_download_worker.start()
        
    def on_update_download_progress(self, bid, percent, speed_str):
        pct = percent if percent >= 0 else 50
        self.statusBar.showMessage(f"Güncelleme indiriliyor: %{pct} ({speed_str})")
        
    def on_update_download_finished(self, bid, file_path):
        self.statusBar.showMessage("Güncelleme dosyası indirildi, kuruluyor...")
        
        # Start installation process
        self.update_installer_worker = UpdateInstaller(file_path)
        self.update_installer_worker.status_changed.connect(lambda msg: self.statusBar.showMessage(msg))
        self.update_installer_worker.finished.connect(self.on_update_install_finished)
        self.update_installer_worker.start()
        
    def on_update_download_error(self, bid, err_msg):
        self.statusBar.showMessage("Güncelleme indirme hatası!", 5000)
        QMessageBox.warning(self, "Güncelleme Başarısız", f"Güncelleme dosyası indirilemedi:\n{err_msg}")
        
    def on_update_install_finished(self, success):
        if success:
            self.statusBar.showMessage("Güncelleme tamamlandı!", 5000)
            QMessageBox.information(
                self,
                "Güncelleme Başarılı",
                "Etkileşimli Kitap Kütüphanesi başarıyla güncellendi!\nYeni sürümün geçerli olması için lütfen uygulamayı kapatıp yeniden başlatın."
            )
            self.close()
        else:
            self.statusBar.showMessage("Güncelleme hatası!", 5000)
            QMessageBox.critical(
                self,
                "Güncelleme Hatası",
                "Güncelleme yüklenemedi. Lütfen yönetici şifresini doğru girdiğinizden emin olun."
            )

    def on_tab_changed(self):
        """Handles switcher tab toggle between Market and Library views."""
        # Toggle visibility of filters depending on view
        if self.tab_library_btn.isChecked():
            # In Library view, we can hide search or publisher filter if needed, 
            # but keeping them works too.
            pass
        self.refresh_grid()

    def get_filtered_books(self):
        query = self.search_input.text()
        pub_filter = self.publisher_combo.currentText()
        
        books = self.db.search_books(query)
        if pub_filter != "Tüm Yayıncılar":
            books = [b for b in books if b['publisher'] == pub_filter]
            
        # Filter by active category
        if hasattr(self, "active_category") and self.active_category != "Tümü":
            books = [b for b in books if b.get('category') == self.active_category]
            
        # Filter by switcher tab state
        if self.tab_library_btn.isChecked():
            installed_set = get_all_installed_packages()
            books = [b for b in books if is_book_installed(b, installed_set)]
            
        return books

    def refresh_grid(self):
        """Re-populates the vertical list layout container with filtered items."""
        # Hide and remove all card widgets from list layout
        for card in self.card_widgets.values():
            card.hide()
            self.list_layout.removeWidget(card)

        # Retrieve filtered list
        books = self.get_filtered_books()
        self.count_label.setText(f"{len(books)} kitap listelendi.")

        # Cache package status query
        installed_set = get_all_installed_packages()

        for idx, book in enumerate(books):
            book_id = book['id']
            
            installed = is_book_installed(book, installed_set)
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
                self.placeholder_label.setText("Kütüphanenizde yüklü kitap bulunamadı.\nMarket sekmesinden kitap inceleyip yükleyebilirsiniz.")
            else:
                self.placeholder_label.setText("Aramanızla eşleşen kitap bulunamadı.")
            self.placeholder_widget.show()
        else:
            self.placeholder_widget.hide()

    def refresh_all_statuses(self):
        """Check all books' actual installation state in the background."""
        self.check_network_status()
        self.offline_badge.setVisible(self.is_offline)
        
        installed_set = get_all_installed_packages()
        
        for book_id, card in self.card_widgets.items():
            if book_id in self.active_downloads or book_id in self.active_installations:
                continue
            
            installed = is_book_installed(card.book, installed_set)
            card.update_status(installed, is_offline=self.is_offline)

    def on_search_changed(self, text):
        self.refresh_grid()

    def on_filter_changed(self, text):
        self.refresh_grid()

    # --- Actions / Core Operations ---

    def start_download(self, book):
        book_id = book['id']
        if book_id in self.active_downloads:
            return

        file_name = book['file_name']
        if os.environ.get("ETKILESIMLI_KITAP_KUTUPHANESI_DEV") == "1":
            cache_dir = os.path.abspath(os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                "mock_system", 
                "cache"
            ))
        else:
            cache_dir = os.path.expanduser("~/.cache/etkilesimli-kitap-kutuphanesi/downloads")
        local_file_path = os.path.join(cache_dir, file_name)

        card = self.card_widgets[book_id]
        card.update_status(is_installed=False, downloading=True, percent=0, speed_str="Hazırlanıyor...")

        worker = DownloadWorker(book_id, book['download_url'], local_file_path)
        worker.progress_changed.connect(self.on_download_progress)
        worker.finished.connect(self.on_download_finished)
        worker.error.connect(self.on_download_error)
        
        self.active_downloads[book_id] = worker
        self.statusBar.showMessage(f"{book['title']} indiriliyor...")
        worker.start()

    def on_download_progress(self, book_id, percent, speed_str):
        if book_id in self.card_widgets:
            card = self.card_widgets[book_id]
            pct = percent if percent >= 0 else 50
            card.update_status(is_installed=False, downloading=True, percent=pct, speed_str=speed_str)

    def on_download_finished(self, book_id, local_file_path):
        worker = self.active_downloads.pop(book_id, None)
        if worker:
            worker.deleteLater()

        book = self.card_widgets[book_id].book
        self.start_installation(book, local_file_path)

    def on_download_error(self, book_id, err_msg):
        worker = self.active_downloads.pop(book_id, None)
        if worker:
            worker.deleteLater()

        self.statusBar.showMessage(f"İndirme hatası: {err_msg}", 5000)
        
        if book_id in self.card_widgets:
            card = self.card_widgets[book_id]
            card.update_status(is_installed=False)
            
        if "İndirme iptal edildi" not in err_msg:
            QMessageBox.critical(self, "İndirme Hatası", f"Dosya indirilirken hata oluştu:\n{err_msg}")

    def cancel_download(self, book):
        book_id = book['id']
        if book_id in self.active_downloads:
            worker = self.active_downloads[book_id]
            worker.cancel()
            self.statusBar.showMessage("İndirme iptal ediliyor...", 3000)

    def start_installation(self, book, local_file_path):
        book_id = book['id']
        if book_id in self.active_installations:
            return

        card = self.card_widgets[book_id]
        card.status_label.setText("Kuruluyor")
        card.status_label.setObjectName("StatusDownloadingLabel")
        card.status_label.style().unpolish(card.status_label)
        card.status_label.style().polish(card.status_label)
        card.primary_btn.setEnabled(False)
        card.primary_btn.setText("Kuruluyor")
        
        worker = InstallerWorker(book, local_file_path, action="install")
        worker.status_changed.connect(lambda bid, msg: self.statusBar.showMessage(f"{book['title']}: {msg}"))
        worker.finished.connect(self.on_installation_finished)
        worker.output_received.connect(self.on_install_output)
        
        self.active_installations[book_id] = worker
        self.statusBar.showMessage(f"{book['title']} kuruluyor...")
        worker.start()

    def on_install_output(self, book_id, text):
        print(f"[{book_id} install stdout]: {text.strip()}")

    def on_installation_finished(self, book_id, success):
        worker = self.active_installations.pop(book_id, None)
        if worker:
            worker.deleteLater()

        book = self.card_widgets[book_id].book
        card = self.card_widgets[book_id]
        card.primary_btn.setEnabled(True)
        
        installed = is_book_installed(book)
        card.update_status(installed, is_offline=self.is_offline)
        
        if success and installed:
            self.statusBar.showMessage(f"{book['title']} başarıyla kuruldu!", 5000)
            if book.get('file_type') == 'deb':
                try:
                    if os.environ.get("ETKILESIMLI_KITAP_KUTUPHANESI_DEV") == "1":
                        cache_dir = os.path.abspath(os.path.join(
                            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                            "mock_system", 
                            "cache"
                        ))
                    else:
                        cache_dir = os.path.expanduser("~/.cache/etkilesimli-kitap-kutuphanesi/downloads")
                    local_file_path = os.path.join(cache_dir, book['file_name'])
                    if os.path.exists(local_file_path):
                        os.remove(local_file_path)
                except:
                    pass
            # Trigger refresh to update list layout view
            self.refresh_grid()
        else:
            self.statusBar.showMessage(f"{book['title']} kurulum hatası!", 5000)
            QMessageBox.critical(self, "Kurulum Hatası", f"'{book['title']}' kurulumu başarısız oldu. Lütfen yönetici şifresini doğru girdiğinizden emin olun.")

    def start_uninstallation(self, book):
        book_id = book['id']
        if book_id in self.active_installations:
            return

        reply = QMessageBox.question(
            self,
            "Kütüphaneyi Kaldır",
            f"'{book['title']}' kütüphanesini sistemden kaldırmak istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return

        card = self.card_widgets[book_id]
        card.primary_btn.setEnabled(False)
        card.secondary_btn.setEnabled(False)
        card.primary_btn.setText("Kaldırılıyor")
        
        worker = InstallerWorker(book, None, action="uninstall")
        worker.status_changed.connect(lambda bid, msg: self.statusBar.showMessage(f"{book['title']}: {msg}"))
        worker.finished.connect(self.on_uninstallation_finished)
        worker.output_received.connect(self.on_install_output)
        
        self.active_installations[book_id] = worker
        self.statusBar.showMessage(f"{book['title']} kaldırılıyor...")
        worker.start()

    def on_uninstallation_finished(self, book_id, success):
        worker = self.active_installations.pop(book_id, None)
        if worker:
            worker.deleteLater()

        book = self.card_widgets[book_id].book
        card = self.card_widgets[book_id]
        card.primary_btn.setEnabled(True)
        card.secondary_btn.setEnabled(True)
        
        installed = is_book_installed(book)
        card.update_status(installed, is_offline=self.is_offline)
        
        if success and not installed:
            self.statusBar.showMessage(f"{book['title']} başarıyla kaldırıldı!", 5000)
            self.refresh_grid()
        else:
            self.statusBar.showMessage(f"{book['title']} kaldırma hatası!", 5000)
            QMessageBox.critical(self, "Kaldırma Hatası", f"'{book['title']}' kaldırılırken hata oluştu.")

    def launch_book(self, book):
        if os.environ.get("ETKILESIMLI_KITAP_KUTUPHANESI_DEV") == "1":
            print(f"[GELİŞTİRİCİ MODU] Kitap başlatıldı: {book['title']} (Dosya: {book['file_name']})")
            QMessageBox.information(
                self,
                "Kitap Başlatıldı (Simülasyon)",
                f"Geliştirici Modu:\n'{book['title']}' kütüphane uygulaması simüle edilerek başlatıldı.\n\nYayınevi: {book['publisher']}\nDosya: {book['file_name']}"
            )
            return
        
        file_type = book.get('file_type', 'deb')
        
        if file_type == 'deb':
            package_name = get_deb_package_name(book)
            cmd = ["gtk-launch", package_name]
            
            try:
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.statusBar.showMessage(f"Başlatılıyor: {book['title']}", 3000)
            except Exception as e:
                try:
                    subprocess.Popen([package_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self.statusBar.showMessage(f"Başlatılıyor: {book['title']}", 3000)
                except Exception as e2:
                    self.statusBar.showMessage("Çalıştırma hatası!", 5000)
                    QMessageBox.warning(
                        self, 
                        "Uygulama Başlatılamadı", 
                        f"Kütüphane başlatılamadı.\\nSistem menüsünden (Pardus) aramayı deneyebilirsiniz.\\nDetay: {str(e2)}"
                    )
                    
        elif file_type in ['zip', 'fernus']:
            desktop_name = f"etkilesimli-kitap-kutuphanesi-{book['id']}"
            cmd = ["gtk-launch", desktop_name]
            
            try:
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.statusBar.showMessage(f"Başlatılıyor: {book['title']}", 3000)
            except Exception as e:
                self.statusBar.showMessage("Çalıştırma hatası!", 5000)
                QMessageBox.warning(self, "Uygulama Başlatılamadı", f"Kitap başlatılamadı:\n{str(e)}")
