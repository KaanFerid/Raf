import os
from gi.repository import Gtk, Adw
from src.core.translation import tr
from src.core.version import __version__ as APP_VERSION

def show_about_window(parent=None):
    about = Adw.AboutWindow()
    if parent:
        about.set_transient_for(parent)
        
    about.set_application_name(tr("ui.app_title"))
    about.set_version(APP_VERSION)
    about.set_developer_name("KaanFerid")
    
    icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "raf.png")
    if os.path.exists(icon_path):
        about.set_application_icon("education") # Fallback to standard icon
        
    about.set_comments(tr("ui.about_content", version=APP_VERSION).replace("<br>", "\n").replace("<b>", "").replace("</b>", ""))
    
    # Check Updates link
    about.add_link(tr("ui.check_updates"), "https://github.com/KaanFerid/Raf/releases")
    
    about.present()
