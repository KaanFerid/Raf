import os
import subprocess
import shutil
import zipfile
import json
import re
from src.qt_compat import QThread, Signal
from src.core.config import get_cached_package_name, set_cached_package_name
from src.core.translation import tr

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
        if os.environ.get("ETKILESIMLI_KITAP_KUTUPHANESI_DEV") == "1":
            self.run_mock()
            return
            
        if self.action == "install":
            self.install()
        elif self.action == "uninstall":
            self.uninstall()

    def run_mock(self):
        if self.action == "install":
            self.status_changed.emit(self.book_id, tr("installer.sim_installing", title=self.book['title']))
            self.msleep(1500)  # Wait 1.5 seconds (simulate)
            installed = load_mock_installed()
            installed.add(self.book_id)
            save_mock_installed(installed)
            self.status_changed.emit(self.book_id, tr("installer.sim_install_completed"))
            self.finished.emit(self.book_id, True)
        elif self.action == "uninstall":
            self.status_changed.emit(self.book_id, tr("installer.sim_uninstalling", title=self.book['title']))
            self.msleep(1000)  # Wait 1 second (simulate)
            installed = load_mock_installed()
            if self.book_id in installed:
                installed.remove(self.book_id)
            save_mock_installed(installed)
            self.status_changed.emit(self.book_id, tr("installer.sim_uninstall_completed"))
            self.finished.emit(self.book_id, True)

    def install(self):
        file_type = self.book.get('file_type', 'deb')
        
        if file_type == 'deb':
            self.install_deb()
        elif file_type in ['zip', 'fernus']:
            self.install_zip()
        else:
            self.status_changed.emit(self.book_id, tr("installer.unsupported_file_type"))
            self.finished.emit(self.book_id, False)

    def uninstall(self):
        file_type = self.book.get('file_type', 'deb')
        
        if file_type == 'deb':
            self.uninstall_deb()
        elif file_type in ['zip', 'fernus']:
            self.uninstall_zip()
        else:
            self.status_changed.emit(self.book_id, tr("installer.unsupported_file_type"))
            self.finished.emit(self.book_id, False)

    def install_deb(self):
        self.status_changed.emit(self.book_id, tr("installer.querying_package_info"))
        
        # Extract the exact package name from the downloaded .deb file
        try:
            res = subprocess.run(
                ["dpkg-deb", "-f", self.file_path, "Package"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            if res.returncode == 0:
                package_name = res.stdout.strip()
                if package_name:
                    set_cached_package_name(self.book_id, package_name)
                    print(f"[{self.book_id}] Resolved package name from deb file: {package_name}")
        except Exception as e:
            print(f"[{self.book_id}] Error reading package name from deb file: {e}")

        self.status_changed.emit(self.book_id, tr("installer.installing_system_package"))
        
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
                self.status_changed.emit(self.book_id, tr("installer.install_completed"))
                self.finished.emit(self.book_id, True)
            else:
                self.status_changed.emit(self.book_id, tr("installer.install_failed", code=process.returncode))
                self.finished.emit(self.book_id, False)
        except Exception as e:
            self.output_received.emit(self.book_id, str(e))
            self.status_changed.emit(self.book_id, tr("ui.error") + f": {str(e)}")
            self.finished.emit(self.book_id, False)

    def uninstall_deb(self):
        self.status_changed.emit(self.book_id, tr("installer.uninstalling_system_package"))
        package_name = get_deb_package_name(self.book)
        
        if not package_name:
            self.status_changed.emit(self.book_id, tr("installer.package_name_not_found"))
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
                self.status_changed.emit(self.book_id, tr("installer.uninstall_completed"))
                self.finished.emit(self.book_id, True)
            else:
                self.status_changed.emit(self.book_id, tr("installer.uninstall_failed", code=process.returncode))
                self.finished.emit(self.book_id, False)
        except Exception as e:
            self.output_received.emit(self.book_id, str(e))
            self.status_changed.emit(self.book_id, tr("ui.error") + f": {str(e)}")
            self.finished.emit(self.book_id, False)

    def install_zip(self):
        self.status_changed.emit(self.book_id, tr("installer.extracting_files"))
        
        apps_dir = os.path.expanduser(f"~/.local/share/etkilesimli-kitap-kutuphanesi/apps/{self.book_id}")
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
                        self.status_changed.emit(self.book_id, tr("installer.extracting_percent", percent=percent))
            
            # Make sure all files are executable if they are scripts/binaries
            for root, dirs, files in os.walk(apps_dir):
                for f in files:
                    fpath = os.path.join(root, f)
                    if f.endswith('.sh') or '.' not in f: # executable scripts or binaries
                        try:
                            os.chmod(fpath, 0o755)
                        except:
                            pass

            self.status_changed.emit(self.book_id, tr("installer.creating_desktop_launcher"))
            create_desktop_launcher(self.book, apps_dir)
            
            self.status_changed.emit(self.book_id, tr("installer.install_completed"))
            self.finished.emit(self.book_id, True)

        except Exception as e:
            self.output_received.emit(self.book_id, str(e))
            self.status_changed.emit(self.book_id, tr("ui.error") + f": {str(e)}")
            self.finished.emit(self.book_id, False)

    def uninstall_zip(self):
        self.status_changed.emit(self.book_id, tr("installer.deleting_files"))
        
        apps_dir = os.path.expanduser(f"~/.local/share/etkilesimli-kitap-kutuphanesi/apps/{self.book_id}")
        desktop_file = os.path.expanduser(f"~/.local/share/applications/etkilesimli-kitap-kutuphanesi-{self.book_id}.desktop")
        
        try:
            if os.path.exists(apps_dir):
                shutil.rmtree(apps_dir)
            if os.path.exists(desktop_file):
                os.remove(desktop_file)
                
            self.status_changed.emit(self.book_id, tr("installer.library_uninstalled"))
            self.finished.emit(self.book_id, True)
        except Exception as e:
            self.output_received.emit(self.book_id, str(e))
            self.status_changed.emit(self.book_id, tr("ui.error") + f": {str(e)}")
            self.finished.emit(self.book_id, False)


def get_all_installed_packages():
    """Queries all installed debian packages on the system in a single subprocess run."""
    if os.environ.get("ETKILESIMLI_KITAP_KUTUPHANESI_DEV") == "1":
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

def turkish_to_ascii(text):
    """Normalizes Turkish characters to their standard ASCII lowercase equivalents."""
    text = text.lower()
    mapping = {
        '\u0131': 'i', 'i\u0307': 'i', '\u0130': 'i', 'I\u0307': 'i',
        '\u011f': 'g', '\u00fc': 'u', '\u015f': 's', '\u00f6': 'o', '\u00e7': 'c'
    }
    for k, v in mapping.items():
        text = text.replace(k, v)
    return text

def generate_package_guesses(book):
    """Generates a list of likely package names based on the book file name."""
    file_name = book['file_name']
    base_name = file_name
    if base_name.endswith('.deb'):
        base_name = base_name[:-4]
    elif base_name.endswith('.fernus'):
        base_name = base_name[:-7]
    elif base_name.endswith('.zip'):
        base_name = base_name[:-4]
        
    # Remove version suffixes if present (e.g. -v2-23)
    base_name = re.sub(r'-v\d+.*$', '', base_name)
    base_name = re.sub(r'_\d+.*$', '', base_name)
    
    # Convert Turkish characters to ASCII
    base_clean = turkish_to_ascii(base_name)
    
    # List of keywords to strip out for shorter names
    keywords_to_remove = ['yayinlari', 'yayincilik', 'yayiningurubu', 'yayingurubu', 'yayin', 'dagitim', 'perakende', 'gurubu', 'grubu']
    
    # Generate variations
    bases = [base_clean]
    
    # Also generate base with keywords removed
    short_base = base_clean
    for kw in keywords_to_remove:
        short_base = short_base.replace(kw, '')
    if short_base != base_clean and short_base != 'kutuphane' and len(short_base) > 3:
        bases.append(short_base)
        
    # For each base, generate suffix variations
    guesses = []
    for b in bases:
        guesses.append(b)
        guesses.append(b.replace('kutuphane', '-kutuphane'))
        guesses.append(b.replace('kutuphanesi', '-kutuphanesi'))
        
        # If b doesn't end with kutuphane, add it
        if not b.endswith('kutuphane') and not b.endswith('kutuphanesi'):
            guesses.append(b + 'kutuphane')
            guesses.append(b + '-kutuphane')
            guesses.append(b + 'kutuphanesi')
            guesses.append(b + '-kutuphanesi')
            
    # Clean all guesses to alphanumeric and dashes/plus/dots only
    cleaned_guesses = []
    for g in guesses:
        clean = "".join([c if c.isalnum() or c in ['-', '+', '.'] else '' for c in g])
        clean = clean.strip('-')
        if clean and clean not in cleaned_guesses:
            cleaned_guesses.append(clean)
            
    return cleaned_guesses

def get_deb_package_name(book):
    """Retrieves or queries the debian package name of the book."""
    # 1. Try config cache first
    cached_name = get_cached_package_name(book['id'])
    if cached_name:
        return cached_name
        
    # 2. Fall back to smart guesses
    cleaned_guesses = generate_package_guesses(book)
        
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
                # Cache it now for subsequent calls
                set_cached_package_name(book['id'], pkg)
                return pkg
        except:
            pass
            
    # Default fallback
    return cleaned_guesses[0]

def is_book_installed(book, installed_set=None):
    """Checks if a book/app is currently installed on the system."""
    if os.environ.get("ETKILESIMLI_KITAP_KUTUPHANESI_DEV") == "1":
        m_set = installed_set if installed_set is not None else load_mock_installed()
        return book['id'] in m_set
        
    file_type = book.get('file_type', 'deb')
    
    if file_type == 'deb':
        # 1. Check cached package name first
        cached_name = get_cached_package_name(book['id'])
        if cached_name:
            if installed_set is not None:
                return cached_name in installed_set
            try:
                res = subprocess.run(
                    ["dpkg-query", "-W", "-f=${Status}", cached_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                return "install ok installed" in res.stdout
            except:
                return False
                
        # 2. Set-lookup path with smart guesses
        cleaned_guesses = generate_package_guesses(book)
        if installed_set is not None:
            for g in cleaned_guesses:
                if g in installed_set:
                    set_cached_package_name(book['id'], g)
                    return True
            return False
            
        # 3. Standard query path with smart guesses
        for pkg in cleaned_guesses:
            try:
                res = subprocess.run(
                    ["dpkg-query", "-W", "-f=${Status}", pkg],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                if "install ok installed" in res.stdout:
                    set_cached_package_name(book['id'], pkg)
                    return True
            except:
                pass
        return False
            
    elif file_type in ['zip', 'fernus']:
        apps_dir = os.path.expanduser(f"~/.local/share/etkilesimli-kitap-kutuphanesi/apps/{book['id']}")
        desktop_file = os.path.expanduser(f"~/.local/share/applications/etkilesimli-kitap-kutuphanesi-{book['id']}.desktop")
        return os.path.exists(apps_dir) and os.path.exists(desktop_file)
        
    return False

def create_desktop_launcher(book, apps_dir):
    """Detects the executable and creates a desktop entry launcher in applications menu."""
    os.makedirs(os.path.expanduser("~/.local/share/applications"), exist_ok=True)
    desktop_path = os.path.expanduser(f"~/.local/share/applications/etkilesimli-kitap-kutuphanesi-{book['id']}.desktop")
    
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
Comment={tr("installer.desktop_comment", publisher=book['publisher'])}
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
