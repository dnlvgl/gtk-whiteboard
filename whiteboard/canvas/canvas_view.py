"""
Main canvas view widget
"""

import gi
gi.require_version('Gtk', '4.0')

from gi.repository import Gtk, Gdk

from whiteboard.canvas.viewport import Viewport
from whiteboard.canvas.spatial_index import SpatialGrid
from whiteboard.canvas.grid import Grid
from whiteboard.canvas.undo import (
    UndoManager, AddObjectCommand, DeleteObjectsCommand,
    MoveObjectsCommand, ResizeObjectCommand, EditTextCommand,
    ChangeColorCommand, ChangeZOrderCommand,
)
from whiteboard.objects import NoteObject, TextObject, ImageObject


class CanvasView(Gtk.DrawingArea):
    """
    Main canvas widget for rendering and interacting with objects
    """

    def __init__(self):
        super().__init__()
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.set_focusable(True)

        # Canvas state
        self.viewport = Viewport()
        self.objects = []
        self.selected_objects = set()
        self.spatial_index = SpatialGrid()
        self.grid = Grid()
        self.undo_manager = UndoManager()

        # Callback for when canvas is modified
        self.on_modified = None

        # Note color preference
        self.last_note_color = 'yellow'

        # Interaction state
        self.drag_start = None
        self.drag_object = None
        self.is_panning = False
        self.resize_handle = None
        self._hovered_object = None

        # Multi-selection rectangle state
        self.is_selecting = False
        self.selection_rect = None  # (x, y, w, h) in canvas coords

        # Drag tracking for undo
        self._drag_original_positions = {}
        self._resize_original = None

        # Sorted cache
        self._sorted_cache = []
        self._sorted_dirty = True

        # Background color
        self.bg_color = (0.95, 0.95, 0.95)

        # Set up drawing
        self.set_draw_func(self.on_draw)

        # Set up event controllers
        self._setup_event_controllers()

    # ── Backward-compatible selected_object property ──────────────

    @property
    def selected_object(self):
        """Returns a single selected object or None (backward compat)"""
        if len(self.selected_objects) == 1:
            return next(iter(self.selected_objects))
        return None

    @selected_object.setter
    def selected_object(self, obj):
        """Set selection to a single object or clear"""
        self.selected_objects.clear()
        if obj is not None:
            self.selected_objects.add(obj)

    # ── Helpers ───────────────────────────────────────────────────

    def _deselect_all(self):
        """Deselect all objects"""
        for obj in self.selected_objects:
            obj.selected = False
        self.selected_objects.clear()

    def _add_object(self, obj):
        """Add an object maintaining both list and spatial index"""
        self.objects.append(obj)
        self.spatial_index.insert(obj)
        self._mark_sorted_dirty()

    def _remove_object(self, obj):
        """Remove an object from list and spatial index"""
        if obj in self.objects:
            self.objects.remove(obj)
        self.spatial_index.remove(obj)
        self._mark_sorted_dirty()

    def _update_object_position(self, obj):
        """Update spatial index after position/size change"""
        self.spatial_index.update(obj)

    def _mark_sorted_dirty(self):
        """Mark the sorted object cache as needing refresh"""
        self._sorted_dirty = True

    def _get_sorted_objects(self, objects=None):
        """Get z-index sorted objects, using cache when possible"""
        if objects is not None:
            return sorted(objects, key=lambda o: o.z_index)
        if self._sorted_dirty:
            self._sorted_cache = sorted(self.objects, key=lambda o: o.z_index)
            self._sorted_dirty = False
        return self._sorted_cache

    def _hit_test(self, canvas_x, canvas_y):
        """Find topmost object at canvas point using spatial index"""
        candidates = self.spatial_index.query_point(canvas_x, canvas_y)
        hit = None
        for obj in sorted(candidates, key=lambda o: o.z_index, reverse=True):
            if obj.contains_point(canvas_x, canvas_y):
                hit = obj
                break
        return hit

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

        # Right-click gesture for context menu
        right_click_gesture = Gtk.GestureClick()
        right_click_gesture.set_button(3)  # Right mouse button
        right_click_gesture.connect('pressed', self.on_right_click)
        self.add_controller(right_click_gesture)

        # Scroll for zooming
        scroll_controller = Gtk.EventControllerScroll()
        scroll_controller.set_flags(
            Gtk.EventControllerScrollFlags.VERTICAL |
            Gtk.EventControllerScrollFlags.DISCRETE
        )
        scroll_controller.connect('scroll', self.on_scroll)
        self.add_controller(scroll_controller)

        # Motion for cursor changes and hover
        motion_controller = Gtk.EventControllerMotion()
        motion_controller.connect('motion', self.on_motion)
        motion_controller.connect('leave', self.on_motion_leave)
        self.add_controller(motion_controller)

        # Keyboard controller for delete and other keys
        key_controller = Gtk.EventControllerKey()
        key_controller.connect('key-pressed', self.on_key_pressed)
        self.add_controller(key_controller)

    # ── Drawing ───────────────────────────────────────────────────

    def on_draw(self, area, context, width, height):
        """Draw callback - renders the entire canvas"""
        # Clear background
        context.set_source_rgb(*self.bg_color)
        context.paint()

        # Save context state
        context.save()

        # Apply viewport transformation
        context.scale(self.viewport.zoom, self.viewport.zoom)
        context.translate(-self.viewport.offset_x, -self.viewport.offset_y)

        # Render grid before objects
        vx, vy, vw, vh = self.viewport.get_visible_rect(width, height)
        self.grid.render(context, vx, vy, vw, vh, self.viewport.zoom)

        # Get visible objects
        visible_objects = self.viewport.get_visible_objects(
            self.objects, width, height, self.spatial_index
        )

        # Render objects sorted by z-index
        for obj in self._get_sorted_objects(visible_objects):
            context.save()
            obj.render(context)
            context.restore()

            # Render selection handles
            if obj.selected:
                obj.render_selection_handles(context)

        # Render selection rectangle
        if self.is_selecting and self.selection_rect:
            sx, sy, sw, sh = self.selection_rect
            context.set_source_rgba(0.2, 0.5, 1.0, 0.15)
            context.rectangle(sx, sy, sw, sh)
            context.fill()
            context.set_source_rgba(0.2, 0.5, 1.0, 0.6)
            context.set_line_width(1.0)
            context.rectangle(sx, sy, sw, sh)
            context.stroke()

        # Restore context
        context.restore()

    # ── Click / Selection ─────────────────────────────────────────

    def on_click(self, gesture, n_press, x, y):
        """Handle click events for selection"""
        canvas_x, canvas_y = self.viewport.screen_to_canvas(x, y)

        # Check modifier keys
        state = gesture.get_current_event_state()
        ctrl = bool(state & Gdk.ModifierType.CONTROL_MASK)

        # Find clicked object
        clicked_object = self._hit_test(canvas_x, canvas_y)

        # Handle double-click for editing
        if n_press == 2 and clicked_object:
            if hasattr(clicked_object, 'text'):
                self.edit_object_text(clicked_object)
                return

        # Update selection
        if clicked_object:
            if ctrl:
                # Ctrl+click toggles selection
                if clicked_object in self.selected_objects:
                    clicked_object.selected = False
                    self.selected_objects.discard(clicked_object)
                else:
                    clicked_object.selected = True
                    self.selected_objects.add(clicked_object)
            else:
                # Plain click selects only this object
                if clicked_object not in self.selected_objects:
                    self._deselect_all()
                    clicked_object.selected = True
                    self.selected_objects.add(clicked_object)
        else:
            if not ctrl:
                # Clicked empty space - deselect all
                self._deselect_all()

        self.queue_draw()

    def on_right_click(self, gesture, n_press, x, y):
        """Handle right-click for context menu"""
        canvas_x, canvas_y = self.viewport.screen_to_canvas(x, y)

        clicked_object = self._hit_test(canvas_x, canvas_y)

        if not clicked_object:
            return

        # Select the object if not already selected
        if clicked_object not in self.selected_objects:
            self._deselect_all()
            clicked_object.selected = True
            self.selected_objects.add(clicked_object)
            self.queue_draw()

        # Show context menu
        self.show_context_menu(x, y)

    def show_context_menu(self, x, y):
        """Show context menu for selected objects"""
        from gi.repository import Gtk, Gio, Gdk

        menu = Gio.Menu()

        # Show "Edit Text" only when exactly one editable object selected
        if len(self.selected_objects) == 1:
            obj = next(iter(self.selected_objects))
            if hasattr(obj, 'text'):
                menu.append('Edit Text', 'canvas.edit-text')

        # Add color submenu if exactly one note is selected
        if len(self.selected_objects) == 1:
            obj = next(iter(self.selected_objects))
            if isinstance(obj, NoteObject):
                color_menu = Gio.Menu()
                colors = [
                    ('yellow', '🟨 Yellow'),
                    ('orange', '🟧 Orange'),
                    ('blue', '🟦 Blue'),
                    ('green', '🟩 Green'),
                    ('purple', '🟪 Purple')
                ]
                for color_name, color_label in colors:
                    color_menu.append(color_label, f'canvas.color-{color_name}')
                menu.append_submenu('Change Color', color_menu)

        menu.append('Duplicate', 'canvas.duplicate')
        menu.append('Bring to Front', 'canvas.bring-front')
        menu.append('Send to Back', 'canvas.send-back')
        menu.append('Delete', 'canvas.delete')

        popover = Gtk.PopoverMenu()
        popover.set_menu_model(menu)
        popover.set_parent(self)
        popover.set_has_arrow(False)

        rect = Gdk.Rectangle()
        rect.x = int(x)
        rect.y = int(y)
        rect.width = 1
        rect.height = 1
        popover.set_pointing_to(rect)

        action_group = Gio.SimpleActionGroup()

        edit_action = Gio.SimpleAction.new('edit-text', None)
        edit_action.connect('activate', lambda a, p: self.edit_object_text(
            next(iter(self.selected_objects)) if self.selected_objects else None
        ))
        action_group.add_action(edit_action)

        duplicate_action = Gio.SimpleAction.new('duplicate', None)
        duplicate_action.connect('activate', lambda a, p: self.duplicate_selected())
        action_group.add_action(duplicate_action)

        front_action = Gio.SimpleAction.new('bring-front', None)
        front_action.connect('activate', lambda a, p: self.bring_to_front())
        action_group.add_action(front_action)

        back_action = Gio.SimpleAction.new('send-back', None)
        back_action.connect('activate', lambda a, p: self.send_to_back())
        action_group.add_action(back_action)

        delete_action = Gio.SimpleAction.new('delete', None)
        delete_action.connect('activate', lambda a, p: self._delete_selected())
        action_group.add_action(delete_action)

        # Add color actions for notes
        if len(self.selected_objects) == 1:
            obj = next(iter(self.selected_objects))
            if isinstance(obj, NoteObject):
                colors = ['yellow', 'orange', 'blue', 'green', 'purple']
                for color_name in colors:
                    color_action = Gio.SimpleAction.new(f'color-{color_name}', None)
                    color_action.connect('activate',
                                       lambda a, p, c=color_name: self.change_note_color(obj, c))
                    action_group.add_action(color_action)

        self.insert_action_group('canvas', action_group)
        popover.popup()

    # ── Delete / Duplicate ────────────────────────────────────────

    def _delete_selected(self):
        """Delete all selected objects"""
        if not self.selected_objects:
            return
        objects = list(self.selected_objects)
        cmd = DeleteObjectsCommand(self, objects)
        self.undo_manager.execute(cmd)
        self._notify_modified()
        self.queue_draw()

    def duplicate_object(self, obj):
        """Duplicate a single object"""
        new_obj = self._create_duplicate(obj)
        if not new_obj:
            return
        self._deselect_all()
        new_obj.selected = True
        self.selected_objects.add(new_obj)
        cmd = AddObjectCommand(self, new_obj)
        self.undo_manager.execute(cmd)
        self._notify_modified()
        self.queue_draw()

    def duplicate_selected(self):
        """Duplicate all selected objects"""
        if not self.selected_objects:
            return
        objects = list(self.selected_objects)
        self._deselect_all()
        for obj in objects:
            new_obj = self._create_duplicate(obj)
            if new_obj:
                new_obj.selected = True
                self.selected_objects.add(new_obj)
                cmd = AddObjectCommand(self, new_obj)
                self.undo_manager.execute(cmd)
        self._notify_modified()
        self.queue_draw()

    def _create_duplicate(self, obj):
        """Create a duplicate of an object (not yet added to canvas)"""
        obj_data = obj.to_dict()
        obj_type = obj.get_type()
        if obj_type == 'note':
            new_obj = NoteObject.from_dict(obj_data)
        elif obj_type == 'text':
            new_obj = TextObject.from_dict(obj_data)
        elif obj_type == 'image':
            new_obj = ImageObject.from_dict(obj_data)
        else:
            return None

        new_obj.x += 20
        new_obj.y += 20
        from uuid import uuid4
        new_obj.id = str(uuid4())
        new_obj.z_index = len(self.objects)
        return new_obj

    # ── Drag ──────────────────────────────────────────────────────

    def on_drag_begin(self, gesture, start_x, start_y):
        """Handle drag start"""
        self.drag_start = (start_x, start_y)

        canvas_x, canvas_y = self.viewport.screen_to_canvas(start_x, start_y)

        # Check modifier keys for selection rectangle
        state = gesture.get_current_event_state()
        shift = bool(state & Gdk.ModifierType.SHIFT_MASK)

        # Check if we're starting a resize on a selected object
        for obj in self.selected_objects:
            handle = obj.get_resize_handle(canvas_x, canvas_y)
            if handle:
                self.resize_handle = handle
                self.drag_object = obj
                self._resize_original = {
                    'x': obj.x, 'y': obj.y,
                    'width': obj.width, 'height': obj.height
                }
                self.set_cursor_from_name('grabbing')
                return

        # Check if we're clicking on an object to drag
        hit = self._hit_test(canvas_x, canvas_y)
        if hit:
            # If the hit object is in the selection, drag all selected
            if hit not in self.selected_objects:
                self._deselect_all()
                hit.selected = True
                self.selected_objects.add(hit)
            self.drag_object = hit
            # Store original positions of all selected objects for undo
            self._drag_original_positions = {
                obj: (obj.x, obj.y) for obj in self.selected_objects
            }
            self.set_cursor_from_name('grabbing')
            return

        # Shift+drag on empty space → selection rectangle
        if shift:
            self.is_selecting = True
            self.selection_rect = (canvas_x, canvas_y, 0, 0)
            self._selection_origin = (canvas_x, canvas_y)
            self.set_cursor_from_name('crosshair')
            return

        # Otherwise, we're panning
        self.is_panning = True

    def on_drag_update(self, gesture, offset_x, offset_y):
        """Handle drag update"""
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
            orig = self._resize_original

            new_x, new_y = orig['x'], orig['y']
            new_width, new_height = orig['width'], orig['height']

            if 'e' in handle:
                new_width = canvas_current_x - new_x
            if 'w' in handle:
                new_width = orig['x'] + orig['width'] - canvas_current_x
                new_x = canvas_current_x
            if 's' in handle:
                new_height = canvas_current_y - new_y
            if 'n' in handle:
                new_height = orig['y'] + orig['height'] - canvas_current_y
                new_y = canvas_current_y

            # Maintain aspect ratio for images
            if hasattr(obj, 'original_width') and hasattr(obj, 'original_height'):
                if obj.original_width > 0 and obj.original_height > 0:
                    aspect_ratio = obj.original_width / obj.original_height
                    if 'e' in handle or 'w' in handle:
                        new_height = new_width / aspect_ratio
                    else:
                        new_width = new_height * aspect_ratio

            new_width = max(20, new_width)
            new_height = max(20, new_height)

            # Apply grid snap to size
            if self.grid.snap_enabled:
                new_x, new_y = self.grid.snap_point(new_x, new_y)
                new_width, new_height = self.grid.snap_size(new_width, new_height)

            obj.x = new_x
            obj.y = new_y
            obj.width = new_width
            obj.height = new_height

            self.queue_draw()

        elif self.is_selecting:
            # Selection rectangle
            canvas_current_x, canvas_current_y = self.viewport.screen_to_canvas(
                current_x, current_y
            )
            ox, oy = self._selection_origin
            sx = min(ox, canvas_current_x)
            sy = min(oy, canvas_current_y)
            sw = abs(canvas_current_x - ox)
            sh = abs(canvas_current_y - oy)
            self.selection_rect = (sx, sy, sw, sh)
            self.queue_draw()

        elif self.drag_object:
            # Moving selected objects
            canvas_start_x, canvas_start_y = self.viewport.screen_to_canvas(
                start_x, start_y
            )
            canvas_current_x, canvas_current_y = self.viewport.screen_to_canvas(
                current_x, current_y
            )

            dx = canvas_current_x - canvas_start_x
            dy = canvas_current_y - canvas_start_y

            for obj in self.selected_objects:
                orig_x, orig_y = self._drag_original_positions.get(obj, (obj.x, obj.y))
                new_x = orig_x + dx
                new_y = orig_y + dy
                if self.grid.snap_enabled:
                    new_x, new_y = self.grid.snap_point(new_x, new_y)
                obj.x = new_x
                obj.y = new_y

            self.queue_draw()

        elif self.is_panning:
            # Panning canvas
            self.viewport.pan(offset_x - getattr(self, '_last_pan_x', 0),
                            offset_y - getattr(self, '_last_pan_y', 0))
            self._last_pan_x = offset_x
            self._last_pan_y = offset_y
            self.queue_draw()

    def on_drag_end(self, gesture, offset_x, offset_y):
        """Handle drag end"""
        # Create undo commands for move/resize
        if self.resize_handle and self.drag_object and self._resize_original:
            orig = self._resize_original
            obj = self.drag_object
            if (obj.x != orig['x'] or obj.y != orig['y'] or
                    obj.width != orig['width'] or obj.height != orig['height']):
                cmd = ResizeObjectCommand(
                    self, obj,
                    orig['x'], orig['y'], orig['width'], orig['height'],
                    obj.x, obj.y, obj.width, obj.height
                )
                self.undo_manager.push_done(cmd)
                self._update_object_position(obj)
                self._notify_modified()

        elif self.drag_object and self._drag_original_positions:
            # Check if anything actually moved
            moved = []
            total_dx = 0
            total_dy = 0
            for obj in self.selected_objects:
                orig_x, orig_y = self._drag_original_positions.get(obj, (obj.x, obj.y))
                if obj.x != orig_x or obj.y != orig_y:
                    moved.append(obj)
                    total_dx = obj.x - orig_x
                    total_dy = obj.y - orig_y
            if moved:
                cmd = MoveObjectsCommand(self, moved, 0, 0)
                # Override the delta: objects are already at final positions
                # Store the actual delta for undo
                cmd.dx = total_dx
                cmd.dy = total_dy
                # Objects are already moved, so execute is a no-op for position
                # but we use push_done
                self.undo_manager.push_done(cmd)
                for obj in moved:
                    self._update_object_position(obj)
                self._notify_modified()

        elif self.is_selecting and self.selection_rect:
            # Select all objects intersecting the rectangle
            sx, sy, sw, sh = self.selection_rect
            if sw > 0 and sh > 0:
                candidates = self.spatial_index.query_rect(sx, sy, sw, sh)
                state = gesture.get_current_event_state()
                ctrl = bool(state & Gdk.ModifierType.CONTROL_MASK)
                if not ctrl:
                    self._deselect_all()
                for obj in candidates:
                    if obj.intersects(sx, sy, sw, sh):
                        obj.selected = True
                        self.selected_objects.add(obj)

        # Reset all state
        self.drag_start = None
        self.drag_object = None
        self.is_panning = False
        self.is_selecting = False
        self.selection_rect = None
        self.resize_handle = None
        self._resize_original = None
        self._drag_original_positions = {}
        self._last_pan_x = 0
        self._last_pan_y = 0
        self.set_cursor_from_name('default')
        self.queue_draw()

    # ── Scroll / Zoom ─────────────────────────────────────────────

    def on_scroll(self, controller, dx, dy):
        """Handle scroll events for zooming"""
        x, y = controller.get_device().get_surface_at_position()[1:3]

        zoom_factor = 1.1
        if dy < 0:
            self.viewport.zoom_at(x, y, zoom_factor)
        elif dy > 0:
            self.viewport.zoom_at(x, y, 1 / zoom_factor)

        self.queue_draw()
        return True

    # ── Motion / Hover ────────────────────────────────────────────

    def on_motion(self, controller, x, y):
        """Handle mouse motion for cursor changes and hover"""
        canvas_x, canvas_y = self.viewport.screen_to_canvas(x, y)

        # Update hover state
        hit = self._hit_test(canvas_x, canvas_y)
        if hit != self._hovered_object:
            if self._hovered_object:
                self._hovered_object.hovered = False
            if hit:
                hit.hovered = True
            self._hovered_object = hit
            self.queue_draw()

        # Check if we're over a resize handle on any selected object
        for obj in self.selected_objects:
            handle = obj.get_resize_handle(canvas_x, canvas_y)
            if handle:
                cursor_name = self._get_resize_cursor_name(handle)
                self.set_cursor_from_name(cursor_name)
                return

        # Check if we're over an object
        if hit:
            self.set_cursor_from_name('grab')
            return

        self.set_cursor_from_name('default')

    def on_motion_leave(self, controller):
        """Handle mouse leaving the canvas"""
        if self._hovered_object:
            self._hovered_object.hovered = False
            self._hovered_object = None
            self.queue_draw()

    def _get_resize_cursor_name(self, handle):
        """Get the appropriate cursor name for a resize handle"""
        cursor_map = {
            'nw': 'nw-resize', 'ne': 'ne-resize',
            'sw': 'sw-resize', 'se': 'se-resize',
            'n': 'n-resize', 's': 's-resize',
            'e': 'e-resize', 'w': 'w-resize',
        }
        return cursor_map.get(handle, 'default')

    # ── Keyboard ──────────────────────────────────────────────────

    def on_key_pressed(self, controller, keyval, keycode, state):
        """Handle keyboard events"""
        # Delete key - delete selected objects
        if keyval == Gdk.KEY_Delete or keyval == Gdk.KEY_BackSpace:
            if self.selected_objects:
                self._delete_selected()
                return True

        # Ctrl+D - duplicate selected
        if (state & Gdk.ModifierType.CONTROL_MASK) and keyval == Gdk.KEY_d:
            if self.selected_objects:
                self.duplicate_selected()
                return True

        return False

    # ── Object operations ─────────────────────────────────────────

    def zoom_in(self):
        """Zoom in on the canvas"""
        width = self.get_width()
        height = self.get_height()
        self.viewport.set_zoom(
            self.viewport.zoom * 1.2, width / 2, height / 2
        )
        self.queue_draw()

    def zoom_out(self):
        """Zoom out on the canvas"""
        width = self.get_width()
        height = self.get_height()
        self.viewport.set_zoom(
            self.viewport.zoom / 1.2, width / 2, height / 2
        )
        self.queue_draw()

    def add_note(self):
        """Add a new note to the canvas using the last used color"""
        width = self.get_width()
        height = self.get_height()
        center_x, center_y = self.viewport.screen_to_canvas(width / 2, height / 2)

        note = NoteObject(
            x=center_x - 100, y=center_y - 100,
            width=200, height=200,
            text='Double-click to edit',
            color=self.last_note_color
        )
        note.z_index = len(self.objects)
        cmd = AddObjectCommand(self, note)
        self.undo_manager.execute(cmd)
        self._notify_modified()
        self.queue_draw()

    def change_note_color(self, note, new_color):
        """Change the color of a note"""
        old_color_name = note.color_name
        old_color = note.color
        new_color_rgb = NoteObject.COLORS[new_color]

        cmd = ChangeColorCommand(note, old_color_name, old_color, new_color, new_color_rgb)
        self.undo_manager.execute(cmd)
        self.last_note_color = new_color
        self._notify_modified()
        self.queue_draw()

    def add_text(self):
        """Add new text to the canvas"""
        width = self.get_width()
        height = self.get_height()
        center_x, center_y = self.viewport.screen_to_canvas(width / 2, height / 2)

        text = TextObject(
            x=center_x - 150, y=center_y - 25,
            width=300, height=50,
            text='Double-click to edit',
            font_size=16
        )
        text.z_index = len(self.objects)
        cmd = AddObjectCommand(self, text)
        self.undo_manager.execute(cmd)
        self._notify_modified()
        self.queue_draw()

    def add_image(self):
        """Add a new image to the canvas"""
        from gi.repository import Gtk, Gio

        dialog = Gtk.FileDialog()
        filter_images = Gtk.FileFilter()
        filter_images.set_name('Images')
        filter_images.add_mime_type('image/png')
        filter_images.add_mime_type('image/jpeg')
        filter_images.add_mime_type('image/gif')
        filter_images.add_mime_type('image/webp')

        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_images)
        dialog.set_filters(filters)
        dialog.set_default_filter(filter_images)

        window = self.get_root()
        dialog.open(window, None, self._on_image_selected)

    def _on_image_selected(self, dialog, result):
        """Handle image file selection"""
        try:
            file = dialog.open_finish(result)
            if file:
                path = file.get_path()

                width = self.get_width()
                height = self.get_height()
                center_x, center_y = self.viewport.screen_to_canvas(width / 2, height / 2)

                image = ImageObject(
                    x=center_x - 150, y=center_y - 150,
                    image_path=path
                )

                if image.width > 300:
                    scale = 300 / image.width
                    image.width = 300
                    image.height = image.height * scale

                image.z_index = len(self.objects)
                cmd = AddObjectCommand(self, image)
                self.undo_manager.execute(cmd)
                self._notify_modified()
                self.queue_draw()
        except Exception as e:
            print(f'Error loading image: {e}')

    def edit_object_text(self, obj):
        """Show a dialog to edit the text of an object"""
        if not obj or not hasattr(obj, 'text'):
            return

        from gi.repository import Gtk

        dialog = Gtk.Dialog(
            title='Edit Text',
            transient_for=self.get_root(),
            modal=True
        )
        dialog.add_button('Cancel', Gtk.ResponseType.CANCEL)
        dialog.add_button('OK', Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.OK)

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

        buffer = text_view.get_buffer()
        buffer.set_text(obj.text)

        scrolled.set_child(text_view)

        content_area = dialog.get_content_area()
        content_area.append(scrolled)

        old_text = obj.text
        dialog.connect('response', self._on_edit_dialog_response, obj, buffer, old_text)
        dialog.show()

    def _on_edit_dialog_response(self, dialog, response, obj, buffer, old_text):
        """Handle edit dialog response"""
        if response == Gtk.ResponseType.OK:
            start = buffer.get_start_iter()
            end = buffer.get_end_iter()
            new_text = buffer.get_text(start, end, False)

            if new_text != old_text:
                cmd = EditTextCommand(obj, old_text, new_text)
                self.undo_manager.execute(cmd)
                self._notify_modified()
                self.queue_draw()

        dialog.close()

    def bring_to_front(self):
        """Bring selected objects to front"""
        if not self.selected_objects:
            return

        objects = list(self.selected_objects)
        max_z = max(obj.z_index for obj in self.objects) if self.objects else 0

        old_z = [obj.z_index for obj in objects]
        new_z = [max_z + 1 + i for i in range(len(objects))]

        cmd = ChangeZOrderCommand(self, objects, old_z, new_z)
        self.undo_manager.execute(cmd)
        self._notify_modified()
        self.queue_draw()

    def send_to_back(self):
        """Send selected objects to back"""
        if not self.selected_objects:
            return

        objects = list(self.selected_objects)
        min_z = min(obj.z_index for obj in self.objects) if self.objects else 0

        old_z = [obj.z_index for obj in objects]
        new_z = [min_z - len(objects) + i for i in range(len(objects))]

        cmd = ChangeZOrderCommand(self, objects, old_z, new_z)
        self.undo_manager.execute(cmd)
        self._notify_modified()
        self.queue_draw()

    # ── Undo/Redo convenience ─────────────────────────────────────

    def undo(self):
        """Undo the last action"""
        self.undo_manager.undo()
        self._notify_modified()
        self.queue_draw()

    def redo(self):
        """Redo the last undone action"""
        self.undo_manager.redo()
        self._notify_modified()
        self.queue_draw()

    # ── Canvas state ──────────────────────────────────────────────

    def clear(self):
        """Clear all objects from the canvas"""
        self.objects.clear()
        self.selected_objects.clear()
        self.spatial_index.clear()
        self.undo_manager.clear()
        self._mark_sorted_dirty()
        self.viewport = Viewport()
        self.queue_draw()

    def load_objects(self, objects):
        """Load objects into the canvas"""
        self.clear()
        self.objects = objects
        self.selected_objects.clear()
        self.spatial_index.rebuild(objects)
        self._mark_sorted_dirty()
        self.queue_draw()

    def _notify_modified(self):
        """Notify that the canvas has been modified"""
        if self.on_modified:
            self.on_modified()
