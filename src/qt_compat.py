import sys

try:
    # Try importing PySide6
    from PySide6 import QtCore, QtWidgets, QtGui
    from PySide6.QtCore import Signal, Slot, Qt, QThread, QTimer
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QLineEdit, QComboBox, QScrollArea, QGridLayout,
        QMessageBox, QStatusBar, QSizePolicy, QPushButton, QProgressBar, QFrame
    )
    from PySide6.QtGui import QPainter, QColor, QFont, QLinearGradient
    QT_API = "PySide6"
except ImportError:
    # Fallback to PyQt5
    try:
        from PyQt5 import QtCore, QtWidgets, QtGui
        from PyQt5.QtCore import pyqtSignal as Signal, pyqtSlot as Slot, Qt, QThread, QTimer
        from PyQt5.QtWidgets import (
            QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
            QLabel, QLineEdit, QComboBox, QScrollArea, QGridLayout,
            QMessageBox, QStatusBar, QSizePolicy, QPushButton, QProgressBar, QFrame
        )
        from PyQt5.QtGui import QPainter, QColor, QFont, QLinearGradient
        QT_API = "PyQt5"
    except ImportError:
        print("Hata: PySide6 veya PyQt5 kütüphanesi bulunamadı!")
        print("Lütfen 'pip install PySide6' veya 'pip install PyQt5' komutuyla birini kurun.")
        sys.exit(1)
