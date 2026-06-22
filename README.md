# Raf — Interactive Book Library

**Raf** is a modern desktop application for Pardus-based ETAP (smart board) systems that allows teachers and students to search, download, install, launch, and remove interactive book libraries with a single click. It features a polished Libadwaita-style interface with full dark/light theme support, a command-line interface, batch operations, a download queue, toast notifications, Flatpak/Snap support, and an auto-update system.

---

## Table of Contents

1. [Features](#features)
2. [Requirements](#requirements)
3. [Installation](#installation)
4. [Running the Application](#running-the-application)
5. [Command-Line Interface (CLI)](#command-line-interface-cli)
6. [Using the GUI](#using-the-gui)
7. [Preferences & Settings](#preferences--settings)
8. [Building the .deb Package](#building-the-deb-package)
9. [Developer Mode](#developer-mode)
10. [Project Structure](#project-structure)
11. [Running Tests](#running-tests)
12. [License & Credits](#license--credits)

---

## Features

### Core
- 🔍 **Real-time search** across book titles, publishers, and descriptions
- ⬇️ **Resumable downloads** with HTTP `Range` header support and Google Drive bypass
- 📦 **Multi-format installation** — `.deb`, `.zip`/`.fernus`, Flatpak, Snap
- 🚀 **Launch installed books** directly from the app
- 🗑️ **Uninstall** any installed library cleanly

### Queue & Progress
- 📋 **Download queue** — add multiple books; max 2 run concurrently, rest wait in order
- 📊 **Title bar progress** — window title shows `[▼ BookName — 67%]` during downloads
- 🔔 **Toast notifications** — elegant, auto-dismissing alerts for install/uninstall/update events

### Batch Operations
- ✅ **Select mode** — select multiple book cards at once
- 📥 **Install selected** — queues all selected uninstalled books with one click
- 🗑️ **Uninstall selected** — removes all selected installed books after confirmation

### Connectivity & Sync
- 📡 **Remote database sync** — fetch an updated `books.json` from any URL on startup
- 🌐 **Offline mode detection** — disables downloads and shows a badge when no network is available

### Updates
- 🔄 **Auto-update scheduler** — three policies: Manual, Notify, or Auto-install
- 🕐 **Smart interval** — checks at most once per 24 hours, runs every 6 hours in the background

### Interface
- 🎨 **Light and dark themes** with full Libadwaita-style styling
- 🌍 **Multi-language** — English and Turkish, switchable at runtime
- 🔔 **System theme sync** — follows desktop dark/light preference via D-Bus
- ⌨️ **Touchscreen/OSK support** — triggers on-screen keyboard on focus events
- 💾 **Disk space** and **cache size** display in Preferences

---

## Requirements

### System (Production — Pardus/Debian/Ubuntu)

| Dependency | Purpose |
|---|---|
| `python3` (≥ 3.9) | Runtime |
| `python3-pyside6` or `python3-pyqt5` | Qt GUI framework |
| `python3-requests` | HTTP downloads |
| `policykit-1` | Elevated package operations (`pkexec`) |
| `dpkg` / `apt-get` | `.deb` package installation |
| `flatpak` *(optional)* | Flatpak package support |
| `snapd` *(optional)* | Snap package support |

### Developer Machine (any Linux/macOS)

```
PySide6 >= 6.0.0
requests >= 2.25.0
urllib3 >= 1.26.0
```

Install with:
```bash
pip install -r requirements.txt
```

> **Note:** `run_arch.py` handles venv creation and dependency installation automatically.

---

## Installation

### From .deb Package (Recommended for Pardus)

```bash
# Install the pre-built .deb package:
sudo apt install ./raf_1.0.3_all.deb
```

Or via the software centre by double-clicking the `.deb` file.

After installation, Raf is available system-wide as:
```bash
raf           # Launch the GUI
raf list      # Run CLI commands
```

### From Source

```bash
git clone https://github.com/KaanFerid/Raf.git
cd raf
pip install -r requirements.txt
python3 -m src.main
```

---

## Running the Application

### Production Mode (Pardus / Debian)

Runs with full system privileges for installing `.deb` packages:

```bash
python3 -m src.main
```

Or if installed from the `.deb` package:

```bash
raf
```

### Developer / Simulator Mode

The `run_arch.py` script launches the app in a fully sandboxed simulation environment. It makes **zero permanent changes** to your system:

- Downloads are saved to `mock_system/cache/`
- Installs are tracked in `mock_system/installed.json`
- PolicyKit popups are skipped (simulated)

```bash
./run_arch.py
```

If `PySide6` or `requests` are missing, the script automatically creates a `.venv` virtual environment and installs them before launching.

---

## Command-Line Interface (CLI)

Raf includes a full-featured CLI for headless/terminal use. All commands work in both production and developer mode.

### Usage

```bash
raf <command> [arguments]
# or in developer/source mode:
./run_arch.py <command> [arguments]
# or directly:
python3 -m src.main <command> [arguments]
```

### Commands

#### `list` — List all available books
```bash
raf list
```
Prints a formatted table of all books in the database:
```
Total 42 books available:
ID                                  | Title                                         | Publisher
---------------------------------------------------------------------------------------------------------
akademikbasariyayinlarikutuphane    | Akademik Başarı Yayınları Kütüphanesi        | Akademik Başarı
...
```

---

#### `list-installed` — List installed books
```bash
raf list-installed
```
Shows only books currently installed on the system:
```
Total 3 installed books available:
ID                                  | Title                                         | Type
...
```

---

#### `search <term>` — Search the book database
```bash
raf search ankara
raf search "matematik"
```
Searches across book titles, publishers, and descriptions. Case-insensitive.

---

#### `install <book_id>` — Download and install a book
```bash
raf install akademikbasariyayinlarikutuphane
```

This command:
1. Looks up the book in the database by ID
2. Downloads the package (with a real-time progress bar)
3. Installs it via `pkexec apt-get install` (for `.deb`) or extracts it (for `.zip`)

Progress display:
```
Downloading: [========================================] %100 (2.34 MB/s)
```

> **Note:** Already-installed books will show an info message and skip re-installation.

---

#### `uninstall <book_id>` — Uninstall a book
```bash
raf uninstall akademikbasariyayinlarikutuphane
```

Removes the package from the system using `pkexec apt-get remove` for `.deb` packages, or deletes the extracted directory and `.desktop` launcher for `.zip` packages.

---

#### `clean` — Clear download cache
```bash
raf clean
```

Deletes all cached `.deb` and `.zip` files from `~/.cache/raf/downloads/`. Reports the number of deleted files.

---

#### `--help` / `-h` — Show help
```bash
raf --help
raf -h
raf help
```

Prints a summary of all available commands.

---

### CLI Exit Codes

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | Error (missing argument, book not found, download failed, etc.) |

---

## Using the GUI

### Main Window Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  Raf  ↓ 2 queued  [Select]    [Search...]   [Market|Library]  [Preferences] [About] │
├─────────────────────────────────────────────────────────────────┤
│  42 books listed.                                               │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  [AB]  Akademik Başarı Kütüphanesi              [▓▓▓░]  │   │
│  │        Akademik Başarı · Type: DEB          [Install]   │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ...                                                            │
├─────────────────────────────────────────────────────────────────┤
│  [3 selected  [Install Selected]  [Uninstall Selected]  ✕]      │
├─────────────────────────────────────────────────────────────────┤
│  Status bar                                           [OFFLINE] │
└─────────────────────────────────────────────────────────────────┘
```

### Header Bar

| Element | Description |
|---|---|
| **Raf** (title) | Application name / branding |
| **↓ N queued** | Download queue badge — visible when books are waiting |
| **Select** | Toggles batch selection mode |
| **Search bar** | Filters books in real time (title, publisher, description) |
| **Market** tab | Shows all available books |
| **My Library** tab | Shows only installed books |
| **Preferences** | Opens the settings dialog |
| **About** | Shows version and credits |

### Book Cards

Each card shows:
- **Publisher badge** — colored initials icon auto-generated from publisher name
- **Title** — book/library name
- **Publisher** — publisher name
- **Type** — `DEB`, `ZIP`, `FERNUS`, `FLATPAK`, or `SNAP`
- **Progress bar** — visible during download, shows percentage
- **Speed** — download speed in MB/s
- **Status label** — `Not Installed`, `Queued`, `Downloading`, `Installing`, `Installed`
- **Install / Run / Cancel button** — primary action
- **Uninstall button** — shown when installed

### Status Flow

```
[Not Installed] → [Install clicked] → [Queued] → [Downloading ██░░ 45%]
                                                         ↓
                                               [Installing...]
                                                         ↓
                                               [Installed] → [Run]
```

### Search

Type in the search bar to filter books in real time. The search is applied against:
- Book title
- Publisher name  
- Book description

To clear the search, delete the text from the field.

### Download Queue

When you click Install on multiple books quickly, or use **Batch → Install Selected**, books are added to the download queue. At most **2 downloads** run at the same time; the rest show `Queued` status and start automatically as slots open.

- A **↓ N queued** badge appears in the header when books are waiting
- Clicking **Cancel** on a queued book removes it from the queue immediately (no download starts)
- Clicking **Cancel** on a downloading book cancels the in-progress download

### Title Bar Progress

When one or more books are downloading, the window title updates in real time:

- **Single download:** `[▼ Ankara Kitabı — 67%] Raf`
- **Multiple downloads:** `[▼ 3 downloads — avg 45%] Raf`

When all downloads finish, the title returns to `Raf`.

### Toast Notifications

Non-blocking toast notifications appear in the bottom-right corner and auto-dismiss after a few seconds:

| Event | Color | Duration |
|---|---|---|
| Install success | Green | 3.5s |
| Uninstall success | Green | 3.5s |
| Download error | Red | 3.5s |
| Install error | Red | 3.5s |
| Update available | Blue | 8s |
| Library synced | Green | 3.5s |

Click **✕** on any toast to dismiss it immediately.

### Batch Operations

1. Click the **Select** button in the header to enter selection mode
2. Click book cards to toggle their selection (☐ / ☑)
3. The **batch action bar** appears at the bottom showing:
   - Count of selected books
   - **Install Selected** — queues all selected uninstalled books
   - **Uninstall Selected** — confirms, then removes all selected installed books
   - **✕** — exits selection mode
4. Click **Select** again or **✕** to exit selection mode

### Market vs. My Library Tabs

| Tab | Shows |
|---|---|
| **Market** | All books in the database (installed or not) |
| **My Library** | Only currently installed books |

Both tabs respect the current search query.

### Offline Mode

When no network connection is detected:
- A red **`OFFLINE MODE`** badge appears in the status bar
- Install buttons are disabled for uninstalled books
- Books already installed remain fully accessible (launch/uninstall still works)

---

## Preferences & Settings

Open **Preferences** from the header bar. Changes take effect immediately after clicking **Save**.

### Appearance

| Option | Description |
|---|---|
| **System Theme (Automatic)** | Follows the OS dark/light preference via D-Bus |
| **Light Theme** | Forces the light Libadwaita palette |
| **Dark Theme** | Forces the dark Libadwaita palette |

The system theme monitors D-Bus every 4 seconds for changes (e.g. when the smart board auto-switches at night).

### Language

Choose between **Turkish** and **English**. The UI updates instantly without restarting.

### System and Cache

| Field | Description |
|---|---|
| **System Free Space** | Current free disk space on the home partition |
| **Download Cache** | Total size of cached download files |
| **Clear Cache** | Deletes all files in `~/.cache/raf/downloads/` |

### Book Database URL

Enter a URL pointing to a `books.json` file hosted remotely. On each startup, Raf fetches this URL in the background and updates the local library. Leave empty to use the built-in library.

The remote file must be a JSON array of book objects, each containing at minimum: `id`, `title`, `publisher`, `file_name`, `download_url`.

### Automatic Updates

| Policy | Description |
|---|---|
| **Manual** | Checks only on launch; no background checks |
| **Notify me** | Checks every 24h; shows a toast when an update is available |
| **Auto-install** | Checks every 24h; silently downloads and installs the update |

---

## Building the .deb Package

### Quick Build

```bash
./scripts/build_deb.sh
```

This script:
1. Creates a temporary `build/raf-pkg/` staging directory
2. Copies source files to `usr/lib/raf/` within the staging tree
3. Writes the `DEBIAN/control` file
4. Computes MD5 checksums for all files → `DEBIAN/md5sums`
5. Copies the `copyright` file to `usr/share/doc/raf/copyright`
6. Sets correct permissions (`0755` for dirs, `0644` for files)
7. Calls `dpkg-deb --build` or falls back to `scripts/build_deb.py`

Output: `raf_<version>_all.deb` in the project root.

### Pure-Python Fallback

If `dpkg-deb` is not available (e.g. on Arch Linux, macOS):

```bash
python3 scripts/build_deb.py
```

This Python script builds a fully Lintian-compliant `.deb` without any system tools, using only the Python standard library (`tarfile`, `hashlib`, `struct`).

### Verifying the Package

```bash
python3 scripts/inspect_deb.py
```

Prints a summary of the `.deb` structure and verifies:
- `md5sums` is present and contains entries
- `copyright` file is present in `usr/share/doc/raf/`
- File permissions are correct

### Installing the Built Package

```bash
sudo apt install ./raf_<version>_all.deb
# or
sudo dpkg -i raf_<version>_all.deb && sudo apt-get install -f
```

### Package Metadata

The Debian package metadata is defined in [`debian/control`](debian/control):

| Field | Value |
|---|---|
| Package | `raf` |
| Architecture | `all` (pure Python, no compiled extensions) |
| Section | `utils` |
| Depends | `python3`, `python3-pyside6 \| python3-pyqt5`, `python3-requests`, `policykit-1` |
| Maintainer | Kaan Ferid Altundaş |

---

## Developer Mode

### What Simulator Mode Does

Setting `RAF_DEV=1` activates developer mode, which:

| System action | Simulated as |
|---|---|
| `.deb` install via `pkexec` | 1.5s simulated wait, book added to `mock_system/installed.json` |
| `.deb` uninstall | 1s simulated wait, book removed from `mock_system/installed.json` |
| Downloads | Real download to `mock_system/cache/` |
| Update check | Reads `mock_system/update_mock.json` instead of remote URL |
| Config files | Saved to `mock_system/config.json` |

### Launching in Developer Mode

```bash
# GUI mode
./run_arch.py

# CLI mode
./run_arch.py list
./run_arch.py install <book_id>
./run_arch.py search <term>

# Manual launch with environment variable
RAF_DEV=1 python3 -m src.main
```

### Simulating an Update

Edit `mock_system/update_mock.json`:
```json
{
  "version": "99.0.0",
  "download_url": "https://example.com/raf_99.0.0_all.deb",
  "changelog": "Major update with new features."
}
```

Launch the app — the update dialog will appear automatically.

### Qt Backend Selection

Raf supports three Qt backends, tried in this priority order:

| Priority | Backend | Install command |
|---|---|---|
| 1 | **PySide6** | `pip install PySide6` |
| 2 | **PyQt6** | `pip install PyQt6` |
| 3 | **PyQt5** | `pip install PyQt5` |

The active backend is printed at startup: `Qt API: PySide6`.

---

## Project Structure

```
raf/
├── src/                          # Application source code
│   ├── main.py                   # Entry point — GUI or CLI dispatch
│   ├── qt_compat.py              # Qt backend abstraction (PySide6/PyQt6/PyQt5)
│   ├── core/
│   │   ├── database.py           # Book database loader (local JSON + remote sync)
│   │   ├── downloader.py         # DownloadWorker — chunked HTTP download thread
│   │   ├── download_queue.py     # DownloadQueue — FIFO queue, concurrency control
│   │   ├── installer.py          # InstallerWorker — deb/zip/flatpak/snap install
│   │   ├── updater.py            # UpdateChecker, UpdateInstaller, AutoUpdateScheduler
│   │   ├── sync.py               # DatabaseSyncWorker — remote books.json fetcher
│   │   ├── config.py             # User config read/write (~/.config/raf/config.json)
│   │   ├── translation.py        # TranslationManager — runtime language switching
│   │   ├── cli.py                # CLI command handler
│   │   └── version.py            # App version string
│   ├── ui/
│   │   ├── main_window.py        # MainWindow + PreferencesDialog
│   │   ├── components.py         # BookCard, PublisherBadge widgets
│   │   ├── styles.py             # LIGHT_STYLE, DARK_STYLE QSS stylesheets
│   │   └── toast.py              # ToastNotification, ToastManager
│   └── assets/
│       ├── books.json            # Built-in book database
│       ├── raf.png               # Application icon
│       └── locales/
│           ├── en.json           # English strings
│           └── tr.json           # Turkish strings
│
├── debian/                       # Debian package configuration
│   ├── control                   # Package metadata and dependencies
│   ├── changelog                 # Package change log
│   ├── copyright                 # GPL-3.0 license declaration
│   ├── rules                     # Build rules
│   └── compat                    # Debhelper compatibility level
│
├── scripts/
│   ├── build_deb.sh              # Build script (uses dpkg-deb if available)
│   ├── build_deb.py              # Pure-Python .deb builder (no dpkg needed)
│   └── inspect_deb.py            # .deb structure validator
│
├── tests/
│   ├── test_ui_features.py       # UI component and filter assertion tests
│   ├── test_updater.py           # Update flow verification
│   └── test_drive.py             # Google Drive download network tests
│
├── mock_system/                  # Developer mode sandbox
│   ├── cache/                    # Downloaded files (dev mode only)
│   ├── installed.json            # Simulated installation state
│   ├── config.json               # Dev mode config
│   └── update_mock.json          # Simulated update metadata
│
├── docs/
│   ├── architecture.md           # Architecture deep-dive
│   └── packaging.md              # Packaging and Lintian compliance details
│
├── run_arch.py                   # Developer runner (auto-venv + simulation)
├── run_dev.py                    # Alternative dev launcher
├── requirements.txt              # Python dependencies
├── setup.py                      # setuptools packaging config
└── README.md                     # This file
```

---

## Running Tests

### UI Feature Tests

Tests widget creation, search filtering, status updates, and translation switching:

```bash
python3 tests/test_ui_features.py
```

### Self-Updater Tests

Tests the update check flow, version comparison, and `UpdateInstaller`:

```bash
python3 tests/test_updater.py
```

### Google Drive Download Tests

Tests the virus-warning bypass and chunked download resumption:

```bash
python3 tests/test_drive.py
```

### Package Validation

Verifies the built `.deb` is Lintian-compliant:

```bash
python3 scripts/inspect_deb.py
```

---

## Architecture Overview

### Threading Model

All network I/O and package operations run in background `QThread` workers that communicate with the main UI thread exclusively via Qt signals:

```
[UI Thread (MainWindow)]
        │
        ├── DownloadWorker (QThread) ──signals──► progress_changed, finished, error
        │
        ├── InstallerWorker (QThread) ──signals──► status_changed, finished, output_received
        │
        ├── UpdateChecker (QThread) ──signals──► update_available, no_update
        │
        ├── DatabaseSyncWorker (QThread) ──signals──► sync_finished, sync_failed
        │
        └── AutoUpdateScheduler (QObject + QTimer) ──signals──► update_toast_requested, auto_install_requested
```

### Configuration Storage

Config is stored at `~/.config/raf/config.json`:

```json
{
  "theme_mode": "system",
  "language": "tr",
  "auto_update_policy": "check",
  "database_url": "",
  "last_update_check": 1750000000.0,
  "package_names": {
    "book_id_123": "exact-deb-package-name"
  }
}
```

### Book Database Format

`src/assets/books.json` is a JSON array. Each entry:

```json
{
  "id": "unique-book-id",
  "title": "Book Title",
  "publisher": "Publisher Name",
  "file_name": "package.deb",
  "file_type": "deb",
  "download_url": "https://...",
  "description": "Optional description"
}
```

**Supported `file_type` values:**

| Value | Installer | Detection |
|---|---|---|
| `deb` | `pkexec apt-get install` | `dpkg-query` |
| `zip` / `fernus` | Extracts to `~/.local/share/raf/apps/` | Directory + `.desktop` check |
| `flatpak` | `flatpak install --user --noninteractive` | `flatpak list --app` |
| `snap` | `pkexec snap install` | `snap list` |

For `flatpak` entries, also include `"flatpak_ref": "org.example.App"`.  
For `snap` entries, also include `"snap_name": "example-snap"`.

---

## License & Credits

This project is licensed under the **GPL-3.0** license. See [`debian/copyright`](debian/copyright) for the full declaration.

**Developer:** Kaan Ferid Altundaş — kaanferidaltundas@protonmail.com

**Credits:**
- Book shelf icon by Nick Frost and Greg Lapin on [Icon-Icons.com](https://icon-icons.com/authors/237-nick-frost-and-greg-lapin)
