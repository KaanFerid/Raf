<p align="center">
  <img src="src/assets/raf.png" width="128" alt="Raf Logo">
</p>

# Raf — Interactive Book Library

[![Türkçe](https://img.shields.io/badge/Dil-T%C3%BCrk%C3%A7e-red?style=flat-square)](README.md)
[![License: GPL v3](https://img.shields.io/github/license/KaanFerid/Raf?color=blue)](https://github.com/KaanFerid/Raf/blob/main/LICENSE)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/KaanFerid/Raf)](https://github.com/KaanFerid/Raf/releases)
[![Build Debian Package](https://github.com/KaanFerid/Raf/actions/workflows/build.yml/badge.svg)](https://github.com/KaanFerid/Raf/actions/workflows/build.yml)
[![Release](https://github.com/KaanFerid/Raf/actions/workflows/release.yml/badge.svg)](https://github.com/KaanFerid/Raf/actions/workflows/release.yml)

> **[📖 Visit the Raf Wiki](wiki/Home.md)** to explore all documentation, including CLI references, architecture diagrams, and packaging guides.

**Raf** is a modern desktop application for Pardus-based ETAP (smart board) systems that allows teachers and students to search, download, install, launch, and remove interactive book libraries with a single click. It features a polished Libadwaita-style interface with a global dark/light theme engine, a custom zero-dependency i18n translation system, native OS integration for drag & drop and "Open With" sideloading, a command-line interface, and an auto-update system.

> **📢 For Publishers:** Want to add your digital libraries to the Raf ecosystem? Please see our [Contributing](CONTRIBUTING.md) page to get in touch!

---

## Gallery (Photos & Videos)

https://github.com/user-attachments/assets/15a8f0a1-273a-4860-b7f0-801424c240c8

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
- 🔍 **Real-time search** across book titles, publishers, and descriptions with 300ms debouncing for peak GUI performance.
- ⬇️ **Resumable downloads** with HTTP `Range` header support and Google Drive bypass.
- 📦 **Multi-format installation** — `.deb`, `.zip`/`.fernus`, `.appimage`, Flatpak, Snap.
- 🚀 **Launch installed books** directly from the app.
- 🗑️ **Uninstall** any installed library cleanly.

### Sideloading & OS Integration
- 📥 **Drag & Drop** — Drag files directly into the window to install them.
- 📂 **Open With...** — Right-click packages in your file manager and open them with Raf.
- 🛡️ **Confirmation Dialog** — Aggregates all local packages into a review window before requesting administrator passwords.

### Performance & Security
- 🏎️ **Asynchronous Architecture** — System package queries (`dpkg`) and installations happen on separate background threads to ensure the UI never freezes.
- 🔐 **Secure Subprocesses** — All system interactions use safe array execution, preventing shell injection vulnerabilities.
- 🛡️ **Pre-Install Confirmation** — Intercepts the installation flow right before system authentication, explicitly showing the user what package is about to be installed to prevent unexpected `pkexec` popups.
- 📋 **Live Logs Viewer** — A dedicated Logs dialog for debugging installation outputs in real time.

### Queue & Progress
- 📋 **Download queue** — add multiple books; max 2 run concurrently, rest wait in order.
- 📊 **Title bar progress** — window title shows `[▼ BookName — 67%]` during downloads.
- 🔔 **Toast notifications** — elegant, auto-dismissing alerts for install/uninstall/update events.

### Connectivity & Sync
- 📡 **Remote database sync** — fetch an updated `books.json` from any URL on startup.
- 🌐 **Offline mode detection** — disables downloads and shows a badge when no network is available.

### Interface & Theming
- 🎨 **Centralized Theme Engine** — Instantly flips between Light and Dark styles across the entire application (including message boxes and popups) by utilizing native GTK4/Libadwaita color schemes.
- 🌍 **Custom Zero-Dependency i18n Engine** — Built from scratch with flattened JSON traversal, auto-discovery of languages via `_meta` blocks, English fallback prevention, and live-UI updating without app restarts!
- 🔔 **System theme sync** — follows desktop dark/light preference via D-Bus.

---

## Requirements

### System (Production — Pardus/Debian/Ubuntu)

| Dependency | Purpose |
|---|---|
| `python3` (≥ 3.9) | Runtime |
| `python3-gi`, `gir1.2-gtk-4.0`, `gir1.2-adw-1` | GTK4 / Libadwaita GUI framework |
| `python3-requests` | HTTP downloads |
| `policykit-1` | Elevated package operations (`pkexec`) |
| `dpkg` / `apt-get` | `.deb` package installation |

### Developer Machine (any Linux/macOS)

```text
PyGObject >= 3.42.0
requests >= 2.25.0
urllib3 >= 1.26.0
```

Install with:
```bash
pip install -r requirements.txt
```

> **Note:** `run_dev.py` handles venv creation and dependency installation automatically.

---

## Installation

### From .deb Package (Recommended for Pardus)

```bash
# Install the pre-built .deb package:
sudo apt install ./raf_1.0.0_all.deb
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

The `run_dev.py` script launches the app in a fully sandboxed simulation environment. It makes **zero permanent changes** to your system:

- Downloads are saved to `mock_system/cache/`
- Installs are tracked in `mock_system/installed.json`
- PolicyKit popups are skipped (simulated)

```bash
./run_dev.py
```

If `PyGObject` or `requests` are missing, the script automatically creates a `.venv` virtual environment and installs them before launching.

---

## Command-Line Interface (CLI)

Raf includes a full-featured CLI for headless/terminal use. All commands work in both production and developer mode.

### Usage

```bash
raf <command> [arguments]
# or in developer/source mode:
./run_dev.py <command> [arguments]
# or directly:
python3 -m src.main <command> [arguments]
```

### Commands

#### `list` — List all available books
```bash
raf list
```
Prints a formatted table of all books in the database.

---

#### `list-installed` — List installed books
```bash
raf list-installed
```
Shows only books currently installed on the system.

---

#### `search <term>` — Search the book database
```bash
raf search ankara
```
Searches across book titles, publishers, and descriptions. Case-insensitive.

---

#### `install <book_id>` — Download and install a book
```bash
raf install akademikbasariyayinlarikutuphane
```
This command downloads the package (with a real-time progress bar) and installs it via `pkexec apt-get install` (for `.deb`) or extracts it (for `.zip`).

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

### Sideloading (Drag & Drop / Open With)
You don't need to manually browse for files. Simply **Drag & Drop** any supported package directly onto the main window. The app will instantly display a beautiful blue drop-overlay indicating it is ready to receive your files.
Alternatively, right-click any `.deb`, `.zip`, `.appimage`, or `.fernus` file in your Linux file manager and choose **Open With > Raf**. Both methods will prompt an elegant aggregation dialog reviewing what is about to be installed before requesting admin privileges.

### Search
Type in the search bar to filter books in real time. The search utilizes a 300ms debouncer, ensuring your smart board never freezes or drops frames while recalculating complex UI layouts as you type.

### Download Queue
When you click Install on multiple books quickly, or use **Batch → Install Selected**, books are added to the download queue. At most **2 downloads** run at the same time; the rest show `Queued` status and start automatically as slots open.

### Logs Viewer
At any point during the application lifecycle, you can click the "Logs" button in the header bar. This will open a dynamic, dark-themed terminal viewer tracking live output (`stdout`/`stderr`) from active sub-processes like `dpkg`, `apt`, and `unzip`. 

---

## Preferences & Settings

Open **Preferences** from the header bar. Changes take effect immediately after clicking **Save**.

### Appearance
| Option | Description |
|---|---|
| **System Theme (Automatic)** | Follows the OS dark/light preference via D-Bus |
| **Light Theme** | Forces the light Libadwaita palette |
| **Dark Theme** | Forces the dark Libadwaita palette |

Due to the new centralized engine, native GTK4/Libadwaita color schemes are used, meaning every modal, window, and toast notification instantly changes color accurately based on desktop or user preferences.

### Language
Choose between **Turkish** and **English**. The UI updates instantly without restarting, powered by the custom JSON-based `_meta` i18n observer engine.

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
4. Computers MD5 checksums for all files → `DEBIAN/md5sums`
5. Copies the `database/` directory to ensure newly shipped apps include the absolute latest catalog.

Output: `raf_<version>_all.deb` in the project root.

---

## Developer Mode

### Launching in Developer Mode

```bash
# GUI mode
./run_dev.py
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

---

## Project Structure

```
raf/
├── src/                          # Application source code
│   ├── main.py                   # Entry point — GUI or CLI dispatch
│   ├── core/
│   │   ├── database.py           # Book database loader (local JSON + remote sync)
│   │   ├── downloader.py         # DownloadWorker — chunked HTTP download thread
│   │   ├── download_queue.py     # DownloadQueue — FIFO queue, concurrency control
│   │   ├── installer.py          # InstallerWorker — deb/zip/flatpak/snap install
│   │   ├── updater.py            # UpdateChecker, UpdateInstaller, AutoUpdateScheduler
│   │   ├── sync.py               # DatabaseSyncWorker — remote books.json fetcher
│   │   ├── config.py             # User config read/write (~/.config/raf/config.json)
│   │   ├── translation.py        # Custom zero-dependency i18n translation engine
│   │   ├── cli.py                # CLI command handler
│   │   └── version.py            # App version string
│   ├── ui/
│   │   ├── main_window.py        # MainWindow
│   │   ├── components.py         # BookRow, PublisherBadge widgets
│   │   ├── preferences.py        # Native PreferencesWindow
│   │   ├── about.py              # Native AboutWindow
│   │   ├── toast.py              # Toast notification overlay system
│   │   └── logs_dialog.py        # Real-time installation subprocess logger
│   └── assets/
│       ├── raf.png               # Application icon
│       └── locales/
│           ├── en.json           # English strings + _meta data
│           └── tr.json           # Turkish strings + _meta data
│
├── database/                     # Default JSON library catalogs shipped via .deb
├── debian/                       # Debian package configuration
├── scripts/
│   ├── build_deb.sh              # Build script (uses dpkg-deb if available)
│   ├── build_deb.py              # Pure-Python .deb builder (no dpkg needed)
│   └── inspect_deb.py            # .deb structure validator
│
├── tests/                        # Comprehensive unit and integration testing suite
├── mock_system/                  # Developer mode sandbox
├── docs/                         # Architecture and API documentation
├── run_dev.py                   # Developer runner (auto-venv + simulation)
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

---

## Running Tests

### Self-Updater Tests
```bash
python3 tests/test_updater.py
```

### Google Drive Download Tests
```bash
python3 tests/test_drive.py
```

---

## Architecture Overview

### Threading Model

All network I/O and package operations run in background `threading.Thread` workers that communicate with the main UI thread exclusively via `GLib.idle_add` callbacks.

```
[UI Thread (MainWindow)]
        │
        ├── PackageQueryWorker (Thread) ──callbacks──► db_sync_status
        ├── DownloadWorker (Thread) ──callbacks──► progress_changed, finished, error
        ├── InstallerWorker (Thread) ──callbacks──► status_changed, finished, output_received
        ├── UpdateChecker (Thread) ──callbacks──► update_available, no_update
        ├── DatabaseSyncWorker (Thread) ──callbacks──► sync_finished, sync_failed
        └── AutoUpdateScheduler (Thread) ──callbacks──► update_toast_requested
```

### Configuration Storage

Config is stored at `~/.config/raf/config.json`.
The translations use the new flat-key custom engine, parsing nested keys into objects (e.g., `ui.install_button`).

### Book Database Format

`database/books.json` structure natively supports generic comment nodes to circumvent standard JSON parsing limitations.

```json
{
  "_comment": "Your custom text here",
  "books": [
    {
      "id": "unique-book-id",
      "title": "Book Title",
      "publisher": "Publisher Name",
      "file_name": "package.deb",
      "file_type": "deb",
      "download_url": "https://..."
    }
  ]
}
```

---

## License & Credits

This project is licensed under the **GPL-3.0** license. See [`debian/copyright`](debian/copyright) for the full declaration.

**Developer:** Kaan Ferid Altundaş — kaanferidaltundas@protonmail.com

**Credits:**
- Book shelf icon by Nick Frost and Greg Lapin on [Icon-Icons.com](https://icon-icons.com/authors/237-nick-frost-and-greg-lapin)
