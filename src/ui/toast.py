from src.qt_compat import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QApplication, Qt, QTimer)
try:
    from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QPoint, QRect
    from PySide6.QtWidgets import QGraphicsOpacityEffect
except ImportError:
    try:
        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QPoint, QRect
        from PyQt6.QtWidgets import QGraphicsOpacityEffect
    except ImportError:
        from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, QPoint, QRect
        from PyQt5.QtWidgets import QGraphicsOpacityEffect


TOAST_OBJECT_NAMES = {
    "info":    "ToastInfo",
    "success": "ToastSuccess",
    "warning": "ToastWarning",
    "error":   "ToastError",
}


class ToastNotification(QWidget):
    """Single floating toast notification widget with slide-in/fade-out animation."""

    def __init__(self, message, toast_type="info", duration=3500, parent=None):
        super().__init__(parent)
        self.duration = duration
        self.setObjectName(TOAST_OBJECT_NAMES.get(toast_type, "ToastInfo"))
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setFixedWidth(320)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)

        self.msg_label = QLabel(message)
        self.msg_label.setWordWrap(True)
        self.msg_label.setObjectName("ToastLabel")
        layout.addWidget(self.msg_label, 1)

        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("ToastCloseBtn")
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.clicked.connect(self.dismiss)
        layout.addWidget(self.close_btn)

        self.adjustSize()

        # Auto-dismiss timer
        self._dismiss_timer = QTimer(self)
        self._dismiss_timer.setSingleShot(True)
        self._dismiss_timer.timeout.connect(self.dismiss)

        # Opacity effect for fade-out
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity_effect)

    def show_animated(self):
        self.show()
        self._dismiss_timer.start(self.duration)

    def dismiss(self):
        self._dismiss_timer.stop()
        # Fade out animation
        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_anim.setDuration(300)
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._fade_anim.finished.connect(self._on_dismissed)
        self._fade_anim.start()

    def _on_dismissed(self):
        self.hide()
        self.deleteLater()
        # Notify the manager
        if self.parent() and hasattr(self.parent(), '_on_toast_dismissed'):
            self.parent()._on_toast_dismissed(self)


class ToastManager(QWidget):
    """Manages a stack of ToastNotification widgets anchored to the bottom-right of the parent window."""

    MARGIN = 16
    SPACING = 10

    def __init__(self, parent=None):
        super().__init__(parent)
        self._toasts = []
        # Make this widget transparent and non-interactive itself
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setStyleSheet("background: transparent;")
        self.hide()

    def show_toast(self, message, toast_type="info", duration=3500):
        """Creates and displays a new toast notification."""
        toast = ToastNotification(message, toast_type, duration, parent=self.parent())
        toast.raise_()
        self._toasts.append(toast)
        self._reposition_all()
        toast.show_animated()

    def _on_toast_dismissed(self, toast):
        """Called when a toast finishes its dismiss animation."""
        if toast in self._toasts:
            self._toasts.remove(toast)
        self._reposition_all()

    def _reposition_all(self):
        """Repositions all active toasts stacked in the bottom-right corner."""
        parent = self.parent()
        if not parent:
            return

        parent_rect = parent.rect()
        bottom = parent_rect.bottom() - self.MARGIN - 30  # 30px above status bar

        # Stack toasts from bottom to top
        for toast in reversed(self._toasts):
            if not toast.isVisible():
                continue
            toast.adjustSize()
            x = parent_rect.right() - toast.width() - self.MARGIN
            y = bottom - toast.height()
            toast.move(x, y)
            bottom = y - self.SPACING
            toast.raise_()
