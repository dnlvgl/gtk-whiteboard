"""
Undo/Redo system with command pattern
"""

from abc import ABC, abstractmethod


class Command(ABC):
    """Base class for undoable commands"""

    @abstractmethod
    def execute(self):
        """Execute the command"""
        pass

    @abstractmethod
    def undo(self):
        """Undo the command"""
        pass


class AddObjectCommand(Command):
    """Command for adding an object to the canvas"""

    def __init__(self, canvas, obj):
        self.canvas = canvas
        self.obj = obj

    def execute(self):
        self.canvas._add_object(self.obj)

    def undo(self):
        self.obj.selected = False
        self.canvas.selected_objects.discard(self.obj)
        self.canvas._remove_object(self.obj)


class DeleteObjectsCommand(Command):
    """Command for deleting objects from the canvas"""

    def __init__(self, canvas, objects):
        self.canvas = canvas
        # Store objects with their list indices for reinsertion
        self.entries = []
        for obj in objects:
            idx = canvas.objects.index(obj)
            self.entries.append((idx, obj))
        # Sort by index so reinsertion works correctly
        self.entries.sort(key=lambda e: e[0])

    def execute(self):
        for _, obj in reversed(self.entries):
            obj.selected = False
            self.canvas.selected_objects.discard(obj)
            self.canvas._remove_object(obj)

    def undo(self):
        for idx, obj in self.entries:
            idx = min(idx, len(self.canvas.objects))
            self.canvas.objects.insert(idx, obj)
            self.canvas.spatial_index.insert(obj)
        self.canvas._mark_sorted_dirty()


class MoveObjectsCommand(Command):
    """Command for moving objects (stores dx/dy delta)"""

    def __init__(self, canvas, objects, dx, dy):
        self.canvas = canvas
        self.objects = list(objects)
        self.dx = dx
        self.dy = dy

    def execute(self):
        for obj in self.objects:
            obj.x += self.dx
            obj.y += self.dy
            self.canvas.spatial_index.update(obj)

    def undo(self):
        for obj in self.objects:
            obj.x -= self.dx
            obj.y -= self.dy
            self.canvas.spatial_index.update(obj)


class ResizeObjectCommand(Command):
    """Command for resizing an object (stores old/new geometry)"""

    def __init__(self, canvas, obj, old_x, old_y, old_w, old_h, new_x, new_y, new_w, new_h):
        self.canvas = canvas
        self.obj = obj
        self.old_x = old_x
        self.old_y = old_y
        self.old_w = old_w
        self.old_h = old_h
        self.new_x = new_x
        self.new_y = new_y
        self.new_w = new_w
        self.new_h = new_h

    def execute(self):
        self.obj.x = self.new_x
        self.obj.y = self.new_y
        self.obj.width = self.new_w
        self.obj.height = self.new_h
        self.canvas.spatial_index.update(self.obj)

    def undo(self):
        self.obj.x = self.old_x
        self.obj.y = self.old_y
        self.obj.width = self.old_w
        self.obj.height = self.old_h
        self.canvas.spatial_index.update(self.obj)


class EditTextCommand(Command):
    """Command for editing text content"""

    def __init__(self, obj, old_text, new_text):
        self.obj = obj
        self.old_text = old_text
        self.new_text = new_text

    def execute(self):
        self.obj.text = self.new_text

    def undo(self):
        self.obj.text = self.old_text


class ChangeColorCommand(Command):
    """Command for changing note color"""

    def __init__(self, note, old_color_name, old_color, new_color_name, new_color):
        self.note = note
        self.old_color_name = old_color_name
        self.old_color = old_color
        self.new_color_name = new_color_name
        self.new_color = new_color

    def execute(self):
        self.note.color_name = self.new_color_name
        self.note.color = self.new_color

    def undo(self):
        self.note.color_name = self.old_color_name
        self.note.color = self.old_color


class ChangeZOrderCommand(Command):
    """Command for changing z-order (bring to front / send to back)"""

    def __init__(self, canvas, objects, old_z_indices, new_z_indices):
        self.canvas = canvas
        self.objects = list(objects)
        self.old_z_indices = list(old_z_indices)
        self.new_z_indices = list(new_z_indices)

    def execute(self):
        for obj, z in zip(self.objects, self.new_z_indices):
            obj.z_index = z
        self.canvas._mark_sorted_dirty()

    def undo(self):
        for obj, z in zip(self.objects, self.old_z_indices):
            obj.z_index = z
        self.canvas._mark_sorted_dirty()


class UndoManager:
    """Manages undo/redo stacks with a configurable action limit"""

    MAX_ACTIONS = 50

    def __init__(self):
        self._undo_stack = []
        self._redo_stack = []
        self.on_state_changed = None

    @property
    def can_undo(self):
        return len(self._undo_stack) > 0

    @property
    def can_redo(self):
        return len(self._redo_stack) > 0

    def execute(self, command):
        """Execute a command and push it onto the undo stack"""
        command.execute()
        self._undo_stack.append(command)
        self._redo_stack.clear()
        if len(self._undo_stack) > self.MAX_ACTIONS:
            self._undo_stack.pop(0)
        self._notify()

    def push_done(self, command):
        """Push an already-executed command onto the undo stack (record-after-execute pattern)"""
        self._undo_stack.append(command)
        self._redo_stack.clear()
        if len(self._undo_stack) > self.MAX_ACTIONS:
            self._undo_stack.pop(0)
        self._notify()

    def undo(self):
        """Undo the last command"""
        if not self.can_undo:
            return
        command = self._undo_stack.pop()
        command.undo()
        self._redo_stack.append(command)
        self._notify()

    def redo(self):
        """Redo the last undone command"""
        if not self.can_redo:
            return
        command = self._redo_stack.pop()
        command.execute()
        self._undo_stack.append(command)
        self._notify()

    def clear(self):
        """Clear both stacks"""
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._notify()

    def _notify(self):
        if self.on_state_changed:
            self.on_state_changed(self.can_undo, self.can_redo)
