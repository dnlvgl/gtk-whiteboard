#!/usr/bin/env python3
"""
Whiteboard - A native GNOME whiteboard application
"""

import sys
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from whiteboard.app import WhiteboardApplication


def main():
    """Application entry point"""
    app = WhiteboardApplication()
    return app.run(sys.argv)


if __name__ == '__main__':
    sys.exit(main())
