import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib

def on_activate(app):
    win = Adw.ApplicationWindow(application=app)
    header = Adw.HeaderBar()
    win.set_titlebar(header)
    win.present()
    GLib.timeout_add(500, app.quit)

app = Adw.Application('test.app', 0)
app.connect('activate', on_activate)
app.run(None)
