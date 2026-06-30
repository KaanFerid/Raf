import sys
from PyQt5.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from PyQt5.QtCore import QTimer

app = QApplication(sys.argv)
win = MainWindow()
win.show()

def inject_log():
    win.logs_dialog.show()
    win.logs_dialog.append_log("TEST LOG 1")
    win.on_install_output("test_book", "This is an output line")

QTimer.singleShot(1000, inject_log)
QTimer.singleShot(2000, app.quit)

app.exec_()
