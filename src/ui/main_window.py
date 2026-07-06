import os
import subprocess
from gi.repository import Gtk, Adw, GLib, Gio, Gdk
from src.core.translation import tr, on_language_change, remove_language_listener
from src.core.database import Database
from src.core.downloader import DownloadWorker
from src.core.installer import InstallerWorker, is_book_installed, get_deb_package_name, get_all_installed_packages
from src.core.updater import UpdateChecker, UpdateInstaller, AutoUpdateScheduler
from src.core.download_queue import DownloadQueue
from src.core.sync import DatabaseSyncWorker
from src.core.config import load_config
from src.ui.components import BookRow
from src.ui.logs_dialog import InstallationLogsDialog
from src.ui.desktop_editor import show_message

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app, startup_files=None):
        super().__init__(application=app)
        self.startup_files = startup_files or []
        self.set_title(tr("ui.app_title"))
        self.set_default_size(1100, 700)
        
        # State tracking
        self.active_downloads = {}      # book_id -> DownloadWorker
        self.active_installations = {}  # book_id -> InstallerWorker
        self.logs_dialog = InstallationLogsDialog(self)
        self.card_widgets = {}          # book_id -> BookRow
        self._selection_mode = False    # Batch selection mode active
        self._selected_books = set()    # book_ids selected in batch mode
        self.is_offline = False
        
        self.db = Database()
        self.installed_packages_cache = set()
        
        # Drop Target
        drop_target = Gtk.DropTarget(actions=Gdk.DragAction.COPY)
        drop_target.set_gtypes([Gio.File.__gtype__])
        drop_target.connect("drop", self.on_drop)
        self.add_controller(drop_target)

        # Download queue
        self.download_queue = DownloadQueue(max_concurrent=2)
        self.download_queue.on_job_started = self._on_queue_job_started
        self.download_queue.on_queue_changed = self._on_queue_changed

        self.init_ui()
        
        # Auto-update scheduler
        self.auto_update_scheduler = AutoUpdateScheduler()
        self.auto_update_scheduler.on_update_toast_requested = self._on_update_toast
        self.auto_update_scheduler.on_auto_install_requested = self.on_update_available
        self.auto_update_scheduler.start()

        # Database Sync
        config = load_config()
        db_url = config.get("database_url", "").strip()
        if not db_url:
            db_url = "https://raw.githubusercontent.com/KaanFerid/Raf/main/database/"
        
        if db_url and not self.is_offline:
            self.sync_worker = DatabaseSyncWorker(db_url, self.db.database_dir)
            self.sync_worker.on_sync_finished = self._on_sync_finished
            self.sync_worker.on_sync_failed = self._on_sync_failed
            self.sync_worker.start()

        self.refresh_packages_cache()
        GLib.timeout_add_seconds(15, self.refresh_all_statuses)
        on_language_change(self.retranslate_ui)

    def init_ui(self):
        # Toast Overlay
        self.toast_overlay = Adw.ToastOverlay()
        self.set_content(self.toast_overlay)

        # Main Box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.toast_overlay.set_child(main_box)

        # HeaderBar
        self.header = Adw.HeaderBar()
        main_box.append(self.header)

        # Title widget (View Switcher)
        self.view_switcher = Adw.ViewSwitcher()
        self.view_switcher.set_policy(Adw.ViewSwitcherPolicy.WIDE)
        self.header.set_title_widget(self.view_switcher)

        # Search Bar
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_size_request(250, -1)
        self.search_entry.connect("search-changed", self.on_search_changed)
        self.header.pack_start(self.search_entry)

        # Queue Badge
        self.queue_badge = Gtk.Label()
        self.queue_badge.add_css_class("numeric")
        self.queue_badge.set_visible(False)
        self.header.pack_start(self.queue_badge)

        # Select Mode Toggle
        self.select_mode_btn = Gtk.ToggleButton(icon_name="selection-mode-symbolic")
        self.select_mode_btn.connect("toggled", self.toggle_selection_mode)
        self.header.pack_start(self.select_mode_btn)

        # Settings
        menu_btn = Gtk.MenuButton(icon_name="open-menu-symbolic")
        menu = Gio.Menu()
        menu.append(tr("ui.preferences"), "app.preferences")
        menu.append(tr("ui.about_title"), "app.about")
        menu_btn.set_menu_model(menu)
        self.header.pack_end(menu_btn)

        # Local Install
        self.local_install_btn = Gtk.Button(label=tr("ui.install_local_files"))
        self.local_install_btn.connect("clicked", self.on_install_local_clicked)
        self.header.pack_end(self.local_install_btn)

        # ViewStack
        self.stack = Adw.ViewStack()
        self.view_switcher.set_stack(self.stack)
        main_box.append(self.stack)

        # Market Page
        self.market_page, self.market_listbox = self.create_list_page()
        self.stack.add_titled_with_icon(self.market_page, "market", tr("ui.market"), "emblem-system-symbolic")

        # Library Page
        self.library_page, self.library_listbox = self.create_list_page()
        self.stack.add_titled_with_icon(self.library_page, "library", tr("ui.my_library"), "folder-documents-symbolic")

        self.stack.connect("notify::visible-child", self.on_tab_changed)

    def create_list_page(self):
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        
        clamp = Adw.Clamp()
        clamp.set_maximum_size(800)
        scrolled.set_child(clamp)
        
        listbox = Gtk.ListBox()
        listbox.add_css_class("boxed-list")
        listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        clamp.set_child(listbox)
        
        return scrolled, listbox

    def on_tab_changed(self, stack, pspec):
        self.refresh_grid()

    # --- Actions ---
    def refresh_grid(self):
        # Determine current tab
        visible_name = self.stack.get_visible_child_name()
        
        # Get active listbox
        listbox = self.market_listbox if visible_name == "market" else self.library_listbox

        # Clear existing
        while child := listbox.get_first_child():
            listbox.remove(child)

        self.card_widgets.clear()
        
        query = self.search_entry.get_text().lower().strip()
        all_books = self.db.get_all_books()
        
        # Filter
        filtered = []
        for b in all_books:
            if query and query not in b['title'].lower() and query not in b.get('publisher', '').lower():
                continue
            is_inst = is_book_installed(b, self.installed_packages_cache)
            if visible_name == "library" and not is_inst:
                continue
            filtered.append(b)

        # Populate
        for b in filtered:
            is_inst = is_book_installed(b, self.installed_packages_cache)
            row = BookRow(b, is_installed=is_inst)
            row.connect('install-requested', lambda r, bk: self.start_download(bk))
            row.connect('uninstall-requested', lambda r, bk: self.start_uninstallation(bk))
            row.connect('launch-requested', lambda r, bk: self.launch_book(bk))
            row.connect('cancel-requested', lambda r, bk: self.cancel_download(bk))
            
            self.card_widgets[b['id']] = row
            listbox.append(row)

    def start_download(self, book):
        book_id = book['id']
        if book_id in self.active_downloads:
            return

        file_name = book['file_name']
        if os.environ.get("RAF_DEV") == "1":
            cache_dir = os.path.abspath(os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                "mock_system", "cache"
            ))
        else:
            cache_dir = os.path.expanduser("~/.cache/raf/downloads")
        local_file_path = os.path.join(cache_dir, file_name)

        card = self.card_widgets.get(book_id)
        if card:
            card.update_status(is_installed=False, downloading=True, percent=0, speed_str=tr("ui.download_preparing"))

        worker = DownloadWorker(book_id, book['download_url'], local_file_path)
        worker.on_progress_changed = self.on_download_progress
        worker.on_finished = self.on_download_finished
        worker.on_error = self.on_download_error
        
        self.active_downloads[book_id] = worker
        worker.start()

    def on_download_progress(self, book_id, percent, speed_str):
        if book_id in self.card_widgets:
            card = self.card_widgets[book_id]
            pct = percent if percent >= 0 else 50
            card.update_status(is_installed=False, downloading=True, percent=pct, speed_str=speed_str)

    def on_download_finished(self, book_id, local_file_path):
        worker = self.active_downloads.pop(book_id, None)
        self.download_queue.on_download_completed(book_id)

        book = self.card_widgets[book_id].book
        def on_response(dialog, response):
            dialog.close()
            if response == "yes":
                self.start_installation(book, local_file_path)
            else:
                card = self.card_widgets.get(book_id)
                if card: card.update_status(is_installed=False)
                try: os.remove(local_file_path)
                except: pass

        dialog = Adw.MessageDialog(transient_for=self, heading=tr("ui.confirm_install_title"), body=tr("ui.confirm_install_prompt", title=book['title']))
        dialog.add_response("cancel", tr("ui.no"))
        dialog.add_response("yes", tr("ui.yes"))
        dialog.connect("response", on_response)
        dialog.present()

    def on_download_error(self, book_id, err_msg):
        self.active_downloads.pop(book_id, None)
        self.download_queue.on_download_completed(book_id)
        
        if book_id in self.card_widgets:
            self.card_widgets[book_id].update_status(is_installed=False)
            
        if "cancel" not in err_msg.lower():
            self.show_toast(tr("ui.toast_download_error", error=err_msg[:60]))

    def cancel_download(self, book):
        book_id = book['id']
        if self.download_queue.is_queued(book_id):
            self.download_queue.dequeue(book_id)
            card = self.card_widgets.get(book_id)
            if card:
                card.set_queued(False)
                card.update_status(card.is_installed)
            return
            
        if book_id in self.active_downloads:
            self.active_downloads[book_id].cancel()

    def start_installation(self, book, local_file_path):
        book_id = book['id']
        if book_id in self.active_installations:
            return

        card = self.card_widgets.get(book_id)
        if card:
            card.primary_btn.set_sensitive(False)
            card.primary_btn.set_label(tr("ui.installing_btn"))
            card.status_label.set_text(tr("ui.installing_btn"))
        
        worker = InstallerWorker(book, local_file_path, action="install")
        worker.on_finished = self.on_installation_finished
        worker.on_output_received = self.on_install_output
        worker.on_auth_failed = lambda bid: self.on_auth_failed(bid, worker)
        
        self.active_installations[book_id] = worker
        worker.start()

    def on_install_output(self, book_id, text):
        self.logs_dialog.append_log(f"[{book_id}] {text.strip()}")

    def on_installation_finished(self, book_id, success):
        worker = self.active_installations.pop(book_id, None)
        book = worker.book if worker else None
        card = self.card_widgets.get(book_id)
        
        if not book and card: book = card.book

        if card:
            card.primary_btn.set_sensitive(True)
            installed = is_book_installed(book, self.installed_packages_cache)
            card.update_status(installed)
        
        installed = is_book_installed(book, self.installed_packages_cache) if book else success
        
        if success and installed:
            self.show_toast(tr("ui.toast_install_success", title=book['title']))
            if book and book.get('is_local'):
                self.db.add_sideloaded_book(book)
            if book.get('file_type') == 'deb':
                cache_dir = os.path.expanduser("~/.cache/raf/downloads")
                try: os.remove(os.path.join(cache_dir, book['file_name']))
                except: pass
            self.refresh_packages_cache()
        elif getattr(worker, '_auth_failed', False):
            pass
        else:
            self.show_toast(tr("ui.toast_install_error", title=book['title']))

    def start_uninstallation(self, book):
        book_id = book['id']
        if book_id in self.active_installations:
            return

        def on_response(dialog, response):
            dialog.close()
            if response == "yes":
                card = self.card_widgets.get(book_id)
                if card:
                    card.primary_btn.set_sensitive(False)
                    card.secondary_btn.set_sensitive(False)
                    card.primary_btn.set_label(tr("ui.uninstalling_btn"))
                
                worker = InstallerWorker(book, None, action="uninstall")
                worker.on_finished = self.on_uninstallation_finished
                worker.on_output_received = self.on_install_output
                worker.on_auth_failed = lambda bid: self.on_auth_failed(bid, worker)
                
                self.active_installations[book_id] = worker
                worker.start()

        dialog = Adw.MessageDialog(transient_for=self, heading=tr("ui.uninstall_library_title"), body=tr("ui.uninstall_library_prompt", title=book['title']))
        dialog.add_response("cancel", tr("ui.no"))
        dialog.add_response("yes", tr("ui.yes"))
        dialog.set_response_appearance("yes", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", on_response)
        dialog.present()

    def on_uninstallation_finished(self, book_id, success):
        worker = self.active_installations.pop(book_id, None)
        book = worker.book if worker else None
        card = self.card_widgets.get(book_id)
        if not book and card: book = card.book

        if card:
            card.primary_btn.set_sensitive(True)
            installed = is_book_installed(book, self.installed_packages_cache)
            card.update_status(installed)
        
        installed = is_book_installed(book, self.installed_packages_cache) if book else not success
        
        if success and not installed:
            self.show_toast(tr("ui.toast_uninstall_success", title=book['title']))
            if book and book.get('is_local'):
                self.db.remove_sideloaded_book(book['id'])
            self.refresh_packages_cache()
        elif getattr(worker, '_auth_failed', False):
            pass
        else:
            self.show_toast(tr("ui.toast_install_error", title=book['title']))

    def on_auth_failed(self, book_id, worker):
        worker._auth_failed = True
        title = worker.book['title'] if worker.book else ""
        self.show_toast(tr("ui.toast_auth_failed", title=title))

    def launch_book(self, book):
        if os.environ.get("RAF_DEV") == "1":
            show_message(self, tr("ui.book_launched_sim_title"), tr("ui.book_launched_sim_message", title=book['title'], publisher=book['publisher'], filename=book['file_name']))
            return
        
        file_type = book.get('file_type', 'deb')
        
        if file_type == 'deb':
            package_name = get_deb_package_name(book)
            cmd = ["gtk-launch", package_name]
            try:
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                try: subprocess.Popen([package_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception as e:
                    show_message(self, tr("ui.app_launch_failed_title"), tr("ui.app_launch_failed_message", error=str(e)), type="error")
        else:
            desktop_name = f"raf-{book['id']}"
            cmd = ["gtk-launch", desktop_name]
            try:
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                show_message(self, tr("ui.app_launch_failed_title"), tr("ui.book_launch_failed_message", error=str(e)), type="error")

    def refresh_packages_cache(self):
        def _get_pkgs():
            pkgs = get_all_installed_packages()
            GLib.idle_add(lambda: self._on_packages_loaded(pkgs))
        import threading
        threading.Thread(target=_get_pkgs, daemon=True).start()

    def _on_packages_loaded(self, pkgs):
        self.installed_packages_cache = pkgs
        self.refresh_grid()

    def refresh_all_statuses(self):
        self.refresh_packages_cache()
        return True

    def on_search_changed(self, entry):
        self.refresh_grid()

    def toggle_selection_mode(self, btn):
        self._selection_mode = btn.get_active()
        self._selected_books.clear()
        for card in self.card_widgets.values():
            card.set_selection_mode(self._selection_mode)

    def on_install_local_clicked(self, btn):
        def on_response(dialog, response, file):
            if response == Gtk.ResponseType.ACCEPT:
                path = file.get_path()
                if path: self.process_local_files([path])
        
        dialog = Gtk.FileChooserNative(title=tr("ui.select_local_files"), transient_for=self, action=Gtk.FileChooserAction.OPEN)
        filter_all = Gtk.FileFilter()
        filter_all.set_name(tr("ui.supported_files"))
        filter_all.add_pattern("*.deb")
        filter_all.add_pattern("*.zip")
        filter_all.add_pattern("*.appimage")
        filter_all.add_pattern("*.fernus")
        dialog.add_filter(filter_all)
        dialog.connect("response", on_response)
        dialog.show()

    def on_drop(self, target, value, x, y):
        path = value.get_path()
        if path and path.lower().endswith(('.deb', '.zip', '.appimage', '.fernus')):
            self.process_local_files([path])
        return True

    def process_local_files(self, file_paths):
        mock_books = []
        file_list_str = ""
        for path in file_paths:
            filename = os.path.basename(path)
            mock_book = {
                "id": f"local_{filename}",
                "title": os.path.splitext(filename)[0],
                "publisher": tr("cli.local_publisher"),
                "file_name": filename,
                "file_type": os.path.splitext(filename)[1].lstrip('.'),
                "is_local": True,
                "absolute_path": path
            }
            mock_books.append((mock_book, path))
            file_list_str += f"• {filename}\n"
            
        def on_response(dialog, response):
            dialog.close()
            if response == "yes":
                for mock_book, path in mock_books:
                    self.start_installation(mock_book, path)
        
        dialog = Adw.MessageDialog(transient_for=self, heading=tr("ui.confirm_sideload_title"), body=tr("ui.confirm_sideload_prompt", count=len(mock_books), files=file_list_str.strip()))
        dialog.add_response("cancel", tr("ui.no"))
        dialog.add_response("yes", tr("ui.yes"))
        dialog.connect("response", on_response)
        dialog.present()

    def retranslate_ui(self):
        self.set_title(tr("ui.app_title"))
        self.stack.get_page(self.market_page).set_title(tr("ui.market"))
        self.stack.get_page(self.library_page).set_title(tr("ui.my_library"))
        self.local_install_btn.set_label(tr("ui.install_local_files"))
        self.refresh_grid()

    def _on_queue_job_started(self, book_id):
        job = self.download_queue._last_started
        if job:
            book, local_path = job
            self.download_queue.on_download_started(book_id)
            GLib.idle_add(lambda: self.start_download(book))

    def _on_queue_changed(self, count):
        GLib.idle_add(lambda: self.queue_badge.set_visible(count > 0))
        GLib.idle_add(lambda: self.queue_badge.set_text(tr("ui.queue_count", count=count)))

    def _on_sync_finished(self, count):
        self.db.load_books()
        GLib.idle_add(self.refresh_grid)
        GLib.idle_add(lambda: self.show_toast(tr("ui.sync_success", count=count)))

    def _on_sync_failed(self, err):
        print(f"Database sync failed: {err}")

    def _on_update_toast(self, ver):
        GLib.idle_add(lambda: self.show_toast(tr("ui.toast_update_available", version=ver)))

    def on_update_available(self, ver, url, changelog):
        def _show():
            def on_response(dialog, response):
                dialog.close()
                if response == "yes":
                    self.start_app_update(ver, url)
            
            dialog = Adw.MessageDialog(transient_for=self, heading=tr("ui.new_update_available"), body=tr("ui.update_prompt", version=ver, changelog=changelog))
            dialog.add_response("cancel", tr("ui.no"))
            dialog.add_response("yes", tr("ui.yes"))
            dialog.connect("response", on_response)
            dialog.present()
        GLib.idle_add(_show)

    def start_app_update(self, version, download_url):
        cache_dir = os.path.expanduser("~/.cache/raf/downloads")
        file_path = os.path.join(cache_dir, f"raf_{version}_update.deb")
        self.update_download_worker = DownloadWorker("app_update", download_url, file_path)
        
        def on_finished(bid, path):
            self.update_installer_worker = UpdateInstaller(path)
            self.update_installer_worker.on_finished = self.on_update_install_finished
            self.update_installer_worker.start()
            
        self.update_download_worker.on_finished = on_finished
        self.update_download_worker.start()

    def on_update_install_finished(self, success):
        def _show():
            if success:
                show_message(self, tr("ui.update_successful_title"), tr("ui.update_successful_message"))
            else:
                show_message(self, tr("ui.update_error_title"), tr("ui.update_error_message"), type="error")
        GLib.idle_add(_show)

    def show_toast(self, msg):
        toast = Adw.Toast.new(msg)
        self.toast_overlay.add_toast(toast)
