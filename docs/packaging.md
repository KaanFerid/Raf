# Packaging & Distribution Documentation

This document covers everything needed to build, verify, and distribute the Raf `.deb` package. The package is designed to be fully Lintian-compliant for Pardus, Debian, and Ubuntu systems.

---

## 1. Package Metadata

Defined in [`debian/control`](../debian/control):

```
Package: raf
Architecture: all
Version: (see debian/changelog)
Section: utils
Priority: optional
Depends: python3, python3-pyside6 | python3-pyqt5, python3-requests, policykit-1
Maintainer: Kaan Ferid Altundaş <kaanferidaltundas@protonmail.com>
Description: Pardus Akilli Tahta Raf Uygulamasi
 Pardus tabanli akilli tahtalarda interaktif kitap raflarinin
 hizlica aranmasi, indirilmesi, kurulmasi ve silinmesini saglar.
```

### Runtime Dependencies

| Package | Why required |
|---|---|
| `python3` | Application runtime |
| `python3-pyside6` or `python3-pyqt5` | Qt GUI framework |
| `python3-requests` | HTTP downloads and Google Drive bypass |
| `policykit-1` | `pkexec` for privilege escalation when installing `.deb` packages |

Optional system capabilities (not hard dependencies):
- `flatpak` — required only for Flatpak book entries
- `snapd` — required only for Snap book entries

---

## 2. Installed File Layout

When installed via `.deb`, Raf places its files at:

```
/usr/lib/raf/                     # Application source
    src/
        main.py
        qt_compat.py
        core/
        ui/
        assets/
/usr/bin/raf                      # Shell launcher script
/usr/share/applications/raf.desktop  # Desktop entry (for app launcher)
/usr/share/raf/database/          # Master database files (fernus_drive.json, publishers.json)
/usr/share/doc/raf/
    copyright                     # GPL-3.0 copyright declaration
    changelog.gz                  # Compressed changelog
/usr/share/icons/hicolor/.../raf.png  # Application icon
```

The `raf` binary in `/usr/bin/` is a simple shell wrapper:
```bash
#!/bin/sh
exec python3 /usr/lib/raf/src/main.py "$@"
```

---

## 3. Building the Package

### Option A: Shell Build Script (Recommended)

Requires: `dpkg-deb`, `md5sum` (standard on Debian/Ubuntu/Pardus)

```bash
./scripts/build_deb.sh
```

**What the script does, step by step:**

1. **Clean** any previous `build/raf-pkg/` staging directory
2. **Create staging tree:**
   ```
   build/raf-pkg/
   ├── DEBIAN/
   │   ├── control
   │   ├── md5sums          ← auto-generated
   │   └── postinst         ← sets executable bits on /usr/bin/raf
   └── usr/
       ├── bin/raf
       ├── lib/raf/src/...
       └── share/doc/raf/copyright
   ```
3. **Copy source files** to `usr/lib/raf/`
4. **Generate `md5sums`:** computes MD5 of every data file (relative paths, no `DEBIAN/`)
5. **Copy copyright:** places `debian/copyright` at `usr/share/doc/raf/copyright` with `0644` permissions
6. **Set permissions:** `0755` for all directories, `0644` for all files, `0755` for `/usr/bin/raf`
7. **Invoke `dpkg-deb`:**
   ```bash
   dpkg-deb --build build/raf-pkg raf_<version>_all.deb
   ```

If `dpkg-deb` is not found, the script automatically falls back to:
```bash
python3 scripts/build_deb.py
```

---

### Option B: Pure-Python Builder

No system packaging tools required. Works on Arch Linux, macOS, Windows.

```bash
python3 scripts/build_deb.py
```

**How it works internally:**

The `.deb` format is an `ar` archive containing three members:
```
debian-binary   → "2.0\n"
control.tar.gz  → DEBIAN/control + DEBIAN/md5sums
data.tar.gz     → usr/ file tree
```

