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

    print("=== Etkileşimli Kitap Kütüphanesi Başlatılıyor ===")
    print(f"Grafik Arayüz Motoru (Qt API): {QT_API}")
    
    # Create the Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName("Etkileşimli Kitap Kütüphanesi")
    app.setApplicationDisplayName("Etkileşimli Kitap Kütüphanesi")
    app.setOrganizationName("Kaan Ferid Altundaş")
    app.setOrganizationDomain("etkilesimlikitapkutuphanesi.org")
    
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
