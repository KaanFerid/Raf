import os
import time
import json
import requests
import subprocess
import threading
from gi.repository import GLib
from src.core.translation import tr
from src.core.version import __version__ as APP_VERSION
from src.core.config import load_config, get_last_update_check, set_last_update_check

# Remote update metadata file
UPDATE_URL = "https://api.github.com/repos/KaanFerid/Raf/releases/latest"

# 6 hours between automatic checks in seconds
AUTO_CHECK_INTERVAL_SEC = 6 * 60 * 60
# Minimum time between checks (24 hours)
MIN_CHECK_INTERVAL_SECONDS = 86400


class UpdateChecker(threading.Thread):
    """Checks the remote GitHub Releases API once and emits whether an update is available."""

    def __init__(self):
        super().__init__()
        self.daemon = True
        self.on_update_available = None  # func(version, download_url, changelog)
        self.on_no_update = None         # func()

    def _emit_available(self, version, download_url, changelog):
        if self.on_update_available:
            GLib.idle_add(self.on_update_available, version, download_url, changelog)

    def _emit_none(self):
        if self.on_no_update:
            GLib.idle_add(self.on_no_update)

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
                    print(tr("log.error_reading_update", error=e))
        else:
            try:
                headers = {"Accept": "application/vnd.github.v3+json"}
                response = requests.get(UPDATE_URL, headers=headers, timeout=5)
                if response.status_code == 200:
                    data = response.json()
            except Exception:
                pass
                
        if not data:
            self._emit_none()
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
            self._emit_none()
            return
        
        # Numeric comparison
        local_parts = [int(x) for x in APP_VERSION.split('.')]
        latest_parts = [int(x) for x in latest_version.split('.')]
        
        if latest_parts > local_parts:
            self._emit_available(latest_version, download_url, changelog)
        else:
            self._emit_none()


class UpdateInstaller(threading.Thread):
    """Installs a downloaded application update .deb file."""

    def __init__(self, file_path):
        super().__init__()
        self.daemon = True
        self.file_path = file_path
        self.on_status_changed = None  # func(status_message)
        self.on_finished = None        # func(success)

    def _emit_status(self, msg):
        if self.on_status_changed:
            GLib.idle_add(self.on_status_changed, msg)

    def _emit_finished(self, success):
        if self.on_finished:
            GLib.idle_add(self.on_finished, success)

    def run(self):
        # 1. Developer simulation path
        if os.environ.get("RAF_DEV") == "1":
            self._emit_status(tr("updater.sim_installing"))
            time.sleep(2)
            self._emit_finished(True)
            return

        # 2. Production system installation path
        self._emit_status(tr("updater.system_updating"))
        cmd = ["pkexec", "apt-get", "install", "--reinstall", "-y", self.file_path]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
            if res.returncode == 0:
                self._emit_finished(True)
            else:
                self._emit_finished(False)
        except Exception as e:
            print(tr("log.error_installing_update", error=e))
            self._emit_finished(False)


class AutoUpdateScheduler:
    """
    Runs periodic background update checks based on the user's policy setting.
    """
    def __init__(self):
        self._checker = None
        self._timeout_id = None
        
        self.on_update_toast_requested = None  # func(version)
        self.on_auto_install_requested = None  # func(version, url, changelog)

    def start(self):
        """Starts the scheduler timer."""
        # Run once immediately on startup
        self._maybe_check()
        self._timeout_id = GLib.timeout_add_seconds(AUTO_CHECK_INTERVAL_SEC, self._maybe_check_loop)

    def stop(self):
        if self._timeout_id:
            GLib.source_remove(self._timeout_id)
            self._timeout_id = None

    def _maybe_check_loop(self):
        self._maybe_check()
        return True  # Keep the timeout running

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
        self.check_now(on_available=self._on_update_found)

    def check_now(self, force=False, on_available=None, on_none=None):
        if force:
            set_last_update_check(0)
        self._checker = UpdateChecker()
        if on_available:
            self._checker.on_update_available = on_available
        if on_none:
            self._checker.on_no_update = on_none
        self._checker.start()

    def _on_update_found(self, version, download_url, changelog):
        """Handles a newly discovered update according to the current policy."""
        config = load_config()
        policy = config.get("auto_update_policy", "check")

        if policy == "auto" and self.on_auto_install_requested:
            self.on_auto_install_requested(version, download_url, changelog)
        elif self.on_update_toast_requested:
            self.on_update_toast_requested(version)
