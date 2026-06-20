import os
import subprocess
import shutil
import zipfile
import json
from src.qt_compat import QThread, Signal

MOCK_DB_PATH = os.path.abspath(os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
    "mock_system", 
    "installed.json"
))

def load_mock_installed():
    if not os.path.exists(MOCK_DB_PATH):
        os.makedirs(os.path.dirname(MOCK_DB_PATH), exist_ok=True)
        with open(MOCK_DB_PATH, 'w', encoding='utf-8') as f:
            json.dump([], f)
        return set()
    try:
        with open(MOCK_DB_PATH, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    except:
        return set()

def save_mock_installed(installed_set):
    os.makedirs(os.path.dirname(MOCK_DB_PATH), exist_ok=True)
    with open(MOCK_DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(list(installed_set), f, indent=2)

class InstallerWorker(QThread):
    # Signals
    status_changed = Signal(str, str)  # book_id, status_message
    finished = Signal(str, bool)       # book_id, success
    output_received = Signal(str, str) # book_id, console_output

    def __init__(self, book, file_path, action="install"):
        super().__init__()
        self.book = book
        self.book_id = book['id']
        self.file_path = file_path
        self.action = action  # "install" or "uninstall"

    def run(self):
        if os.environ.get("KITAPMARKT_DEV") == "1":
            self.run_mock()
            return
            
        if self.action == "install":
            self.install()
        elif self.action == "uninstall":
            self.uninstall()

    def run_mock(self):
        if self.action == "install":
            self.status_changed.emit(self.book_id, f"Simülasyon: '{self.book['title']}' kuruluyor...")
            self.msleep(1500)  # 1.5 saniye bekle (simüle et)
            installed = load_mock_installed()
            installed.add(self.book_id)
            save_mock_installed(installed)
            self.status_changed.emit(self.book_id, "Simüle kurulum tamamlandı!")
            self.finished.emit(self.book_id, True)
        elif self.action == "uninstall":
            self.status_changed.emit(self.book_id, f"Simülasyon: '{self.book['title']}' kaldırılıyor...")
            self.msleep(1000)  # 1 saniye bekle
            installed = load_mock_installed()
            if self.book_id in installed:
                installed.remove(self.book_id)
            save_mock_installed(installed)
            self.status_changed.emit(self.book_id, "Simüle kaldırma tamamlandı!")
            self.finished.emit(self.book_id, True)

    def install(self):
        file_type = self.book.get('file_type', 'deb')
        
        if file_type == 'deb':
            self.install_deb()
        elif file_type in ['zip', 'fernus']:
            self.install_zip()
        else:
            self.status_changed.emit(self.book_id, "Hata: Desteklenmeyen dosya türü.")
            self.finished.emit(self.book_id, False)

    def uninstall(self):
        file_type = self.book.get('file_type', 'deb')
        
        if file_type == 'deb':
            self.uninstall_deb()
        elif file_type in ['zip', 'fernus']:
            self.uninstall_zip()
        else:
            self.status_changed.emit(self.book_id, "Hata: Desteklenmeyen dosya türü.")
            self.finished.emit(self.book_id, False)

    def install_deb(self):
        self.status_changed.emit(self.book_id, "Sistem paketi kuruluyor (Yetki istenebilir)...")
        
        # We will use pkexec apt-get install -y ./file.deb
        # This will pop up a PolicyKit password prompt for security.
        cmd = ["pkexec", "apt-get", "install", "-y", self.file_path]
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            for line in process.stdout:
                self.output_received.emit(self.book_id, line)
                
            process.wait()
            
            if process.returncode == 0:
                self.status_changed.emit(self.book_id, "Kurulum tamamlandı!")
                self.finished.emit(self.book_id, True)
            else:
                self.status_changed.emit(self.book_id, f"Kurulum başarısız oldu (Hata Kodu: {process.returncode})")
                self.finished.emit(self.book_id, False)
        except Exception as e:
            self.output_received.emit(self.book_id, str(e))
            self.status_changed.emit(self.book_id, f"Hata: {str(e)}")
            self.finished.emit(self.book_id, False)

    def uninstall_deb(self):
        self.status_changed.emit(self.book_id, "Sistem paketi kaldırılıyor (Yetki istenebilir)...")
        package_name = get_deb_package_name(self.book)
        
        if not package_name:
            self.status_changed.emit(self.book_id, "Hata: Paket adı bulunamadı.")
            self.finished.emit(self.book_id, False)
            return

        cmd = ["pkexec", "apt-get", "remove", "-y", package_name]
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            for line in process.stdout:
                self.output_received.emit(self.book_id, line)
                
            process.wait()
            
            if process.returncode == 0:
                self.status_changed.emit(self.book_id, "Paket başarıyla kaldırıldı!")
                self.finished.emit(self.book_id, True)
            else:
                self.status_changed.emit(self.book_id, f"Kaldırma başarısız (Hata Kodu: {process.returncode})")
                self.finished.emit(self.book_id, False)
        except Exception as e:
            self.output_received.emit(self.book_id, str(e))
            self.status_changed.emit(self.book_id, f"Hata: {str(e)}")
            self.finished.emit(self.book_id, False)

    def install_zip(self):
        self.status_changed.emit(self.book_id, "Dosyalar çıkarılıyor...")
        
        apps_dir = os.path.expanduser(f"~/.local/share/kitapmarkt/apps/{self.book_id}")
        if os.path.exists(apps_dir):
            shutil.rmtree(apps_dir)
        os.makedirs(apps_dir, exist_ok=True)

        try:
            with zipfile.ZipFile(self.file_path, 'r') as zip_ref:
                # Get total number of files for progress simulation
                file_list = zip_ref.namelist()
                total_files = len(file_list)
                
                for i, file in enumerate(file_list):
                    zip_ref.extract(file, apps_dir)
                    if i % max(1, total_files // 10) == 0:
                        percent = int((i / total_files) * 100)
                        self.status_changed.emit(self.book_id, f"Çıkartılıyor: %{percent}")
            
            # Make sure all files are executable if they are scripts/binaries
            for root, dirs, files in os.walk(apps_dir):
                for f in files:
                    fpath = os.path.join(root, f)
                    if f.endswith('.sh') or '.' not in f: # executable scripts or binaries
                        try:
                            os.chmod(fpath, 0o755)
                        except:
                            pass

            self.status_changed.emit(self.book_id, "Masaüstü kısayolu oluşturuluyor...")
            create_desktop_launcher(self.book, apps_dir)
            
            self.status_changed.emit(self.book_id, "Kurulum tamamlandı!")
            self.finished.emit(self.book_id, True)

        except Exception as e:
            self.output_received.emit(self.book_id, str(e))
            self.status_changed.emit(self.book_id, f"Hata: {str(e)}")
            self.finished.emit(self.book_id, False)

    def uninstall_zip(self):
        self.status_changed.emit(self.book_id, "Dosyalar siliniyor...")
        
        apps_dir = os.path.expanduser(f"~/.local/share/kitapmarkt/apps/{self.book_id}")
        desktop_file = os.path.expanduser(f"~/.local/share/applications/kitapmarkt-{self.book_id}.desktop")
        
        try:
            if os.path.exists(apps_dir):
                shutil.rmtree(apps_dir)
            if os.path.exists(desktop_file):
                os.remove(desktop_file)
                
            self.status_changed.emit(self.book_id, "Kütüphane kaldırıldı!")
            self.finished.emit(self.book_id, True)
        except Exception as e:
            self.output_received.emit(self.book_id, str(e))
            self.status_changed.emit(self.book_id, f"Hata: {str(e)}")
            self.finished.emit(self.book_id, False)


def get_all_installed_packages():
    """Queries all installed debian packages on the system in a single subprocess run."""
    if os.environ.get("KITAPMARKT_DEV") == "1":
        return load_mock_installed()
    installed = set()
    try:
        res = subprocess.run(
            ["dpkg-query", "-W", "-f=${Package} ${Status}\n"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if res.returncode == 0:
            for line in res.stdout.splitlines():
                parts = line.strip().split()
                if len(parts) >= 4 and "installed" in parts[3]:
                    pkg_name = parts[0].split(':')[0]
                    installed.add(pkg_name)
    except Exception as e:
        print(f"Error querying installed packages: {e}")
    return installed

def get_deb_package_name(book):
    """Guesses or queries the debian package name of the book."""
    file_name = book['file_name']
    base_name = file_name[:-4]  # remove .deb
    
    # Let's list a few guesses
    guesses = [
        base_name.lower(),
        base_name.lower().replace('kutuphane', '-kutuphane'),
        base_name.lower().replace('yayinlari', '-yayinlari'),
        base_name.lower().replace('yayinlari', '-yayinlari-kutuphane'),
        base_name.lower().replace('yayiningurubu', '-yayin-grubu'),
    ]
    
    # Clean the guess list (lowercase, alpha-numeric and dashes only)
    cleaned_guesses = []
    for g in guesses:
        clean = "".join([c if c.isalnum() or c in ['-', '+', '.'] else '' for c in g])
        cleaned_guesses.append(clean)
        
    # Check if any is installed via dpkg-query
    for pkg in cleaned_guesses:
        try:
            res = subprocess.run(
                ["dpkg-query", "-W", "-f=${Status}", pkg],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if "install ok installed" in res.stdout:
                return pkg
        except:
            pass
            
    # Default fallback
    return cleaned_guesses[0]

def is_book_installed(book, installed_set=None):
    """Checks if a book/app is currently installed on the system."""
    if os.environ.get("KITAPMARKT_DEV") == "1":
        m_set = installed_set if installed_set is not None else load_mock_installed()
        return book['id'] in m_set
        
    file_type = book.get('file_type', 'deb')
    
    if file_type == 'deb':
        # High-performance set-lookup path
        if installed_set is not None:
            file_name = book['file_name']
            base_name = file_name[:-4]  # remove .deb
            guesses = [
                base_name.lower(),
                base_name.lower().replace('kutuphane', '-kutuphane'),
                base_name.lower().replace('yayinlari', '-yayinlari'),
                base_name.lower().replace('yayinlari', '-yayinlari-kutuphane'),
                base_name.lower().replace('yayiningurubu', '-yayin-grubu'),
            ]
            for g in guesses:
                clean = "".join([c if c.isalnum() or c in ['-', '+', '.'] else '' for c in g])
                if clean in installed_set:
                    return True
            return False
            
        package_name = get_deb_package_name(book)
        try:
            res = subprocess.run(
                ["dpkg-query", "-W", "-f=${Status}", package_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return "install ok installed" in res.stdout
        except:
            return False
            
    elif file_type in ['zip', 'fernus']:
        apps_dir = os.path.expanduser(f"~/.local/share/kitapmarkt/apps/{book['id']}")
        desktop_file = os.path.expanduser(f"~/.local/share/applications/kitapmarkt-{book['id']}.desktop")
        # Installed if directory exists and desktop file is present
        return os.path.exists(apps_dir) and os.path.exists(desktop_file)
        
    return False

def create_desktop_launcher(book, apps_dir):
    """Detects the executable and creates a desktop entry launcher in applications menu."""
    os.makedirs(os.path.expanduser("~/.local/share/applications"), exist_ok=True)
    desktop_path = os.path.expanduser(f"~/.local/share/applications/kitapmarkt-{book['id']}.desktop")
    
    # 1. Detect executable path
    exec_cmd = None
    icon_path = None
    
    # Search for files inside apps_dir
    all_files = []
    for root, dirs, files in os.walk(apps_dir):
        for f in files:
            all_files.append(os.path.join(root, f))
            
    # Sort files to find best matches first
    # Heuristics:
    # A. Search for .sh scripts (start.sh, run.sh, play.sh, etc.)
    sh_files = [f for f in all_files if f.endswith('.sh')]
    for sh in sh_files:
        fname = os.path.basename(sh).lower()
        if 'start' in fname or 'run' in fname or 'kutuphane' in fname or 'main' in fname:
            exec_cmd = sh
            break
    if not exec_cmd and sh_files:
        exec_cmd = sh_files[0]
        
    # B. Search for HTML index if no shell script (xdg-open index.html)
    if not exec_cmd:
        html_files = [f for f in all_files if f.endswith('.html')]
        for html in html_files:
            if 'index' in os.path.basename(html).lower() or 'main' in os.path.basename(html).lower():
                exec_cmd = f"xdg-open '{html}'"
                break
        if not exec_cmd and html_files:
            exec_cmd = f"xdg-open '{html_files[0]}'"
            
    # C. Search for windows .exe files (run with wine)
    if not exec_cmd:
        exe_files = [f for f in all_files if f.endswith('.exe')]
        # Skip uninstaller exes
        exe_files = [f for f in exe_files if 'unins' not in os.path.basename(f).lower()]
        if exe_files:
            exec_cmd = f"wine '{exe_files[0]}'"
            
    # D. Fallback: Search for binary files (executable files with no extension)
    if not exec_cmd:
        binaries = [f for f in all_files if '.' not in os.path.basename(f) and os.access(f, os.X_OK)]
        if binaries:
            exec_cmd = binaries[0]
            
    # E. Last resort: Just point to the directory
    if not exec_cmd:
        exec_cmd = f"xdg-open '{apps_dir}'"

    # 2. Find Icon
    # Search for icon/png/svg
    img_files = [f for f in all_files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.svg'))]
    for img in img_files:
        fname = os.path.basename(img).lower()
        if 'icon' in fname or 'logo' in fname or 'avatar' in fname:
            icon_path = img
            break
    if not icon_path and img_files:
        icon_path = img_files[0]
        
    # Default icon if none found
    if not icon_path:
        icon_path = "education"  # system icon name
        
    # 3. Create the .desktop file content
    content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name={book['title']}
Comment={book['publisher']} Kütüphane Kitabı (KitapMarkt)
Exec={exec_cmd}
Icon={icon_path}
Terminal=false
Categories=Education;Development;
StartupNotify=true
"""
    
    with open(desktop_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    # Make the .desktop file executable
    try:
        os.chmod(desktop_path, 0o755)
    except:
        pass
