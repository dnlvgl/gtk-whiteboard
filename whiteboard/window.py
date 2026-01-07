"""
Main application window
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio

from whiteboard.canvas.canvas_view import CanvasView


class WhiteboardWindow(Adw.ApplicationWindow):
    """Main application window"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_default_size(1200, 800)
        self.set_title('Whiteboard')

        self.current_file = None
        self.is_modified = False

        self._build_ui()

    def _build_ui(self):
        """Build the user interface"""
        # Create header bar
        header = Adw.HeaderBar()

        # Create primary menu button
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name('open-menu-symbolic')
        menu_button.set_tooltip_text('Main Menu')

        # Create menu model
        menu = Gio.Menu()
        menu.append('New', 'app.new')
        menu.append('Open', 'app.open')
        menu.append('Save', 'app.save')
        menu.append('Quit', 'app.quit')

        menu_button.set_menu_model(menu)
        header.pack_end(menu_button)

        # Create add button with dropdown
        add_menu = Gio.Menu()
        add_menu.append('Add Note', 'win.add-note')
        add_menu.append('Add Text', 'win.add-text')
        add_menu.append('Add Image', 'win.add-image')

        add_button = Gtk.MenuButton()
        add_button.set_icon_name('list-add-symbolic')
        add_button.set_tooltip_text('Add Object')
        add_button.set_menu_model(add_menu)
        header.pack_start(add_button)

        # Create zoom controls
        zoom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        zoom_box.add_css_class('linked')

        zoom_out_button = Gtk.Button()
        zoom_out_button.set_icon_name('zoom-out-symbolic')
        zoom_out_button.set_tooltip_text('Zoom Out')
        zoom_out_button.connect('clicked', self.on_zoom_out)
        zoom_box.append(zoom_out_button)

        zoom_in_button = Gtk.Button()
        zoom_in_button.set_icon_name('zoom-in-symbolic')
        zoom_in_button.set_tooltip_text('Zoom In')
        zoom_in_button.connect('clicked', self.on_zoom_in)
        zoom_box.append(zoom_in_button)

        header.pack_end(zoom_box)

        # Create canvas view
        self.canvas_view = CanvasView()

        # Create main content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.append(header)
        content_box.append(self.canvas_view)

        self.set_content(content_box)

        # Create window actions
        self.create_action('add-note', self.on_add_note)
        self.create_action('add-text', self.on_add_text)
        self.create_action('add-image', self.on_add_image)

    def create_action(self, name, callback):
        """Create a window action"""
        action = Gio.SimpleAction.new(name, None)
        action.connect('activate', callback)
        self.add_action(action)

    def on_zoom_in(self, button):
        """Zoom in on the canvas"""
        self.canvas_view.zoom_in()

    def on_zoom_out(self, button):
        """Zoom out on the canvas"""
        self.canvas_view.zoom_out()

    def on_add_note(self, action, param):
        """Add a new note to the canvas"""
        self.canvas_view.add_note()

    def on_add_text(self, action, param):
        """Add new text to the canvas"""
        self.canvas_view.add_text()

    def on_add_image(self, action, param):
        """Add a new image to the canvas"""
        self.canvas_view.add_image()

    def new_board(self):
        """Create a new whiteboard"""
        # TODO: Implement new board logic
        self.canvas_view.clear()
        self.current_file = None
        self.is_modified = False
        self.set_title('Whiteboard')

    def open_board(self):
        """Open a whiteboard file"""
        # TODO: Implement file opening
        dialog = Gtk.FileDialog()
        dialog.open(self, None, self.on_open_response)

    def on_open_response(self, dialog, result):
        """Handle open file dialog response"""
        try:
            file = dialog.open_finish(result)
            if file:
                path = file.get_path()
                # TODO: Load board from file
                self.current_file = path
                self.set_title(f'Whiteboard - {file.get_basename()}')
        except Exception as e:
            print(f'Error opening file: {e}')

    def save_board(self):
        """Save the current whiteboard"""
        if self.current_file:
            # TODO: Save to existing file
            pass
        else:
            self.save_board_as()

    def save_board_as(self):
        """Save the whiteboard to a new file"""
        # TODO: Implement file saving
        dialog = Gtk.FileDialog()
        dialog.save(self, None, self.on_save_response)

    def on_save_response(self, dialog, result):
        """Handle save file dialog response"""
        try:
            file = dialog.save_finish(result)
            if file:
                path = file.get_path()
                # TODO: Save board to file
                self.current_file = path
                self.is_modified = False
                self.set_title(f'Whiteboard - {file.get_basename()}')
        except Exception as e:
            print(f'Error saving file: {e}')
