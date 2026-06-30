from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
from src.core.translation import tr

class InstallationLogsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("ui.installation_logs_title", default="Installation Logs"))
        self.resize(600, 400)
        
        layout = QVBoxLayout(self)
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        # Use a monospace font for logs
        self.log_output.setStyleSheet("font-family: monospace;")
        layout.addWidget(self.log_output)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1)
        
        self.clear_btn = QPushButton(tr("ui.clear_logs_btn", default="Clear"))
        self.clear_btn.setProperty("class", "AdwSecondaryBtn")
        self.clear_btn.clicked.connect(self.log_output.clear)
        btn_layout.addWidget(self.clear_btn)
        
        self.close_btn = QPushButton(tr("ui.close_btn", default="Close"))
        self.close_btn.setProperty("class", "AdwPrimaryBtn")
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)
        
    def append_log(self, text):
        self.log_output.append(text.strip())
        # Scroll to bottom
        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
