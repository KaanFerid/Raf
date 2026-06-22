# Architecture Documentation

Raf has a layered, asynchronous architecture designed for stability on Pardus ETAP smart boards. All user-visible operations that involve network or filesystem I/O run in background threads, communicating back to the UI thread exclusively via Qt signals.

---

## 1. Layer Overview

```
┌─────────────────────────────────────────────────┐
│                  UI Layer                        │
│  main_window.py · components.py · toast.py      │
│  styles.py (QSS) · PreferencesDialog             │
├─────────────────────────────────────────────────┤
│               Core / Business Logic              │
│  database.py · downloader.py · installer.py     │
│  updater.py · sync.py · download_queue.py       │
│  config.py · translation.py · cli.py            │
├─────────────────────────────────────────────────┤
│            Qt Compatibility Layer                │
│  qt_compat.py (PySide6 / PyQt6 / PyQt5)        │
└─────────────────────────────────────────────────┘
```

---

## 2. Core Modules

### `database.py` — Book Database

Loads the book catalogue from a local JSON file (`src/assets/books.json`). Supports optional remote URL loading: if a `remote_url` is provided, it fetches the remote JSON, validates it, and caches it locally.

**Key class: `Database`**
- `load_books()` — loads from remote URL or local fallback
- `get_all_books()` → `list[dict]` — returns all book entries
- `search_books(query)` → `list[dict]` — full-text search on title, publisher, description

---

### `downloader.py` — Download Worker

A `QThread`-based worker that downloads book packages with:
- **Chunked streaming** (8 KB chunks) to track progress
- **Google Drive virus-warning bypass** — detects HTML confirmation pages and re-submits with extracted `confirm` and `uuid` form tokens
- **HTTP Range resumption** — retries with `Range: bytes=N-` if the connection drops mid-download (up to 3 automatic retries)
- **Cancellation** — `cancel()` sets a flag checked after each chunk
- **Speed calculation** — real MB/s shown in UI

**Signals emitted:**
| Signal | Arguments | Description |
|---|---|---|
| `progress_changed` | `book_id, percent, speed_str` | Fired every 200ms during download |
| `finished` | `book_id, local_file_path` | Download complete, file ready |
| `error` | `book_id, error_message` | Download failed or cancelled |

**Attributes:**
- `last_percent: int` — tracks most recent percent for title bar progress display

---

### `download_queue.py` — Download Queue

A `QObject`-based FIFO queue with configurable concurrency control.

**Key class: `DownloadQueue`**

| Method | Description |
|---|---|
| `enqueue(book, local_path)` | Adds a job; returns `False` if already queued or active |
| `dequeue(book_id)` | Removes a pending (not yet active) job |
| `is_queued(book_id)` | Returns `True` if waiting in the pending list |
| `is_active(book_id)` | Returns `True` if currently downloading |
| `pending_count()` | Number of jobs waiting to start |
| `on_download_started(book_id)` | Called by `MainWindow` to mark a job as active |
| `on_download_completed(book_id)` | Frees a slot and starts the next pending job |

**Signals emitted:**
| Signal | Arguments | Description |
|---|---|---|
| `job_started` | `book_id` | A pending job was promoted to active |
| `job_finished` | `book_id` | A job completed (success or failure) |
| `queue_changed` | `pending_count` | Pending queue length changed |

The queue stores `_last_started: (book, local_path)` which `MainWindow` reads in `_on_queue_job_started()` to retrieve the full job context.

---

### `installer.py` — Package Installer

A `QThread`-based worker that handles installing and uninstalling books based on their `file_type`.

**Key class: `InstallerWorker`**

Constructor: `InstallerWorker(book, file_path, action="install")`

**Supported file types:**

