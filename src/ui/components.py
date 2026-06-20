from src.qt_compat import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QProgressBar, QFrame, QSizePolicy,
                             Signal, Qt, QPainter, QColor, QFont)

class PublisherBadge(QWidget):
    """Draws a clean flat Adwaita-style rounded-square avatar with publisher initials."""
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.text = text
        self.setFixedSize(48, 48)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        first_char = self.text[0].upper() if self.text else 'K'
        char_val = ord(first_char)
        
        # Flat Libadwaita color palette
        flat_colors = [
            QColor("#3584e4"),  # Blue
            QColor("#26a269"),  # Green
            QColor("#e66100"),  # Orange
            QColor("#782a7f"),  # Purple
            QColor("#c01c28"),  # Red
            QColor("#1a5fb4"),  # Dark Blue
            QColor("#986a44"),  # Brown
            QColor("#62ae87"),  # Light Green
        ]
        color = flat_colors[char_val % len(flat_colors)]
        
        # Draw rounded rectangle background (flat, no gradient)
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 10, 10)

        # Draw initials (up to 2 characters)
        words = self.text.split()
        initials = ""
        if len(words) >= 2:
            initials = words[0][0] + words[1][0]
        elif len(words) == 1:
            initials = words[0][:2]
        else:
            initials = "KM"
        initials = initials.upper()

        painter.setPen(QColor("#ffffff"))
        font = QFont("Inter", 13, QFont.Bold)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, initials)


class BookCard(QFrame):
    # Signals (Preserve connections with MainWindow)
    install_requested = Signal(dict)
    uninstall_requested = Signal(dict)
    launch_requested = Signal(dict)
    cancel_requested = Signal(dict)

    def __init__(self, book, is_installed=False, parent=None):
        super().__init__(parent)
        self.book = book
        self.book_id = book['id']
        self.is_installed = is_installed
        self.downloading = False
        
        self.setObjectName("BookCardFrame")
        self.init_ui()

    def init_ui(self):
        # Clean Horizontal Layout (Libadwaita row structure)
        card_layout = QHBoxLayout(self)
        card_layout.setContentsMargins(16, 12, 16, 12)
        card_layout.setSpacing(16)

        # 1. Left Icon / Badge
        self.badge = PublisherBadge(self.book['publisher'])
        card_layout.addWidget(self.badge, 0, Qt.AlignVCenter)

        # 2. Middle Info Panel (Title, Publisher, Size, Progress)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(3)

        self.title_label = QLabel(self.book['title'])
        self.title_label.setObjectName("BookTitleLabel")
        self.title_label.setWordWrap(True)
        info_layout.addWidget(self.title_label)

        # Subtitle containing Publisher and Book Format details
        self.pub_label = QLabel(self.book['publisher'])
        self.pub_label.setObjectName("PublisherLabel")
        info_layout.addWidget(self.pub_label)

        file_type_str = self.book.get('file_type', 'deb').upper()
        self.details_label = QLabel(f"Tür: {file_type_str}")
        self.details_label.setObjectName("BookDetailsLabel")
        info_layout.addWidget(self.details_label)

        # Flat Progress bar (hidden by default, shown during downloads)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        info_layout.addWidget(self.progress_bar)

        # Download speed / state info text
        self.status_info_label = QLabel("")
        self.status_info_label.setStyleSheet("color: #3584e4; font-size: 11px; font-weight: 500;")
        self.status_info_label.setVisible(False)
        info_layout.addWidget(self.status_info_label)

        card_layout.addLayout(info_layout, 1)

        # 3. Right Control Panel (Status indicator + Action Buttons)
        action_layout = QHBoxLayout()
        action_layout.setSpacing(12)
        action_layout.setAlignment(Qt.AlignVCenter | Qt.AlignRight)

        # Simple status text label
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        action_layout.addWidget(self.status_label)

        # Primary Action Button
        self.primary_btn = QPushButton("Yükle")
        self.primary_btn.clicked.connect(self.on_primary_btn_clicked)
        self.primary_btn.setMinimumWidth(90)
        action_layout.addWidget(self.primary_btn)

        # Secondary Action Button (Uninstall)
        self.secondary_btn = QPushButton("Kaldır")
        self.secondary_btn.clicked.connect(self.on_secondary_btn_clicked)
        self.secondary_btn.setVisible(False)
        self.secondary_btn.setMinimumWidth(90)
        action_layout.addWidget(self.secondary_btn)

        card_layout.addLayout(action_layout, 0)
        
        self.update_status(self.is_installed)

    def update_status(self, is_installed, downloading=False, percent=0, speed_str=""):
        self.is_installed = is_installed
        self.downloading = downloading

        if downloading:
            self.status_label.setText("İndiriliyor")
            self.status_label.setObjectName("StatusDownloadingLabel")
            
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(percent)
            
            self.status_info_label.setVisible(True)
            self.status_info_label.setText(speed_str)
            
            self.primary_btn.setText("İptal Et")
            self.primary_btn.setProperty("class", "AdwSecondaryBtn")
            self.secondary_btn.setVisible(False)
            
        elif is_installed:
            self.status_label.setText("Yüklendi")
            self.status_label.setObjectName("StatusInstalledLabel")
            
            self.progress_bar.setVisible(False)
            self.status_info_label.setVisible(False)
            
            self.primary_btn.setText("Çalıştır")
            self.primary_btn.setProperty("class", "AdwSuccessBtn")
            
            # Show secondary uninstall button
            self.secondary_btn.setVisible(True)
            self.secondary_btn.setProperty("class", "AdwDangerBtn")
            
        else:
            self.status_label.setText("Yüklü Değil")
            self.status_label.setObjectName("StatusNotInstalledLabel")
            
            self.progress_bar.setVisible(False)
            self.status_info_label.setVisible(False)
            
            self.primary_btn.setText("Yükle")
            self.primary_btn.setProperty("class", "AdwPrimaryBtn")
            
            self.secondary_btn.setVisible(False)

        # Refresh style repainting dynamically
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        self.primary_btn.style().unpolish(self.primary_btn)
        self.primary_btn.style().polish(self.primary_btn)
        self.secondary_btn.style().unpolish(self.secondary_btn)
        self.secondary_btn.style().polish(self.secondary_btn)

    def on_primary_btn_clicked(self):
        if self.downloading:
            self.cancel_requested.emit(self.book)
        elif self.is_installed:
            self.launch_requested.emit(self.book)
        else:
            self.install_requested.emit(self.book)

    def on_secondary_btn_clicked(self):
        if self.is_installed and not self.downloading:
            self.uninstall_requested.emit(self.book)
