# Contributing & Developer Guide

This guide explains how to set up a development environment, understand the codebase, add new features, and submit changes.

---

## 1. Setting Up the Development Environment

### Prerequisites

- Python 3.9 or later
- Git

### Clone and Run

```bash
git clone https://github.com/KaanFerid/Raf.git
cd raf
./run_arch.py
```

`run_arch.py` automatically:
1. Detects whether `PySide6` and `requests` are available
2. If not, creates an isolated `.venv` in the project directory
3. Installs `PySide6` and `requests` into `.venv`
4. Launches the app in simulation/developer mode

> **The script never modifies system packages.** All dependencies are contained in `.venv`.

### Manual Setup (with pip)

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
RAF_DEV=1 python3 -m src.main
```

---

## 2. Developer Mode (`RAF_DEV=1`)

Setting `RAF_DEV=1` activates the simulation sandbox. Every system-level operation is safely mocked:

| Real operation | Simulated as |
|---|---|
| `pkexec apt-get install` | 1.5s delay → writes to `mock_system/installed.json` |
| `pkexec apt-get remove` | 1s delay → removes from `mock_system/installed.json` |
| `flatpak install` | 1.5s simulated |
| `snap install` | 1.5s simulated |
| Downloads | Real HTTP download to `mock_system/cache/` |
| Update check | Reads `mock_system/update_mock.json` |
| Config | Reads/writes `mock_system/config.json` |

### Mock Files

| File | Purpose | Example content |
|---|---|---|
| `mock_system/installed.json` | Tracks which books are "installed" | `{"book_id_1": true}` |
| `mock_system/update_mock.json` | Triggers a simulated update | `{"version": "99.0", "download_url": "...", "changelog": "..."}` |
| `mock_system/config.json` | App config in dev mode | Same schema as production config |

---

## 3. Project Layout Summary

```
src/
├── core/         Business logic (no Qt widgets)
├── ui/           Qt widgets only
├── assets/       Static resources (JSON, images, locale strings)
└── qt_compat.py  Qt backend abstraction
```

**Rule:** Core modules must never import from `src/ui/`. UI modules may import from `src/core/`.

---

## 4. Adding a New Book to the Database

Edit the files inside the `database/` directory. 
- Use `database/fernus_drive.json` for books hosted on Google Drive.
- Use `database/publishers.json` for direct HTTP download links from publishers.

Each entry is a JSON object inside the main array:

### Minimum required fields

```json
{
  "id": "unique-kebab-case-id",
  "title": "Display Title",
  "publisher": "Publisher Name",
  "file_name": "package_filename.deb",
  "file_type": "deb",
  "download_url": "https://example.com/package.deb"
}
```

### Optional fields

| Field | Type | Used for |
|---|---|---|
| `description` | string | Shown in search; searched against |
| `flatpak_ref` | string | Required when `file_type == "flatpak"` |
| `snap_name` | string | Required when `file_type == "snap"` |

### Supported `file_type` values

| Value | Installer | Detection |
|---|---|---|
| `deb` | `pkexec apt-get install` | `dpkg-query` |
| `zip` | Extract to `~/.local/share/raf/apps/` | Directory exists check |
| `fernus` | Same as `zip` | Same |
| `flatpak` | `flatpak install --user` | `flatpak list --app` |
| `snap` | `pkexec snap install` | `snap list` |

---

## 5. Adding Locale Strings

All user-visible strings must go through the `tr()` translation function. Hard-coded strings in Python files are not acceptable.

### Step 1 — Add to both locale files

`src/assets/locales/en.json`:
```json
{
  "ui": {
    "my_new_key": "My English text with {placeholder}."
  }
}
```

`src/assets/locales/tr.json`:
```json
{
  "ui": {
    "my_new_key": "Türkçe metin {placeholder} ile."
  }
}
```

### Step 2 — Use in code

```python
from src.core.translation import tr

