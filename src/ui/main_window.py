import os
import subprocess
from src.qt_compat import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QLineEdit, QComboBox, QScrollArea, 
                            QGridLayout, QMessageBox, QStatusBar, QSizePolicy,
                            Qt, QTimer, QFrame)
from src.ui.styles import MODERN_STYLE
from src.ui.components import BookCard
from src.core.database import Database
from src.core.downloader import DownloadWorker
from src.core.installer import InstallerWorker, is_book_installed, get_deb_package_name, get_all_installed_packages

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KitapMarkt - Pardus Akıllı Tahta Kitap Marketi")
        self.resize(1100, 750)
        self.setMinimumSize(800, 600)
        
        # Apply CSS style sheet
        self.setStyleSheet(MODERN_STYLE)

        # Core components
        print("Kitap veritabanı yükleniyor...")
        self.db = Database()
        print(f"Veritabanı yüklendi. Toplam {len(self.db.get_all_books())} kitap mevcut.")
        
        # State tracking
        self.active_downloads = {}      # book_id -> DownloadWorker
        self.active_installations = {}  # book_id -> InstallerWorker
        self.card_widgets = {}          # book_id -> BookCard
        
        self.init_ui()
        
        # Periodically refresh installation status of displayed items
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_all_statuses)
        self.refresh_timer.start(5000) # every 5 seconds

    def init_ui(self):
        # Main Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Header Area Widget
        header_widget = QWidget()
        header_widget.setObjectName("HeaderWidget")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(20, 15, 20, 15)
        header_layout.setSpacing(20)

        # App Title / Branding
        logo_title_layout = QHBoxLayout()
        logo_title_layout.setSpacing(10)
        app_title = QLabel("KitapMarkt")
        app_title.setObjectName("AppTitleLabel")
        logo_title_layout.addWidget(app_title)
        
        subtitle = QLabel("|  Pardus Akıllı Tahta")
        subtitle.setStyleSheet("color: #747775; font-size: 14px; font-weight: 500;")
        logo_title_layout.addWidget(subtitle)
        header_layout.addLayout(logo_title_layout)

        header_layout.addStretch(1)

        # Search Bar Input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Kitap veya yayınevi ara...")
        self.search_input.setMinimumWidth(300)
        self.search_input.textChanged.connect(self.on_search_changed)
        header_layout.addWidget(self.search_input)

        # Publisher Filter Combo Box
        self.publisher_combo = QComboBox()
        self.publisher_combo.addItem("Tüm Yayıncılar")
        # Extract unique publishers
        publishers = sorted(list(set(b['publisher'] for b in self.db.get_all_books())))
        for pub in publishers:
            self.publisher_combo.addItem(pub)
        self.publisher_combo.currentTextChanged.connect(self.on_filter_changed)
        header_layout.addWidget(self.publisher_combo)

        main_layout.addWidget(header_widget)

        # 2. Count Label
        self.count_label = QLabel("")
        self.count_label.setStyleSheet("color: #9aa0a6; padding: 10px 25px; font-size: 13px; background-color: #12131a;")
        main_layout.addWidget(self.count_label)

        # 3. Content Scroll Area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("background-color: #12131a;")
        
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background-color: #12131a;")
        
        # Grid layout for books
        self.grid_layout = QGridLayout(self.scroll_content)
        self.grid_layout.setContentsMargins(25, 10, 25, 25)
        self.grid_layout.setSpacing(20)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(scroll_area, 1)

        # 4. Status Bar
        self.statusBar = QStatusBar()
        self.statusBar.setStyleSheet("background-color: #1a1b26; color: #9aa0a6; border-top: 1px solid #2a2b3d;")
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Hazır")

        # Load initial cards
        self.refresh_grid()

    def resizeEvent(self, event):
        """Implement responsive columns for cards grid layout based on window width."""
        super().resizeEvent(event)
        self.refresh_grid()

    def get_columns_count(self):
        width = self.width()
        if width < 700:
            return 1
        elif width < 1150:
            return 2
        else:
            return 3

    def get_filtered_books(self):
        query = self.search_input.text()
        pub_filter = self.publisher_combo.currentText()
        
        books = self.db.search_books(query)
        if pub_filter != "Tüm Yayıncılar":
            books = [b for b in books if b['publisher'] == pub_filter]
        return books

    def refresh_grid(self):
        # Clear current layout
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.hide()

        # Get filtered books list
        books = self.get_filtered_books()
        self.count_label.setText(f"{len(books)} kitap listelendi.")

        # Query all installed packages once to avoid freezing the GUI with multiple subprocess calls
        installed_set = get_all_installed_packages()

        cols = self.get_columns_count()
        for idx, book in enumerate(books):
            book_id = book['id']
            
            # Reuse widget if exists, otherwise create it
            if book_id in self.card_widgets:
                card = self.card_widgets[book_id]
            else:
                installed = is_book_installed(book, installed_set)
                card = BookCard(book, is_installed=installed)
                card.install_requested.connect(self.start_download)
                card.uninstall_requested.connect(self.start_uninstallation)
                card.launch_requested.connect(self.launch_book)
                card.cancel_requested.connect(self.cancel_download)
                self.card_widgets[book_id] = card
            
            # Add to grid
            row = idx // cols
            col = idx % cols
            self.grid_layout.addWidget(card, row, col)
            card.show()

    def refresh_all_statuses(self):
        """Check all books' actual installation state in the background."""
        # Query installed packages once
        installed_set = get_all_installed_packages()
        
        for book_id, card in self.card_widgets.items():
            # Skip if currently downloading or installing
            if book_id in self.active_downloads or book_id in self.active_installations:
                continue
            
            installed = is_book_installed(card.book, installed_set)
            if card.is_installed != installed:
                card.update_status(installed)

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
        cache_dir = os.path.expanduser("~/.cache/kitapmarkt/downloads")
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
            # Handle unknown download size (-1 percent)
            pct = percent if percent >= 0 else 50
            card.update_status(is_installed=False, downloading=True, percent=pct, speed_str=speed_str)

    def on_download_finished(self, book_id, local_file_path):
        worker = self.active_downloads.pop(book_id, None)
        if worker:
            worker.deleteLater()

        # Trigger installation immediately
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
        # We can log this output to file or console
        print(f"[{book_id} install stdout]: {text.strip()}")

    def on_installation_finished(self, book_id, success):
        worker = self.active_installations.pop(book_id, None)
        if worker:
            worker.deleteLater()

        book = self.card_widgets[book_id].book
        card = self.card_widgets[book_id]
        card.primary_btn.setEnabled(True)
        
        installed = is_book_installed(book)
        card.update_status(installed)
        
        if success and installed:
            self.statusBar.showMessage(f"{book['title']} başarıyla kuruldu!", 5000)
            # Remove cached deb package to free up smart board space
            if book.get('file_type') == 'deb':
                try:
                    cache_dir = os.path.expanduser("~/.cache/kitapmarkt/downloads")
                    local_file_path = os.path.join(cache_dir, book['file_name'])
                    if os.path.exists(local_file_path):
                        os.remove(local_file_path)
                except:
                    pass
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
        card.update_status(installed)
        
        if success and not installed:
            self.statusBar.showMessage(f"{book['title']} başarıyla kaldırıldı!", 5000)
        else:
            self.statusBar.showMessage(f"{book['title']} kaldırma hatası!", 5000)
            QMessageBox.critical(self, "Kaldırma Hatası", f"'{book['title']}' kaldırılırken hata oluştu.")

    def launch_book(self, book):
        file_type = book.get('file_type', 'deb')
        
        if file_type == 'deb':
            package_name = get_deb_package_name(book)
            # Try launching using gtk-launch
            cmd = ["gtk-launch", package_name]
            
            try:
                # Run detached
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.statusBar.showMessage(f"Başlatılıyor: {book['title']}", 3000)
            except Exception as e:
                # If gtk-launch fails, try running the package name directly as a command fallback
                try:
                    subprocess.Popen([package_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self.statusBar.showMessage(f"Başlatılıyor: {book['title']}", 3000)
                except Exception as e2:
                    self.statusBar.showMessage("Çalıştırma hatası!", 5000)
                    QMessageBox.warning(
                        self, 
                        "Uygulama Başlatılamadı", 
                        f"Kütüphane başlatılamadı.\nSistem menüsünden (Pardus) aramayı deneyebilirsiniz.\nDetay: {str(e2)}"
                    )
                    
        elif file_type in ['zip', 'fernus']:
            # Launch via our custom desktop file
            desktop_name = f"kitapmarkt-{book['id']}"
            cmd = ["gtk-launch", desktop_name]
            
            try:
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.statusBar.showMessage(f"Başlatılıyor: {book['title']}", 3000)
            except Exception as e:
                self.statusBar.showMessage("Çalıştırma hatası!", 5000)
                QMessageBox.warning(self, "Uygulama Başlatılamadı", f"Kitap başlatılamadı:\n{str(e)}")
