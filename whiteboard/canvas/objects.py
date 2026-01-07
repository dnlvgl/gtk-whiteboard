"""
Base class for canvas objects
"""

import json
from abc import ABC, abstractmethod
from uuid import uuid4


class CanvasObject(ABC):
    """
    Base class for all objects on the canvas
    """

    def __init__(self, x, y, width, height):
        """
        Initialize a canvas object

        Args:
            x: X position on canvas
            y: Y position on canvas
            width: Object width
            height: Object height
        """
        self.id = str(uuid4())
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.z_index = 0
        self.selected = False

    @abstractmethod
    def render(self, context):
        """
        Render the object using Cairo context

        Args:
            context: Cairo context to render to
        """
        pass

    @abstractmethod
    def get_type(self):
        """
        Get the type identifier for this object

        Returns:
            String type identifier
        """
        pass

    @abstractmethod
    def to_dict(self):
        """
        Serialize object to dictionary

        Returns:
            Dictionary containing object data
        """
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data):
        """
        Deserialize object from dictionary

        Args:
            data: Dictionary containing object data

        Returns:
            CanvasObject instance
        """
        pass

    def intersects(self, rect_x, rect_y, rect_width, rect_height):
        """
        Check if this object intersects with a rectangle

        Args:
            rect_x: Rectangle X position
            rect_y: Rectangle Y position
            rect_width: Rectangle width
            rect_height: Rectangle height

        Returns:
            True if objects intersect, False otherwise
        """
        return not (
            self.x + self.width < rect_x or
            rect_x + rect_width < self.x or
            self.y + self.height < rect_y or
            rect_y + rect_height < self.y
        )

    def contains_point(self, x, y):
        """
        Check if a point is inside this object

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            True if point is inside, False otherwise
        """
        return (
            self.x <= x <= self.x + self.width and
            self.y <= y <= self.y + self.height
        )

    def move(self, dx, dy):
        """
        Move the object by a delta

        Args:
            dx: Delta X
            dy: Delta Y
        """
        self.x += dx
        self.y += dy

    def resize(self, new_width, new_height):
        """
        Resize the object

        Args:
            new_width: New width
            new_height: New height
        """
        self.width = max(10, new_width)  # Minimum size
        self.height = max(10, new_height)

    def get_resize_handle(self, x, y, handle_size=10):
        """
        Get which resize handle (if any) contains the point

        Args:
            x: X coordinate
            y: Y coordinate
            handle_size: Size of resize handles

        Returns:
            String handle identifier or None
            Possible values: 'nw', 'ne', 'sw', 'se', 'n', 's', 'e', 'w'
        """
        if not self.selected:
            return None

        # Corner handles
        corners = {
            'nw': (self.x, self.y),
            'ne': (self.x + self.width, self.y),
            'sw': (self.x, self.y + self.height),
            'se': (self.x + self.width, self.y + self.height),
        }

        for handle_name, (hx, hy) in corners.items():
            if abs(x - hx) <= handle_size and abs(y - hy) <= handle_size:
                return handle_name

        # Edge handles
        edges = {
            'n': (self.x + self.width / 2, self.y),
            's': (self.x + self.width / 2, self.y + self.height),
            'e': (self.x + self.width, self.y + self.height / 2),
            'w': (self.x, self.y + self.height / 2),
        }

        for handle_name, (hx, hy) in edges.items():
            if abs(x - hx) <= handle_size and abs(y - hy) <= handle_size:
                return handle_name

        return None

    def render_selection_handles(self, context, handle_size=8):
        """
        Render selection handles around the object

        Args:
            context: Cairo context
            handle_size: Size of handles in pixels
        """
        if not self.selected:
            return

        # Draw selection border
        context.set_source_rgb(0.2, 0.6, 1.0)  # Blue
        context.set_line_width(2)
        context.rectangle(self.x, self.y, self.width, self.height)
        context.stroke()

        # Draw corner handles
        corners = [
            (self.x, self.y),  # NW
            (self.x + self.width, self.y),  # NE
            (self.x, self.y + self.height),  # SW
            (self.x + self.width, self.y + self.height),  # SE
        ]

        for cx, cy in corners:
            context.set_source_rgb(1, 1, 1)
            context.rectangle(
                cx - handle_size / 2,
                cy - handle_size / 2,
                handle_size,
                handle_size
            )
            context.fill()

            context.set_source_rgb(0.2, 0.6, 1.0)
            context.rectangle(
                cx - handle_size / 2,
                cy - handle_size / 2,
                handle_size,
                handle_size
            )
            context.stroke()
