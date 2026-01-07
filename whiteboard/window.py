"""
Main application window
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio

from whiteboard.canvas.canvas_view import CanvasView
from whiteboard.storage import BoardFile


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

        # Object submenu
        object_menu = Gio.Menu()
        object_menu.append('Bring to Front', 'win.bring-to-front')
        object_menu.append('Send to Back', 'win.send-to-back')
        menu.append_submenu('Object', object_menu)

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
        self.create_action('bring-to-front', self.on_bring_to_front)
        self.create_action('send-to-back', self.on_send_to_back)

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

    def on_bring_to_front(self, action, param):
        """Bring selected object to front"""
        self.canvas_view.bring_to_front()

    def on_send_to_back(self, action, param):
        """Send selected object to back"""
        self.canvas_view.send_to_back()

    def new_board(self):
        """Create a new whiteboard"""
        # Check if we need to save current board
        if self.is_modified and self.canvas_view.objects:
            # TODO: Show save confirmation dialog
            pass

        self.canvas_view.clear()
        self.current_file = None
        self.is_modified = False
        self.set_title('Whiteboard')

    def open_board(self):
        """Open a whiteboard file"""
        dialog = Gtk.FileDialog()

        # Set file filter for .wboard files
        filter_wboard = Gtk.FileFilter()
        filter_wboard.set_name('Whiteboard Files')
        filter_wboard.add_pattern('*.wboard')

        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_wboard)
        dialog.set_filters(filters)
        dialog.set_default_filter(filter_wboard)

        dialog.open(self, None, self.on_open_response)

    def on_open_response(self, dialog, result):
        """Handle open file dialog response"""
        try:
            file = dialog.open_finish(result)
            if file:
                path = file.get_path()

                # Load board from file
                board_file = BoardFile(path)
                objects = board_file.load()

                # Update canvas
                self.canvas_view.load_objects(objects)

                self.current_file = path
                self.is_modified = False
                self.set_title(f'Whiteboard - {file.get_basename()}')

        except Exception as e:
            print(f'Error opening file: {e}')
            # Show error dialog
            error_dialog = Adw.MessageDialog.new(
                self,
                'Error Opening File',
                f'Failed to open whiteboard file:\n{str(e)}'
            )
            error_dialog.add_response('ok', 'OK')
            error_dialog.show()

    def save_board(self):
        """Save the current whiteboard"""
        if self.current_file:
            try:
                # Save to existing file
                board_file = BoardFile(self.current_file)
                board_file.save(self.canvas_view.objects)

                self.is_modified = False
                print(f'Saved to {self.current_file}')

            except Exception as e:
                print(f'Error saving file: {e}')
                # Show error dialog
                error_dialog = Adw.MessageDialog.new(
                    self,
                    'Error Saving File',
                    f'Failed to save whiteboard file:\n{str(e)}'
                )
                error_dialog.add_response('ok', 'OK')
                error_dialog.show()
        else:
            self.save_board_as()

    def save_board_as(self):
        """Save the whiteboard to a new file"""
        dialog = Gtk.FileDialog()

        # Set initial name
        dialog.set_initial_name('Untitled.wboard')

        # Set file filter for .wboard files
        filter_wboard = Gtk.FileFilter()
        filter_wboard.set_name('Whiteboard Files')
        filter_wboard.add_pattern('*.wboard')

        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_wboard)
        dialog.set_filters(filters)
        dialog.set_default_filter(filter_wboard)

        dialog.save(self, None, self.on_save_response)

    def on_save_response(self, dialog, result):
        """Handle save file dialog response"""
        try:
            file = dialog.save_finish(result)
            if file:
                path = file.get_path()

                # Ensure .wboard extension
                if not path.endswith('.wboard'):
                    path += '.wboard'

                # Save board to file
                board_file = BoardFile(path)
                board_file.save(self.canvas_view.objects)

                self.current_file = path
                self.is_modified = False
                self.set_title(f'Whiteboard - {file.get_basename()}')
                print(f'Saved to {path}')

        except Exception as e:
            print(f'Error saving file: {e}')
            # Show error dialog
            error_dialog = Adw.MessageDialog.new(
                self,
                'Error Saving File',
                f'Failed to save whiteboard file:\n{str(e)}'
            )
            error_dialog.add_response('ok', 'OK')
            error_dialog.show()
