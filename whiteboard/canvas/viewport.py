"""
Viewport management for infinite canvas
"""


class Viewport:
    """
    Manages the visible area of the infinite canvas
    Handles coordinate transformations and culling
    """

    def __init__(self):
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.zoom = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 4.0

    def screen_to_canvas(self, screen_x, screen_y):
        """
        Convert screen coordinates to canvas coordinates

        Args:
            screen_x: X coordinate in screen space
            screen_y: Y coordinate in screen space

        Returns:
            Tuple of (canvas_x, canvas_y)
        """
        canvas_x = screen_x / self.zoom + self.offset_x
        canvas_y = screen_y / self.zoom + self.offset_y
        return (canvas_x, canvas_y)

    def canvas_to_screen(self, canvas_x, canvas_y):
        """
        Convert canvas coordinates to screen coordinates

        Args:
            canvas_x: X coordinate in canvas space
            canvas_y: Y coordinate in canvas space

        Returns:
            Tuple of (screen_x, screen_y)
        """
        screen_x = (canvas_x - self.offset_x) * self.zoom
        screen_y = (canvas_y - self.offset_y) * self.zoom
        return (screen_x, screen_y)

    def pan(self, delta_x, delta_y):
        """
        Pan the viewport by screen pixel amounts

        Args:
            delta_x: Pixels to pan in X direction (screen space)
            delta_y: Pixels to pan in Y direction (screen space)
        """
        self.offset_x -= delta_x / self.zoom
        self.offset_y -= delta_y / self.zoom

    def zoom_at(self, screen_x, screen_y, zoom_delta):
        """
        Zoom the viewport centered at a specific screen point

        Args:
            screen_x: X coordinate of zoom center (screen space)
            screen_y: Y coordinate of zoom center (screen space)
            zoom_delta: Amount to change zoom (multiplicative)
        """
        # Get canvas position under cursor
        canvas_x, canvas_y = self.screen_to_canvas(screen_x, screen_y)

        # Update zoom level with constraints
        old_zoom = self.zoom
        self.zoom *= zoom_delta
        self.zoom = max(self.min_zoom, min(self.max_zoom, self.zoom))

        # Adjust offset to keep canvas point under cursor
        # This makes it feel like we're zooming "into" the point
        if self.zoom != old_zoom:
            self.offset_x = canvas_x - screen_x / self.zoom
            self.offset_y = canvas_y - screen_y / self.zoom

    def set_zoom(self, new_zoom, center_x=None, center_y=None):
        """
        Set the zoom level, optionally centered at a point

        Args:
            new_zoom: New zoom level
            center_x: X coordinate to center zoom on (screen space)
            center_y: Y coordinate to center zoom on (screen space)
        """
        new_zoom = max(self.min_zoom, min(self.max_zoom, new_zoom))

        if center_x is not None and center_y is not None:
            zoom_delta = new_zoom / self.zoom
            self.zoom_at(center_x, center_y, zoom_delta)
        else:
            self.zoom = new_zoom

    def get_visible_rect(self, screen_width, screen_height):
        """
        Get the rectangle of canvas space visible in the viewport

        Args:
            screen_width: Width of the screen area
            screen_height: Height of the screen area

        Returns:
            Tuple of (x, y, width, height) in canvas coordinates
        """
        x, y = self.screen_to_canvas(0, 0)
        width = screen_width / self.zoom
        height = screen_height / self.zoom
        return (x, y, width, height)

    def get_visible_objects(self, all_objects, screen_width, screen_height):
        """
        Get objects that are visible in the current viewport

        Args:
            all_objects: List of all canvas objects
            screen_width: Width of the screen area
            screen_height: Height of the screen area

        Returns:
            List of visible objects
        """
        visible_rect = self.get_visible_rect(screen_width, screen_height)
        vx, vy, vw, vh = visible_rect

        visible = []
        for obj in all_objects:
            # Check if object intersects visible rectangle
            if obj.intersects(vx, vy, vw, vh):
                visible.append(obj)

        return visible
