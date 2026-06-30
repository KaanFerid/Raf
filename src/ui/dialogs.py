from PyQt5.QtWidgets import QMessageBox
from src.core.translation import tr

class RafMessageBox:
    @staticmethod
    def question(parent, title, text, default_no=True):
        msg = QMessageBox(parent)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(QMessageBox.Question)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.button(QMessageBox.Yes).setText(tr("ui.yes", default="Yes"))
        msg.button(QMessageBox.No).setText(tr("ui.no", default="No"))
        if default_no:
            msg.setDefaultButton(QMessageBox.No)
        return msg.exec_() == QMessageBox.Yes

    @staticmethod
    def information(parent, title, text):
        msg = QMessageBox(parent)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(QMessageBox.Information)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.button(QMessageBox.Ok).setText(tr("ui.ok", default="OK"))
        msg.exec_()

    @staticmethod
    def warning(parent, title, text):
        msg = QMessageBox(parent)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(QMessageBox.Warning)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.button(QMessageBox.Ok).setText(tr("ui.ok", default="OK"))
        msg.exec_()

    @staticmethod
    def critical(parent, title, text):
        msg = QMessageBox(parent)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(QMessageBox.Critical)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.button(QMessageBox.Ok).setText(tr("ui.ok", default="OK"))
        msg.exec_()
