import sys
from src.qt_compat import QApplication, QIcon, QT_API
from src.ui.main_window import MainWindow

def main():
    # If command line arguments are provided, switch to CLI mode
    args = sys.argv[1:]
    if args and args[0] == "-c":
        args = args[1:]
        
    if args:
        from src.core.cli import handle_cli
        handle_cli()
        return

    from src.core.translation import tr

    print(f"=== {tr('ui.app_title')} ===")
    print(tr("log.qt_api", api=QT_API))
    
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
    window = MainWindow()
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
