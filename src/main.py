import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from src.ui.main_window import MainWindow

def main():
    # If command line arguments are provided, switch to CLI mode
    args = sys.argv[1:]
    
    import os
    startup_files = []
    gui_mode = False
    
    if args:
        if args[0] == "-c":
            args = args[1:]
        elif all(os.path.exists(a) for a in args):
            # Arguments are existing file paths (OS "Open With" context)
            startup_files = [os.path.abspath(a) for a in args]
            gui_mode = True
            
        if not gui_mode and args:
            from src.core.cli import handle_cli
            handle_cli()
            return

    from src.core.translation import tr

    print(f"=== {tr('ui.app_title')} ===")
    print(tr("log.qt_api", api="PyQt5"))
    
    # Create the Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName("raf")
    app.setApplicationDisplayName(tr("ui.app_display_name"))
    app.setOrganizationName("Kaan Ferid Altundas")
    app.setOrganizationDomain("raf.org")
    
    # Set application window icon
    import os
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "raf.png")
    if os.path.exists(icon_path):
        try:
            app.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            print(tr("log.error_icon", error=e))
    
    print(tr("log.creating_main_window"))
    # Create and show the main window
    window = MainWindow(startup_files)
    print(tr("log.showing_main_window"))
    window.show()
    print(tr("log.app_ready"))
    
    # Execute the application loop (exec() in PySide6, exec_() in PyQt5)
    if hasattr(app, 'exec'):
        sys.exit(app.exec())
    else:
        sys.exit(app.exec_())

if __name__ == "__main__":
    main()
