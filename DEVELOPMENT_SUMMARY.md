# Raf — Development Summary

[![Türkçe](https://img.shields.io/badge/Dil-T%C3%BCrk%C3%A7e-red?style=flat-square)](DEVELOPMENT_SUMMARY-tr.md)

This document provides a chronological account of every completed development stage, the rationale behind key design decisions, and a full reference of the application's capabilities. It is intended for maintainers and contributors who need to understand how the project evolved.

---

## 👥 Project Information

| Field | Value |
|---|---|
| **Developer** | Kaan Ferid Altundaş |
| **Contact** | kaanferidaltundas@protonmail.com |
| **License** | GPL-3.0 (see `debian/copyright`) |
| **Target Platform** | Pardus ETAP Smart Boards (Debian-based) |
| **Language** | Python 3.9+ |
| **GUI Framework** | GTK4 / Libadwaita |

---

## 🛠️ Stage-by-Stage Development History

### Stage 1 — Project Foundation & Architecture

**Goal:** Establish a clean, maintainable project structure from scratch.

- Reorganized the project into a standard open-source Python layout:
  - `src/core/` — all business logic, fully separated from UI
  - `src/ui/` — all GTK widgets
  - `src/assets/` — book database and icon assets
  - `debian/` — Debian packaging configuration
  - `docs/` — technical documentation
  - `scripts/` — packaging and utility automation
  - `tests/` — automated test suite
  - `mock_system/` — sandboxed developer environment
- Wrote the initial `Database` class to load and serve `books.json`
- Created the `DownloadWorker` `threading.Thread` with callbacks

---

### Stage 2 — GUI Design: Libadwaita / Adwaita Style

**Goal:** Create a visually modern interface matching Pardus/GNOME desktop conventions.

- Implemented `Adw.ApplicationWindow` layout with native GTK4 widgets mimicking GTK Libadwaita's flat, rounded-corner aesthetic
- Built the `BookRow` widget — a horizontal `Adw.ActionRow`
- Built the header bar with centered search, left branding, right view switcher tabs (Market / My Library), Settings, and About buttons
- Implemented `PreferencesWindow` natively using `Adw.PreferencesWindow`
- Added `set_linux_dark_titlebar()` using `xprop` to sync the window manager's title bar decoration with the app's chosen theme

---

### Stage 3 — Download Engine & Smart Board Integration

**Goal:** Make downloads reliable on smart board network conditions.

- Implemented chunked HTTP streaming download with an 8 KB chunk size
- Added **Google Drive virus-warning bypass**: detects when the response is an HTML confirmation page (presence of `<form` in the first 2 KB), extracts `id`, `confirm`, and `uuid` tokens via regex, and re-submits the correct POST to `drive.usercontent.google.com/download`
- Added **HTTP Range resumption**: if the connection drops after partial download, retries with `Range: bytes=<bytes_received>-` header; up to 3 automatic retries before raising an error
- Integrated **on-screen keyboard (OSK) trigger**: an `eventFilter` on the search `QLineEdit` detects focus events and fires `onboard` (or `florence`) for touchscreen environments
- Added `last_percent` attribute to `DownloadWorker` for title bar progress reporting
- Built the `InstallerWorker` Thread covering:
  - `.deb` packages via `pkexec apt-get install -y ./file.deb`
  - `.zip`/`.fernus` packages: extract to `~/.local/share/raf/apps/<id>/`, create `.desktop` launcher
  - Simulated install/uninstall in developer mode (1.5s / 1s artificial delays)
- Implemented `cancel_download()` with graceful worker thread termination

---

### Stage 4 — Debian Package & Self-Updater

**Goal:** Distribute Raf as a Lintian-compliant `.deb` package with a self-update mechanism.

- Created `scripts/build_deb.sh` — standard build path using `dpkg-deb`
- Created `scripts/build_deb.py` — pure-Python `.deb` builder that constructs the `ar` archive format (with correct `control.tar.gz` and `data.tar.gz`) entirely using `tarfile`, `hashlib`, and `struct` — no system tools required
- Achieved Lintian compliance:
  - `DEBIAN/md5sums` — MD5 checksums of all packaged data files
  - `usr/share/doc/raf/copyright` — GPL-3.0 declaration with strict `0o644` permissions
  - File permission enforcement (directories `0755`, files `0644`, executables `0755`)
- Built `UpdateChecker` (Thread) — fetches `update.json` from GitHub, compares version tuples, and invokes callbacks
- Built `UpdateInstaller` (Thread) — downloads the update `.deb` and installs it via `pkexec apt-get install --reinstall -y`
- Connected the update flow to `MainWindow.on_update_available()` which presents a rich-text confirmation dialog with changelog

---

### Stage 5 — CLI Panel

**Goal:** Enable headless/terminal usage for system administrators.

- Created `src/core/cli.py` handling six commands: `list`, `list-installed`, `search`, `install`, `uninstall`, `clean`
- Modified `src/main.py` to route to CLI mode when any argument is present
- CLI reuses `DownloadWorker` and `InstallerWorker` directly
- Added `--help` / `-h` / `help` argument for usage summary
- Implemented a real-time ASCII progress bar in the terminal during downloads
- All CLI strings are fully localized through the same `tr()` system as the GUI

---

### Stage 6 — UI Polish & Theme Fixes

**Goal:** Fix visual regressions and tighten the user experience.

- Built a native GTK4 UI, dropping custom QSS in favor of standard GTK themes
- Removed unused locale keys (eliminated ~15 orphaned keys including `primary_keywords`, `middle_keywords`, `high_keywords`, and all category-related strings)
- Replaced deprecated `locale.getdefaultlocale()` with `locale.getlocale()` in `translation.py`
- Replaced all bare `except:` clauses with `except Exception:` across all core modules

---

### Stage 7 — Major Feature Expansion

**Goal:** Bring the app up to a feature-complete v1.x product.

Seven new features were designed, implemented, and integrated:

#### 7.1 Download Queue (`src/core/download_queue.py`)

- `DownloadQueue` — a FIFO queue with configurable max concurrency (default: 2)
- Prevents duplicate enqueuing of the same book (checked by `book_id`)
- Prevents duplicate enqueuing of the same book (checked by `book_id`)
- `MainWindow` responds to queue changes to update the header badge
- Clicking Cancel on a queued (not yet downloading) card calls `DownloadQueue.dequeue()` — instant removal, no download started

#### 7.2 Toast Notifications & Prompts (`src/ui/toast.py`, `src/ui/dialogs.py`)

- `ToastManager` — stacks active toasts via Adwaita Toast overlays.
- Four types with distinct colors: `info` (blue), `success` (green), `warning` (amber), `error` (red)
- Toasts are shown for: install success/error, uninstall success/error, download error, update available, database sync success
- **Pre-Install Confirmation:** Added an intercepting modal prompt that asks users to confirm before escalating privileges via `pkexec`. This prompt appears immediately after a download completes but before `start_installation` is executed, preventing accidental root authentication popups.

#### 7.3 Title Bar Progress

- `MainWindow._update_title_progress()` called on every progress callback and on download finish/error
- Single download: `[▼ Ankara Kitabı — 67%] Raf`
- Multiple downloads: `[▼ 3 downloads — avg 45%] Raf`
- Title resets to `Raf` when no active downloads remain

#### 7.4 Batch Operations

- **Select mode** toggle button in the header
- `BookRow.set_selection_mode(active)` shows/hides a checkbox
- Batch bar appears with: selected count label, Install Selected button, Uninstall Selected button
- `install_selected()` — queues all selected uninstalled books via the download queue
- `uninstall_selected()` — shows a confirmation dialog then triggers `uninstall_requested` on each selected card

#### 7.5 Remote Database Sync (`src/core/sync.py`)

- `DatabaseSyncWorker` — Thread that fetches a remote `books.json` URL on startup
- Validates the JSON structure before writing to the local cache
- `_on_sync_finished()` reloads the `Database` and refreshes the grid
- Completely silent on failure — local cache always used as fallback
- URL configured in `PreferencesDialog` under "Book Database URL"

#### 7.6 Flatpak & Snap Support (`src/core/installer.py`)

- `InstallerWorker` now handles two new `file_type` values:
  - `"flatpak"` → `flatpak install --user --noninteractive <flatpak_ref>`
  - `"snap"` → `pkexec snap install <snap_name>`
- Uninstall path: `flatpak uninstall --user`, `pkexec snap remove`
- Detection helpers: `get_all_installed_flatpaks()`, `get_all_installed_snaps()`
- Availability checks: if `flatpak`/`snap` binary is not in PATH, emits a localized error message
- `is_book_installed()` routes to the appropriate detector by `file_type`
- Locale strings added for all Flatpak/Snap status messages (EN + TR)

#### 7.7 Auto-Update Scheduler (`src/core/updater.py`)

- `AutoUpdateScheduler` runs inside a background thread loop at 6-hour intervals
- Three user-configurable policies stored in `config.json` under `"auto_update_policy"`:
  - `"off"` — no background checks at all
  - `"check"` — checks at most once per 24h; shows a toast if an update is found
  - `"auto"` — checks at most once per 24h; silently triggers install if an update is found
- `last_update_check` timestamp stored in config prevents redundant network calls
- Policy is configurable in `PreferencesDialog` under "Automatic Updates"

---

### Stage 8 — Full Localization & UX Polish

**Goal:** Ensure 100% translatability of all user-facing strings and fix lingering modal bugs.

- Completed a comprehensive sweep of all source files to replace hardcoded strings with `tr(...)`.
- Fully localized installation log traces (`installer.py`) so background bash script steps report properly in the active UI language.
- Wrapped standalone icons and formatting placeholders in localizable blocks where appropriate.
- Fixed an interaction blocker bug where clicking "Logs" inside the modal `AboutDialog` spawned a non-clickable `LogsDialog` in the background (About window is now dismissed first).
- Combined `run_arch.py` and `run_dev.py` into a unified `run_dev.py` that automatically provisions a Python virtual environment if dependencies are missing.

---

## 📁 Complete File Inventory

### Source Files

| File | Role |
|---|---|
| `src/main.py` | Entry point — GUI or CLI routing |
| `src/core/database.py` | JSON book catalogue loader |
| `src/core/downloader.py` | HTTP download Thread |
| `src/core/download_queue.py` | FIFO download queue with concurrency control |
| `src/core/installer.py` | Package install/uninstall for deb/zip/flatpak/snap |
| `src/core/updater.py` | Update checker, installer, auto-update scheduler |
| `src/core/sync.py` | Remote database sync worker |
| `src/core/config.py` | Config persistence |
| `src/core/translation.py` | Runtime i18n engine |
| `src/core/cli.py` | CLI command handler |
| `src/core/version.py` | App version constant |
| `src/ui/main_window.py` | MainWindow |
| `src/ui/components.py` | BookRow |
| `src/ui/preferences.py` | Native Preferences Window |
| `src/ui/about.py` | Native About Window |
| `src/ui/logs_dialog.py` | Real-time installation subprocess logger |
| `src/assets/raf.png` | Application icon |
| `src/assets/locales/en.json` | English locale strings |
| `src/assets/locales/tr.json` | Turkish locale strings |

### Build & Packaging

| File | Role |
|---|---|
| `scripts/build_deb.sh` | Shell build script using `dpkg-deb` |
| `scripts/build_deb.py` | Pure-Python `.deb` builder (no system tools) |
| `scripts/inspect_deb.py` | Package structure validator |
| `debian/control` | Package metadata |
| `debian/changelog` | Version history |
| `debian/copyright` | GPL-3.0 license declaration |
| `debian/rules` | Debhelper build rules |
| `debian/compat` | Debhelper compatibility level |
| `MANIFEST.in` | setuptools manifest inclusions |
| `setup.py` | Python packaging config |
| `requirements.txt` | Python dependency list |

### Developer Tools

| File | Role |
|---|---|
| `run_dev.py` | Dev runner: auto-venv + simulation mode |
| `mock_system/` | Sandboxed install/download environment |

### Tests

| File | What it tests |
|---|---|
| `tests/test_ui_features.py` | Widget creation, search, status updates |
| `tests/test_updater.py` | Update checker flow |
| `tests/test_drive.py` | Google Drive download bypass |

---

## 🚀 Quick Reference — Running & Building

### Start GUI (Developer Mode)
```bash
./run_dev.py
```

### Start GUI (Production)
```bash
python3 -m src.main
# or if installed:
raf
```

### CLI Commands
```bash
raf list
raf list-installed
raf search <term>
raf install <book_id>
raf uninstall <book_id>
raf clean
raf --help
```

### Build .deb Package
```bash
./scripts/build_deb.sh         # Standard (requires dpkg-deb)
python3 scripts/build_deb.py   # Pure Python (no dpkg needed)
python3 scripts/inspect_deb.py # Verify the built package
```

### Run Tests
```bash
python3 tests/test_ui_features.py
python3 tests/test_updater.py
python3 tests/test_drive.py
```

---

## 🔧 Key Design Decisions

### Why GTK4 / Libadwaita?

Libadwaita provides native styling that perfectly fits modern Pardus/GNOME desktop conventions, with built-in animations, responsive design out of the box, and a unified ecosystem approach. QSS maintenance became unwieldy and non-native.

### Why a local JSON database instead of SQLite?

The book catalogue is small (< 100 entries), read-only at runtime, and needs to be bundled into the `.deb` without a schema migration system. JSON is simpler to edit, diff, and distribute. Remote sync replaces the need for an online query API.

### Why `pkexec` instead of `sudo`?

`pkexec` is the PolicyKit standard for privilege escalation on modern GNOME/Pardus desktops. It presents the OS authentication dialog rather than a terminal password prompt, which is consistent with the smart board user experience.

### Why a pure-Python `.deb` builder?

ETAP developers often work on Arch Linux or macOS where `dpkg-deb` is unavailable. The pure-Python builder allows the project to be compiled anywhere without installing Debian system tools.