label.setText(tr("ui.my_new_key", placeholder="value"))
```

### Key naming convention

| Prefix | Section |
|---|---|
| `ui.*` | Main window, dialogs, card labels |
| `installer.*` | Package installer status messages |
| `downloader.*` | Download worker messages |
| `updater.*` | Self-updater messages |
| `cli.*` | CLI panel text |

---

## 6. Adding a New Core Worker

Workers that do background I/O (network, filesystem) must:

1. Extend `QThread`
2. Emit all results via signals (no direct UI calls from background threads)
3. Accept cancellation via a `self._cancelled` flag

Template:

```python
from src.qt_compat import QThread, Signal

class MyWorker(QThread):
    result_ready = Signal(str)   # emit data back to the UI
    error = Signal(str)          # emit errors

    def __init__(self, param, parent=None):
        super().__init__(parent)
        self._cancelled = False
        self.param = param

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            for chunk in some_operation(self.param):
                if self._cancelled:
                    return
                # process chunk ...
            self.result_ready.emit("Done")
        except Exception as e:
            self.error.emit(str(e))
```

In `MainWindow`:
```python
self.worker = MyWorker("input", parent=self)
self.worker.result_ready.connect(self.on_result)
self.worker.error.connect(self.on_error)
self.worker.start()
```

Always call `worker.deleteLater()` in the finished slot to avoid memory leaks.

---

## 7. Theming New Widgets

All new widgets must be styleable via `objectName` or `property("class")`:

```python
# Object name targeting (specific widget):
my_label = QLabel("text")
my_label.setObjectName("MySpecialLabel")

# Class targeting (reusable button type):
my_btn = QPushButton("Click")
my_btn.setProperty("class", "AdwPrimaryBtn")
```

Then in `src/ui/styles.py`, add to both `LIGHT_STYLE` and `DARK_STYLE`:

```css
/* Light version */
#MySpecialLabel {
    color: #1c1c1e;
    font-weight: 600;
}

/* Dark version */
/* (in DARK_STYLE) */
#MySpecialLabel {
    color: #f0f0f0;
    font-weight: 600;
}
```

After changing a property at runtime, force Qt to reapply styles:
```python
widget.style().unpolish(widget)
widget.style().polish(widget)
```

---

## 8. Toast Notifications

Show a toast anywhere you have access to `MainWindow`:

```python
# From MainWindow or any slot connected to it:
self.toast_manager.show_toast(
    message=tr("ui.my_toast_key"),
    toast_type="success",    # "info", "success", "warning", "error"
    duration=3500            # ms before auto-dismiss
)
```

Toasts are non-blocking and do not interrupt user interaction.

---

## 9. Running the Test Suite

```bash
# All tests from project root:
python3 tests/test_ui_features.py
python3 tests/test_updater.py
python3 tests/test_drive.py
```

Tests use `RAF_DEV=1` implicitly. UI tests use the `offscreen` Qt platform (no display needed).

### Writing a New Test

```python
import os, sys
os.environ["RAF_DEV"] = "1"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.qt_compat import QApplication
app = QApplication.instance() or QApplication(sys.argv)

# ... test assertions ...

print("All tests passed.")
```

---

## 10. Commit Guidelines

- Use **present-tense, imperative** commit messages:  
  ✅ `Add toast notification for install error`  
  ❌ `Added toast notification`

- Prefix with a tag:  
  `feat:` new feature  
  `fix:` bug fix  
  `style:` CSS/QSS only changes  
  `refactor:` code restructure without behavior change  
  `docs:` documentation only  
  `test:` test additions  
  `build:` packaging/build scripts  

- Keep commits focused — one logical change per commit.

---

## 11. Release Checklist

Before tagging a new release:

- [ ] Update `src/core/version.py` with the new version string
- [ ] Add entry to `debian/changelog` with correct date and maintainer
- [ ] Run all tests — `python3 tests/test_ui_features.py`, `test_updater.py`, `test_drive.py`
- [ ] Build and inspect the `.deb`: `./scripts/build_deb.sh && python3 scripts/inspect_deb.py`
- [ ] Update `update.json` on GitHub with new version + download URL
- [ ] Create a GitHub release and attach the `.deb`
- [ ] Test installation on a clean Pardus VM: `sudo apt install ./raf_<version>_all.deb`
