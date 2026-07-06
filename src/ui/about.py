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
    
    # In GTK4/Adw, the icon must be in the current icon theme or resource.
    # We will just use a standard system icon for the store/application market.
    about.set_application_icon("system-software-install")
        
    about.set_comments(tr("ui.about_content"))
    
    # Check Updates link
    about.add_link(tr("ui.check_updates"), "https://github.com/KaanFerid/Raf/releases")
    
    about.present()
