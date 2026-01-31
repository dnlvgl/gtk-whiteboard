"""
Grid-based spatial index for efficient object queries
"""

import math


class SpatialGrid:
    """
    Grid-based spatial index with configurable cell size.
    Objects are stored in the cells they overlap.
    """

    def __init__(self, cell_size=500):
        self.cell_size = cell_size
        self._cells = {}  # (col, row) -> set of objects
        self._obj_cells = {}  # obj id -> set of (col, row)

    def _get_cells(self, obj):
        """Get all grid cells that an object overlaps"""
        min_col = math.floor(obj.x / self.cell_size)
        min_row = math.floor(obj.y / self.cell_size)
        max_col = math.floor((obj.x + obj.width) / self.cell_size)
        max_row = math.floor((obj.y + obj.height) / self.cell_size)
        cells = set()
        for col in range(min_col, max_col + 1):
            for row in range(min_row, max_row + 1):
                cells.add((col, row))
        return cells

    def insert(self, obj):
        """Insert an object into the index"""
        cells = self._get_cells(obj)
        self._obj_cells[obj.id] = cells
        for cell in cells:
            if cell not in self._cells:
                self._cells[cell] = set()
            self._cells[cell].add(obj)

    def remove(self, obj):
        """Remove an object from the index"""
        cells = self._obj_cells.pop(obj.id, set())
        for cell in cells:
            bucket = self._cells.get(cell)
            if bucket:
                bucket.discard(obj)
                if not bucket:
                    del self._cells[cell]

    def update(self, obj):
        """Update an object's position in the index"""
        self.remove(obj)
        self.insert(obj)

    def query_rect(self, x, y, w, h):
        """Return candidate objects that may intersect the given rectangle"""
        min_col = math.floor(x / self.cell_size)
        min_row = math.floor(y / self.cell_size)
        max_col = math.floor((x + w) / self.cell_size)
        max_row = math.floor((y + h) / self.cell_size)
        result = set()
        for col in range(min_col, max_col + 1):
            for row in range(min_row, max_row + 1):
                bucket = self._cells.get((col, row))
                if bucket:
                    result.update(bucket)
        return result

    def query_point(self, x, y):
        """Return candidate objects that may contain the given point"""
        col = math.floor(x / self.cell_size)
        row = math.floor(y / self.cell_size)
        return set(self._cells.get((col, row), set()))

    def rebuild(self, objects):
        """Rebuild the entire index from a list of objects"""
        self.clear()
        for obj in objects:
            self.insert(obj)

    def clear(self):
        """Clear the index"""
        self._cells.clear()
        self._obj_cells.clear()
