import os
import json
import requests
from src.qt_compat import QThread, Signal
from src.core.translation import tr


class DatabaseSyncWorker(QThread):
    """
    Background worker that fetches the remote books.json database,
    validates it, and writes it to the local cache file.
    Emits sync_finished on success, sync_failed on error.
    """

    sync_finished = Signal(int)  # new book count
    sync_failed = Signal(str)    # error message

    REQUIRED_BOOK_KEYS = {'id', 'title', 'publisher', 'file_name', 'download_url'}

    def __init__(self, remote_url, database_dir, parent=None):
        super().__init__(parent)
        self.remote_url = remote_url
        self.database_dir = database_dir

    def run(self):
        try:
            # Determine if legacy (single json) or base URL
            if self.remote_url.endswith('.json'):
                files_to_sync = [
                    (self.remote_url, "fernus_drive.json")
                ]
            else:
                base = self.remote_url.rstrip('/')
                files_to_sync = [
                    (f"{base}/fernus_drive.json", "fernus_drive.json"),
                    (f"{base}/publishers.json", "publishers.json")
                ]

            total_books = 0
            os.makedirs(self.database_dir, exist_ok=True)

            for url, filename in files_to_sync:
                try:
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    
                    if not isinstance(data, list):
                        continue # Skip invalid files instead of failing entire sync

                    for entry in data:
                        if not isinstance(entry, dict):
                            continue
                        missing = self.REQUIRED_BOOK_KEYS - entry.keys()
                        if missing:
                            continue # Skip bad entries
                            
                    # Write validated data to local cache
                    local_file = os.path.join(self.database_dir, filename)
                    with open(local_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                        
                    total_books += len(data)
                except Exception as e:
                    print(tr("log.sync_failed", file=filename, url=url, error=e))
                    # Don't fail the whole sync if one file is missing (e.g. publishers.json doesn't exist yet on some remotes)
                    pass

            if total_books > 0:
                self.sync_finished.emit(total_books)
            else:
                self.sync_failed.emit("No valid books could be synced from the provided URL.")

        except requests.exceptions.ConnectionError:
            self.sync_failed.emit("No network connection.")
        except Exception as e:
            self.sync_failed.emit(str(e))
