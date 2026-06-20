import os
import time
import re
import requests
from src.qt_compat import QThread, Signal

class DownloadWorker(QThread):
    # Signals to communicate with the GUI thread
    progress_changed = Signal(str, int, str)  # book_id, percentage, speed_str
    finished = Signal(str, str)               # book_id, local_file_path
    error = Signal(str, str)                  # book_id, error_message

    def __init__(self, book_id, url, dest_path):
        super().__init__()
        self.book_id = book_id
        self.url = url
        self.dest_path = dest_path
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        temp_dest_path = self.dest_path + ".tmp"
        
        # Ensure destination directory exists
        dest_dir = os.path.dirname(self.dest_path)
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir, exist_ok=True)

        try:
            # We must use a Session to handle cookies and download in chunks
            session = requests.Session()
            response = session.get(self.url, stream=True, timeout=15)
            response.raise_for_status()

            # Google Drive virus warning page detection and bypass
            if "text/html" in response.headers.get("Content-Type", ""):
                html_text = response.text
                confirm_match = re.search(r'name="confirm"\s+value="([^"]+)"', html_text)
                uuid_match = re.search(r'name="uuid"\s+value="([^"]+)"', html_text)
                id_match = re.search(r'name="id"\s+value="([^"]+)"', html_text)
                
                if confirm_match and uuid_match:
                    confirm_val = confirm_match.group(1)
                    uuid_val = uuid_match.group(1)
                    file_id = id_match.group(1) if id_match else ""
                    if not file_id:
                        # Extract id from self.url query parameter
                        match = re.search(r"[?&]id=([^&]+)", self.url)
                        if match:
                            file_id = match.group(1)
                            
                    download_url = "https://drive.usercontent.google.com/download"
                    params = {
                        "id": file_id,
                        "export": "download",
                        "confirm": confirm_val,
                        "uuid": uuid_val
                    }
                    response = session.get(download_url, params=params, stream=True, timeout=15)
                    response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            start_time = time.time()
            last_update_time = start_time

            with open(temp_dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=65536):
                    if self._is_cancelled:
                        f.close()
                        if os.path.exists(temp_dest_path):
                            os.remove(temp_dest_path)
                        self.error.emit(self.book_id, "İndirme iptal edildi.")
                        return

                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        current_time = time.time()
                        # Update progress every 0.1 seconds or at 100%
                        if current_time - last_update_time >= 0.2 or downloaded == total_size:
                            last_update_time = current_time
                            elapsed = current_time - start_time
                            speed = downloaded / (elapsed if elapsed > 0 else 0.001)  # bytes per sec
                            speed_mb = speed / (1024 * 1024)
                            speed_str = f"{speed_mb:.2f} MB/s"
                            
                            if total_size > 0:
                                percent = int((downloaded / total_size) * 100)
                                self.progress_changed.emit(self.book_id, percent, speed_str)
                            else:
                                # Unknown content length, just emit downloaded bytes in MB format
                                downloaded_mb = downloaded / (1024 * 1024)
                                self.progress_changed.emit(self.book_id, -1, f"{downloaded_mb:.1f} MB ({speed_str})")

            # Rename temp file to final destination file
            if os.path.exists(self.dest_path):
                os.remove(self.dest_path)
            os.rename(temp_dest_path, self.dest_path)
            
            self.finished.emit(self.book_id, self.dest_path)

        except Exception as e:
            if os.path.exists(temp_dest_path):
                try:
                    os.remove(temp_dest_path)
                except:
                    pass
            self.error.emit(self.book_id, str(e))
