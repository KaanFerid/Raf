import sys

try:
    # Try importing PySide6
    from PySide6 import QtCore, QtWidgets, QtGui
    from PySide6.QtCore import Signal, Slot, Qt, QThread, QTimer, QEvent
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QLineEdit, QComboBox, QScrollArea, QGridLayout,
        QMessageBox, QStatusBar, QSizePolicy, QPushButton, QProgressBar, QFrame,
        QMenu, QDialog, QButtonGroup, QRadioButton, QGroupBox
    )
    from PySide6.QtGui import QPainter, QColor, QFont, QLinearGradient, QAction
    QT_API = "PySide6"
except ImportError:
    # Fallback to PyQt6
    try:
        from PyQt6 import QtCore, QtWidgets, QtGui
        from PyQt6.QtCore import pyqtSignal as Signal, pyqtSlot as Slot, Qt, QThread, QTimer, QEvent
        from PyQt6.QtWidgets import (
            QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
            QLabel, QLineEdit, QComboBox, QScrollArea, QGridLayout,
            QMessageBox, QStatusBar, QSizePolicy, QPushButton, QProgressBar, QFrame,
            QMenu, QDialog, QButtonGroup, QRadioButton, QGroupBox
        )
        from PyQt6.QtGui import QPainter, QColor, QFont, QLinearGradient, QAction
        QT_API = "PyQt6"
        
        # Map enum values for compatibility with PyQt5/PySide6
        if not hasattr(Qt, "NoPen"):
            Qt.NoPen = Qt.PenStyle.NoPen
        if not hasattr(Qt, "AlignCenter"):
            Qt.AlignCenter = Qt.AlignmentFlag.AlignCenter
        if not hasattr(Qt, "AlignVCenter"):
            Qt.AlignVCenter = Qt.AlignmentFlag.AlignVCenter
        if not hasattr(Qt, "AlignRight"):
            Qt.AlignRight = Qt.AlignmentFlag.AlignRight
        if not hasattr(Qt, "AlignTop"):
            Qt.AlignTop = Qt.AlignmentFlag.AlignTop
        if not hasattr(Qt, "AlignLeft"):
            Qt.AlignLeft = Qt.AlignmentFlag.AlignLeft
    except ImportError:
        # Fallback to PyQt5
        try:
            from PyQt5 import QtCore, QtWidgets, QtGui
            from PyQt5.QtCore import pyqtSignal as Signal, pyqtSlot as Slot, Qt, QThread, QTimer, QEvent
            from PyQt5.QtWidgets import (
                QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                QLabel, QLineEdit, QComboBox, QScrollArea, QGridLayout,
                QMessageBox, QStatusBar, QSizePolicy, QPushButton, QProgressBar, QFrame,
                QMenu, QDialog, QButtonGroup, QRadioButton, QGroupBox, QAction
            )
            from PyQt5.QtGui import QPainter, QColor, QFont, QLinearGradient
            QT_API = "PyQt5"
        except ImportError:
            print("Hata: PySide6, PyQt6 veya PyQt5 kütüphanesi bulunamadı!")
            print("Lütfen 'pip install PySide6', 'pip install PyQt6' veya 'pip install PyQt5' komutuyla birini kurun.")
            sys.exit(1)
