"""
Main application class
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio

from whiteboard.window import WhiteboardWindow


class WhiteboardApplication(Adw.Application):
    """Main application class"""

    def __init__(self):
        super().__init__(
            application_id='com.example.Whiteboard',
            flags=Gio.ApplicationFlags.FLAGS_NONE
        )
        self.create_action('quit', self.on_quit, ['<primary>q'])
        self.create_action('new', self.on_new, ['<primary>n'])
        self.create_action('open', self.on_open, ['<primary>o'])
        self.create_action('save', self.on_save, ['<primary>s'])

    def do_activate(self):
        """Called when the application is activated"""
        win = self.props.active_window
        if not win:
            win = WhiteboardWindow(application=self)
        win.present()

    def create_action(self, name, callback, shortcuts=None):
        """Create an application action with optional keyboard shortcuts"""
        action = Gio.SimpleAction.new(name, None)
        action.connect('activate', callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f'app.{name}', shortcuts)

    def on_quit(self, action, param):
        """Quit the application"""
        self.quit()

    def on_new(self, action, param):
        """Create a new whiteboard"""
        win = self.props.active_window
        if win:
            win.new_board()

    def on_open(self, action, param):
        """Open a whiteboard file"""
        win = self.props.active_window
        if win:
            win.open_board()

    def on_save(self, action, param):
        """Save the current whiteboard"""
        win = self.props.active_window
        if win:
            win.save_board()
