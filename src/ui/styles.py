# Modern QSS (Qt Style Sheets) for KitapMarkt

MODERN_STYLE = """
/* Global Window Styles */
QMainWindow {
    background-color: #12131a;
}

QWidget {
    font-family: 'Inter', 'Outfit', 'Google Sans Text', sans-serif;
    color: #e3e3e3;
    font-size: 14px;
}

/* ScrollBar Styles */
QScrollBar:vertical {
    border: none;
    background: #1e1f29;
    width: 10px;
    margin: 0px 0px 0px 0px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #4a4b5d;
    min-height: 20px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #0b57d0;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}

/* Header & Search Bar */
#HeaderWidget {
    background-color: #1a1b26;
    border-bottom: 1px solid #2a2b3d;
    padding: 10px;
}

#AppTitleLabel {
    font-size: 22px;
    font-weight: bold;
    color: #ffffff;
    padding-left: 10px;
}

QLineEdit {
    background-color: #1e1f29;
    border: 2px solid #2a2b3d;
    border-radius: 20px;
    padding: 10px 20px;
    color: #ffffff;
    font-size: 15px;
}
QLineEdit:focus {
    border: 2px solid #0b57d0;
    background-color: #242636;
}

/* Filter Combo Box */
QComboBox {
    background-color: #1e1f29;
    border: 2px solid #2a2b3d;
    border-radius: 20px;
    padding: 8px 15px;
    color: #ffffff;
    font-size: 14px;
    min-width: 150px;
}
QComboBox:hover {
    border: 2px solid #0b57d0;
}
QComboBox::drop-down {
    border: none;
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 30px;
}
QComboBox QAbstractItemView {
    background-color: #1e1f29;
    border: 2px solid #2a2b3d;
    selection-background-color: #0b57d0;
    selection-color: white;
}

/* Book Card Styles */
#BookCardFrame {
    background-color: #1e1f29;
    border: 1px solid #2a2b3d;
    border-radius: 16px;
}
#BookCardFrame:hover {
    border: 2px solid #0b57d0;
    background-color: #242636;
}

#BookTitleLabel {
    font-size: 16px;
    font-weight: bold;
    color: #ffffff;
}

#PublisherLabel {
    font-size: 13px;
    color: #9aa0a6;
    font-weight: 500;
}

#DescriptionLabel {
    font-size: 12px;
    color: #bdc1c6;
}

/* Progress Bar */
QProgressBar {
    background-color: #12131a;
    border: none;
    border-radius: 6px;
    text-align: center;
    color: white;
    font-weight: bold;
    font-size: 11px;
    height: 12px;
}
QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0b57d0, stop:1 #00b894);
    border-radius: 6px;
}

/* Custom Buttons */
QPushButton {
    background-color: #0b57d0;
    border: none;
    border-radius: 18px;
    padding: 8px 16px;
    color: white;
    font-weight: bold;
    font-size: 13px;
    min-height: 20px;
}
QPushButton:hover {
    background-color: #1a73e8;
}
QPushButton:pressed {
    background-color: #0d559f;
}
QPushButton:disabled {
    background-color: #2a2b3d;
    color: #5f6368;
}

/* Secondary Button (Uninstall / Open) */
QPushButton#SecondaryActionBtn {
    background-color: #2a2b3d;
    color: #e3e3e3;
    border: 1px solid #3a3b50;
}
QPushButton#SecondaryActionBtn:hover {
    background-color: #3a3b50;
    color: #ffffff;
}

QPushButton#UninstallBtn {
    background-color: #3a1a1a;
    color: #ff7675;
    border: 1px solid #5a2a2a;
}
QPushButton#UninstallBtn:hover {
    background-color: #d63031;
    color: white;
}

/* Status Labels */
#StatusInstalledLabel {
    color: #00b894;
    font-weight: bold;
    font-size: 12px;
}

#StatusNotInstalledLabel {
    color: #9aa0a6;
    font-size: 12px;
}

#StatusDownloadingLabel {
    color: #fdcb6e;
    font-weight: bold;
    font-size: 12px;
}
"""
