from PyQt5.QtCore import pyqtSignal as Signal, Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QFrame, QSizePolicy
from PyQt5.QtGui import QPainter, QColor, QFont
from src.core.translation import tr

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
    selection_changed = Signal(str, bool)  # book_id, is_selected

    def __init__(self, book, is_installed=False, parent=None):
        super().__init__(parent)
        self.book = book
        self.book_id = book['id']
        self.is_installed = is_installed
        self.downloading = False
        self.is_queued = False        # True when waiting in the download queue
        self.is_selected = False      # True in batch selection mode
        self._selection_mode = False  # Whether selection mode is globally active
        
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
        self.details_label = QLabel(tr("ui.type_label", type=file_type_str))
        self.details_label.setObjectName("BookDetailsLabel")
        info_layout.addWidget(self.details_label)

        # Flat Progress bar (hidden by default, shown during downloads)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        info_layout.addWidget(self.progress_bar)

        # Download speed / state info text
        self.status_info_label = QLabel("")
        self.status_info_label.setObjectName("StatusInfoLabel")
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
        self.primary_btn = QPushButton(tr("ui.install_btn"))
        self.primary_btn.clicked.connect(self.on_primary_btn_clicked)
        self.primary_btn.setMinimumWidth(90)
        action_layout.addWidget(self.primary_btn)

        # Secondary Action Button (Uninstall)
        self.secondary_btn = QPushButton(tr("ui.uninstall_btn"))
        self.secondary_btn.clicked.connect(self.on_secondary_btn_clicked)
        self.secondary_btn.setVisible(False)
        self.secondary_btn.setMinimumWidth(90)
        action_layout.addWidget(self.secondary_btn)

        # Tertiary Action Button (Edit Launcher)
        self.edit_launcher_btn = QPushButton(tr("ui.edit_launcher"))
        self.edit_launcher_btn.setProperty("class", "AdwSecondaryBtn")
        self.edit_launcher_btn.clicked.connect(self.on_edit_launcher_clicked)
        self.edit_launcher_btn.setVisible(False)
        self.edit_launcher_btn.setMinimumWidth(100)
        action_layout.addWidget(self.edit_launcher_btn)

        # Selection checkbox (shown in batch selection mode)
        self.select_checkbox = QPushButton("☐")
        self.select_checkbox.setObjectName("SelectCheckbox")
        self.select_checkbox.setFixedSize(32, 32)
        self.select_checkbox.setVisible(False)
        self.select_checkbox.clicked.connect(self._toggle_selection)
        action_layout.addWidget(self.select_checkbox)

        card_layout.addLayout(action_layout, 0)
        
        self.update_status(self.is_installed)

    def set_selection_mode(self, active):
        """Shows/hides the selection checkbox. Clears selection when exiting mode."""
        self._selection_mode = active
        self.select_checkbox.setVisible(active)
        if not active:
            self.is_selected = False
            self.select_checkbox.setText("☐")
            self.setProperty("selected", False)
            self.style().unpolish(self)
            self.style().polish(self)

    def _toggle_selection(self):
        """Toggles the selected state of this card."""
        self.is_selected = not self.is_selected
        self.select_checkbox.setText("☑" if self.is_selected else "☐")
        self.selection_changed.emit(self.book_id, self.is_selected)

    def set_queued(self, queued):
        """Marks this card as waiting in the download queue."""
        self.is_queued = queued
        if queued:
            self.status_label.setText(tr("ui.queued_btn"))
            self.status_label.setObjectName("StatusQueuedLabel")
            self.primary_btn.setText(tr("ui.cancel_btn"))
            self.primary_btn.setProperty("class", "AdwSecondaryBtn")
            self.primary_btn.setEnabled(True)
            self.secondary_btn.setVisible(False)
            self.edit_launcher_btn.setVisible(False)
            self.progress_bar.setVisible(False)
            self.status_info_label.setVisible(False)
            self.status_label.style().unpolish(self.status_label)
            self.status_label.style().polish(self.status_label)

    def update_status(self, is_installed, downloading=False, percent=0, speed_str="", is_offline=False):
        self.is_installed = is_installed
        self.downloading = downloading

        # Queued state takes precedence over idle states (but not active downloads)
        if self.is_queued and not downloading:
            self.set_queued(True)
            return

        if downloading:
            self.is_queued = False
            self.status_label.setText(tr("ui.downloading_btn"))
            self.status_label.setObjectName("StatusDownloadingLabel")
            
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(percent)
            
            self.status_info_label.setVisible(True)
            self.status_info_label.setText(speed_str)
            
            self.primary_btn.setText(tr("ui.cancel_btn"))
            self.primary_btn.setProperty("class", "AdwSecondaryBtn")
            self.primary_btn.setEnabled(True)
            self.primary_btn.setToolTip("")
            self.secondary_btn.setVisible(False)
            self.edit_launcher_btn.setVisible(False)
            
        elif is_installed:
            self.status_label.setText(tr("ui.installed_btn"))
            self.status_label.setObjectName("StatusInstalledLabel")
            
            self.progress_bar.setVisible(False)
            self.status_info_label.setVisible(False)
            
            self.primary_btn.setText(tr("ui.run_btn"))
            self.primary_btn.setProperty("class", "AdwSuccessBtn")
            self.primary_btn.setEnabled(True)
            self.primary_btn.setToolTip("")
            
            # Show secondary uninstall button
            self.secondary_btn.setVisible(True)
            self.secondary_btn.setProperty("class", "AdwDangerBtn")
            
            # Show tertiary edit launcher button if it's a local app or we just want to allow editing for all installed apps
            self.edit_launcher_btn.setVisible(True)
            
        else:
            self.status_label.setText(tr("ui.not_installed_btn"))
            self.status_label.setObjectName("StatusNotInstalledLabel")
            
            self.progress_bar.setVisible(False)
            self.status_info_label.setVisible(False)
            
            self.primary_btn.setText(tr("ui.install_btn"))
            self.primary_btn.setProperty("class", "AdwPrimaryBtn")
            if is_offline:
                self.primary_btn.setEnabled(False)
                self.primary_btn.setToolTip(tr("ui.offline_download_tooltip"))
            else:
                self.primary_btn.setEnabled(True)
                self.primary_btn.setToolTip("")
                
            self.secondary_btn.setVisible(False)
            self.edit_launcher_btn.setVisible(False)

        # Refresh style repainting dynamically
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        self.primary_btn.style().unpolish(self.primary_btn)
        self.primary_btn.style().polish(self.primary_btn)
        self.secondary_btn.style().unpolish(self.secondary_btn)
        self.secondary_btn.style().polish(self.secondary_btn)

    def retranslate_ui(self, is_offline=False):
        file_type_str = self.book.get('file_type', 'deb').upper()
        self.details_label.setText(tr("ui.type_label", type=file_type_str))
        self.secondary_btn.setText(tr("ui.uninstall_btn"))
        self.update_status(self.is_installed, self.downloading, self.progress_bar.value(), self.status_info_label.text(), is_offline=is_offline)

    def on_primary_btn_clicked(self):
        if self.is_installed:
            self.launch_requested.emit(self.book)
        elif self.downloading or self.is_queued:
            self.cancel_requested.emit(self.book)
        else:
            self.install_requested.emit(self.book)

    def on_secondary_btn_clicked(self):
        if self.is_installed and not self.downloading:
            self.uninstall_requested.emit(self.book)

    def on_edit_launcher_clicked(self):
        from src.ui.desktop_editor import DesktopEditorDialog
        dialog = DesktopEditorDialog(self.book, self.window())
        dialog.exec_()
