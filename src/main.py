import sys
from src.qt_compat import QApplication, QT_API
from src.ui.main_window import MainWindow

def main():
    print("=== KitapMarkt Başlatılıyor ===")
    print(f"Grafik Arayüz Motoru (Qt API): {QT_API}")
    
    # Create the Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName("KitapMarkt")
    app.setApplicationDisplayName("KitapMarkt")
    app.setOrganizationName("KitapMarkt Team")
    app.setOrganizationDomain("kitapmarkt.org")
    
    print("Ana pencere oluşturuluyor...")
    # Create and show the main window
    window = MainWindow()
    print("Ana pencere gösteriliyor...")
    window.show()
    print("Etkinlik döngüsü (event loop) başlatıldı. Uygulama hazır.")
    
    # Execute the application loop (exec() in PySide6, exec_() in PyQt5)
    if hasattr(app, 'exec'):
        sys.exit(app.exec())
    else:
        sys.exit(app.exec_())

if __name__ == "__main__":
    main()
