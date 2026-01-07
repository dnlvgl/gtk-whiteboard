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
            # TODO: Implement resize based on handle
            pass
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
                # TODO: Set cursor based on handle type
                return

        # Check if we're over an object
        for obj in reversed(sorted(self.objects, key=lambda o: o.z_index)):
            if obj.contains_point(canvas_x, canvas_y):
                # TODO: Set move cursor
                return

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

    def clear(self):
        """Clear all objects from the canvas"""
        self.objects.clear()
        self.selected_object = None
        self.viewport = Viewport()
        self.queue_draw()
