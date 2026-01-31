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

        # Edit submenu
        edit_menu = Gio.Menu()
        edit_menu.append('Undo', 'app.undo')
        edit_menu.append('Redo', 'app.redo')
        menu.append_submenu('Edit', edit_menu)

        # Object submenu
        object_menu = Gio.Menu()
        object_menu.append('Bring to Front', 'win.bring-to-front')
        object_menu.append('Send to Back', 'win.send-to-back')
        menu.append_submenu('Object', object_menu)

        # Grid submenu
        grid_menu = Gio.Menu()
        grid_menu.append('Toggle Grid', 'win.toggle-grid')
        grid_menu.append('Toggle Snap', 'win.toggle-snap')
        menu.append_submenu('Grid', grid_menu)

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

        # Undo/Redo buttons
        undo_redo_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        undo_redo_box.add_css_class('linked')

        self.undo_button = Gtk.Button()
        self.undo_button.set_icon_name('edit-undo-symbolic')
        self.undo_button.set_tooltip_text('Undo (Ctrl+Z)')
        self.undo_button.set_sensitive(False)
        self.undo_button.connect('clicked', self.on_undo)
        undo_redo_box.append(self.undo_button)

        self.redo_button = Gtk.Button()
        self.redo_button.set_icon_name('edit-redo-symbolic')
        self.redo_button.set_tooltip_text('Redo (Ctrl+Shift+Z)')
        self.redo_button.set_sensitive(False)
        self.redo_button.connect('clicked', self.on_redo)
        undo_redo_box.append(self.redo_button)

        header.pack_start(undo_redo_box)

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
        self.canvas_view.on_modified = self.mark_modified
        self.canvas_view.undo_manager.on_state_changed = self._on_undo_state_changed

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
        self.create_action('toggle-grid', self.on_toggle_grid)
        self.create_action('toggle-snap', self.on_toggle_snap)

    def _on_undo_state_changed(self, can_undo, can_redo):
        """Update undo/redo button sensitivity"""
        self.undo_button.set_sensitive(can_undo)
        self.redo_button.set_sensitive(can_redo)

    def create_action(self, name, callback):
        """Create a window action"""
        action = Gio.SimpleAction.new(name, None)
        action.connect('activate', callback)
        self.add_action(action)

    def on_undo(self, button):
        """Undo the last action"""
        self.canvas_view.undo()

    def on_redo(self, button):
        """Redo the last action"""
        self.canvas_view.redo()

    def on_zoom_in(self, button):
        self.canvas_view.zoom_in()

    def on_zoom_out(self, button):
        self.canvas_view.zoom_out()

    def on_add_note(self, action, param):
        self.canvas_view.add_note()

    def on_add_text(self, action, param):
        self.canvas_view.add_text()

    def on_add_image(self, action, param):
        self.canvas_view.add_image()

    def on_bring_to_front(self, action, param):
        self.canvas_view.bring_to_front()

    def on_send_to_back(self, action, param):
        self.canvas_view.send_to_back()

    def on_toggle_grid(self, action, param):
        """Toggle grid visibility"""
        grid = self.canvas_view.grid
        grid.enabled = not grid.enabled
        grid.visible = grid.enabled
        self.canvas_view.queue_draw()

    def on_toggle_snap(self, action, param):
        """Toggle snap to grid"""
        grid = self.canvas_view.grid
        grid.snap_enabled = not grid.snap_enabled
        # Auto-enable grid visibility when snap is turned on
        if grid.snap_enabled and not grid.visible:
            grid.enabled = True
            grid.visible = True
            self.canvas_view.queue_draw()

    def new_board(self):
        """Create a new whiteboard"""
        if self.is_modified and self.canvas_view.objects:
            self.show_save_confirmation(self._do_new_board)
            return
        self._do_new_board()

    def _do_new_board(self):
        """Actually create new board after confirmation"""
        self.canvas_view.clear()
        self.current_file = None
        self.is_modified = False
        self.set_title('Whiteboard')

    def mark_modified(self):
        """Mark the board as modified"""
        if not self.is_modified:
            self.is_modified = True
            title = self.get_title()
            if not title.startswith('*'):
                self.set_title(f'*{title}')

    def show_save_confirmation(self, callback):
        dialog = Adw.MessageDialog.new(
            self,
            'Save Changes?',
            'There are unsaved changes. Do you want to save them?'
        )
        dialog.add_response('cancel', 'Cancel')
        dialog.add_response('discard', 'Discard')
        dialog.add_response('save', 'Save')
        dialog.set_response_appearance('discard', Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_response_appearance('save', Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response('save')
        dialog.set_close_response('cancel')
        dialog.connect('response', self._on_save_confirmation_response, callback)
        dialog.show()

    def _on_save_confirmation_response(self, dialog, response, callback):
        if response == 'save':
            self.save_board()
            if callback:
                callback()
        elif response == 'discard':
            if callback:
                callback()

    def open_board(self):
        """Open a whiteboard file"""
        dialog = Gtk.FileDialog()

        filter_wboard = Gtk.FileFilter()
        filter_wboard.set_name('Whiteboard Files')
        filter_wboard.add_pattern('*.wboard')

        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_wboard)
        dialog.set_filters(filters)
        dialog.set_default_filter(filter_wboard)

        dialog.open(self, None, self.on_open_response)

    def on_open_response(self, dialog, result):
        try:
            file = dialog.open_finish(result)
            if file:
                path = file.get_path()

                board_file = BoardFile(path)
                objects = board_file.load()

                self.canvas_view.load_objects(objects)

                self.current_file = path
                self.is_modified = False
                self.set_title(f'Whiteboard - {file.get_basename()}')

        except Exception as e:
            print(f'Error opening file: {e}')
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
                board_file = BoardFile(self.current_file)
                board_file.save(self.canvas_view.objects)

                self.is_modified = False
                import os
                filename = os.path.basename(self.current_file)
                self.set_title(f'Whiteboard - {filename}')
                print(f'Saved to {self.current_file}')

            except Exception as e:
                print(f'Error saving file: {e}')
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
        dialog.set_initial_name('Untitled.wboard')

        filter_wboard = Gtk.FileFilter()
        filter_wboard.set_name('Whiteboard Files')
        filter_wboard.add_pattern('*.wboard')

        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_wboard)
        dialog.set_filters(filters)
        dialog.set_default_filter(filter_wboard)

        dialog.save(self, None, self.on_save_response)

    def on_save_response(self, dialog, result):
        try:
            file = dialog.save_finish(result)
            if file:
                path = file.get_path()

                if not path.endswith('.wboard'):
                    path += '.wboard'

                board_file = BoardFile(path)
                board_file.save(self.canvas_view.objects)

                self.current_file = path
                self.is_modified = False
                self.set_title(f'Whiteboard - {file.get_basename()}')
                print(f'Saved to {path}')

        except Exception as e:
            print(f'Error saving file: {e}')
            error_dialog = Adw.MessageDialog.new(
                self,
                'Error Saving File',
                f'Failed to save whiteboard file:\n{str(e)}'
            )
            error_dialog.add_response('ok', 'OK')
            error_dialog.show()
