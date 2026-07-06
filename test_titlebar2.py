import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib

class MyApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id='test.app')
    def do_activate(self):
        win = Gtk.ApplicationWindow(application=self)
        header = Adw.HeaderBar()
        win.set_titlebar(header)
        win.present()
        GLib.timeout_add(500, self.quit)

app = MyApp()
app.run(None)
