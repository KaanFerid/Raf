import os
import subprocess
import shutil
import zipfile
import json
import re
import time
import threading
from gi.repository import GLib
from src.core.config import get_cached_package_name, set_cached_package_name
from src.core.translation import tr

MOCK_DB_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "mock_system",
        "installed.json",
    )
)


def load_mock_installed():
    if not os.path.exists(MOCK_DB_PATH):
        os.makedirs(os.path.dirname(MOCK_DB_PATH), exist_ok=True)
        with open(MOCK_DB_PATH, "w", encoding="utf-8") as f:
            json.dump([], f)
        return set()
    try:
        with open(MOCK_DB_PATH, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_mock_installed(installed_set):
    os.makedirs(os.path.dirname(MOCK_DB_PATH), exist_ok=True)
    with open(MOCK_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(list(installed_set), f, indent=2)


class InstallerWorker(threading.Thread):
    def __init__(self, book, file_path, action="install", sudo_password=None):
        super().__init__()
        self.daemon = True
        self.book = book
        self.book_id = book["id"]
        self.file_path = file_path
        self.action = action  # "install" or "uninstall"
        self.sudo_password = sudo_password

        # Callbacks
        self.on_status_changed = None  # func(book_id, status_message)
        self.on_finished = None  # func(book_id, success)
        self.on_output_received = None  # func(book_id, console_output)
        self.on_auth_failed = None  # func(book_id)

    def _emit_status(self, book_id, msg):
        if self.on_status_changed:
            GLib.idle_add(self.on_status_changed, book_id, msg)

    def _emit_finished(self, book_id, success):
        if self.on_finished:
            GLib.idle_add(self.on_finished, book_id, success)

    def _emit_output(self, book_id, output):
        if self.on_output_received:
            GLib.idle_add(self.on_output_received, book_id, output)

    def _emit_auth_failed(self, book_id):
        if self.on_auth_failed:
            GLib.idle_add(self.on_auth_failed, book_id)

    def _execute_elevated(self, cmd):
        if cmd[0] == "pkexec":
            cmd = cmd[1:]

        if self.sudo_password:
            full_cmd = ["sudo", "-S"] + cmd
            process = subprocess.Popen(
                full_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
            try:
                process.stdin.write(self.sudo_password + "\n")
                process.stdin.flush()
                process.stdin.close()
            except:
                pass
            return process
        else:
            full_cmd = ["pkexec"] + cmd
            return subprocess.Popen(
                full_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

    def _run_subprocess(self, cmd, start_log_msg, success_status_msg, success_log_msg):
        self._emit_output(self.book_id, start_log_msg)
        self._emit_output(
            self.book_id,
            tr(
                "log.executing_cmd",
                cmd=" ".join(cmd),
                default=f"Executing: {' '.join(cmd)}",
            ),
        )

        try:
            process = self._execute_elevated(cmd)
            for line in process.stdout:
                self._emit_output(self.book_id, line)
            process.wait()

            if process.returncode == 0:
                if getattr(self, "action", "") == "uninstall":
                    local_desktop_file = os.path.expanduser(
                        f"~/.local/share/applications/raf-{self.book_id}.desktop"
                    )
                    if os.path.exists(local_desktop_file):
                        try:
                            os.remove(local_desktop_file)
                        except Exception:
                            pass
                self._emit_output(self.book_id, success_log_msg)
                self._emit_status(self.book_id, success_status_msg)
                self._emit_finished(self.book_id, True)
            elif process.returncode in (126, 127):
                self._emit_status(self.book_id, tr("installer.auth_failed"))
                self._emit_auth_failed(self.book_id)
                self._emit_finished(self.book_id, False)
            else:
                fail_key = (
                    "installer.install_failed"
                    if self.action == "install"
                    else "installer.uninstall_failed"
                )
                self._emit_status(self.book_id, tr(fail_key, code=process.returncode))
                self._emit_finished(self.book_id, False)
        except Exception as e:
            self._emit_output(self.book_id, str(e))
            self._emit_status(self.book_id, tr("ui.error") + f": {str(e)}")
            self._emit_finished(self.book_id, False)

    INSTALL_LOCK = threading.Lock()

    def run(self):
        with self.INSTALL_LOCK:
            if os.environ.get("RAF_DEV") == "1":
                self.run_mock()
                return

            if self.action == "install":
                self.install()
            elif self.action == "uninstall":
                self.uninstall()

    def run_mock(self):
        if self.action == "install":
            self._emit_status(tr("installer.sim_installing", title=self.book["title"]))
            time.sleep(1.5)  # Wait 1.5 seconds (simulate)
            installed = load_mock_installed()
            installed.add(self.book_id)
            save_mock_installed(installed)
            self._emit_status(tr("installer.sim_install_completed"))
            self._emit_finished(True)
        elif self.action == "uninstall":
            self._emit_status(
                tr("installer.sim_uninstalling", title=self.book["title"])
            )
            time.sleep(1.0)  # Wait 1 second (simulate)
            installed = load_mock_installed()
            if self.book_id in installed:
                installed.remove(self.book_id)
            save_mock_installed(installed)
            self._emit_status(tr("installer.sim_uninstall_completed"))
            self._emit_finished(True)

    def install(self):
        file_type = self.book.get("file_type", "deb")

        if file_type == "deb":
            self.install_deb()
        elif file_type == "zip":
            self.install_zip()
        elif file_type in ["appimage", "fernus"]:
            self.install_standalone()
        elif file_type == "flatpak":
            self.install_flatpak()
        elif file_type == "snap":
            self.install_snap()
        else:
            self._emit_status(self.book_id, tr("installer.unsupported_file_type"))
            self._emit_finished(self.book_id, False)

    def uninstall(self):
        file_type = self.book.get("file_type", "deb")

        if file_type == "deb":
            self.uninstall_deb()
        elif file_type == "zip":
            self.uninstall_zip()
        elif file_type in ["appimage", "fernus"]:
            self.uninstall_standalone()
        elif file_type == "flatpak":
            self.uninstall_flatpak()
        elif file_type == "snap":
            self.uninstall_snap()
        else:
            self._emit_status(self.book_id, tr("installer.unsupported_file_type"))
            self._emit_finished(self.book_id, False)

    def install_deb(self):
        self._emit_status(self.book_id, tr("installer.querying_package_info"))

        # Extract the exact package name from the downloaded .deb file
        try:
            res = subprocess.run(
                ["dpkg-deb", "-f", self.file_path, "Package"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5,
            )
            if res.returncode == 0:
                package_name = res.stdout.strip()
                if package_name:
                    set_cached_package_name(self.book_id, package_name)
                    print(tr("log.resolved_pkg", id=self.book_id, pkg=package_name))
        except Exception as e:
            print(tr("log.error_reading_pkg", id=self.book_id, error=e))

        self._emit_status(self.book_id, tr("installer.installing_system_package"))

        # We will use pkexec apt-get install -y ./file.deb
        # This will pop up a PolicyKit password prompt for security.
        cmd = ["pkexec", "apt-get", "install", "-y", self.file_path]

        self._run_subprocess(
            cmd,
            start_log_msg=tr(
                "log.start_deb_install",
                title=self.book.get("title"),
                default=f"--- Starting DEB installation of {self.book.get('title')} ---",
            ),
            success_status_msg=tr("installer.install_completed"),
            success_log_msg=tr(
                "log.install_completed",
                default="--- Installation completed successfully ---",
            ),
        )

    def uninstall_deb(self):
        self._emit_status(self.book_id, tr("installer.uninstalling_system_package"))
        package_name = get_deb_package_name(self.book)

        if not package_name:
            self._emit_status(self.book_id, tr("installer.package_name_not_found"))
            self._emit_finished(self.book_id, False)
            return

        cmd = ["pkexec", "apt-get", "remove", "-y", package_name]

        self._run_subprocess(
            cmd,
            start_log_msg=tr(
                "log.start_deb_uninstall",
                title=self.book.get("title"),
                default=f"--- Starting DEB uninstallation of {self.book.get('title')} ---",
            ),
            success_status_msg=tr("installer.uninstall_completed"),
            success_log_msg=tr(
                "log.uninstall_completed",
                default="--- Uninstallation completed successfully ---",
            ),
        )

    def install_zip(self):
        self._emit_status(self.book_id, tr("installer.extracting_files"))

        import tempfile

        tmp_dir = tempfile.mkdtemp(prefix=f"raf_{self.book_id}_")

        try:
            with zipfile.ZipFile(self.file_path, "r") as zip_ref:
                # Get total number of files for progress simulation
                file_list = zip_ref.namelist()
                total_files = len(file_list)

                for i, file in enumerate(file_list):
                    zip_ref.extract(file, tmp_dir)
                    if i % max(1, total_files // 10) == 0:
                        percent = int((i / total_files) * 100)
                        self._emit_status(
                            self.book_id,
                            tr("installer.extracting_percent", percent=percent),
                        )

            # Make sure all files are executable if they are scripts/binaries
            for root, dirs, files in os.walk(tmp_dir):
                for f in files:
                    fpath = os.path.join(root, f)
                    if (
                        f.endswith(".sh") or "." not in f
                    ):  # executable scripts or binaries
                        try:
                            os.chmod(fpath, 0o755)
                        except Exception:
                            pass

            self._emit_status(self.book_id, tr("installer.creating_desktop_launcher"))
            tmp_desktop_path = create_desktop_launcher(self.book, tmp_dir)

            self._emit_status(self.book_id, tr("installer.installing_system_package"))
            self._emit_output(
                self.book_id,
                tr(
                    "log.start_zip_install",
                    title=self.book.get("title"),
                    default=f"--- Starting ZIP installation of {self.book.get('title')} ---",
                ),
            )

            script = """
            set -ex
            rm -rfv "$1"
            mkdir -pv "$1"
            cp -rv "$2/"* "$1/"
            cp -v "$3" "$4"
            chmod -v 644 "$4"
            rm -rfv "$2"
            rm -fv "$3"
            """

            cmd = [
                "pkexec",
                "bash",
                "-c",
                script,
                "_",
                f"/opt/raf/apps/{self.book_id}",
                tmp_dir,
                tmp_desktop_path,
                f"/usr/share/applications/raf-{self.book_id}.desktop",
            ]
            self._run_subprocess(
                cmd,
                start_log_msg=tr(
                    "log.start_zip_install",
                    title=self.book.get("title"),
                    default=f"--- Starting ZIP/AppImage installation of {self.book.get('title')} ---",
                ),
                success_status_msg=tr("installer.install_completed"),
                success_log_msg=tr(
                    "log.install_completed",
                    default="--- Installation completed successfully ---",
                ),
            )

        except Exception as e:
            self._emit_output(self.book_id, str(e))
            self._emit_status(self.book_id, tr("ui.error") + f": {str(e)}")
            self._emit_finished(self.book_id, False)
        finally:
            try:
                shutil.rmtree(tmp_dir)
            except:
                pass

    def uninstall_zip(self):
        self._emit_status(self.book_id, tr("installer.deleting_files"))

        apps_dir = f"/opt/raf/apps/{self.book_id}"
        desktop_file = f"/usr/share/applications/raf-{self.book_id}.desktop"

        try:
            self._emit_output(
                self.book_id,
                tr(
                    "log.start_zip_uninstall",
                    title=self.book.get("title"),
                    default=f"--- Starting ZIP uninstallation of {self.book.get('title')} ---",
                ),
            )
            script = """
            set -ex
            rm -rfv "$1"
            rm -fv "$2"
            """

            cmd = ["pkexec", "bash", "-c", script, "_", apps_dir, desktop_file]
            self._run_subprocess(
                cmd,
                start_log_msg=tr(
                    "log.start_zip_uninstall",
                    title=self.book.get("title"),
                    default=f"--- Starting ZIP/AppImage uninstallation of {self.book.get('title')} ---",
                ),
                success_status_msg=tr("installer.library_uninstalled"),
                success_log_msg=tr(
                    "log.uninstall_completed",
                    default="--- Uninstallation completed successfully ---",
                ),
            )
        except Exception as e:
            self._emit_output(self.book_id, str(e))
            self._emit_status(self.book_id, tr("ui.error") + f": {str(e)}")
            self._emit_finished(self.book_id, False)

    def install_standalone(self):
        self._emit_status(self.book_id, tr("installer.extracting_files"))

        import tempfile

        tmp_dir = tempfile.mkdtemp(prefix=f"raf_{self.book_id}_")

        try:
            # Copy the file to temp dir
            file_name = os.path.basename(self.file_path)
            tmp_file_path = os.path.join(tmp_dir, file_name)
            shutil.copy2(self.file_path, tmp_file_path)
            os.chmod(tmp_file_path, 0o755)

            self._emit_status(self.book_id, tr("installer.creating_desktop_launcher"))
            tmp_desktop_path = create_desktop_launcher(
                self.book, tmp_dir, is_standalone=True, exec_name=file_name
            )

            self._emit_status(self.book_id, tr("installer.installing_system_package"))

            self._emit_output(
                self.book_id,
                tr(
                    "log.start_standalone_install",
                    title=self.book.get("title"),
                    default=f"--- Starting AppImage/Standalone installation of {self.book.get('title')} ---",
                ),
            )
            script = """
            set -ex
            rm -rfv "$1"
            mkdir -pv "$1"
            cp -v "$2" "$1/$3"
            cp -v "$4" "$5"
            chmod -v 644 "$5"
            rm -rfv "$6"
            rm -fv "$4"
            """

            cmd = [
                "pkexec",
                "bash",
                "-c",
                script,
                "_",
                f"/opt/raf/apps/{self.book_id}",
                tmp_file_path,
                file_name,
                tmp_desktop_path,
                f"/usr/share/applications/raf-{self.book_id}.desktop",
                tmp_dir,
            ]
            self._run_subprocess(
                cmd,
                start_log_msg=tr(
                    "log.start_standalone_install",
                    title=self.book.get("title"),
                    default=f"--- Starting AppImage/Standalone installation of {self.book.get('title')} ---",
                ),
                success_status_msg=tr("installer.install_completed"),
                success_log_msg=tr(
                    "log.install_completed",
                    default="--- Installation completed successfully ---",
                ),
            )

        except Exception as e:
            self._emit_output(self.book_id, str(e))
            self._emit_status(self.book_id, tr("ui.error") + f": {str(e)}")
            self._emit_finished(self.book_id, False)
            try:
                shutil.rmtree(tmp_dir)
            except:
                pass

    def uninstall_standalone(self):
        # Same logic as uninstall_zip since they share the same directory structure
        self.uninstall_zip()

    def install_flatpak(self):
        """Installs a Flatpak application for the current user."""
        # Check flatpak is available
        if not shutil.which("flatpak"):
            self._emit_status(self.book_id, tr("installer.flatpak_not_available"))
            self._emit_finished(self.book_id, False)
            return

        flatpak_ref = self.book.get("flatpak_ref", "")
        if not flatpak_ref:
            self._emit_status(self.book_id, tr("installer.package_name_not_found"))
            self._emit_finished(self.book_id, False)
            return

        cmd = ["flatpak", "install", "--user", "--noninteractive", flatpak_ref]
        self._run_subprocess(
            cmd,
            start_log_msg=tr(
                "log.start_flatpak_install",
                title=self.book.get("title"),
                default=f"--- Starting Flatpak installation of {self.book.get('title')} ---",
            ),
            success_status_msg=tr("installer.install_completed"),
            success_log_msg=tr(
                "log.install_completed",
                default="--- Installation completed successfully ---",
            ),
        )

    def uninstall_flatpak(self):
        """Removes a Flatpak application for the current user."""
        if not shutil.which("flatpak"):
            self._emit_status(self.book_id, tr("installer.flatpak_not_available"))
            self._emit_finished(self.book_id, False)
            return

        flatpak_ref = self.book.get("flatpak_ref", "")
        if not flatpak_ref:
            self._emit_status(self.book_id, tr("installer.package_name_not_found"))
            self._emit_finished(self.book_id, False)
            return

        cmd = ["flatpak", "uninstall", "--user", "--noninteractive", flatpak_ref]
        self._run_subprocess(
            cmd,
            start_log_msg=tr(
                "log.start_flatpak_uninstall",
                title=self.book.get("title"),
                default=f"--- Starting Flatpak uninstallation of {self.book.get('title')} ---",
            ),
            success_status_msg=tr("installer.uninstall_completed"),
            success_log_msg=tr(
                "log.uninstall_completed",
                default="--- Uninstallation completed successfully ---",
            ),
        )

    def install_snap(self):
        """Installs a Snap package (requires elevated privileges via pkexec)."""
        if not shutil.which("snap"):
            self._emit_status(self.book_id, tr("installer.snap_not_available"))
            self._emit_finished(self.book_id, False)
            return

        snap_name = self.book.get("snap_name", "")
        if not snap_name:
            self._emit_status(self.book_id, tr("installer.package_name_not_found"))
            self._emit_finished(self.book_id, False)
            return

        cmd = ["pkexec", "snap", "install", snap_name]
        self._run_subprocess(
            cmd,
            start_log_msg=tr(
                "log.start_snap_install",
                title=self.book.get("title"),
                default=f"--- Starting Snap installation of {self.book.get('title')} ---",
            ),
            success_status_msg=tr("installer.install_completed"),
            success_log_msg=tr(
                "log.install_completed",
                default="--- Installation completed successfully ---",
            ),
        )

    def uninstall_snap(self):
        """Removes a Snap package (requires elevated privileges via pkexec)."""
        if not shutil.which("snap"):
            self._emit_status(self.book_id, tr("installer.snap_not_available"))
            self._emit_finished(self.book_id, False)
            return

        snap_name = self.book.get("snap_name", "")
        if not snap_name:
            self._emit_status(self.book_id, tr("installer.package_name_not_found"))
            self._emit_finished(self.book_id, False)
            return

        cmd = ["pkexec", "snap", "remove", snap_name]
        self._run_subprocess(
            cmd,
            start_log_msg=tr(
                "log.start_snap_uninstall",
                title=self.book.get("title"),
                default=f"--- Starting Snap uninstallation of {self.book.get('title')} ---",
            ),
            success_status_msg=tr("installer.uninstall_completed"),
            success_log_msg=tr(
                "log.uninstall_completed",
                default="--- Uninstallation completed successfully ---",
            ),
        )


def get_all_installed_packages():
    """Queries all installed debian packages on the system in a single subprocess run."""
    if os.environ.get("RAF_DEV") == "1":
        return load_mock_installed()
    installed = set()
    try:
        res = subprocess.run(
            ["dpkg-query", "-W", "-f=${Package} ${Status}\n"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if res.returncode == 0:
            for line in res.stdout.splitlines():
                parts = line.strip().split()
                if len(parts) >= 4 and "installed" in parts[3]:
                    pkg_name = parts[0].split(":")[0]
                    installed.add(pkg_name)
    except Exception as e:
        print(tr("log.error_query_installed", error=e))
    return installed


def get_all_installed_flatpaks():
    """Returns a set of installed Flatpak application IDs."""
    installed = set()
    try:
        res = subprocess.run(
            ["flatpak", "list", "--app", "--columns=application"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if res.returncode == 0:
            for line in res.stdout.splitlines():
                app_id = line.strip()
                if app_id:
                    installed.add(app_id)
    except Exception as e:
        print(tr("log.error_query_flatpak", error=e))
    return installed


def get_all_installed_snaps():
    """Returns a set of installed Snap package names."""
    installed = set()
    try:
        res = subprocess.run(
            ["snap", "list"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        if res.returncode == 0:
            lines = res.stdout.splitlines()
            for line in lines[1:]:  # skip header row
                parts = line.strip().split()
                if parts:
                    installed.add(parts[0])
    except Exception as e:
        print(tr("log.error_query_snap", error=e))
    return installed


def turkish_to_ascii(text):
    """Normalizes Turkish characters to their standard ASCII lowercase equivalents."""
    text = text.lower()
    mapping = {
        "\u0131": "i",
        "i\u0307": "i",
        "\u0130": "i",
        "I\u0307": "i",
        "\u011f": "g",
        "\u00fc": "u",
        "\u015f": "s",
        "\u00f6": "o",
        "\u00e7": "c",
    }
    for k, v in mapping.items():
        text = text.replace(k, v)
    return text


def generate_package_guesses(book):
    """
    Generates a list of likely Debian package names based on the book's file name.

    Because upstream digital library `.deb` files often deviate from the exact download
    filename (e.g. by dropping suffixes, removing publisher keywords, or appending
    '-kutuphane'), this function employs heuristics to guess the actual installed
    package name as reported by `dpkg`.

    Examples:
        - "UcDortBesDijitalKutuphane.deb" -> ["ucdortbesdijitalkutuphane", "ucdortbesdijital-kutuphane", ...]
        - "ToprakYayinlari.fernus" -> ["toprakyayinlari", "toprak", "toprak-kutuphane", ...]

    Process:
        1. Strips extensions (.deb, .fernus, .zip) and version strings (-v2-23).
        2. Normalizes Turkish characters to ASCII.
        3. Generates a 'shortened' base name by stripping publisher keywords ('yayinlari').
        4. Appends standard permutations of library suffixes ('-kutuphane', 'kutuphanesi').
    """
    file_name = book["file_name"]
    base_name = file_name
    if base_name.endswith(".deb"):
        base_name = base_name[:-4]
    elif base_name.endswith(".fernus"):
        base_name = base_name[:-7]
    elif base_name.endswith(".zip"):
        base_name = base_name[:-4]

    # Remove version suffixes if present (e.g. -v2-23)
    base_name = re.sub(r"-v\d+.*$", "", base_name)
    base_name = re.sub(r"_\d+.*$", "", base_name)

    # Convert Turkish characters to ASCII
    base_clean = turkish_to_ascii(base_name)

    # List of keywords to strip out for shorter names
    keywords_to_remove = [
        "yayinlari",
        "yayincilik",
        "yayiningurubu",
        "yayingurubu",
        "yayin",
        "dagitim",
        "perakende",
        "gurubu",
        "grubu",
    ]

    # Generate variations
    bases = [base_clean]

    # Also generate base with keywords removed
    short_base = base_clean
    for kw in keywords_to_remove:
        short_base = short_base.replace(kw, "")
    if short_base != base_clean and short_base != "kutuphane" and len(short_base) > 3:
        bases.append(short_base)

    # For each base, generate suffix variations
    guesses = []
    for b in bases:
        guesses.append(b)
        guesses.append(b.replace("kutuphane", "-kutuphane"))
        guesses.append(b.replace("kutuphanesi", "-kutuphanesi"))

        # If b doesn't end with kutuphane, add it
        if not b.endswith("kutuphane") and not b.endswith("kutuphanesi"):
            guesses.append(b + "kutuphane")
            guesses.append(b + "-kutuphane")
            guesses.append(b + "kutuphanesi")
            guesses.append(b + "-kutuphanesi")

    # Clean all guesses to alphanumeric and dashes/plus/dots only
    cleaned_guesses = []
    for g in guesses:
        clean = "".join([c if c.isalnum() or c in ["-", "+", "."] else "" for c in g])
        clean = clean.strip("-")
        if clean and clean not in cleaned_guesses:
            cleaned_guesses.append(clean)

    return cleaned_guesses


def get_deb_package_name(book):
    """
    Retrieves or queries the underlying Debian package name of the book.

    This is necessary because the app needs to track installed `.deb` packages using
    `dpkg-query`, but the remote API often provides filenames that do not exactly match
    the internal Debian package name defined in the `.deb` control file.

    Process:
        1. Checks if the package name has already been resolved and cached (O(1)).
        2. If not, generates heuristic guesses via `generate_package_guesses(book)`.
        3. Queries the system (`dpkg-query`) for each guess.
        4. Caches and returns the first successful match. Returns None if no matches found.
    """
    # 1. Try config cache first
    cached_name = get_cached_package_name(book["id"])
    if cached_name:
        return cached_name

    # 2. Fall back to smart guesses
    cleaned_guesses = generate_package_guesses(book)

    # Check if any is installed via dpkg-query
    for pkg in cleaned_guesses:
        try:
            res = subprocess.run(
                ["dpkg-query", "-W", "-f=${Status}", pkg],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if "install ok installed" in res.stdout:
                # Cache it now for subsequent calls
                set_cached_package_name(book["id"], pkg)
                return pkg
        except Exception:
            pass

    # Default fallback
    return cleaned_guesses[0]


def is_book_installed(book, installed_set=None):
    """Checks if a book/app is currently installed on the system."""
    if os.environ.get("RAF_DEV") == "1":
        m_set = installed_set if installed_set is not None else load_mock_installed()
        return book["id"] in m_set

    file_type = book.get("file_type", "deb")

    if file_type == "deb":
        # 1. Check cached package name first
        cached_name = get_cached_package_name(book["id"])
        if cached_name:
            if installed_set is not None:
                return cached_name in installed_set
            try:
                res = subprocess.run(
                    ["dpkg-query", "-W", "-f=${Status}", cached_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                return "install ok installed" in res.stdout
            except Exception:
                return False

        # 2. Set-lookup path with smart guesses
        cleaned_guesses = generate_package_guesses(book)
        if installed_set is not None:
            for g in cleaned_guesses:
                if g in installed_set:
                    set_cached_package_name(book["id"], g)
                    return True
            return False

        # 3. Standard query path with smart guesses
        for pkg in cleaned_guesses:
            try:
                res = subprocess.run(
                    ["dpkg-query", "-W", "-f=${Status}", pkg],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                if "install ok installed" in res.stdout:
                    set_cached_package_name(book["id"], pkg)
                    return True
            except Exception:
                pass
        return False

    elif file_type in ["zip", "fernus", "appimage"]:
        apps_dir = f"/opt/raf/apps/{book['id']}"
        desktop_file = f"/usr/share/applications/raf-{book['id']}.desktop"
        return os.path.exists(apps_dir) and os.path.exists(desktop_file)

    elif file_type == "flatpak":
        flatpak_ref = book.get("flatpak_ref", "")
        if not flatpak_ref:
            return False
        app_id = flatpak_ref.split("/")[0] if "/" in flatpak_ref else flatpak_ref
        installed_flatpaks = get_all_installed_flatpaks()
        return app_id in installed_flatpaks

    elif file_type == "snap":
        snap_name = book.get("snap_name", "")
        if not snap_name:
            return False
        installed_snaps = get_all_installed_snaps()
        return snap_name in installed_snaps

    return False


def create_desktop_launcher(book, apps_dir, is_standalone=False, exec_name=""):
    """Detects the executable and creates a desktop entry launcher in applications menu."""
    import tempfile

    # Target directory after pkexec copy will be:
    target_apps_dir = f"/opt/raf/apps/{book['id']}"

    # 1. Detect executable path
    exec_cmd = None
    icon_path = None

    if is_standalone:
        exec_cmd = f"'{target_apps_dir}/{exec_name}'"
        icon_path = ""
    else:
        # Search for files inside apps_dir (the local temp directory)
        all_files = []
        for root, dirs, files in os.walk(apps_dir):
            for f in files:
                all_files.append(os.path.join(root, f))

        # Sort files to find best matches first
        # Heuristics:
        # A. Search for .sh scripts (start.sh, run.sh, play.sh, etc.)
        sh_files = [f for f in all_files if f.endswith(".sh")]
        for sh in sh_files:
            fname = os.path.basename(sh).lower()
            if (
                "start" in fname
                or "run" in fname
                or "kutuphane" in fname
                or "main" in fname
            ):
                rel_path = os.path.relpath(sh, apps_dir)
                exec_cmd = f"'{target_apps_dir}/{rel_path}'"
                break
        if not exec_cmd and sh_files:
            rel_path = os.path.relpath(sh_files[0], apps_dir)
            exec_cmd = f"'{target_apps_dir}/{rel_path}'"

        # B. Search for HTML index if no shell script (xdg-open index.html)
        if not exec_cmd:
            html_files = [f for f in all_files if f.endswith(".html")]
            for html in html_files:
                if (
                    "index" in os.path.basename(html).lower()
                    or "main" in os.path.basename(html).lower()
                ):
                    rel_path = os.path.relpath(html, apps_dir)
                    exec_cmd = f"xdg-open '{target_apps_dir}/{rel_path}'"
                    break
            if not exec_cmd and html_files:
                rel_path = os.path.relpath(html_files[0], apps_dir)
                exec_cmd = f"xdg-open '{target_apps_dir}/{rel_path}'"

        # C. Search for windows .exe files (run with wine)
        if not exec_cmd:
            exe_files = [f for f in all_files if f.endswith(".exe")]
            # Skip uninstaller exes
            exe_files = [
                f for f in exe_files if "unins" not in os.path.basename(f).lower()
            ]
            if exe_files:
                rel_path = os.path.relpath(exe_files[0], apps_dir)
                exec_cmd = f"wine '{target_apps_dir}/{rel_path}'"

        # D. Fallback: Search for binary files (executable files with no extension)
        if not exec_cmd:
            binaries = [
                f
                for f in all_files
                if "." not in os.path.basename(f) and os.access(f, os.X_OK)
            ]
            if binaries:
                rel_path = os.path.relpath(binaries[0], apps_dir)
                exec_cmd = f"'{target_apps_dir}/{rel_path}'"

        # E. Last resort: Just point to the directory
        if not exec_cmd:
            exec_cmd = f"xdg-open '{target_apps_dir}'"

        # 2. Find Icon
        # Search for icon/png/svg
        img_files = [
            f
            for f in all_files
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".svg"))
        ]
        for img in img_files:
            fname = os.path.basename(img).lower()
            if "icon" in fname or "logo" in fname or "avatar" in fname:
                rel_path = os.path.relpath(img, apps_dir)
                icon_path = f"{target_apps_dir}/{rel_path}"
                break
        if not icon_path and img_files:
            rel_path = os.path.relpath(img_files[0], apps_dir)
            icon_path = f"{target_apps_dir}/{rel_path}"

    # Default icon if none found
    if not icon_path:
        icon_path = "education"  # system icon name

    # 3. Create the .desktop file content
    content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name={book['title']}
Comment={tr("installer.desktop_comment", publisher=book.get('publisher', ''))}
Exec={exec_cmd}
Icon={icon_path}
Terminal=false
Categories=Education;Development;
StartupNotify=true
"""

    fd, tmp_desktop_path = tempfile.mkstemp(suffix=".desktop")
    with os.fdopen(fd, "w") as f:
        f.write(content)

    return tmp_desktop_path
