from gi.repository import Adw
from src.core.translation import tr
from src.core.version import __version__ as APP_VERSION


def show_about_window(parent=None):
    about = Adw.AboutWindow(transient_for=parent) if parent else Adw.AboutWindow()
    about.set_modal(True)

    about.set_application_name(tr("ui.app_title"))
    about.set_version(APP_VERSION)
    about.set_developer_name("KaanFerid")

    # We added src/assets to the icon theme search path in main.py
    about.set_application_icon("raf")

    about.set_comments(tr("ui.about_content"))
    about.set_support_url("mailto:kaanferidaltundas@protonmail.com")
    about.set_issue_url("https://github.com/KaanFerid/Raf/issues")
    about.add_link("GitHub", "https://github.com/KaanFerid/Raf")

    about.present()
