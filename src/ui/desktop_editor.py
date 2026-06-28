import os
from src.qt_compat import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QPlainTextEdit, QMessageBox, QLabel
from src.core.translation import tr

class DesktopEditorDialog(QDialog):
    def __init__(self, book, parent=None):
        super().__init__(parent)
        self.book = book
        self.book_id = book['id']
        
        # Determine paths
        self.global_path = f"/usr/share/applications/raf-{self.book_id}.desktop"
        self.local_path = os.path.expanduser(f"~/.local/share/applications/raf-{self.book_id}.desktop")
        
        self.init_ui()
        self.load_desktop_file()
        
    def init_ui(self):
        self.setWindowTitle(tr("ui.desktop_editor_title", title=self.book['title']))
        self.resize(600, 450)
        
        layout = QVBoxLayout(self)
        
        info_label = QLabel(tr("ui.desktop_editor_info"))
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        self.text_editor = QPlainTextEdit()
        # Use monospace font for editor
        font = self.text_editor.font()
        font.setFamily("monospace")
        self.text_editor.setFont(font)
        layout.addWidget(self.text_editor)
        
        btn_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton(tr("ui.cancel"))
        self.cancel_btn.clicked.connect(self.reject)
        
        self.save_btn = QPushButton(tr("ui.save"))
        self.save_btn.setProperty("class", "AdwPrimaryBtn")
        self.save_btn.clicked.connect(self.save_desktop_file)
        
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        
        layout.addLayout(btn_layout)

    def load_desktop_file(self):
        """Loads from local if exists, else from global."""
        path_to_load = self.local_path if os.path.exists(self.local_path) else self.global_path
        
        if os.path.exists(path_to_load):
            try:
                with open(path_to_load, 'r', encoding='utf-8') as f:
                    self.text_editor.setPlainText(f.read())
            except Exception as e:
                self.text_editor.setPlainText(f"# Error loading file: {e}")
        else:
            # Fallback template if neither exists
            template = f"""[Desktop Entry]
Name={self.book['title']}
Comment={self.book.get('publisher', '')}
Exec=/opt/raf/apps/{self.book_id}/start.sh
Icon=application-x-executable
Terminal=false
Type=Application
Categories=Education;
"""
            self.text_editor.setPlainText(template)
            
    def save_desktop_file(self):
        """Saves changes to ~/.local/share/applications/"""
        content = self.text_editor.toPlainText()
        try:
            os.makedirs(os.path.dirname(self.local_path), exist_ok=True)
            with open(self.local_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            QMessageBox.information(self, tr("ui.success"), tr("ui.desktop_editor_saved"))
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, tr("ui.error"), tr("ui.desktop_editor_save_failed", error=str(e)))