| `file_type` | Install method | Uninstall method |
|---|---|---|
| `deb` | `pkexec apt-get install -y ./file.deb` | `pkexec apt-get remove -y <pkg>` |
| `zip` / `fernus` | Extracts to `~/.local/share/raf/apps/<id>/` + creates `.desktop` | Deletes app dir + `.desktop` |
| `flatpak` | `flatpak install --user --noninteractive <ref>` | `flatpak uninstall --user --noninteractive <ref>` |
| `snap` | `pkexec snap install <snap_name>` | `pkexec snap remove <snap_name>` |

For `.deb` installs, the exact package name is extracted from the `.deb` file using `dpkg-deb -f Package` and cached in `config.json` to speed up future `is_installed` checks.

**Signals emitted:**
| Signal | Arguments | Description |
|---|---|---|
| `status_changed` | `book_id, message` | Status updates for the status bar |
| `finished` | `book_id, success` | Install/uninstall completed |
| `output_received` | `book_id, line` | Raw stdout/stderr output from subprocess |

**Helper functions:**
- `is_book_installed(book, installed_set=None)` — checks whether a book is installed, routing by `file_type`
- `get_all_installed_packages()` — bulk queries `dpkg-query` for all installed `.deb` packages
- `get_all_installed_flatpaks()` — queries `flatpak list --app`
- `get_all_installed_snaps()` — queries `snap list`
- `generate_package_guesses(book)` — generates likely package name variants for fuzzy matching
- `create_desktop_launcher(book, apps_dir)` — writes `.desktop` entry for `.zip` installs

---

### `updater.py` — Update System

Three classes handle different aspects of the update flow:

**`UpdateChecker(QThread)`**
Fetches `update.json` from GitHub, compares version tuples, emits `update_available(version, url, changelog)` or `no_update`.

**`UpdateInstaller(QThread)`**
Downloads and installs a `.deb` update file via `pkexec apt-get install --reinstall -y`.

**`AutoUpdateScheduler(QObject)`**
Runs a `QTimer` at 6-hour intervals. Reads `auto_update_policy` from config:
- `"off"` — no background checks
- `"check"` — checks once per 24h, emits `update_toast_requested(version)` on new version
- `"auto"` — checks once per 24h, emits `auto_install_requested(version, url, changelog)` on new version

Respects `last_update_check` timestamp to prevent redundant network calls.

---

### `sync.py` — Remote Database Sync

**`DatabaseSyncWorker(QThread)`**
Fetches a remote `books.json` URL on startup, validates the JSON structure (checks for required keys: `id`, `title`, `publisher`, `file_name`, `download_url`), and writes it to the local cache path.

Emits `sync_finished(count)` on success, `sync_failed(error_message)` on failure. Failures are silent — the local cache is always used as fallback.

---

### `config.py` — Persistent Configuration

Manages `~/.config/raf/config.json` (or `mock_system/config.json` in dev mode).

**Functions:**
| Function | Description |
|---|---|
| `load_config()` | Returns the config dict, creating defaults if absent |
| `save_config(config)` | Persists the config dict to disk |
| `get_cached_package_name(book_id)` | Returns the known `.deb` package name for a book |
| `set_cached_package_name(book_id, name)` | Caches a resolved package name |
| `get_last_update_check()` | Returns the UNIX timestamp of the last update check |
| `set_last_update_check(ts)` | Saves the current update check timestamp |

**Default config:**
```json
{
  "theme_mode": "system",
  "language": "tr",
  "auto_update_policy": "check",
  "database_url": "",
  "last_update_check": 0.0,
  "package_names": {}
}
```

---

### `translation.py` — Runtime Language Switching

**`TranslationManager`**
Loads locale files from `src/assets/locales/`. Supports runtime language switching without restarting.

**Functions:**
- `tr(key, **kwargs)` — returns the translated string for `key`, formatted with `kwargs`
  - Keys use dot notation: `"ui.install_btn"`, `"installer.install_completed"`
  - Missing keys fall back to the key string itself
