import os
from gi.repository import Gtk, Adw
from src.core.translation import tr
from src.core.version import __version__ as APP_VERSION

def show_about_window(parent=None):
    from gi.repository import Gdk
    about = Gtk.AboutDialog()
    if parent:
        about.set_transient_for(parent)
        
    about.set_program_name(tr("ui.app_title"))
    about.set_version(APP_VERSION)
    
    icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "raf.png")
    if os.path.exists(icon_path):
        try:
            texture = Gdk.Texture.new_from_filename(icon_path)
            about.set_logo(texture)
        except Exception:
            pass
            
    about.set_comments(tr("ui.about_content"))
    about.set_website("https://github.com/KaanFerid/Raf/releases")
    about.set_website_label(tr("ui.check_updates"))
    
    about.present()
