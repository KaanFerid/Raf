import sys

try:
    # Try importing PySide6
    from PySide6 import QtCore, QtWidgets, QtGui
    from PySide6.QtCore import Signal, Slot, Qt, QThread, QTimer, QEvent, QEventLoop, QObject
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QLineEdit, QComboBox, QScrollArea,
        QMessageBox, QStatusBar, QSizePolicy, QPushButton, QProgressBar, QFrame,
        QDialog, QButtonGroup, QRadioButton, QGroupBox, QFileDialog, QPlainTextEdit
    )
    from PySide6.QtGui import QPainter, QColor, QFont, QIcon, QPixmap, QPen
    QT_API = "PySide6"
except ImportError:
    # Fallback to PyQt6
    try:
        from PyQt6 import QtCore, QtWidgets, QtGui
        from PyQt6.QtCore import pyqtSignal as Signal, pyqtSlot as Slot, Qt, QThread, QTimer, QEvent, QEventLoop, QObject
        from PyQt6.QtWidgets import (
            QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
            QLabel, QLineEdit, QComboBox, QScrollArea,
            QMessageBox, QStatusBar, QSizePolicy, QPushButton, QProgressBar, QFrame,
            QDialog, QButtonGroup, QRadioButton, QGroupBox, QFileDialog, QPlainTextEdit
        )
        from PyQt6.QtGui import QPainter, QColor, QFont, QIcon, QPixmap, QPen
        QT_API = "PyQt6"
        
        # Map enum values for compatibility with PySide6-style access
        if not hasattr(Qt, "NoPen"):
            Qt.NoPen = Qt.PenStyle.NoPen
        if not hasattr(Qt, "RoundCap"):
            Qt.RoundCap = Qt.PenCapStyle.RoundCap
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
        if not hasattr(Qt, "transparent"):
            Qt.transparent = Qt.GlobalColor.transparent
        if not hasattr(QLineEdit, "LeadingPosition"):
            QLineEdit.LeadingPosition = QLineEdit.ActionPosition.LeadingPosition
        if not hasattr(QSizePolicy, "Fixed"):
            QSizePolicy.Fixed = QSizePolicy.Policy.Fixed
        if not hasattr(QSizePolicy, "Preferred"):
            QSizePolicy.Preferred = QSizePolicy.Policy.Preferred
        if not hasattr(QFont, "Bold"):
            QFont.Bold = QFont.Weight.Bold
        if not hasattr(QPainter, "Antialiasing"):
            QPainter.Antialiasing = QPainter.RenderHint.Antialiasing
        if not hasattr(QFrame, "NoFrame"):
            QFrame.NoFrame = QFrame.Shape.NoFrame
        if not hasattr(QMessageBox, "Yes"):
            QMessageBox.Yes = QMessageBox.StandardButton.Yes
        if not hasattr(QMessageBox, "No"):
            QMessageBox.No = QMessageBox.StandardButton.No
        if not hasattr(QEvent, "FocusIn"):
            QEvent.FocusIn = QEvent.Type.FocusIn
        if not hasattr(QEvent, "MouseButtonPress"):
            QEvent.MouseButtonPress = QEvent.Type.MouseButtonPress
    except ImportError:
        # Fallback to PyQt5
        try:
            from PyQt5 import QtCore, QtWidgets, QtGui
            from PyQt5.QtCore import pyqtSignal as Signal, pyqtSlot as Slot, Qt, QThread, QTimer, QEvent, QEventLoop, QObject
            from PyQt5.QtWidgets import (
                QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                QLabel, QLineEdit, QComboBox, QScrollArea,
                QMessageBox, QStatusBar, QSizePolicy, QPushButton, QProgressBar, QFrame,
                QDialog, QButtonGroup, QRadioButton, QGroupBox, QFileDialog, QPlainTextEdit
            )
            from PyQt5.QtGui import QPainter, QColor, QFont, QIcon, QPixmap, QPen
            QT_API = "PyQt5"
        except ImportError:
            print("Error: PySide6, PyQt6 or PyQt5 library not found!")
            print("Please install one of them via 'pip install PySide6', 'pip install PyQt6' or 'pip install PyQt5'.")
            sys.exit(1)