- `translation_manager.set_language(lang_code)` — switches language and notifies all registered listeners
- `translation_manager.register_listener(fn)` / `unregister_listener(fn)` — subscribe `retranslate_ui` methods to language changes

**Locale file format (`locales/en.json`):**
```json
{
  "language_name": "English",
  "ui": {
    "install_btn": "Install",
    "queue_count": "↓ {count} queued"
  },
  "installer": {
    "install_completed": "Installation completed!"
  }
}
```

---

### `cli.py` — CLI Handler

Invoked when any command-line argument is passed to `src.main`. Uses a headless Qt application (`QT_QPA_PLATFORM=offscreen`) to reuse the same worker threads as the GUI.

Reads `RAF_DEV` to choose simulation vs. real package operations.

---

## 3. UI Layer

### `main_window.py` — MainWindow

The top-level `QMainWindow` that:
- Owns the `Database`, `DownloadQueue`, `ToastManager`, `AutoUpdateScheduler`, and `DatabaseSyncWorker`
- Manages `active_downloads` and `active_installations` dicts
- Handles all signal connections between workers and UI updates
- Contains the `PreferencesDialog` inner class

**Key method groups:**

| Group | Methods |
|---|---|
| Download lifecycle | `start_download()`, `on_download_progress()`, `on_download_finished()`, `on_download_error()`, `cancel_download()` |
| Install lifecycle | `start_installation()`, `on_installation_finished()`, `start_uninstallation()`, `on_uninstallation_finished()` |
| Queue | `_on_queue_job_started()`, `_on_queue_changed()`, `_enqueue_book()` |
| Title progress | `_update_title_progress()` |
| Batch mode | `toggle_selection_mode()`, `_on_card_selection_changed()`, `install_selected()`, `uninstall_selected()`, `_update_batch_bar()` |
| Sync | `_on_sync_finished()`, `_on_sync_failed()` |
| Theming | `update_theme()`, `get_system_theme()`, `check_system_theme_update()` |
| Refresh | `refresh_grid()`, `refresh_all_statuses()` |
| Navigation | `on_tab_changed()`, `on_search_changed()` |

---

### `components.py` — BookCard

A `QFrame`-based widget representing one book entry.

**Key attributes:**
- `is_installed: bool` — tracks install state
- `downloading: bool` — tracks active download
- `is_queued: bool` — waiting in the download queue
- `is_selected: bool` — selected in batch mode
- `_selection_mode: bool` — whether selection mode is globally active

**Key methods:**
- `update_status(is_installed, downloading, percent, speed_str, is_offline)` — updates all visual elements
- `set_queued(queued)` — switches card to the "Queued" visual state
- `set_selection_mode(active)` — shows/hides the selection checkbox
- `_toggle_selection()` — toggles `is_selected` and emits `selection_changed`

**Signals:**
| Signal | Arguments |
|---|---|
| `install_requested` | `dict` (book) |
| `uninstall_requested` | `dict` (book) |
| `launch_requested` | `dict` (book) |
| `cancel_requested` | `dict` (book) |
| `selection_changed` | `str` (book_id), `bool` (is_selected) |

---

### `toast.py` — Toast Notifications

**`ToastNotification(QWidget)`**
A frameless, semi-transparent overlay with message text, a type badge, and a close button. Animates in with a `QPropertyAnimation` opacity fade.

**`ToastManager(QWidget)`**
Manages a stack of active toasts anchored to the bottom-right of the main window. Repositions all active toasts on each dismiss and on `resizeEvent`.

```python
self.toast_manager.show_toast("Message", toast_type="success", duration=3500)
```

Supported `toast_type` values: `"info"`, `"success"`, `"warning"`, `"error"`.

---

### `styles.py` — QSS Stylesheets

Contains `DARK_STYLE` and `LIGHT_STYLE` strings assembled from a shared `COMMON_STYLE` base.

**Key styled selectors:**

