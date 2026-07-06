# CLI Reference

[![Türkçe](https://img.shields.io/badge/Dil-T%C3%BCrk%C3%A7e-red?style=flat-square)](cli-tr.md)
Complete reference for the Raf command-line interface. The CLI shares all logic with the GUI — the same installer, downloader, and database modules are used.

---

## Invocation

```bash
# If installed via .deb:
raf <command> [arguments]

# From source (developer mode — no system changes):
./run_arch.py <command> [arguments]

# From source (production mode):
python3 -m src.main <command> [arguments]
```

---

## Global Options

| Flag | Description |
|---|---|
| `--help`, `-h`, `help` | Print command summary and exit |

---

## Commands

---

### `list` — List all available books

**Synopsis:**
```bash
raf list
```

**Description:**
Prints all books in the database as a formatted table. Columns are aligned to fixed widths.

**Output:**
```
Total 42 books available:
ID                                  | Title                                         | Publisher
--------------------------------------------------------------------------------------------------------------
akademikbasariyayinlarikutuphane    | Akademik Başarı Yayınları Kütüphanesi         | Akademik Başarı Yay.
ankarakutuphane                     | Ankara İl Milli Eğitim Kütüphanesi            | Ankara İl MEM
...
```

**Exit code:** `0`

---

### `list-installed` — List installed books

**Synopsis:**
```bash
raf list-installed
```

**Description:**
Queries the system for all installed books and shows only those that are present. Uses `dpkg-query` for `.deb` packages, `flatpak list` for Flatpak, and `snap list` for Snap.

**Output:**
```
Total 3 installed books available:
ID                                  | Title                                         | Type
--------------------------------------------------------------------------------------------------------------
ankarakutuphane                     | Ankara İl Milli Eğitim Kütüphanesi            | deb
```

**Exit code:** `0`

---

### `search <term>` — Search books

**Synopsis:**
```bash
raf search <term>
raf search "multiple words"
```

**Description:**
Searches book titles, publisher names, and descriptions (case-insensitive) and prints matching results.

**Arguments:**
| Argument | Required | Description |
|---|---|---|
| `term` | Yes | The search string. Quote multi-word terms. |

**Example:**
```bash
raf search ankara
# Output:
Search results (2 items):
ID                                  | Title                                         | Publisher
ankarakutuphane                     | Ankara İl Milli Eğitim Kütüphanesi            | Ankara İl MEM
...
```

**Exit code:** `0` (success, including zero results), `1` (missing term argument)

---

### `install <book_id>` — Download and install a book

**Synopsis:**
```bash
raf install <book_id>
```

**Description:**
Downloads the book package and installs it. The `book_id` must exactly match the `id` field in `books.json`. Use `raf list` to find IDs.

**Arguments:**
| Argument | Required | Description |
|---|---|---|
| `book_id` | Yes | The exact book ID from `raf list` |

**Process:**
1. Looks up the book in the database — exits with error if not found
2. Checks if already installed — exits with info message if so
3. Downloads the package file, showing a real-time progress bar:
   ```
   Downloading: [========================================] %100 (2.34 MB/s)
   ```
4. Installs via `pkexec apt-get install -y ./file.deb` (or `flatpak`/`snap` equivalents)
5. Reports success or failure

**Example:**
```bash
raf install akademikbasariyayinlarikutuphane
```

**Exit codes:**
| Code | Meaning |
|---|---|
| `0` | Installed successfully |
| `1` | Book not found / download error / install failed / already installed |

**Notes:**
- Requires `pkexec` and PolicyKit — the OS will ask for admin credentials
- In developer mode (`RAF_DEV=1`), installation is simulated without system changes
- Downloads are cached in `~/.cache/raf/downloads/` (or `mock_system/cache/` in dev mode)
- If a download is interrupted, the next run will attempt to resume from the offset using `Range` headers

---

### `install-local <path>` — Install local file or directory

**Synopsis:**
```bash
raf install-local <file_or_directory_path>
```

**Description:**
Installs local application files (.deb, .appimage, .zip, .fernus) without downloading. If a directory is provided, it attempts to install all supported files in that directory. Unrecognized files are skipped with a warning.

**Arguments:**
| Argument | Required | Description |
|---|---|---|
| `path` | Yes | Absolute or relative path to a file or directory |

**Example:**
```bash
raf install-local ~/Downloads/myapp.deb
raf install-local /media/usb/apps/
```

**Output:**
```
Warning: The following unsupported files were skipped:
- notes.txt
Installing: myapp
 Status: Extracting files...
 Status: Installing system package (authorization may be requested)...
Success: 'myapp' successfully installed.
```

**Exit code:** `0` on success, `1` on error.

---

### `uninstall <book_id>` — Uninstall a book

**Synopsis:**
```bash
raf uninstall <book_id>
```

**Description:**
Removes the specified book from the system. The command checks that the book is actually installed before proceeding.

**Arguments:**
| Argument | Required | Description |
|---|---|---|
| `book_id` | Yes | The exact book ID from `raf list-installed` |

**Example:**
```bash
raf uninstall akademikbasariyayinlarikutuphane
```

**Process:**
1. Looks up the book — exits with error if not in database
2. Checks if installed — exits with info if not installed
3. Removes via `pkexec apt-get remove -y <package>` (for `.deb`)
4. For `.zip`/`.fernus` books: deletes the app directory and `.desktop` launcher
5. Reports result

**Exit codes:**
| Code | Meaning |
|---|---|
| `0` | Uninstalled successfully |
| `1` | Book not found / not installed / uninstall failed |

---

### `clean` — Clear the download cache

**Synopsis:**
```bash
raf clean
```

**Description:**
Deletes all files from `~/.cache/raf/downloads/` (or `mock_system/cache/` in developer mode). Useful to free disk space after installations.

**Output:**
```
Success: Download cache cleared. 5 files deleted.
# or if already empty:
Cache folder is empty or does not exist.
```

**Exit code:** `0`

---

## Environment Variables

| Variable | Values | Effect |
|---|---|---|
| `RAF_DEV` | `1` | Activate developer/simulation mode |

---

## Examples

```bash
# List everything
raf list

# Find all books related to "matematik"
raf search matematik

# Install a specific book
raf install ankarakutuphane

# Check what's installed
raf list-installed

# Remove a book
raf uninstall ankarakutuphane

# Free up download cache space
raf clean

# Run all the above in dev mode (no system changes)
RAF_DEV=1 raf list
RAF_DEV=1 raf install ankarakutuphane
```

---

## Error Messages

| Message | Cause |
|---|---|
| `Error: Book with ID '{id}' not found.` | Typo in book ID — run `raf list` to verify |
| `Error: Search term not specified.` | Ran `raf search` without a term |
| `Error: Book ID to install not specified.` | Ran `raf install` without an ID |
| `Error: Book ID to uninstall not specified.` | Ran `raf uninstall` without an ID |
| `Info: '{title}' is already installed.` | Book is already present on the system |
| `Info: '{title}' is already not installed.` | Tried to uninstall a book that isn't there |
| `Download error: {error}` | Network failure, bad URL, or disk full |
| `Error: Installation cannot proceed because the download failed.` | Install aborted after download failure |

---

## Differences from the GUI

| Behaviour | GUI | CLI |
|---|---|---|
| Download queue | FIFO, max 2 concurrent | Sequential, one at a time |
| Progress | Animated progress bar in card | ASCII text progress bar |
| PolicyKit dialog | Graphical OS dialog | Same graphical OS dialog |
| Language | Configured in Preferences | Follows system locale |
| Theme | Light/dark | N/A |
| Offline detection | Banner in UI | Error message on download attempt |
