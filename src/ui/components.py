from gi.repository import Gtk, Adw, Pango, GLib
from src.core.translation import tr

class PublisherBadge(Gtk.DrawingArea):
    """Draws a clean flat Adwaita-style rounded-square avatar with publisher initials."""
    def __init__(self, text):
        super().__init__()
        self.text = text
        self.set_size_request(48, 48)
        self.set_valign(Gtk.Align.CENTER)
        self.set_halign(Gtk.Align.CENTER)
        self.set_draw_func(self.on_draw)

    def on_draw(self, area, cr, width, height):
        first_char = self.text[0].upper() if self.text else 'K'
        char_val = ord(first_char)
        
        # Flat Libadwaita color palette
        flat_colors = [
            (0.208, 0.518, 0.894),  # Blue #3584e4
            (0.149, 0.635, 0.412),  # Green #26a269
            (0.902, 0.380, 0.000),  # Orange #e66100
            (0.471, 0.165, 0.498),  # Purple #782a7f
            (0.753, 0.110, 0.157),  # Red #c01c28
            (0.102, 0.373, 0.706),  # Dark Blue #1a5fb4
            (0.596, 0.416, 0.267),  # Brown #986a44
            (0.384, 0.682, 0.529),  # Light Green #62ae87
        ]
        r, g, b = flat_colors[char_val % len(flat_colors)]
        
        # Draw rounded rectangle
        radius = 10.0
        cr.arc(radius, radius, radius, 3.14159, -1.57079)
        cr.arc(width - radius, radius, radius, -1.57079, 0)
        cr.arc(width - radius, height - radius, radius, 0, 1.57079)
        cr.arc(radius, height - radius, radius, 1.57079, 3.14159)
        cr.close_path()
        cr.set_source_rgb(r, g, b)
        cr.fill()

        # Initials
        words = self.text.split()
        if len(words) >= 2:
            initials = words[0][0] + words[1][0]
        elif len(words) == 1:
            initials = words[0][:2]
        else:
            initials = "KM"
        initials = initials.upper()

        cr.set_source_rgb(1.0, 1.0, 1.0)
        cr.select_font_face("Inter", 0, 1)
        cr.set_font_size(16)
        
        extents = cr.text_extents(initials)
        x = (width - extents.width) / 2 - extents.x_bearing
        y = (height - extents.height) / 2 - extents.y_bearing
        cr.move_to(x, y)
        cr.show_text(initials)


