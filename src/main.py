import sys
from src.qt_compat import QApplication, QT_API
from src.ui.main_window import MainWindow

def main():
    # If command line arguments are provided, switch to CLI mode
    import sys
    args = sys.argv[1:]
    if args and args[0] == "-c":
        args = args[1:]
        
    if args:
        from src.core.cli import handle_cli
        handle_cli()
        return

    from src.core.translation import tr

    print(f"=== {tr('ui.app_title')} ===")
    print(f"Qt API: {QT_API}")
    
    # Create the Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName("etkilesimli-kitap-kutuphanesi")
    app.setApplicationDisplayName(tr("ui.app_display_name"))
    app.setOrganizationName("Kaan Ferid Altundas")
    app.setOrganizationDomain("etkilesimlikitapkutuphanesi.org")
    
    print("Creating main window...")
    # Create and show the main window
    window = MainWindow()
    print("Showing main window...")
    window.show()
    print("Event loop started. Application ready.")
    
    # Execute the application loop (exec() in PySide6, exec_() in PyQt5)
    if hasattr(app, 'exec'):
        sys.exit(app.exec())
    else:
        sys.exit(app.exec_())

if __name__ == "__main__":
    main()
