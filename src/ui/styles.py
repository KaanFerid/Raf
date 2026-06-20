# Libadwaita / Bottles Style Sheets for KitapMarkt

COMMON_STYLE = """
QWidget {
    font-family: 'Inter', 'Segoe UI', sans-serif;
    font-size: 14px;
}

QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 8px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: %SCROLLBAR_HANDLE%;
    min-height: 30px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: %SCROLLBAR_HANDLE_HOVER%;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}
"""

DARK_STYLE = COMMON_STYLE.replace(
    "%SCROLLBAR_HANDLE%", "#4c4c4c"
).replace(
    "%SCROLLBAR_HANDLE_HOVER%", "#6f6f6f"
) + """
QMainWindow {
    background-color: #1e1e1e;
}

/* HeaderBar */
#HeaderWidget {
    background-color: #242424;
    border-bottom: 1px solid #303030;
}

#AppTitleLabel {
    font-size: 18px;
    font-weight: bold;
    color: #ffffff;
}

/* Segmented View Switcher (Bottles style) */
#ViewSwitcherContainer {
    background-color: #303030;
    border-radius: 8px;
    padding: 3px;
}

QPushButton.ViewSwitcherBtn {
    background-color: transparent;
    color: #c0c0c0;
    border: none;
    border-radius: 6px;
    padding: 6px 16px;
    font-weight: 500;
    font-size: 13px;
}

QPushButton.ViewSwitcherBtn:hover {
    color: #ffffff;
    background-color: #383838;
}

QPushButton.ViewSwitcherBtn:checked {
    color: #ffffff;
    background-color: #4a4a4a;
}

/* Inputs & Combo Boxes */
QLineEdit {
    background-color: #2d2d2d;
    border: 1px solid #3a3a3a;
    border-radius: 6px;
    padding: 6px 12px;
    color: #ffffff;
}
QLineEdit:focus {
    border: 1px solid #3584e4;
    background-color: #2d2d2d;
}

QComboBox {
    background-color: #2d2d2d;
    border: 1px solid #3a3a3a;
    border-radius: 6px;
    padding: 6px 24px 6px 12px;
    color: #ffffff;
}
QComboBox:hover {
    background-color: #353535;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background-color: #242424;
    border: 1px solid #3a3a3a;
    color: #ffffff;
    selection-background-color: #3584e4;
    selection-color: #ffffff;
}

/* ListView Items (Book Rows) */
#BookCardFrame {
    background-color: #2d2d2d;
    border: 1px solid #353535;
    border-radius: 10px;
}
#BookCardFrame:hover {
    background-color: #323232;
    border: 1px solid #404040;
}

#BookTitleLabel {
    font-size: 15px;
    font-weight: 600;
    color: #ffffff;
}

#PublisherLabel {
    font-size: 13px;
    color: #9a9a9a;
}

/* Info Subtitle */
#BookDetailsLabel {
    color: #8a8a8a;
    font-size: 12px;
}

/* Buttons */
QPushButton.AdwPrimaryBtn {
    background-color: #3584e4;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 600;
    font-size: 13px;
}
QPushButton.AdwPrimaryBtn:hover {
    background-color: #4a90e2;
}
QPushButton.AdwPrimaryBtn:pressed {
    background-color: #1b6ac6;
}

QPushButton.AdwSecondaryBtn {
    background-color: #3a3a3a;
    color: #ffffff;
    border: 1px solid #4a4a4a;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 500;
    font-size: 13px;
}
QPushButton.AdwSecondaryBtn:hover {
    background-color: #444444;
}

QPushButton.AdwDangerBtn {
    background-color: #c01c28;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 600;
    font-size: 13px;
}
QPushButton.AdwDangerBtn:hover {
    background-color: #d62c39;
}

QPushButton.AdwSuccessBtn {
    background-color: #26a269;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 600;
    font-size: 13px;
}
QPushButton.AdwSuccessBtn:hover {
    background-color: #2ec27e;
}

QPushButton:disabled {
    background-color: #282828;
    color: #606060;
}

/* Progress bar */
QProgressBar {
    background-color: #1a1a1a;
    border: none;
    border-radius: 3px;
    text-align: right;
    color: transparent;
    height: 6px;
}
QProgressBar::chunk {
    background-color: #3584e4;
    border-radius: 3px;
}

/* Status Labels */
#StatusInstalledLabel {
    color: #26a269;
    font-weight: bold;
    font-size: 12px;
}
#StatusNotInstalledLabel {
    color: #8a8a8a;
    font-size: 12px;
}
#StatusDownloadingLabel {
    color: #fdcb6e;
    font-weight: bold;
    font-size: 12px;
}

/* Count Label */
#CountLabel {
    color: #8a8a8a;
    font-size: 13px;
    background-color: #1e1e1e;
}
"""

