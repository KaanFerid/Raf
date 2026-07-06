import sys
import os

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
    from gi.repository import Gtk, Adw, Gio
    from src.core.translation import tr

    print(f"=== {tr('ui.app_title')} ===")
    print(tr("log.qt_api", api="GTK4 (Libadwaita)"))
    
    class RafApp(Adw.Application):
        def __init__(self, **kwargs):
            super().__init__(application_id="org.raf.App", flags=Gio.ApplicationFlags.HANDLES_OPEN, **kwargs)
            self.startup_files = startup_files
            self.connect("startup", self.on_startup)
            self.connect("activate", self.on_activate)
            self.connect("open", self.on_open)

        def on_startup(self, app):
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
            print(tr("log.creating_main_window"))
            win = self.props.active_window
            if not win:
                win = MainWindow(app=self, startup_files=self.startup_files)
            win.present()
            print(tr("log.app_ready"))

        def on_open(self, app, files, n_files, hint):
            self.startup_files.extend([f.get_path() for f in files if f.get_path()])
            self.on_activate(app)

    app = RafApp()
    # Adw.Application.run parses sys.argv automatically if we just pass None, or we can pass args
    # Wait, passing args directly.
    return app.run(None)

if __name__ == "__main__":
    sys.exit(main())