| Selector | Component |
|---|---|
| `#HeaderWidget` | Top header bar |
| `#BookCardFrame` | Individual book list cards |
| `#StatusInstalledLabel` / `#StatusQueuedLabel` | Status text badges |
| `#ToastInfo` / `#ToastSuccess` / `#ToastWarning` / `#ToastError` | Toast type colors |
| `#BatchBar` | Batch action bar (blue floating strip) |
| `QPushButton.BatchActionBtn` | Buttons inside the batch bar |
| `QPushButton#SelectModeBtn` | Select toggle in header |
| `#DatabaseUrlField` | URL input in PreferencesDialog |
| `#QueueBadge` | Queue count label in header |

---

### `qt_compat.py` — Qt Compatibility Layer

Provides a unified import surface for all Qt classes regardless of which backend is installed:

```
PySide6 → PyQt6 → PyQt5
```

Also patches missing enum shims on PyQt6 (e.g. `Qt.AlignCenter → Qt.AlignmentFlag.AlignCenter`) so the codebase can always use PySide6-style attribute access.

Exports: `QApplication`, `QMainWindow`, `QWidget`, `QVBoxLayout`, `QHBoxLayout`, `QLabel`, `QLineEdit`, `QComboBox`, `QScrollArea`, `QMessageBox`, `QStatusBar`, `QSizePolicy`, `QPushButton`, `QProgressBar`, `QFrame`, `Qt`, `QTimer`, `QDialog`, `QButtonGroup`, `QRadioButton`, `QGroupBox`, `QEvent`, `QIcon`, `QPixmap`, `QPen`, `QColor`, `QPainter`, `QThread`, `QEventLoop`, `QObject`, `Signal`, `Slot`, `QT_API`

---

## 4. Signal Flow Diagram

### Download → Install Flow

```
User clicks Install
        │
        ▼
MainWindow._enqueue_book(book)
        │
        ▼
DownloadQueue.enqueue(book, path)
        │
  slot available?
  ┌─────┴─────┐
  Yes          No
  │            │
  ▼            ▼
job_started   card.set_queued(True)
  signal       queue_badge updates
  │
  ▼
MainWindow.start_download(book, path)
  │
  ▼
DownloadWorker.start()
  │ progress_changed ──► card.update_status(downloading=True, %)
  │ progress_changed ──► _update_title_progress()
  │
  ▼ finished
download_queue.on_download_completed()
_update_title_progress()
  │
  ▼
MainWindow.start_installation(book, file_path)
  │
  ▼
InstallerWorker.start()
  │ status_changed ──► statusBar.showMessage()
  │
  ▼ finished(True)
card.update_status(installed=True)
toast_manager.show_toast("Installed!", "success")
```

### Auto-Update Flow

```
App launch
  │
  ▼
AutoUpdateScheduler.start()
  │
  ├── immediate: _maybe_check()
  └── QTimer (6h): _maybe_check()
              │
         policy == "off"? → skip
         last_check < 24h? → skip
              │
              ▼
         UpdateChecker.start()
              │
         update_available
              │
         ┌───┴───────────────────────────────────┐
         │ policy == "check"      policy == "auto"│
         ▼                        ▼               │
    toast "v{x} available"   auto_install_requested
                                  │
                             MainWindow.on_update_available()
                             → downloads + installs silently
```

---

## 5. File Path Reference

| Path | Purpose |
|---|---|
| `~/.config/raf/config.json` | User configuration |
| `~/.cache/raf/downloads/` | Download cache |
| `~/.local/share/raf/apps/<id>/` | Extracted `.zip`/`.fernus` books |
| `~/.local/share/applications/raf-<id>.desktop` | Desktop launchers for `.zip` books |
| `mock_system/config.json` | Dev mode config |
| `mock_system/cache/` | Dev mode downloads |
| `mock_system/installed.json` | Dev mode install state |
| `mock_system/update_mock.json` | Dev mode update metadata |