LIGHT_STYLE = COMMON_STYLE.replace(
    "%SCROLLBAR_HANDLE%", "#c0c0c0"
).replace(
    "%SCROLLBAR_HANDLE_HOVER%", "#a0a0a0"
) + """
QMainWindow {
    background-color: #f6f6f6;
}

/* HeaderBar */
#HeaderWidget {
    background-color: #ebebeb;
    border-bottom: 1px solid #d5d5d5;
}

#AppTitleLabel {
    font-size: 18px;
    font-weight: bold;
    color: #242424;
}

/* Segmented View Switcher (Bottles style) */
#ViewSwitcherContainer {
    background-color: #dedede;
    border-radius: 8px;
    padding: 3px;
}

QPushButton.ViewSwitcherBtn {
    background-color: transparent;
    color: #505050;
    border: none;
    border-radius: 6px;
    padding: 6px 16px;
    font-weight: 500;
    font-size: 13px;
}

QPushButton.ViewSwitcherBtn:hover {
    color: #242424;
    background-color: #e5e5e5;
}

QPushButton.ViewSwitcherBtn:checked {
    color: #242424;
    background-color: #ffffff;
}

/* Inputs & Combo Boxes */
QLineEdit {
    background-color: #ffffff;
    border: 1px solid #d0d0d0;
    border-radius: 6px;
    padding: 6px 12px;
    color: #242424;
}
QLineEdit:focus {
    border: 1px solid #3584e4;
    background-color: #ffffff;
}

QComboBox {
    background-color: #ffffff;
    border: 1px solid #d0d0d0;
    border-radius: 6px;
    padding: 6px 24px 6px 12px;
    color: #242424;
}
QComboBox:hover {
    background-color: #f0f0f0;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #d0d0d0;
    color: #242424;
    selection-background-color: #3584e4;
    selection-color: #ffffff;
}

/* ListView Items (Book Rows) */
#BookCardFrame {
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 10px;
}
#BookCardFrame:hover {
    background-color: #fcfcfc;
    border: 1px solid #d5d5d5;
}

#BookTitleLabel {
    font-size: 15px;
    font-weight: 600;
    color: #242424;
}

#PublisherLabel {
    font-size: 13px;
    color: #6a6a6a;
}

/* Info Subtitle */
#BookDetailsLabel {
    color: #7e7e7e;
    font-size: 12px;
}

/* Buttons */
QPushButton.AdwPrimaryBtn {
    background-color: #3584e4;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 600;
    font-size: 13px;
}
QPushButton.AdwPrimaryBtn:hover {
    background-color: #4a90e2;
}
QPushButton.AdwPrimaryBtn:pressed {
    background-color: #1b6ac6;
}

QPushButton.AdwSecondaryBtn {
    background-color: #e5e5e5;
    color: #242424;
    border: 1px solid #d0d0d0;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 500;
    font-size: 13px;
}
QPushButton.AdwSecondaryBtn:hover {
    background-color: #dcdcdc;
}

QPushButton.AdwDangerBtn {
    background-color: #e01b24;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 600;
    font-size: 13px;
}
QPushButton.AdwDangerBtn:hover {
    background-color: #ec5b62;
}

QPushButton.AdwSuccessBtn {
    background-color: #26a269;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 600;
    font-size: 13px;
}
QPushButton.AdwSuccessBtn:hover {
    background-color: #2ec27e;
}

QPushButton:disabled {
    background-color: #eeeeee;
    color: #b0b0b0;
}

/* Progress bar */
QProgressBar {
    background-color: #e0e0e0;
    border: none;
    border-radius: 3px;
    text-align: right;
    color: transparent;
    height: 6px;
}
QProgressBar::chunk {
    background-color: #3584e4;
    border-radius: 3px;
}

/* Status Labels */
#StatusInstalledLabel {
    color: #26a269;
    font-weight: bold;
    font-size: 12px;
}
#StatusNotInstalledLabel {
    color: #6a6a6a;
    font-size: 12px;
}
#StatusDownloadingLabel {
    color: #d29b22;
    font-weight: bold;
    font-size: 12px;
}

/* Count Label */
#CountLabel {
    color: #6a6a6a;
    font-size: 13px;
    background-color: #f6f6f6;
}
"""
