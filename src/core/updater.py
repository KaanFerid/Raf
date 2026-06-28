import os
import time
import json
import requests
import subprocess
from src.qt_compat import QThread, QObject, QTimer, Signal
from src.core.translation import tr
from src.core.version import __version__ as APP_VERSION
from src.core.config import load_config, get_last_update_check, set_last_update_check

# Remote update metadata file
UPDATE_URL = "https://api.github.com/repos/KaanFerid/Raf/releases/latest"

# 6 hours between automatic checks
AUTO_CHECK_INTERVAL_MS = 6 * 60 * 60 * 1000
# Minimum time between checks (24 hours)
MIN_CHECK_INTERVAL_SECONDS = 86400


class UpdateChecker(QThread):
    """Checks the remote GitHub Releases API once and emits whether an update is available."""

    # Signals to notify the UI
    update_available = Signal(str, str, str)  # version, download_url, changelog
    no_update = Signal()

    def run(self):
        # Determine data source
        data = None
        if os.environ.get("RAF_DEV") == "1":
            mock_path = os.path.abspath(os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "mock_system",
                "update_mock.json"
            ))
            if os.path.exists(mock_path):
                try:
                    with open(mock_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except Exception as e:
                    print(f"Error reading update mock: {e}")
        else:
            try:
                headers = {"Accept": "application/vnd.github.v3+json"}
                response = requests.get(UPDATE_URL, headers=headers, timeout=5)
                if response.status_code == 200:
                    data = response.json()
            except Exception:
                pass
                
        if not data:
            self.no_update.emit()
            return
            
        # Parse GitHub Release format
        tag_name = data.get("tag_name", "")
        latest_version = tag_name.lstrip("v") if tag_name else "1.0.0"
        changelog = data.get("body", "")
        
        # Find the .deb asset download URL
        download_url = ""
        for asset in data.get("assets", []):
            if asset.get("name", "").endswith(".deb"):
                download_url = asset.get("browser_download_url", "")
                break
                
        if not download_url:
            self.no_update.emit()
            return
        
        # Numeric comparison
        local_parts = [int(x) for x in APP_VERSION.split('.')]
        latest_parts = [int(x) for x in latest_version.split('.')]
        
        if latest_parts > local_parts:
            self.update_available.emit(latest_version, download_url, changelog)
        else:
            self.no_update.emit()


class UpdateInstaller(QThread):
    """Installs a downloaded application update .deb file."""

    status_changed = Signal(str)
    finished = Signal(bool)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        # 1. Developer simulation path
        if os.environ.get("RAF_DEV") == "1":
            self.status_changed.emit(tr("updater.sim_installing"))
            self.msleep(2000)
            self.finished.emit(True)
            return

        # 2. Production system installation path
        self.status_changed.emit(tr("updater.system_updating"))
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


class AutoUpdateScheduler(QObject):
    """
    Runs periodic background update checks based on the user's policy setting.
    Policy values (stored in config as 'auto_update_policy'):
      'off'    — Never check automatically (only on launch)
      'check'  — Check daily, show a toast notification
      'auto'   — Check daily, download and install automatically
    """

    # Emitted when an update is found (in 'check' policy mode)
    update_toast_requested = Signal(str)          # formatted toast message
    # Emitted when an update should be installed automatically ('auto' mode)
    auto_install_requested = Signal(str, str, str) # version, url, changelog

    def __init__(self, parent=None):
        super().__init__(parent)
        self._checker = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._maybe_check)

    def start(self):
        """Starts the scheduler timer."""
        self._timer.start(AUTO_CHECK_INTERVAL_MS)
        # Also run once immediately on startup
        self._maybe_check()

    def stop(self):
        self._timer.stop()

    def _maybe_check(self):
        """Runs an update check if the policy allows and enough time has passed."""
        config = load_config()
        policy = config.get("auto_update_policy", "check")

        if policy == "off":
            return

        last_checked = get_last_update_check()
        if time.time() - last_checked < MIN_CHECK_INTERVAL_SECONDS:
            return

        # Record that we are checking now
        set_last_update_check(time.time())

        self._checker = UpdateChecker()
        self._checker.update_available.connect(self._on_update_found)
        self._checker.start()

    def _on_update_found(self, version, download_url, changelog):
        """Handles a newly discovered update according to the current policy."""
        config = load_config()
        policy = config.get("auto_update_policy", "check")

        if policy == "auto":
            self.auto_install_requested.emit(version, download_url, changelog)
        else:
            self.update_toast_requested.emit(version)
