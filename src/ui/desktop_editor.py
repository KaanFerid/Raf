import os
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel, QFormLayout
from src.ui.dialogs import RafMessageBox
from src.core.translation import tr

class DesktopEditorDialog(QDialog):
    def __init__(self, book, parent=None):
        super().__init__(parent)
        self.book = book
        self.book_id = book['id']
        
        # Determine paths
        self.global_path = f"/usr/share/applications/raf-{self.book_id}.desktop"
        self.local_path = os.path.expanduser(f"~/.local/share/applications/raf-{self.book_id}.desktop")
        
        self.original_lines = []
        self.current_name = book['title']
        
        self.init_ui()
        self.load_desktop_file()
        
    def init_ui(self):
        self.setWindowTitle(tr("ui.desktop_editor_title", title=self.book['title']))
        self.resize(400, 150)
        
        layout = QVBoxLayout(self)
        
        info_label = QLabel(tr("ui.desktop_editor_info"))
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        form_layout = QFormLayout()
        self.name_input = QLineEdit()
        form_layout.addRow(tr("ui.name", default="Name:"), self.name_input)
        layout.addLayout(form_layout)
        
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
                    self.original_lines = f.readlines()
                    
                for line in self.original_lines:
                    if line.startswith("Name="):
                        self.current_name = line.split("=", 1)[1].strip()
                        break
            except Exception as e:
                pass
        else:
            # Fallback template if neither exists
            template = f"[Desktop Entry]\nName={self.book['title']}\nComment={self.book.get('publisher', '')}\nExec=/opt/raf/apps/{self.book_id}/start.sh\nIcon=application-x-executable\nTerminal=false\nType=Application\nCategories=Education;\n"
            self.original_lines = template.splitlines(True)
            
        self.name_input.setText(self.current_name)
            
    def save_desktop_file(self):
        """Saves changes to ~/.local/share/applications/"""
        new_name = self.name_input.text().strip()
        if not new_name:
            RafMessageBox.warning(self, tr("ui.error"), tr("ui.name_empty_error", default="Name cannot be empty."))
            return
            
        try:
            os.makedirs(os.path.dirname(self.local_path), exist_ok=True)
            with open(self.local_path, 'w', encoding='utf-8') as f:
                name_replaced = False
                for line in self.original_lines:
                    if line.startswith("Name="):
                        f.write(f"Name={new_name}\n")
                        name_replaced = True
                    else:
                        f.write(line)
                
                # Fallback if there wasn't a Name= for some reason
                if not name_replaced:
                    f.write(f"Name={new_name}\n")
            
            RafMessageBox.information(self, tr("ui.success"), tr("ui.desktop_editor_saved"))
            self.accept()
        except Exception as e:
            RafMessageBox.critical(self, tr("ui.error"), tr("ui.desktop_editor_save_failed", error=str(e)))