The Python builder:
1. Walks the source tree to collect all files
2. Builds `control.tar.gz` in-memory using `tarfile.open(mode='w:gz', fileobj=BytesIO())`
3. Computes MD5 checksums with `hashlib.md5()` during file reads
4. Builds `data.tar.gz` with correct `TarInfo` metadata (uid/gid=0, mode bits)
5. Writes `ar` archive headers using `struct.pack` per the BSD `ar` format specification:
   ```
   Offset  Size  Field
   0       16    File name (padded with spaces)
   16      12    Modification timestamp
   28      6     Owner ID
   34      6     Group ID
   40      8     File mode (octal)
   48      10    File size in bytes
   58      2     Magic: "`\n"
   60      N     File data (padded to even size)
   ```

Output: `raf_<version>_all.deb` in the project root.

---

## 4. Lintian Compliance

The package is designed to pass `lintian --pedantic` checks:

### MD5 Checksums (`DEBIAN/md5sums`)

All files in the `data.tar.gz` (the installed file tree) must have their MD5 hashes listed:

```
d41d8cd98f00b204e9800998ecf8427e  usr/lib/raf/src/main.py
...
```

Both the shell and Python build scripts compute this automatically.

### Copyright Declaration

Per Debian Policy §12.5, a `copyright` file must exist at `usr/share/doc/<pkg>/copyright`.

The file at `debian/copyright` declares GPL-3.0 and is copied to the correct location during build:
```
usr/share/doc/raf/copyright   (permissions: 0644)
```

### File Permissions

| Path | Mode |
|---|---|
| Directories | `0755` |
| Regular files | `0644` |
| `/usr/bin/raf` | `0755` (executable) |

### Package Architecture

`Architecture: all` is correct because Raf is pure Python with no compiled C extensions.

---

## 5. Verifying a Built Package

```bash
python3 scripts/inspect_deb.py
```

This script extracts and inspects the built `.deb` without installing it. It checks:

- ✅ Package is a valid `ar` archive starting with `!<arch>\n`
- ✅ `debian-binary` reads `2.0`
- ✅ `control.tar.gz` contains `control` and `md5sums`
- ✅ `data.tar.gz` contains `usr/share/doc/raf/copyright`
- ✅ MD5 entries are non-empty
- ✅ Package name and version match expectations

Sample output:
```
=== Raf Package Inspector ===
Package: raf_1.0.3_all.deb  (46,112 bytes)
✓ Valid ar archive
✓ debian-binary: 2.0
Control files: ['control', 'md5sums']
✓ md5sums present (42 entries)
✓ copyright present at usr/share/doc/raf/copyright
All checks passed.
```

---

## 6. Installing the Package

### Direct installation
```bash
sudo apt install ./raf_1.0.3_all.deb
```

### Via dpkg (manual)
```bash
sudo dpkg -i raf_1.0.3_all.deb
sudo apt-get install -f   # resolve any missing dependencies
```

### Uninstalling
```bash
sudo apt remove raf
# or to remove config files too:
sudo apt purge raf
```

---

## 7. Version Management

The version number is defined in:
- `src/core/version.py` — `__version__ = "1.0.3"` (used by the app and CLI)
- `debian/changelog` — Debian changelog entry with version and date

When releasing a new version:
1. Update `src/core/version.py`
2. Add a new entry to `debian/changelog` following the standard format.
3. Commit and push the changes to GitHub. (This will automatically trigger the `Build Debian Package` GitHub Action).
4. Go to the **Actions** tab on GitHub, select the **Publish Release** workflow, and click **Run workflow**. Enter the new version tag (e.g., `v1.0.4`).
5. The Action will automatically build the `.deb`, create an official GitHub Release, and attach the `.deb` asset.

---

## 8. GitHub Releases & Auto-Updater

The auto-updater fetches the latest release metadata directly from the GitHub API:
```
https://api.github.com/repos/KaanFerid/Raf/releases/latest
```

The app parses the GitHub API response:
- **Version:** Extracted from the `tag_name` (e.g., `"v1.0.4"` becomes `"1.0.4"`).
- **Changelog:** Extracted from the `body` of the release notes.
- **Download URL:** The updater automatically scans the release `assets` array to find the `.deb` file and uses its `browser_download_url`.

The app compares this version string numerically (split on `.`) against the local `APP_VERSION`. Any higher version triggers the update notification or auto-install depending on the user's policy. No manual `update.json` maintenance is required!

---

## 9. Standalone Apps, Flatpak & Snap Packaging (Future)

While Raf itself is distributed as a `.deb`, it can **install standalone Apps (AppImage, Fernus, ZIP), Flatpak, and Snap packages** for managed books.

To add a standalone AppImage to the database:
**AppImage entry in `publishers.json`:**
```json
{
  "id": "my-appimage",
  "title": "My AppImage Book",
  "publisher": "Example Publisher",
  "file_name": "myapp.AppImage",
  "file_type": "appimage",
  "download_url": "https://example.com/myapp.AppImage"
}
```

To add a Flatpak or Snap book to the database:

**Flatpak entry in `books.json`:**
```json
{
  "id": "org.gnome.Calculator",
  "title": "GNOME Calculator",
  "publisher": "GNOME",
  "file_name": "gnome-calculator.flatpak",
  "file_type": "flatpak",
  "flatpak_ref": "org.gnome.Calculator",
  "download_url": ""
}
```

**Snap entry in `books.json`:**
```json
{
  "id": "vlc-snap",
  "title": "VLC Media Player",
  "publisher": "VideoLAN",
  "file_name": "vlc.snap",
  "file_type": "snap",
  "snap_name": "vlc",
  "download_url": ""
}
```

> **Note:** For Flatpak/Snap entries, the `download_url` and `file_name` fields are not used — the installer communicates directly with the Flatpak/Snap daemons. Leave them as empty strings.
