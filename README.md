# Interactive Book Library

Interactive book library client with a modern user interface, developed for Pardus-based smart boards (ETAP).

This client allows teachers and students to easily search, download, install, run, and uninstall interactive book libraries on smart boards.

---

## 🚀 Getting Started

The project is designed to run both in the Pardus smart board environment (production) and on personal developer computers (simulation/developer mode).

### 💻 Developer / Simulator Mode (Arch Linux etc.)

You can use the developer runner script to safely try out the application without making any permanent changes to your system, installing global libraries, or adding packages to the OS. If the necessary dependencies (PySide6, requests) are not installed globally, this script creates an isolated virtual environment (`.venv`) inside the project directory and launches the application:

```bash
# To run safely in simulator mode:
./run_arch.py
```

### 🏫 Production Mode (Pardus / Debian Smart Board)

To run the application in authorized mode, where it can install and uninstall actual system packages (`.deb`):

```bash
python3 -m src.main
```

---

## 📦 Debian Package Compilation & Standardization

Interactive Book Library has a package compilation structure fully compliant with Debian and Lintian standards (License/Copyright and MD5 checksum compatibility).

### Compilation Steps

You can compile the Debian package by running the following script in the project directory. When compilation is complete, the package `etkilesimli-kitap-kutuphanesi_1.0.0_all.deb` will be created in the root directory:

```bash
./scripts/build_deb.sh
```

> [!NOTE]
> If the standard packaging tool `dpkg-deb` is not installed on your system, the build script automatically triggers the pure Python-based package compiler (`scripts/build_deb.py`).

### Verifying the Compiled Package

To inspect the structure of the created `.deb` package and ensure the presence of `md5sums` and `copyright` files in compliance with Debian policies:

```bash
# To verify the package structure:
python3 scripts/inspect_deb.py
```

---

## 🛠 Project Structure

The directory structure offers a modular and clean architecture:

- `src/`: Application source code.
  - `src/main.py`: Main application entry point.
  - `src/qt_compat.py`: Automatic compatibility layer between PySide6, PyQt6, and PyQt5.
  - `src/core/`: Background business logic (database, downloader, installer, config, updater).
  - `src/ui/`: Interface designs (Libadwaita / Bottles style modern windows and themes).
  - `src/assets/`: Application graphics, logos, and books database (`books.json`).
- `debian/`: Standard Debian package configuration files (`control`, `rules`, `changelog`, `copyright`).
- `docs/`: Expanded documentation directory containing architecture and packaging details.
- `scripts/`: Scripts for building, packaging, database parsing, and other automation tasks.
- `tests/`: Automated unit/integration tests for UI, updater, and network connectivity.
- `mock_system/`: Local cache directory used to simulate downloads and installations in developer mode.

---

## ℹ️ License

This project is licensed under the **GPL-3.0** license. See the `debian/copyright` file for details.
