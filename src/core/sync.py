import os
import json
import requests
from src.qt_compat import QThread, Signal


class DatabaseSyncWorker(QThread):
    """
    Background worker that fetches the remote books.json database,
    validates it, and writes it to the local cache file.
    Emits sync_finished on success, sync_failed on error.
    """

    sync_finished = Signal(int)  # new book count
    sync_failed = Signal(str)    # error message

    REQUIRED_BOOK_KEYS = {'id', 'title', 'publisher', 'file_name', 'download_url'}

    def __init__(self, remote_url, local_path, parent=None):
        super().__init__(parent)
        self.remote_url = remote_url
        self.local_path = local_path

    def run(self):
        try:
            response = requests.get(self.remote_url, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Validate: must be a non-empty list of dicts with required keys
            if not isinstance(data, list) or not data:
                self.sync_failed.emit("Remote database is empty or not a list.")
                return

            for entry in data:
                if not isinstance(entry, dict):
                    self.sync_failed.emit("Remote database contains invalid entries.")
                    return
                missing = self.REQUIRED_BOOK_KEYS - entry.keys()
                if missing:
                    self.sync_failed.emit(f"Remote book entry missing keys: {missing}")
                    return

            # Write validated data to local cache
            os.makedirs(os.path.dirname(self.local_path), exist_ok=True)
            with open(self.local_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self.sync_finished.emit(len(data))

        except requests.exceptions.ConnectionError:
            self.sync_failed.emit("No network connection.")
        except requests.exceptions.Timeout:
            self.sync_failed.emit("Connection timed out.")
        except requests.exceptions.HTTPError as e:
            self.sync_failed.emit(f"HTTP error: {e}")
        except json.JSONDecodeError:
            self.sync_failed.emit("Remote database returned invalid JSON.")
        except Exception as e:
            self.sync_failed.emit(str(e))
