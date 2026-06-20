# Architecture Documentation

Interactive Book Library has a modular, asynchronous architecture designed to optimize smart board performance and user experience.

## 1. Layered Architecture

The application is structured into two main layers:

### A. Business Logic Layer (Core)
- **`database.py`**: Manages the local JSON-based book database (`books.json`), serving search and filter queries.
- **`downloader.py`**: Contains the `QThread`-based `DownloadWorker`. Implements a Google Drive virus warning bypass, HTTP `Range` resumption, and auto-retry network recovery.
- **`installer.py`**: Installs downloaded books according to their package type (`.deb`, `.zip`, `.fernus`). Uses `pkexec` for elevated package operations and auto-generates `.desktop` desktop entry files for non-deb packages.
- **`updater.py`**: Handles self-updater processes. Performs checks against `update_mock.json` in simulation mode and a remote server metadata config in production mode.
- **`config.py`**: Persists user preferences (such as theme configurations) locally.

### B. User Interface Layer (UI)
- **`main_window.py`**: Manages the main window container, view switchers (`Market` and `Kütüphanem` tabs), search/category filters, and options menu.
- **`components.py`**: Houses custom widgets including `PublisherBadge` and single-column list card widgets (`BookCard`).
- **`styles.py`**: Houses the QSS (Qt Style Sheets) light and dark theme configurations mimicking the GTK/Adwaita layout aesthetics.

## 2. Asynchronous Communication & Signal Design

To keep the UI responsive, network and file system IO tasks run in separate threads using Qt's `QThread` and notify the main application thread via Qt's event bus (`Signal`):

```
[Main Window (UI Thread)]  <-- Signals --  [DownloadWorker (QThread)]
         |                                           |
         |-- Start / Cancel ------------------------>|
         |                                           |--> requests.Session (chunked download)
```
- **`progress_changed`**: Reports downloaded chunks percent and speed.
- **`finished`**: Returns target file path on successful download.
- **`error`**: Dispatches details of any exceptions to the main thread.
