"""
Main canvas view widget
"""

import gi
gi.require_version('Gtk', '4.0')

from gi.repository import Gtk, Gdk

from whiteboard.canvas.viewport import Viewport
from whiteboard.objects import NoteObject, TextObject, ImageObject


class CanvasView(Gtk.DrawingArea):
    """
    Main canvas widget for rendering and interacting with objects
    """

    def __init__(self):
        super().__init__()
        self.set_hexpand(True)
        self.set_vexpand(True)

        # Canvas state
        self.viewport = Viewport()
        self.objects = []
        self.selected_object = None

        # Interaction state
        self.drag_start = None
        self.drag_object = None
        self.is_panning = False
        self.resize_handle = None

        # Background color
        self.bg_color = (0.95, 0.95, 0.95)

        # Set up drawing
        self.set_draw_func(self.on_draw)

        # Set up event controllers
        self._setup_event_controllers()

    def _setup_event_controllers(self):
        """Set up mouse and keyboard event controllers"""
        # Gesture for dragging (pan or move objects)
        drag_gesture = Gtk.GestureDrag()
        drag_gesture.connect('drag-begin', self.on_drag_begin)
        drag_gesture.connect('drag-update', self.on_drag_update)
        drag_gesture.connect('drag-end', self.on_drag_end)
        self.add_controller(drag_gesture)

        # Click gesture for selection
        click_gesture = Gtk.GestureClick()
        click_gesture.connect('pressed', self.on_click)
        self.add_controller(click_gesture)

        # Scroll for zooming
        scroll_controller = Gtk.EventControllerScroll()
        scroll_controller.set_flags(
            Gtk.EventControllerScrollFlags.VERTICAL |
            Gtk.EventControllerScrollFlags.DISCRETE
        )
        scroll_controller.connect('scroll', self.on_scroll)
        self.add_controller(scroll_controller)

        # Motion for cursor changes
        motion_controller = Gtk.EventControllerMotion()
        motion_controller.connect('motion', self.on_motion)
        self.add_controller(motion_controller)

        # Keyboard controller for delete and other keys
        key_controller = Gtk.EventControllerKey()
        key_controller.connect('key-pressed', self.on_key_pressed)
        self.add_controller(key_controller)

    def on_draw(self, area, context, width, height):
        """
        Draw callback - renders the entire canvas

        Args:
            area: DrawingArea widget
            context: Cairo context
            width: Widget width
            height: Widget height
        """
        # Clear background
        context.set_source_rgb(*self.bg_color)
        context.paint()

        # Save context state
        context.save()

        # Apply viewport transformation
        context.scale(self.viewport.zoom, self.viewport.zoom)
        context.translate(-self.viewport.offset_x, -self.viewport.offset_y)

        # Get visible objects
        visible_objects = self.viewport.get_visible_objects(
            self.objects, width, height
        )

        # Render objects sorted by z-index
        for obj in sorted(visible_objects, key=lambda o: o.z_index):
            context.save()
            obj.render(context)
            context.restore()

            # Render selection handles
            if obj.selected:
                obj.render_selection_handles(context)

        # Restore context
        context.restore()

    def on_click(self, gesture, n_press, x, y):
        """
        Handle click events for selection

        Args:
            gesture: GestureClick controller
            n_press: Number of clicks
            x: X coordinate
            y: Y coordinate
        """
        # Convert to canvas coordinates
        canvas_x, canvas_y = self.viewport.screen_to_canvas(x, y)

        # Find clicked object (search in reverse z-order)
        clicked_object = None
        for obj in reversed(sorted(self.objects, key=lambda o: o.z_index)):
            if obj.contains_point(canvas_x, canvas_y):
                clicked_object = obj
                break

        # Handle double-click for editing
        if n_press == 2 and clicked_object:
            # Check if object is editable (note or text)
            if hasattr(clicked_object, 'text'):
                self.edit_object_text(clicked_object)
                return

        # Update selection
        if clicked_object:
            # Deselect previous
            if self.selected_object and self.selected_object != clicked_object:
                self.selected_object.selected = False

            # Select new
            clicked_object.selected = True
            self.selected_object = clicked_object
        else:
            # Clicked empty space - deselect all
            if self.selected_object:
                self.selected_object.selected = False
                self.selected_object = None

        self.queue_draw()

    def on_drag_begin(self, gesture, start_x, start_y):
        """
        Handle drag start

        Args:
            gesture: GestureDrag controller
            start_x: Start X coordinate
            start_y: Start Y coordinate
        """
        self.drag_start = (start_x, start_y)

        # Convert to canvas coordinates
        canvas_x, canvas_y = self.viewport.screen_to_canvas(start_x, start_y)

        # Check if we're starting a resize
        if self.selected_object:
            handle = self.selected_object.get_resize_handle(canvas_x, canvas_y)
            if handle:
                self.resize_handle = handle
                self.drag_object = self.selected_object
                return

        # Check if we're clicking on an object to drag
        for obj in reversed(sorted(self.objects, key=lambda o: o.z_index)):
            if obj.contains_point(canvas_x, canvas_y):
                self.drag_object = obj
                return

        # Otherwise, we're panning
        self.is_panning = True

    def on_drag_update(self, gesture, offset_x, offset_y):
        """
        Handle drag update

        Args:
            gesture: GestureDrag controller
            offset_x: X offset from drag start
            offset_y: Y offset from drag start
        """
        if self.drag_start is None:
            return

        start_x, start_y = self.drag_start
        current_x = start_x + offset_x
        current_y = start_y + offset_y

        if self.resize_handle and self.drag_object:
            # Resizing object
            canvas_current_x, canvas_current_y = self.viewport.screen_to_canvas(
                current_x, current_y
            )

            obj = self.drag_object
            handle = self.resize_handle

            # Store original bounds if not already stored
            if not hasattr(self, '_resize_original'):
                self._resize_original = {
                    'x': obj.x,
                    'y': obj.y,
                    'width': obj.width,
                    'height': obj.height
                }

            orig = self._resize_original

            # Calculate new bounds based on handle
            new_x, new_y = orig['x'], orig['y']
            new_width, new_height = orig['width'], orig['height']

            if 'e' in handle:  # East (right side)
                new_width = canvas_current_x - new_x
            if 'w' in handle:  # West (left side)
                new_width = orig['x'] + orig['width'] - canvas_current_x
                new_x = canvas_current_x
            if 's' in handle:  # South (bottom)
                new_height = canvas_current_y - new_y
            if 'n' in handle:  # North (top)
                new_height = orig['y'] + orig['height'] - canvas_current_y
                new_y = canvas_current_y

            # Maintain aspect ratio for images
            if hasattr(obj, 'original_width') and hasattr(obj, 'original_height'):
                if obj.original_width > 0 and obj.original_height > 0:
                    aspect_ratio = obj.original_width / obj.original_height
                    # Use width to determine height
                    if 'e' in handle or 'w' in handle:
                        new_height = new_width / aspect_ratio
                    else:
                        new_width = new_height * aspect_ratio

            # Apply new bounds with minimum size
            obj.x = new_x
            obj.y = new_y
            obj.width = max(20, new_width)
            obj.height = max(20, new_height)

            self.queue_draw()
        elif self.drag_object:
            # Moving object
            delta_canvas_x = offset_x / self.viewport.zoom
            delta_canvas_y = offset_y / self.viewport.zoom

            # Get the current position
            canvas_start_x, canvas_start_y = self.viewport.screen_to_canvas(
                start_x, start_y
            )
            canvas_current_x, canvas_current_y = self.viewport.screen_to_canvas(
                current_x, current_y
            )

            # Calculate actual delta
            dx = canvas_current_x - canvas_start_x
            dy = canvas_current_y - canvas_start_y

            # Move object
            self.drag_object.x = self.drag_object.x + dx - (
                getattr(self, '_last_drag_dx', 0)
            )
            self.drag_object.y = self.drag_object.y + dy - (
                getattr(self, '_last_drag_dy', 0)
            )

            self._last_drag_dx = dx
            self._last_drag_dy = dy

            self.queue_draw()
        elif self.is_panning:
            # Panning canvas
            self.viewport.pan(offset_x - getattr(self, '_last_pan_x', 0),
                            offset_y - getattr(self, '_last_pan_y', 0))
            self._last_pan_x = offset_x
            self._last_pan_y = offset_y
            self.queue_draw()

    def on_drag_end(self, gesture, offset_x, offset_y):
        """
        Handle drag end

        Args:
            gesture: GestureDrag controller
            offset_x: Final X offset
            offset_y: Final Y offset
        """
        self.drag_start = None
        self.drag_object = None
        self.is_panning = False
        self.resize_handle = None
        self._last_pan_x = 0
        self._last_pan_y = 0
        self._last_drag_dx = 0
        self._last_drag_dy = 0
        if hasattr(self, '_resize_original'):
            delattr(self, '_resize_original')

    def on_scroll(self, controller, dx, dy):
        """
        Handle scroll events for zooming

        Args:
            controller: EventControllerScroll
            dx: Horizontal scroll delta
            dy: Vertical scroll delta

        Returns:
            True if event was handled
        """
        # Get pointer position for zoom center
        x, y = controller.get_device().get_surface_at_position()[1:3]

        # Zoom in or out based on scroll direction
        zoom_factor = 1.1
        if dy < 0:
            # Scroll up - zoom in
            self.viewport.zoom_at(x, y, zoom_factor)
        elif dy > 0:
            # Scroll down - zoom out
            self.viewport.zoom_at(x, y, 1 / zoom_factor)

        self.queue_draw()
        return True

    def on_motion(self, controller, x, y):
        """
        Handle mouse motion for cursor changes

        Args:
            controller: EventControllerMotion
            x: X coordinate
            y: Y coordinate
        """
        # Convert to canvas coordinates
        canvas_x, canvas_y = self.viewport.screen_to_canvas(x, y)

        # Check if we're over a resize handle
        if self.selected_object:
            handle = self.selected_object.get_resize_handle(canvas_x, canvas_y)
            if handle:
                # Set cursor based on handle type
                cursor_name = self._get_resize_cursor_name(handle)
                self.set_cursor_from_name(cursor_name)
                return

        # Check if we're over an object
        for obj in reversed(sorted(self.objects, key=lambda o: o.z_index)):
            if obj.contains_point(canvas_x, canvas_y):
                # Set move cursor
                self.set_cursor_from_name('grab')
                return

        # Default cursor
        self.set_cursor_from_name('default')

    def _get_resize_cursor_name(self, handle):
        """
        Get the appropriate cursor name for a resize handle

        Args:
            handle: Handle identifier (nw, ne, sw, se, n, s, e, w)

        Returns:
            Cursor name string
        """
        cursor_map = {
            'nw': 'nw-resize',
            'ne': 'ne-resize',
            'sw': 'sw-resize',
            'se': 'se-resize',
            'n': 'n-resize',
            's': 's-resize',
            'e': 'e-resize',
            'w': 'w-resize',
        }
        return cursor_map.get(handle, 'default')

    def on_key_pressed(self, controller, keyval, keycode, state):
        """
        Handle keyboard events

        Args:
            controller: EventControllerKey
            keyval: Key value
            keycode: Hardware keycode
            state: Modifier state

        Returns:
            True if event was handled
        """
        from gi.repository import Gdk

        # Delete key - delete selected object
        if keyval == Gdk.KEY_Delete or keyval == Gdk.KEY_BackSpace:
            if self.selected_object:
                self.objects.remove(self.selected_object)
                self.selected_object = None
                self.queue_draw()
                return True

        # Ctrl+D - duplicate selected object
        if (state & Gdk.ModifierType.CONTROL_MASK) and keyval == Gdk.KEY_d:
            if self.selected_object:
                self.duplicate_object(self.selected_object)
                return True

        return False

    def duplicate_object(self, obj):
        """
        Duplicate an object

        Args:
            obj: Object to duplicate
        """
        # Create a copy of the object data
        obj_data = obj.to_dict()

        # Import the appropriate class
        from whiteboard.objects import NoteObject, TextObject, ImageObject

        # Recreate object from data
        obj_type = obj.get_type()
        if obj_type == 'note':
            new_obj = NoteObject.from_dict(obj_data)
        elif obj_type == 'text':
            new_obj = TextObject.from_dict(obj_data)
        elif obj_type == 'image':
            new_obj = ImageObject.from_dict(obj_data)
        else:
            return

        # Offset the position slightly
        new_obj.x += 20
        new_obj.y += 20

        # Give it a new ID and z-index
        from uuid import uuid4
        new_obj.id = str(uuid4())
        new_obj.z_index = len(self.objects)

        # Deselect old object, select new one
        if self.selected_object:
            self.selected_object.selected = False
        new_obj.selected = True
        self.selected_object = new_obj

        # Add to canvas
        self.objects.append(new_obj)
        self.queue_draw()

    def zoom_in(self):
        """Zoom in on the canvas"""
        width = self.get_width()
        height = self.get_height()
        self.viewport.set_zoom(
            self.viewport.zoom * 1.2,
            width / 2,
            height / 2
        )
        self.queue_draw()

    def zoom_out(self):
        """Zoom out on the canvas"""
        width = self.get_width()
        height = self.get_height()
        self.viewport.set_zoom(
            self.viewport.zoom / 1.2,
            width / 2,
            height / 2
        )
        self.queue_draw()

    def add_note(self):
        """Add a new note to the canvas"""
        # Create note in center of viewport
        width = self.get_width()
        height = self.get_height()
        center_x, center_y = self.viewport.screen_to_canvas(width / 2, height / 2)

        # Create a new note
        note = NoteObject(
            x=center_x - 100,
            y=center_y - 100,
            width=200,
            height=200,
            text='Double-click to edit',
            color='yellow'
        )
        note.z_index = len(self.objects)
        self.objects.append(note)
        self.queue_draw()

    def add_text(self):
        """Add new text to the canvas"""
        # Create text in center of viewport
        width = self.get_width()
        height = self.get_height()
        center_x, center_y = self.viewport.screen_to_canvas(width / 2, height / 2)

        # Create a new text object
        text = TextObject(
            x=center_x - 150,
            y=center_y - 25,
            width=300,
            height=50,
            text='Double-click to edit',
            font_size=16
        )
        text.z_index = len(self.objects)
        self.objects.append(text)
        self.queue_draw()

    def add_image(self):
        """Add a new image to the canvas"""
        # Show file chooser dialog
        from gi.repository import Gtk

        dialog = Gtk.FileDialog()
        filter_images = Gtk.FileFilter()
        filter_images.set_name('Images')
        filter_images.add_mime_type('image/png')
        filter_images.add_mime_type('image/jpeg')
        filter_images.add_mime_type('image/gif')
        filter_images.add_mime_type('image/webp')

        filters = Gtk.ListStore.new([Gtk.FileFilter])
        filters.append([filter_images])
        dialog.set_filters(filters)

        # Get the toplevel window
        window = self.get_root()
        dialog.open(window, None, self._on_image_selected)

    def _on_image_selected(self, dialog, result):
        """Handle image file selection"""
        try:
            file = dialog.open_finish(result)
            if file:
                path = file.get_path()

                # Create image in center of viewport
                width = self.get_width()
                height = self.get_height()
                center_x, center_y = self.viewport.screen_to_canvas(width / 2, height / 2)

                # Create image object
                image = ImageObject(
                    x=center_x - 150,
                    y=center_y - 150,
                    image_path=path
                )

                # Scale down large images
                if image.width > 300:
                    scale = 300 / image.width
                    image.width = 300
                    image.height = image.height * scale

                image.z_index = len(self.objects)
                self.objects.append(image)
                self.queue_draw()
        except Exception as e:
            print(f'Error loading image: {e}')

    def edit_object_text(self, obj):
        """
        Show a dialog to edit the text of an object

        Args:
            obj: Object to edit (must have 'text' attribute)
        """
        from gi.repository import Gtk

        # Create dialog
        dialog = Gtk.Dialog(
            title='Edit Text',
            transient_for=self.get_root(),
            modal=True
        )
        dialog.add_button('Cancel', Gtk.ResponseType.CANCEL)
        dialog.add_button('OK', Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.OK)

        # Create text view for multi-line editing
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_min_content_width(400)
        scrolled.set_min_content_height(200)
        scrolled.set_vexpand(True)

        text_view = Gtk.TextView()
        text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        text_view.set_top_margin(10)
        text_view.set_bottom_margin(10)
        text_view.set_left_margin(10)
        text_view.set_right_margin(10)

        # Set current text
        buffer = text_view.get_buffer()
        buffer.set_text(obj.text)

        scrolled.set_child(text_view)

        # Add to dialog content area
        content_area = dialog.get_content_area()
        content_area.append(scrolled)

        # Show dialog and handle response
        dialog.connect('response', self._on_edit_dialog_response, obj, buffer)
        dialog.show()

    def _on_edit_dialog_response(self, dialog, response, obj, buffer):
        """
        Handle edit dialog response

        Args:
            dialog: The dialog
            response: Response type
            obj: Object being edited
            buffer: Text buffer with new text
        """
        if response == Gtk.ResponseType.OK:
            # Get text from buffer
            start = buffer.get_start_iter()
            end = buffer.get_end_iter()
            new_text = buffer.get_text(start, end, False)

            # Update object
            obj.text = new_text
            self.queue_draw()

        dialog.close()

    def bring_to_front(self):
        """Bring selected object to front (highest z-index)"""
        if not self.selected_object:
            return

        # Find max z-index
        max_z = max([obj.z_index for obj in self.objects]) if self.objects else 0

        # Set selected object to max + 1
        self.selected_object.z_index = max_z + 1
        self.queue_draw()

    def send_to_back(self):
        """Send selected object to back (lowest z-index)"""
        if not self.selected_object:
            return

        # Find min z-index
        min_z = min([obj.z_index for obj in self.objects]) if self.objects else 0

        # Set selected object to min - 1
        self.selected_object.z_index = min_z - 1
        self.queue_draw()

    def clear(self):
        """Clear all objects from the canvas"""
        self.objects.clear()
        self.selected_object = None
        self.viewport = Viewport()
        self.queue_draw()
