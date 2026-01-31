"""
Grid overlay and snap-to-grid support
"""

import math


class Grid:
    """
    Grid with configurable size, visibility, and snapping.
    Renders minor and major grid lines, skipping minor lines when too dense.
    """

    def __init__(self):
        self.enabled = False
        self.visible = False
        self.snap_enabled = False
        self.size = 25.0
        self.major_interval = 4

    def snap(self, value):
        """Snap a single value to the nearest grid line"""
        if not self.snap_enabled:
            return value
        return round(value / self.size) * self.size

    def snap_point(self, x, y):
        """Snap a point to the nearest grid intersection"""
        return self.snap(x), self.snap(y)

    def snap_size(self, w, h):
        """Snap a size to grid increments (minimum one grid unit)"""
        if not self.snap_enabled:
            return w, h
        sw = max(self.size, round(w / self.size) * self.size)
        sh = max(self.size, round(h / self.size) * self.size)
        return sw, sh

    def render(self, context, vx, vy, vw, vh, zoom):
        """
        Render grid lines for the visible viewport area.

        Args:
            context: Cairo context (already transformed to canvas space)
            vx, vy, vw, vh: Visible rectangle in canvas coordinates
            zoom: Current zoom level
        """
        if not self.visible:
            return

        # Screen-space pixel size of one grid cell
        cell_screen = self.size * zoom
        # Skip minor lines if they would be smaller than 8 pixels
        draw_minor = cell_screen >= 8

        major_size = self.size * self.major_interval

        # Compute range of lines
        start_x = math.floor(vx / self.size) * self.size
        end_x = math.ceil((vx + vw) / self.size) * self.size
        start_y = math.floor(vy / self.size) * self.size
        end_y = math.ceil((vy + vh) / self.size) * self.size

        context.save()

        # Draw minor lines
        if draw_minor:
            context.set_source_rgba(0.0, 0.0, 0.0, 0.08)
            context.set_line_width(0.5)
            x = start_x
            while x <= end_x:
                # Skip if this is a major line
                if abs(x % major_size) > 0.01:
                    context.move_to(x, start_y)
                    context.line_to(x, end_y)
                x += self.size
            y = start_y
            while y <= end_y:
                if abs(y % major_size) > 0.01:
                    context.move_to(start_x, y)
                    context.line_to(end_x, y)
                y += self.size
            context.stroke()

        # Draw major lines
        context.set_source_rgba(0.0, 0.0, 0.0, 0.15)
        context.set_line_width(1.0)
        major_start_x = math.floor(vx / major_size) * major_size
        major_end_x = math.ceil((vx + vw) / major_size) * major_size
        major_start_y = math.floor(vy / major_size) * major_size
        major_end_y = math.ceil((vy + vh) / major_size) * major_size

        x = major_start_x
        while x <= major_end_x:
            context.move_to(x, start_y)
            context.line_to(x, end_y)
            x += major_size
        y = major_start_y
        while y <= major_end_y:
            context.move_to(start_x, y)
            context.line_to(end_x, y)
            y += major_size
        context.stroke()

        context.restore()
