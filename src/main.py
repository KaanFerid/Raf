import sys
import os

# Force GTK to use Client-Side Decorations (CSD) to prevent double titlebars on XFCE/X11
os.environ["GTK_CSD"] = "1"

def main():
    args = sys.argv[1:]
    
    startup_files = []
    gui_mode = False
    
    if args:
        if args[0] == "-c":
            args = args[1:]
        elif all(os.path.exists(a) for a in args):
            startup_files = [os.path.abspath(a) for a in args]
            gui_mode = True
            
        if not gui_mode and args:
            from src.core.cli import handle_cli
            handle_cli()
            return

    import gi
    gi.require_version('Gtk', '4.0')
    gi.require_version('Adw', '1')
    from gi.repository import Gtk, Adw, Gio, Gdk
    from src.core.translation import tr

    from src.core.translation import tr
    class RafApp(Adw.Application):
        def __init__(self, **kwargs):
            super().__init__(application_id="org.raf.App", flags=Gio.ApplicationFlags.HANDLES_OPEN, **kwargs)
            self.startup_files = startup_files
            self.connect("startup", self.on_startup)
            self.connect("activate", self.on_activate)
            self.connect("open", self.on_open)

        def on_startup(self, app):
            from src.core.config import load_config
            config = load_config()
            mode = config.get("theme_mode", "system")
            manager = Adw.StyleManager.get_default()
            if mode == "system": manager.set_color_scheme(Adw.ColorScheme.DEFAULT)
            elif mode == "light": manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
            elif mode == "dark": manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)

            # Setup icon theme
            display = Gdk.Display.get_default()
            if display:
                icon_theme = Gtk.IconTheme.get_for_display(display)
                base_dir = os.path.dirname(os.path.abspath(__file__))
                icon_theme.add_search_path(os.path.join(base_dir, "assets"))

            # Setup Preferences Action
            action = Gio.SimpleAction.new("preferences", None)
            action.connect("activate", self.on_preferences_action)
            self.add_action(action)
            
            # Setup About Action
            action = Gio.SimpleAction.new("about", None)
            action.connect("activate", self.on_about_action)
            self.add_action(action)

        def on_preferences_action(self, action, param):
            from src.ui.preferences import PreferencesWindow
            win = self.props.active_window
            pref_win = PreferencesWindow(parent=win)
            pref_win.present()

        def on_about_action(self, action, param):
            from src.ui.about import show_about_window
            win = self.props.active_window
            show_about_window(parent=win)

        def on_activate(self, app):
            from src.ui.main_window import MainWindow
            win = self.props.active_window
            if not win:
                win = MainWindow(app=self, startup_files=self.startup_files)
            win.present()

        def on_open(self, app, files, n_files, hint):
            self.startup_files.extend([f.get_path() for f in files if f.get_path()])
            self.on_activate(app)

    app = RafApp()
    # Adw.Application.run parses sys.argv automatically if we just pass None, or we can pass args
    # Wait, passing args directly.
    return app.run(None)

if __name__ == "__main__":
    sys.exit(main())
