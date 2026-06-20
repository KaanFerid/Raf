import sys
from src.qt_compat import QApplication
from src.ui.main_window import MainWindow

def main():
    # Create the Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName("KitapMarkt")
    app.setApplicationDisplayName("KitapMarkt")
    app.setOrganizationName("KitapMarkt Team")
    app.setOrganizationDomain("kitapmarkt.org")
    
    # Create and show the main window
    window = MainWindow()
    window.show()
    
    # Execute the application loop (exec() in PySide6, exec_() in PyQt5)
    if hasattr(app, 'exec'):
        sys.exit(app.exec())
    else:
        sys.exit(app.exec_())

if __name__ == "__main__":
    main()
