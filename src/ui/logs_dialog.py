from gi.repository import Gtk, Adw, Pango, GLib
from src.core.translation import tr

class InstallationLogsDialog(Adw.Window):
    def __init__(self, parent=None):
        super().__init__(transient_for=parent, modal=False)
        self.set_title(tr("ui.installation_logs_title", default="Installation Logs"))
        self.set_default_size(600, 400)
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(box)
        
        header = Adw.HeaderBar()
        box.append(header)
        
        clear_btn = Gtk.Button(label=tr("ui.clear_logs_btn", default="Clear"))
        clear_btn.connect("clicked", lambda x: self.buffer.set_text("", -1))
        header.pack_start(clear_btn)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        box.append(scrolled)
        
        self.textview = Gtk.TextView()
        self.textview.set_editable(False)
        self.textview.set_cursor_visible(False)
        self.textview.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.textview.set_monospace(True)
        self.textview.set_margin_start(8)
        self.textview.set_margin_end(8)
        self.textview.set_margin_top(8)
        self.textview.set_margin_bottom(8)
        scrolled.set_child(self.textview)
        
        self.buffer = self.textview.get_buffer()
        
    def append_log(self, text):
        def _append():
            end_iter = self.buffer.get_end_iter()
            self.buffer.insert(end_iter, text.strip() + "\n")
            # Auto-scroll
            adj = self.textview.get_parent().get_vadjustment()
            GLib.idle_add(lambda: adj.set_value(adj.get_upper() - adj.get_page_size()))
        GLib.idle_add(_append)
