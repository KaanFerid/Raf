# Architecture Documentation

[![Türkçe](https://img.shields.io/badge/Dil-T%C3%BCrk%C3%A7e-red?style=flat-square)](architecture-tr.md)
Raf has a layered, asynchronous architecture designed for stability on Pardus ETAP smart boards. All user-visible operations that involve network or filesystem I/O run in background `threading.Thread` workers, communicating back to the UI thread exclusively via `GLib.idle_add` callbacks.

---

## 1. Layer Overview

```
┌─────────────────────────────────────────────────┐
│                  UI Layer                        │
│  main_window.py · components.py                 │
│  desktop_editor.py · logs_dialog.py             │
│  preferences.py · about.py                      │
├─────────────────────────────────────────────────┤
│               Core / Business Logic              │
│  database.py · downloader.py · installer.py     │
│  updater.py · sync.py · download_queue.py       │
│  config.py · translation.py · cli.py            │
└─────────────────────────────────────────────────┘
```

---

## 2. Core Modules

### `database.py` — Book Database

Loads the book catalogue from the `database/` directory. Reads both `fernus_drive.json` and `publishers.json`, merging them into a single list of available books.
Supports remote synchronization handled by `sync.py`.

**Key class: `Database`**
- `load_books()` — reads from the local `database/` folder and merges all files
- `get_all_books()` → `list[dict]` — returns all book entries
- `search_books(query)` → `list[dict]` — full-text search on title, publisher, description

---

### `downloader.py` — Download Worker

A standard python thread-based worker that downloads book packages with:
- **Chunked streaming** (8 KB chunks) to track progress
- **Google Drive virus-warning bypass** — detects HTML confirmation pages and re-submits with extracted `confirm` and `uuid` form tokens
- **HTTP Range resumption** — retries with `Range: bytes=N-` if the connection drops mid-download (up to 3 automatic retries)
- **Cancellation** — `cancel()` sets a flag checked after each chunk
- **Speed calculation** — real MB/s shown in UI

**Callbacks:**
- `on_progress_changed(book_id, percent, speed_str)`
- `on_finished(book_id, local_file_path)`
- `on_error(book_id, error_message)`

---

### `download_queue.py` — Download Queue

A FIFO queue with configurable concurrency control.

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

---

### `installer.py` — Package Installer

A thread-based worker that handles installing and uninstalling books based on their `file_type`.

**Key class: `InstallerWorker`**

Constructor: `InstallerWorker(book, file_path, action="install")`

**Supported file types:**

| `file_type` | Install method | Uninstall method |
|---|---|---|
| `deb` | `pkexec apt-get install -y ./file.deb` | `pkexec apt-get remove -y <pkg>` |
| `zip` / `fernus` / `appimage` | Extracts/Copies to `/opt/raf/apps/<id>/` + creates global `.desktop` via `pkexec` | `pkexec` deletes app dir + `.desktop` |
| `flatpak` | `flatpak install --user --noninteractive <ref>` | `flatpak uninstall --user --noninteractive <ref>` |
| `snap` | `pkexec snap install <snap_name>` | `pkexec snap remove <snap_name>` |

For `.deb` installs, the exact package name is extracted from the `.deb` file using `dpkg-deb -f Package` and cached in `config.json` to speed up future `is_installed` checks.

**Callbacks:**
- `on_status_changed(book_id, message)`
- `on_finished(book_id, success)`
- `on_output_received(book_id, line)`

---

### `updater.py` — Update System

Three classes handle different aspects of the update flow:

**`UpdateChecker`**
Fetches `update.json` from GitHub, compares version tuples, fires callbacks on new versions.

**`UpdateInstaller`**
Downloads and installs a `.deb` update file via `pkexec apt-get install --reinstall -y`.

**`AutoUpdateScheduler`**
Runs background thread checks at 6-hour intervals. Reads `auto_update_policy` from config.

---

### `sync.py` — Remote Database Sync

Synchronizes the local database directory with a remote server. If the configured `database_url` points to a base URL, it concurrently fetches `fernus_drive.json` and `publishers.json`, validates them, and saves them to the local `database/` cache path.

---

### `config.py` — Persistent Configuration

Manages `~/.config/raf/config.json` (or `mock_system/config.json` in dev mode).

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

Loads locale files from `src/assets/locales/`. Supports runtime language switching without restarting via callbacks.

**Functions:**
- `tr(key, **kwargs)` — returns the translated string for `key`, formatted with `kwargs`
- `set_language(lang_code)` — switches language and notifies all registered listeners

---

### `cli.py` — CLI Handler

Invoked when any command-line argument is passed to `src.main`. 
Reads `RAF_DEV` to choose simulation vs. real package operations.

---

## 3. UI Layer

### `main_window.py` — MainWindow

The top-level `Adw.ApplicationWindow` that:
- Owns the `Database`, `DownloadQueue`, `AutoUpdateScheduler`, and `DatabaseSyncWorker`
- Manages `active_downloads` and `active_installations` dicts
- Handles all callbacks between workers and UI updates via `GLib.idle_add`

**Key method groups:**

| Group | Methods |
|---|---|
| Download lifecycle | `start_download()`, `on_download_progress()`, `on_download_finished()`, `on_download_error()`, `cancel_download()` |
| Install lifecycle | `start_installation()`, `on_installation_finished()`, `start_uninstallation()`, `on_uninstallation_finished()` |
| Batch mode | `toggle_selection_mode()`, `process_local_files()` |
| Refresh | `refresh_grid()`, `refresh_packages_cache()` |

---

### `components.py` — BookRow

An `Adw.ActionRow` representing one book entry.

**Key attributes:**
- `is_installed: bool` — tracks install state
- `downloading: bool` — tracks active download

---

## 4. File Path Reference

| Path | Purpose |
|---|---|
| `~/.config/raf/config.json` | User configuration |
| `~/.cache/raf/downloads/` | Download cache |
| `/opt/raf/apps/<id>/` | System-wide extracted `.zip`/`.fernus`/`.appimage` books |
| `/usr/share/applications/raf-<id>.desktop` | Global desktop launchers for standalone books |
| `/usr/share/raf/database/` | Master database files (`fernus_drive.json`, `publishers.json`) |
| `mock_system/config.json` | Dev mode config |
| `mock_system/cache/` | Dev mode downloads |
| `mock_system/installed.json` | Dev mode install state |
| `mock_system/update_mock.json` | Dev mode update metadata |
| `~/.config/raf/sideloaded.json` | Database for user-added local apps |
| `~/.local/share/applications/raf-<id>.desktop` | User-edited desktop launchers for local apps |

---

## 5. Sideloading & Local Launcher Editor

Raf supports the installation of local standalone application files (`.deb`, `.zip`, `.appimage`, `.fernus`) outside of the central remote database. 

### Sideload Workflow

1. **Discovery:** User selects local files or a directory via `MainWindow.on_install_local_clicked()` or drag-and-drop on the main window.
2. **Parsing:** `src/core/sideload.py` validates the files against `SUPPORTED_EXTENSIONS`. Unrecognized files are skipped.
3. **Database Injection:** Valid local applications are given a unique ID (`local_<safe_filename>`) and added to the user's `~/.config/raf/sideloaded.json` database. The `Database` class automatically merges these sideloaded apps with the main `fernus_drive.json` list so they appear seamlessly in the Library tab.
4. **Execution:** The file path is handed off to `InstallerWorker`, which processes it identically to a downloaded remote application.

### Launcher Customization

Since sideloaded applications lack centralized metadata (publisher, proper titles, icons), Raf provides a built-in Desktop Launcher Editor (`src/ui/desktop_editor.py`).

- Accessible from the "Edit Launcher" button on installed local apps in the Library.
- By saving to `~/.local/share/applications/`, the editor safely overrides global `/usr/share/applications/` launchers without requiring `sudo` privileges.
- Uses native GTK4/Adwaita layout widgets wrapped in an `Adw.Window` to directly modify the `.desktop` INI specification.
