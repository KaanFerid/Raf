import os
from gi.repository import Gtk, Adw
from src.core.translation import tr

def show_message(parent, title, text, type="info"):
    dialog = Adw.MessageDialog(
        transient_for=parent,
        heading=title,
        body=text
    )
    dialog.add_response("ok", tr("ui.ok_btn", default="OK"))
    dialog.set_default_response("ok")
    dialog.set_close_response("ok")
    if type == "error":
        dialog.set_response_appearance("ok", Adw.ResponseAppearance.DESTRUCTIVE)
    dialog.present()


class DesktopEditorDialog(Adw.Window):
    def __init__(self, book, parent=None):
        super().__init__()
        self.set_title(tr("ui.desktop_editor_title", title=book['title']))
        self.set_default_size(400, 200)
        self.book = book
        self.book_id = book['id']
        
        self.global_path = f"/usr/share/applications/raf-{self.book_id}.desktop"
        self.local_path = os.path.expanduser(f"~/.local/share/applications/raf-{self.book_id}.desktop")
        
        self.original_lines = []
        self.current_name = book['title']
        
        self.init_ui()
        self.load_desktop_file()
        
    def init_ui(self):
        # Layout
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(content_box)
        
        # Header
        header = Adw.HeaderBar()
        content_box.append(header)
        
        # Buttons
        cancel_btn = Gtk.Button(label=tr("ui.cancel"))
        cancel_btn.connect("clicked", lambda btn: self.close())
        header.pack_start(cancel_btn)
        
        save_btn = Gtk.Button(label=tr("ui.save"))
        save_btn.add_css_class("suggested-action")
        save_btn.connect("clicked", self.save_desktop_file)
        header.pack_end(save_btn)
        
        # Body
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        body.set_margin_start(16)
        body.set_margin_end(16)
        body.set_margin_top(16)
        body.set_margin_bottom(16)
        content_box.append(body)
        
        info_label = Gtk.Label(label=tr("ui.desktop_editor_info"))
        info_label.set_wrap(True)
        body.append(info_label)
        
        pref_group = Adw.PreferencesGroup()
        body.append(pref_group)
        
        self.name_input = Adw.EntryRow(title=tr("ui.name", default="Name:"))
        pref_group.add(self.name_input)

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
            
        self.name_input.set_text(self.current_name)
            
    def save_desktop_file(self, btn):
        """Saves changes to ~/.local/share/applications/"""
        new_name = self.name_input.get_text().strip()
        if not new_name:
            show_message(self, tr("ui.error"), tr("ui.name_empty_error", default="Name cannot be empty."), type="error")
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
            
            show_message(self, tr("ui.success"), tr("ui.desktop_editor_saved"))
            self.close()
        except Exception as e:
            show_message(self, tr("ui.error"), tr("ui.desktop_editor_save_failed", error=str(e)), type="error")
