import os
os.environ['GTK_CSD'] = '1'
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib

def on_activate(app):
    win = Gtk.ApplicationWindow(application=app)
    header = Gtk.HeaderBar()
    win.set_titlebar(header)
    win.present()
    GLib.timeout_add(500, app.quit)

app = Gtk.Application(application_id='test.csd')
app.connect('activate', on_activate)
app.run(None)
