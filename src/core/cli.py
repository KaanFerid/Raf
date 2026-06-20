import os
import sys
import time
import requests
import re

# Set headless mode for Qt
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from src.qt_compat import QApplication, QEventLoop
from src.core.database import Database
from src.core.installer import InstallerWorker, is_book_installed, get_all_installed_packages
from src.core.downloader import DownloadWorker

def print_progress_bar(percent, speed_str):
    bar_length = 40
    filled_length = int(round(bar_length * percent / 100))
    bar = '=' * filled_length + '-' * (bar_length - filled_length)
    sys.stdout.write(f"\rİndiriliyor: [{bar}] %{percent} ({speed_str})")
    sys.stdout.flush()

def handle_cli():
    # Make sure app context is initialized
    app = QApplication.instance() or QApplication(sys.argv)
    
    db = Database()
    
    args = sys.argv[1:]
    if not args or args[0] in ["-h", "--help", "help"]:
        print("KitapMarkt CLI Yönetim Paneli")
        print("Kullanım: kitapmarkt <komut> [parametreler]")
        print("\nKomutlar:")
        print("  list               Mevcut tüm kitapları listeler.")
        print("  list-installed     Sistemde yüklü olan kitapları listeler.")
        print("  search <terim>     Kitaplarda arama yapar.")
        print("  install <id>       Belirtilen kitap ID'sine sahip kitabı indirir ve kurar.")
        print("  uninstall <id>     Belirtilen kitap ID'sine sahip kitabı sistemden kaldırır.")
        print("  clean              İndirme önbelleğini temizler.")
        sys.exit(0)
        
    cmd = args[0]
    
    if cmd == "list":
        books = db.get_all_books()
        print(f"Toplam {len(books)} kitap mevcut:")
        print(f"{'ID':<35} | {'Başlık':<45} | {'Kategori':<12}")
        print("-" * 100)
        for b in books:
            print(f"{b['id']:<35} | {b['title'][:45]:<45} | {b.get('category', 'Genel'):<12}")
            
    elif cmd == "list-installed":
        books = db.get_all_books()
        installed_set = get_all_installed_packages()
        installed_books = [b for b in books if is_book_installed(b, installed_set)]
        print(f"Toplam {len(installed_books)} yüklü kitap mevcut:")
        print(f"{'ID':<35} | {'Başlık':<45} | {'Tür':<6}")
        print("-" * 92)
        for b in installed_books:
            print(f"{b['id']:<35} | {b['title'][:45]:<45} | {b.get('file_type', 'deb').upper():<6}")
            
    elif cmd == "search":
        if len(args) < 2:
            print("Hata: Arama terimi belirtilmedi. Örnek: kitapmarkt search Ankara")
            sys.exit(1)
        query = " ".join(args[1:])
        books = db.search_books(query)
        print(f"Arama sonuçları ({len(books)} adet):")
        print(f"{'ID':<35} | {'Başlık':<45} | {'Yayıncı':<25}")
        print("-" * 110)
        for b in books:
            print(f"{b['id']:<35} | {b['title'][:45]:<45} | {b['publisher'][:25]:<25}")
            
    elif cmd == "clean":
        if os.environ.get("KITAPMARKT_DEV") == "1":
            cache_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "mock_system", "cache"))
        else:
            cache_dir = os.path.expanduser("~/.cache/kitapmarkt/downloads")
        if os.path.exists(cache_dir):
            files_deleted = 0
            for f in os.listdir(cache_dir):
                file_path = os.path.join(cache_dir, f)
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                        files_deleted += 1
                    except:
                        pass
            print(f"Başarılı: İndirme önbelleği temizlendi. {files_deleted} dosya silindi.")
        else:
            print("Önbellek klasörü boş veya mevcut değil.")
            
    elif cmd == "install":
        if len(args) < 2:
            print("Hata: Kurulacak kitap ID'si belirtilmedi. Örnek: kitapmarkt install akademikbasariyayinlarikutuphane")
            sys.exit(1)
        book_id = args[1]
        books = db.get_all_books()
        book = next((b for b in books if b['id'] == book_id), None)
        if not book:
            print(f"Hata: '{book_id}' ID'li kitap bulunamadı. Tüm kitapları listelemek için 'kitapmarkt list' komutunu çalıştırın.")
            sys.exit(1)
            
        installed_set = get_all_installed_packages()
        if is_book_installed(book, installed_set):
            print(f"Bilgi: '{book['title']}' zaten sistemde yüklü.")
            sys.exit(0)
            
        # Download step
        if os.environ.get("KITAPMARKT_DEV") == "1":
            cache_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "mock_system", "cache"))
        else:
            cache_dir = os.path.expanduser("~/.cache/kitapmarkt/downloads")
            
        file_path = os.path.join(cache_dir, book['file_name'])
        print(f"Kuruluyor: {book['title']}")
        
        # We start the download worker using QEventLoop
        loop = QEventLoop()
        worker = DownloadWorker(book_id, book['download_url'], file_path)
        
        download_success = [False]
        def on_progress(bid, percent, speed_str):
            print_progress_bar(percent, speed_str)
            
        def on_finished(bid, path):
            print("\nİndirme tamamlandı.")
            download_success[0] = True
            loop.quit()
            
        def on_error(bid, msg):
            print(f"\nİndirme hatası: {msg}")
            loop.quit()
            
        worker.progress_changed.connect(on_progress)
        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        
        worker.start()
        loop.exec()
        
        if not download_success[0]:
            print("Hata: İndirme başarısız olduğu için kuruluma geçilemiyor.")
            sys.exit(1)
            
        # Install step
        print("Paket sisteme kuruluyor...")
        install_loop = QEventLoop()
        install_success = [False]
        
        inst_worker = InstallerWorker(book, file_path, action="install")
        inst_worker.status_changed.connect(lambda bid, msg: print(f" Durum: {msg}"))
        
        def on_inst_finished(bid, success):
            install_success[0] = success
            install_loop.quit()
            
        inst_worker.finished.connect(on_inst_finished)
        inst_worker.start()
        install_loop.exec()
        
        if install_success[0]:
            print(f"\nBaşarılı: '{book['title']}' başarıyla kuruldu.")
            sys.exit(0)
        else:
            print(f"\nHata: '{book['title']}' kurulumu başarısız oldu.")
            sys.exit(1)
            
    elif cmd == "uninstall":
        if len(args) < 2:
            print("Hata: Kaldırılacak kitap ID'si belirtilmedi. Örnek: kitapmarkt uninstall akademikbasariyayinlarikutuphane")
            sys.exit(1)
        book_id = args[1]
        books = db.get_all_books()
        book = next((b for b in books if b['id'] == book_id), None)
        if not book:
            print(f"Hata: '{book_id}' ID'li kitap bulunamadı.")
            sys.exit(1)
            
        installed_set = get_all_installed_packages()
        if not is_book_installed(book, installed_set):
            print(f"Bilgi: '{book['title']}' zaten sistemde yüklü değil.")
            sys.exit(0)
            
        print(f"Kaldırılıyor: {book['title']}")
        uninstall_loop = QEventLoop()
        uninstall_success = [False]
        
        inst_worker = InstallerWorker(book, None, action="uninstall")
        inst_worker.status_changed.connect(lambda bid, msg: print(f" Durum: {msg}"))
        
        def on_uninst_finished(bid, success):
            uninstall_success[0] = success
            uninstall_loop.quit()
            
        inst_worker.finished.connect(on_uninst_finished)
        inst_worker.start()
        uninstall_loop.exec()
        
        if uninstall_success[0]:
            print(f"\nBaşarılı: '{book['title']}' başarıyla sistemden kaldırıldı.")
            sys.exit(0)
        else:
            print(f"\nHata: '{book['title']}' kaldırma işlemi başarısız oldu.")
            sys.exit(1)
            
    else:
        print(f"Hata: Bilinmeyen komut '{cmd}'. Yardım için 'kitapmarkt --help' yazın.")
        sys.exit(1)
