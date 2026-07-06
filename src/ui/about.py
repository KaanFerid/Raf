import os
from gi.repository import Gtk, Adw
from src.core.translation import tr
from src.core.version import __version__ as APP_VERSION

class AboutWindow(Adw.AboutWindow):
    def __init__(self, parent=None):
        super().__init__(transient_for=parent)
        self.set_application_name(tr("ui.app_title"))
        self.set_version(APP_VERSION)
        self.set_developer_name("KaanFerid")
        
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "raf.png")
        if os.path.exists(icon_path):
            self.set_application_icon("education") # Fallback to standard icon, Adw usually uses theme icons
            
        self.set_comments(tr("ui.about_content", version=APP_VERSION).replace("<br>", "\n").replace("<b>", "").replace("</b>", ""))

        # Check Updates link
        self.add_link(tr("ui.check_updates"), "https://github.com/KaanFerid/Raf/releases")
        
        # We can't directly open logs from here in Adw.AboutWindow easily, 
        # but users can check the terminal output. Or we can just add a simple action.
