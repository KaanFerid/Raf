import os
import json
import requests
import threading
from gi.repository import GLib
from src.core.translation import tr

class DatabaseSyncWorker(threading.Thread):
    """
    Background worker that fetches the remote books.json database,
    validates it, and writes it to the local cache file.
    """
    REQUIRED_BOOK_KEYS = {'id', 'title', 'publisher', 'file_name', 'download_url'}

    def __init__(self, remote_url, database_dir):
        super().__init__()
        self.daemon = True
        self.remote_url = remote_url
        self.database_dir = database_dir
        
        self.on_sync_finished = None # func(new_book_count)
        self.on_sync_failed = None   # func(error_message)

    def _emit_finished(self, count):
        if self.on_sync_finished:
            GLib.idle_add(self.on_sync_finished, count)
            
    def _emit_failed(self, error):
        if self.on_sync_failed:
            GLib.idle_add(self.on_sync_failed, error)

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
                    
                    if isinstance(data, dict) and "books" in data:
                        book_list = data["books"]
                    elif isinstance(data, list):
                        book_list = data
                    else:
                        continue # Skip invalid files instead of failing entire sync

                    for entry in book_list:
                        if not isinstance(entry, dict):
                            continue
                        missing = self.REQUIRED_BOOK_KEYS - entry.keys()
                        if missing:
                            continue # Skip bad entries
                            
                    # Write validated data to local cache
                    local_file = os.path.join(self.database_dir, filename)
                    with open(local_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                        
                    total_books += len(book_list)
                except Exception as e:
                    print(tr("log.sync_failed", file=filename, url=url, error=e))
                    # Don't fail the whole sync if one file is missing (e.g. publishers.json doesn't exist yet on some remotes)
                    pass

            if total_books > 0:
                self._emit_finished(total_books)
            else:
                self._emit_failed(tr("sync.no_valid_books"))
        except requests.exceptions.ConnectionError:
            self._emit_failed(tr("sync.no_network"))
        except Exception as e:
            self._emit_failed(str(e))
