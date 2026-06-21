# Raf - Development Summary

This document summarizes all completed stages, added features, architectural structure, and verification methods in the **Raf** project, developed with a modern user interface for Pardus-based smart boards (ETAP).

---

## 👥 Development Team and Rights
* **Developer:** Kaan Ferid Altundaş
* **License:** GPL-3.0 (See the `debian/copyright` file for details)

---

## 🛠️ Completed Development Stages & Features

### 1. File and Git Repository Structure
* The project directory layout has been refactored into a modular, clean, and standard open-source Python project layout:
  * `src/core/`: Business logic, network operations, self-updater, downloader, and installer.
  * `src/ui/`: User interface, Libadwaita theme stylesheets, and custom widgets.
  * `src/assets/`: Book database (`books.json`) and logo/icon assets.
  * `debian/`: Debian packaging and standardization configuration files.
  * `docs/`: Expanded architecture and packaging reference documentation.
  * `scripts/`: Packaging, building, database parsing, and utility scripts.
  * `tests/`: Automated unit and integration testing scripts.

### 2. UI Design & Libadwaita Compatibility
* **Adwaita & Bottles Style Layout:** Modern, clean, flat user interface styled with rounded corners matching modern desktop environments.
* **Theme Engine:** Fully features Light (`LIGHT_STYLE`) and Dark (`DARK_STYLE`) theme palettes.
* **D-Bus Integration:** Monitors system appearance preferences via D-Bus portal (e.g. automatically switches themes when the smart board theme transitions).
* **Preferences Window:** Allows users to manually force Light/Dark modes or keep them synchronized with the system theme.
* **Custom Publisher Badge Design:** Elegant, colored initials badges generated dynamically from the publisher's name, avoiding cluttered icons.

### 3. Search Bar and Symbol Enhancements
* **Dynamically Drawn Search Icon:** To avoid broken Unicode characters on older systems or ETAP boards without modern emoji fonts, a custom magnifying glass icon is rendered directly via `QPainter` onto the search text field.
* **Virtual Keyboard Integration:** Removed the non-functional keyboard button next to search, while preserving touch screen auto-focus events that trigger the system on-screen keyboard.

### 4. Smart Board Integration (Stage 1)
* **Touchscreen Virtual Keyboard Trigger:** Utilizes an `eventFilter` to intercept focus and click events on the search bar in touch environments, automatically bringing up the system OSK (e.g., Onboard or GNOME Caribou).
* **Resumption Downloader:** Robust downloader utilizing HTTP `Range` headers to resume interrupted book package downloads and auto-retry on drops.

### 5. Debian Package Standardization & Self-Updater (Stage 2)
* **Pure-Python Debian Compiler (`build_deb.py`):** Automatically packages the `.deb` archive on developer machines where standard `dpkg` utilities are missing.
* **Lintian Alignment:**
  * Compiles checksum summaries of all packaged files into `md5sums`.
  * Integrates upstream author copyright declarations in `usr/share/doc/raf/copyright` with strict `644` file permissions.
* **Self-Updater (Application self-update):** Periodically runs an asynchronous checker in the background to detect updates, download the packages, and trigger updates via `pkexec apt-get install`.
* **Google Drive Warn Bypass:** Bypasses Google Drive virus warning screens programmatically to guarantee direct download operations.

### 6. Rich Features & Classroom Alignment (Stage 3)
* **Category Filtering:** Filter pill buttons to easily sort books by Primary, Middle, High School, or General categories.
* **Offline Mode Detection:** Displays a bright red `ÇEVRİMDIŞI MOD` warning and disables download actions for uninstalled items when the internet connection goes offline.
* **Disk Space Calculation:** Calculates and displays free space left on the target installation drive inside Preferences.
* **Cache Clean Utility:** Button to purge downloaded cache files.

### 7. Remote Management & CLI Panel (Stage 4)
* The entry point `main.py` parses CLI arguments managed inside `src/core/cli.py`.
* **Available CLI Commands:**
  * `./run_arch.py list` -> Lists all books with categories.
  * `./run_arch.py list-installed` -> Lists installed packages.
  * `./run_arch.py search <term>` -> Searches database for a term.
  * `./run_arch.py install <book_id>` -> Downloads and installs the book.
  * `./run_arch.py uninstall <book_id>` -> Removes the book package.
  * `./run_arch.py clean` -> Purges download cache.

---

## 🚀 Execution and Testing Methods

### 1. Run in Developer Mode (Simulation)
To test the app in a sandbox environment without installing packages system-wide or requiring root elevation:
```bash
./run_arch.py
```

### 2. Run in Production Mode (Pardus / Debian)
```bash
python3 -m src.main
```

### 3. Build Debian Package (.deb)
```bash
./scripts/build_deb.sh
```

### 4. Run Automated Test Suite
* **UI Features & Filter Tests:**
  ```bash
  python3 tests/test_ui_features.py
  ```
* **Self-Updater Flow Tests:**
  ```bash
  python3 tests/test_updater.py
  ```
* **Google Drive Network Tests:**
  ```bash
  python3 tests/test_drive.py
  ```
* **Debian Package Validation Check:**
  ```bash
  python3 scripts/inspect_deb.py
  ```

---

*This application is fully aligned with smart board hardware, focusing on high stability and performance.*
