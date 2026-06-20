import os
import json
import requests
import subprocess
from src.qt_compat import QThread, Signal

APP_VERSION = "1.0.0"
# Remote update metadata file
UPDATE_URL = "https://raw.githubusercontent.com/kaan-gok/etkilesimli-kitap-kutuphanesi/main/update.json"

class UpdateChecker(QThread):
    # Signals to notify the UI
    update_available = Signal(str, str, str)  # version, download_url, changelog
    no_update = Signal()

    def run(self):
        # 1. Developer simulation path
        if os.environ.get("ETKILESIMLI_KITAP_KUTUPHANESI_DEV") == "1":
            mock_path = os.path.abspath(os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "mock_system",
                "update_mock.json"
            ))
            if os.path.exists(mock_path):
                try:
                    with open(mock_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    latest_version = data.get("version", "1.0.0")
                    download_url = data.get("download_url", "")
                    changelog = data.get("changelog", "")
                    
                    if latest_version != APP_VERSION:
                        self.update_available.emit(latest_version, download_url, changelog)
                        return
                except Exception as e:
                    print(f"Error reading update mock: {e}")
            self.no_update.emit()
            return

        # 2. Production network check path
        try:
            response = requests.get(UPDATE_URL, timeout=5)
            if response.status_code == 200:
                data = response.json()
                latest_version = data.get("version", "1.0.0")
                download_url = data.get("download_url", "")
                changelog = data.get("changelog", "")
                
                # Numeric comparison
                local_parts = [int(x) for x in APP_VERSION.split('.')]
                latest_parts = [int(x) for x in latest_version.split('.')]
                
                if latest_parts > local_parts:
                    self.update_available.emit(latest_version, download_url, changelog)
                else:
                    self.no_update.emit()
            else:
                self.no_update.emit()
        except:
            # Silent fallback if offline or failed
            self.no_update.emit()


class UpdateInstaller(QThread):
    status_changed = Signal(str)
    finished = Signal(bool)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        # 1. Developer simulation path
        if os.environ.get("ETKILESIMLI_KITAP_KUTUPHANESI_DEV") == "1":
            self.status_changed.emit("Güncelleme paketi simüle edilerek yükleniyor...")
            self.msleep(2000)
            self.finished.emit(True)
            return

        # 2. Production system installation path
        self.status_changed.emit("Sistem güncellemesi yapılıyor (Yetki istenebilir)...")
        # Run pkexec apt-get install --reinstall -y ./file.deb
        cmd = ["pkexec", "apt-get", "install", "--reinstall", "-y", self.file_path]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
            if res.returncode == 0:
                self.finished.emit(True)
            else:
                self.finished.emit(False)
        except Exception as e:
            print(f"Error installing update deb: {e}")
            self.finished.emit(False)
