import os
import sys

# Set headless mode for Qt
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from src.qt_compat import QApplication, QEventLoop
from src.core.database import Database
from src.core.installer import InstallerWorker, is_book_installed, get_all_installed_packages
from src.core.downloader import DownloadWorker
from src.core.translation import tr

def print_progress_bar(percent, speed_str):
    bar_length = 40
    filled_length = int(round(bar_length * percent / 100))
    bar = '=' * filled_length + '-' * (bar_length - filled_length)
    sys.stdout.write("\r" + tr("cli.downloading_progress", bar=bar, percent=percent, speed=speed_str))
    sys.stdout.flush()

def handle_cli():
    # Make sure app context is initialized
    app = QApplication.instance() or QApplication(sys.argv)
    
    db = Database()
    
    args = sys.argv[1:]
    if not args or args[0] in ["-h", "--help", "help"]:
        print(tr("cli.panel_title"))
        print(tr("cli.usage"))
        print("\n" + tr("cli.commands_header"))
        print(tr("cli.cmd_list"))
        print(tr("cli.cmd_list_installed"))
        print(tr("cli.cmd_search"))
        print(tr("cli.cmd_install"))
        print(tr("cli.cmd_uninstall"))
        print(tr("cli.cmd_clean"))
        sys.exit(0)
        
    cmd = args[0]
    
    if cmd == "list":
        books = db.get_all_books()
        print(tr("cli.total_books", count=len(books)))
        print(tr("cli.list_header", id=tr("cli.id"), title=tr("cli.title"), publisher=tr("cli.publisher")))
        print("-" * 110)
        for b in books:
            print(f"{b['id']:<35} | {b['title'][:45]:<45} | {b['publisher'][:25]:<25}")
            
    elif cmd == "list-installed":
        books = db.get_all_books()
        installed_set = get_all_installed_packages()
        installed_books = [b for b in books if is_book_installed(b, installed_set)]
        print(tr("cli.total_installed", count=len(installed_books)))
        print(tr("cli.installed_header", id=tr("cli.id"), title=tr("cli.title"), type=tr("cli.type")))
        print("-" * 92)
        for b in installed_books:
            print(f"{b['id']:<35} | {b['title'][:45]:<45} | {b.get('file_type', 'deb').upper():<6}")
            
    elif cmd == "search":
        if len(args) < 2:
            print(tr("cli.search_missing_term"))
            sys.exit(1)
        query = " ".join(args[1:])
        books = db.search_books(query)
        print(tr("cli.search_results", count=len(books)))
        print(tr("cli.search_header", id=tr("cli.id"), title=tr("cli.title"), publisher=tr("cli.publisher")))
        print("-" * 110)
        for b in books:
            print(f"{b['id']:<35} | {b['title'][:45]:<45} | {b['publisher'][:25]:<25}")
            
    elif cmd == "clean":
        if os.environ.get("RAF_DEV") == "1":
            cache_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "mock_system", "cache"))
        else:
            cache_dir = os.path.expanduser("~/.cache/raf/downloads")
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
            print(tr("cli.clean_success", count=files_deleted))
        else:
            print(tr("cli.clean_empty"))
            
    elif cmd == "install":
        if len(args) < 2:
            print(tr("cli.install_missing_id"))
            sys.exit(1)
        book_id = args[1]
        books = db.get_all_books()
        book = next((b for b in books if b['id'] == book_id), None)
        if not book:
            print(tr("cli.book_not_found", id=book_id))
            sys.exit(1)
            
        installed_set = get_all_installed_packages()
        if is_book_installed(book, installed_set):
            print(tr("cli.already_installed", title=book['title']))
            sys.exit(0)
            
        # Download step
        if os.environ.get("RAF_DEV") == "1":
            cache_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "mock_system", "cache"))
        else:
            cache_dir = os.path.expanduser("~/.cache/raf/downloads")
            
        file_path = os.path.join(cache_dir, book['file_name'])
        print(tr("cli.installing_book", title=book['title']))
        
        # We start the download worker using QEventLoop
        loop = QEventLoop()
        worker = DownloadWorker(book_id, book['download_url'], file_path)
        
        download_success = [False]
        def on_progress(bid, percent, speed_str):
            print_progress_bar(percent, speed_str)
            
        def on_finished(bid, path):
            print("\n" + tr("cli.download_completed"))
            download_success[0] = True
            loop.quit()
            
        def on_error(bid, msg):
            print("\n" + tr("cli.download_error", error=msg))
            loop.quit()
            
        worker.progress_changed.connect(on_progress)
        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        
        worker.start()
        loop.exec() if hasattr(loop, 'exec') else loop.exec_()
        
        if not download_success[0]:
            print(tr("cli.install_failed_download"))
            sys.exit(1)
            
        # Install step
        print(tr("cli.installing_package"))
        install_loop = QEventLoop()
        install_success = [False]
        
        inst_worker = InstallerWorker(book, file_path, action="install")
        inst_worker.status_changed.connect(lambda bid, msg: print(tr("cli.status_prefix", status=msg)))
        
        def on_inst_finished(bid, success):
            install_success[0] = success
            install_loop.quit()
            
        inst_worker.finished.connect(on_inst_finished)
        inst_worker.start()
        install_loop.exec() if hasattr(install_loop, 'exec') else install_loop.exec_()
        
        if install_success[0]:
            print("\n" + tr("cli.install_completed_success", title=book['title']))
            sys.exit(0)
        else:
            print("\n" + tr("cli.install_completed_failed", title=book['title']))
            sys.exit(1)
            
    elif cmd == "uninstall":
        if len(args) < 2:
            print(tr("cli.uninstall_missing_id"))
            sys.exit(1)
        book_id = args[1]
        books = db.get_all_books()
        book = next((b for b in books if b['id'] == book_id), None)
        if not book:
            print(tr("cli.uninstall_book_not_found", id=book_id))
            sys.exit(1)
            
        installed_set = get_all_installed_packages()
        if not is_book_installed(book, installed_set):
            print(tr("cli.uninstall_already_removed", title=book['title']))
            sys.exit(0)
            
        print(tr("cli.uninstalling_book", title=book['title']))
        uninstall_loop = QEventLoop()
        uninstall_success = [False]
        
        inst_worker = InstallerWorker(book, None, action="uninstall")
        inst_worker.status_changed.connect(lambda bid, msg: print(tr("cli.status_prefix", status=msg)))
        
        def on_uninst_finished(bid, success):
            uninstall_success[0] = success
            uninstall_loop.quit()
            
        inst_worker.finished.connect(on_uninst_finished)
        inst_worker.start()
        uninstall_loop.exec() if hasattr(uninstall_loop, 'exec') else uninstall_loop.exec_()
        
        if uninstall_success[0]:
            print("\n" + tr("cli.uninstall_completed_success", title=book['title']))
            sys.exit(0)
        else:
            print("\n" + tr("cli.uninstall_completed_failed", title=book['title']))
            sys.exit(1)
            
    else:
        print(tr("cli.unknown_command", cmd=cmd))
        sys.exit(1)
