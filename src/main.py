import sys
from PySide6.QtWidgets import QApplication
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
    
    # Execute the application loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
