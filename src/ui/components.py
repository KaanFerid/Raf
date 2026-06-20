from src.qt_compat import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QProgressBar, QFrame, QSizePolicy,
                            Signal, Qt, QPainter, QColor, QFont, QLinearGradient)

class PublisherBadge(QWidget):
    """Draws a premium circular badge with initials of the publisher."""
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.text = text
        self.setFixedSize(64, 64)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Generate a distinct gradient based on the first letter to add visual variety
        first_char = self.text[0].upper() if self.text else 'K'
        char_val = ord(first_char)
        
        # Colors list for gradients
        gradient_presets = [
            (QColor("#0b57d0"), QColor("#00b894")),
            (QColor("#6c5ce7"), QColor("#a29bfe")),
            (QColor("#d63031"), QColor("#ff7675")),
            (QColor("#e17055"), QColor("#ffeaa7")),
            (QColor("#00cec9"), QColor("#81ecec")),
            (QColor("#fd79a8"), QColor("#ffeaa7")),
        ]
        color1, color2 = gradient_presets[char_val % len(gradient_presets)]

        # Draw circle background
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, color1)
        gradient.setColorAt(1, color2)
        
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(2, 2, self.width() - 4, self.height() - 4)

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
        font = QFont("Inter", 16, QFont.Bold)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, initials)


class BookCard(QFrame):
    # Signals
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
        # Card Layout
        card_layout = QHBoxLayout(self)
        card_layout.setContentsMargins(15, 15, 15, 15)
        card_layout.setSpacing(15)

        # 1. Left Icon (Publisher Badge)
        self.badge = PublisherBadge(self.book['publisher'])
        card_layout.addWidget(self.badge, 0, Qt.AlignVCenter)

        # 2. Middle Information Panel
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        self.title_label = QLabel(self.book['title'])
        self.title_label.setObjectName("BookTitleLabel")
        self.title_label.setWordWrap(True)
        info_layout.addWidget(self.title_label)

        self.pub_label = QLabel(self.book['publisher'])
        self.pub_label.setObjectName("PublisherLabel")
        info_layout.addWidget(self.pub_label)

        # File details (Type & Approx Size)
        file_type_str = self.book.get('file_type', 'deb').upper()
        details_str = f"Tür: {file_type_str}"
        self.details_label = QLabel(details_str)
        self.details_label.setStyleSheet("color: #747775; font-size: 11px;")
        info_layout.addWidget(self.details_label)

        # Progress bar (Hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        info_layout.addWidget(self.progress_bar)

        # Download status / speed info (Hidden by default)
        self.status_info_label = QLabel("")
        self.status_info_label.setStyleSheet("color: #fdcb6e; font-size: 11px;")
        self.status_info_label.setVisible(False)
        info_layout.addWidget(self.status_info_label)

        card_layout.addLayout(info_layout, 1)

        # 3. Right Action Panel
        action_layout = QVBoxLayout()
        action_layout.setSpacing(6)
        action_layout.setAlignment(Qt.AlignVCenter | Qt.AlignRight)

        # Status Label
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        action_layout.addWidget(self.status_label)

        # Primary Action Button
        self.primary_btn = QPushButton("Yükle")
        self.primary_btn.clicked.connect(self.on_primary_btn_clicked)
        self.primary_btn.setMinimumWidth(100)
        action_layout.addWidget(self.primary_btn)

        # Secondary Action Button (Uninstall)
        self.secondary_btn = QPushButton("Kaldır")
        self.secondary_btn.setObjectName("UninstallBtn")
        self.secondary_btn.clicked.connect(self.on_secondary_btn_clicked)
        self.secondary_btn.setVisible(False)
        self.secondary_btn.setMinimumWidth(100)
        action_layout.addWidget(self.secondary_btn)

        card_layout.addLayout(action_layout, 0)
        
        self.update_status(self.is_installed)

    def update_status(self, is_installed, downloading=False, percent=0, speed_str=""):
        self.is_installed = is_installed
        self.downloading = downloading

        if downloading:
            self.status_label.setText("İndiriliyor")
            self.status_label.setObjectName("StatusDownloadingLabel")
            self.status_label.setStyleSheet("") # clears custom styles
            
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(percent)
            
            self.status_info_label.setVisible(True)
            self.status_info_label.setText(speed_str)
            
            self.primary_btn.setText("İptal Et")
            self.primary_btn.setStyleSheet("background-color: #3c2a1a; color: #fdcb6e;")
            self.secondary_btn.setVisible(False)
            
        elif is_installed:
            self.status_label.setText("Yüklendi")
            self.status_label.setObjectName("StatusInstalledLabel")
            self.status_label.setStyleSheet("")
            
            self.progress_bar.setVisible(False)
            self.status_info_label.setVisible(False)
            
            self.primary_btn.setText("Çalıştır")
            self.primary_btn.setStyleSheet("background-color: #00b894; color: white;")
            
            # Show uninstall button
            self.secondary_btn.setVisible(True)
            
        else:
            self.status_label.setText("Yüklü Değil")
            self.status_label.setObjectName("StatusNotInstalledLabel")
            self.status_label.setStyleSheet("")
            
            self.progress_bar.setVisible(False)
            self.status_info_label.setVisible(False)
            
            self.primary_btn.setText("Yükle")
            self.primary_btn.setStyleSheet("") # fallback to QSS default
            
            self.secondary_btn.setVisible(False)

        # Refresh QSS styling
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        self.primary_btn.style().unpolish(self.primary_btn)
        self.primary_btn.style().polish(self.primary_btn)

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
class FlowLayout(QWidget):
    # A generic widget container that acts like a grid with flow properties (useful for cards layout)
    # We will implement custom grid layout logic directly in MainWindow using QGridLayout,
    # which is simpler and built-in.
    pass