class BookRow(Adw.ActionRow):
    def __init__(self, book, is_installed=False, main_window=None):
        super().__init__()
        self.book = book
        self.book_id = book['id']
        self.is_installed = is_installed
        self.downloading = False
        self.is_queued = False
        self.main_window = main_window

        self.set_title(self.book['title'])
        self.set_title_lines(2)
        
        file_type_str = self.book.get('file_type', 'deb').upper()
        self.type_str = file_type_str
        self.set_subtitle(f"{self.book['publisher']} • {tr('ui.type_label', type=file_type_str)}")
        self.set_subtitle_lines(1)

        # Prefix Badge
        self.badge = PublisherBadge(self.book['publisher'])
        self.add_prefix(self.badge)

        # Center info (Progress bar & Speed)
        self.center_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.center_box.set_valign(Gtk.Align.CENTER)
        
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_visible(False)
        self.progress_bar.set_size_request(120, -1)
        
        self.speed_label = Gtk.Label()
        self.speed_label.set_visible(False)
        self.speed_label.add_css_class("caption")
        
        self.center_box.append(self.progress_bar)
        self.center_box.append(self.speed_label)
        # Using suffix for everything on the right
        self.add_suffix(self.center_box)

        # Actions
        self.action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.action_box.set_valign(Gtk.Align.CENTER)
        
        self.status_label = Gtk.Label()
        self.status_label.add_css_class("dim-label")
        self.action_box.append(self.status_label)
        
        self.primary_btn = Gtk.Button()
        self.primary_btn.set_valign(Gtk.Align.CENTER)
        self.primary_btn.connect("clicked", self.on_primary_clicked)
        self.action_box.append(self.primary_btn)
        
        self.secondary_btn = Gtk.Button()
        self.secondary_btn.set_valign(Gtk.Align.CENTER)
        self.secondary_btn.add_css_class("destructive-action")
        self.secondary_btn.connect("clicked", self.on_secondary_clicked)
        self.action_box.append(self.secondary_btn)
        
        self.edit_btn = Gtk.Button(label=tr("ui.edit_launcher"))
        self.edit_btn.set_valign(Gtk.Align.CENTER)
        self.edit_btn.connect("clicked", self.on_edit_clicked)
        self.action_box.append(self.edit_btn)
        
        # Batch Select Checkbox
        self.select_check = Gtk.CheckButton()
        self.select_check.set_valign(Gtk.Align.CENTER)
        self.select_check.set_visible(False)
        self.select_check.connect("toggled", self.on_select_toggled)
        self.action_box.append(self.select_check)
        
        self.add_suffix(self.action_box)

        self.update_status(self.is_installed)

    def set_selection_mode(self, active):
        self.select_check.set_visible(active)
        if not active:
            self.select_check.set_active(False)

    def on_select_toggled(self, checkbtn):
        if self.main_window:
            self.main_window.on_book_selection_changed(self.book_id, checkbtn.get_active())

    def update_status(self, is_installed, downloading=False, percent=0, speed_str="", is_offline=False):
        self.is_installed = is_installed
        self.downloading = downloading

        if self.is_queued and not downloading:
            self.status_label.set_text(tr("ui.queued_btn"))
            self.primary_btn.set_label(tr("ui.cancel_btn"))
            self.primary_btn.remove_css_class("suggested-action")
            self.primary_btn.remove_css_class("destructive-action")
            self.primary_btn.set_sensitive(True)
            self.secondary_btn.set_visible(False)
            self.edit_btn.set_visible(False)
            self.progress_bar.set_visible(False)
            self.speed_label.set_visible(False)
            return

        if downloading:
            self.is_queued = False
            self.status_label.set_text(tr("ui.downloading_btn"))
            
            self.progress_bar.set_visible(True)
            self.progress_bar.set_fraction(percent / 100.0)
            
            self.speed_label.set_visible(True)
            self.speed_label.set_text(speed_str)
            
            self.primary_btn.set_label(tr("ui.cancel_btn"))
            self.primary_btn.remove_css_class("suggested-action")
            self.primary_btn.set_sensitive(True)
            
            self.secondary_btn.set_visible(False)
            self.edit_btn.set_visible(False)
            
        elif is_installed:
            self.status_label.set_text(tr("ui.installed_btn"))
            self.progress_bar.set_visible(False)
            self.speed_label.set_visible(False)
            
            self.primary_btn.set_label(tr("ui.run_btn"))
            self.primary_btn.add_css_class("suggested-action")
            self.primary_btn.set_sensitive(True)
            
            self.secondary_btn.set_label(tr("ui.uninstall_btn"))
            self.secondary_btn.set_visible(True)
            self.edit_btn.set_visible(True)
            
        else:
            self.status_label.set_text(tr("ui.not_installed_btn"))
            self.progress_bar.set_visible(False)
            self.speed_label.set_visible(False)
            
            self.primary_btn.set_label(tr("ui.install_btn"))
            self.primary_btn.add_css_class("suggested-action")
            
            if is_offline:
                self.primary_btn.set_sensitive(False)
                self.primary_btn.set_tooltip_text(tr("ui.offline_download_tooltip"))
            else:
                self.primary_btn.set_sensitive(True)
                self.primary_btn.set_tooltip_text("")
                
            self.secondary_btn.set_visible(False)
            self.edit_btn.set_visible(False)

    def retranslate_ui(self, is_offline=False):
        self.set_subtitle(f"{self.book['publisher']} • {tr('ui.type_label', type=self.type_str)}")
        self.update_status(self.is_installed, self.downloading, 
                           self.progress_bar.get_fraction() * 100, 
                           self.speed_label.get_text(), is_offline=is_offline)
        self.edit_btn.set_label(tr("ui.edit_launcher"))

    def set_queued(self, queued):
        self.is_queued = queued
        self.update_status(self.is_installed)

    def on_primary_clicked(self, btn):
        if self.main_window:
            if self.is_installed:
                self.main_window.launch_requested(self.book)
            elif self.downloading or self.is_queued:
                self.main_window.cancel_requested(self.book)
            else:
                self.main_window.install_requested(self.book)

    def on_secondary_clicked(self, btn):
        if self.is_installed and not self.downloading and self.main_window:
            self.main_window.uninstall_requested(self.book)

    def on_edit_clicked(self, btn):
        from src.ui.desktop_editor import DesktopEditorDialog
        window = self.get_root()
        dialog = DesktopEditorDialog(self.book, parent=window)
        dialog.present()
