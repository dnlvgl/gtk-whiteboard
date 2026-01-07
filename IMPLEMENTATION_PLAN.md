# Whiteboard App Implementation Plan

## Overview
A native GNOME whiteboard application with infinite canvas support, built with Python and GTK4. Users can add notes, text, and images, move and resize them freely on an infinite canvas.

## Technology Stack

### Core
- **Language**: Python 3.11+
- **UI Framework**: GTK4 + libadwaita (for GNOME integration)
- **Graphics**: Cairo (via GTK4)
- **Data Storage**: SQLite + ZIP archive

### Key Libraries
- `PyGObject` - GTK4 bindings
- `sqlite3` - Built-in Python database
- `Pillow` - Image loading and manipulation
- `zipfile` - Built-in archive handling

## File Format

### `.wboard` File Structure
A `.wboard` file is a ZIP archive containing:

```
myboard.wboard/
├── board.db          # SQLite database with object metadata
└── assets/
    ├── image1.png
    ├── image2.jpg
    └── ...
```

### SQLite Schema

```sql
-- Metadata table
CREATE TABLE board_metadata (
    key TEXT PRIMARY KEY,
    value TEXT
);

-- Canvas objects table
CREATE TABLE objects (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,  -- 'note', 'text', 'image'
    x REAL NOT NULL,
    y REAL NOT NULL,
    width REAL NOT NULL,
    height REAL NOT NULL,
    z_index INTEGER NOT NULL,
    data TEXT NOT NULL,  -- JSON blob with type-specific data
    created_at INTEGER NOT NULL,
    modified_at INTEGER NOT NULL
);

-- Index for spatial queries
CREATE INDEX idx_objects_position ON objects(x, y);
CREATE INDEX idx_objects_z_index ON objects(z_index);
```

### Object Data JSON Structure

**Note object:**
```json
{
  "text": "My note content",
  "color": "#ffeb3b",
  "font_size": 14
}
```

**Text object:**
```json
{
  "text": "Plain text",
  "font_family": "Sans",
  "font_size": 16,
  "color": "#000000"
}
```

**Image object:**
```json
{
  "asset_path": "assets/image1.png",
  "original_width": 800,
  "original_height": 600
}
```

## Architecture

### Application Structure

```
whiteboard/
├── main.py                 # Application entry point
├── app.py                  # GtkApplication subclass
├── window.py               # Main application window
├── canvas/
│   ├── canvas_view.py      # Main canvas widget (GTK DrawingArea)
│   ├── viewport.py         # Viewport management (pan, zoom)
│   ├── objects.py          # Canvas object base classes
│   └── renderer.py         # Rendering logic with culling
├── objects/
│   ├── note.py             # Note object implementation
│   ├── text.py             # Text object implementation
│   └── image.py            # Image object implementation
├── storage/
│   ├── board_file.py       # .wboard file I/O
│   └── database.py         # SQLite operations
├── ui/
│   ├── toolbar.py          # Top toolbar with tools
│   └── dialogs.py          # File dialogs, etc.
└── resources/
    └── ui/
        └── window.ui       # GTK UI definition (optional)
```

### Core Components

#### 1. CanvasView
- Custom `Gtk.DrawingArea` widget
- Handles infinite canvas rendering
- Mouse/touch input for pan, zoom, selection
- Viewport culling for performance

#### 2. Viewport
- Manages visible area (x, y, zoom)
- Converts screen coordinates ↔ canvas coordinates
- Culling: determines which objects are visible

#### 3. Canvas Objects
Base class hierarchy:
```python
CanvasObject (abstract)
├── NoteObject
├── TextObject
└── ImageObject
```

Each object:
- Has position, size, z-index
- Can render itself via Cairo
- Handles hit testing (for selection)
- Can be serialized to/from JSON

#### 4. Object Manager
- Maintains list of all canvas objects
- Spatial indexing (simple quadtree or grid) for fast queries
- Selection management
- Provides objects in viewport for rendering

#### 5. Board Storage
- Saves/loads .wboard files
- Manages SQLite database
- Handles asset extraction and compression

## Key Features Implementation

### Infinite Canvas
```python
class Viewport:
    def __init__(self):
        self.offset_x = 0
        self.offset_y = 0
        self.zoom = 1.0

    def screen_to_canvas(self, screen_x, screen_y):
        return (
            screen_x / self.zoom + self.offset_x,
            screen_y / self.zoom + self.offset_y
        )

    def get_visible_objects(self, all_objects, screen_width, screen_height):
        # Calculate visible rectangle in canvas coordinates
        x1, y1 = self.screen_to_canvas(0, 0)
        x2, y2 = self.screen_to_canvas(screen_width, screen_height)

        # Return only objects that intersect visible area
        return [obj for obj in all_objects if obj.intersects(x1, y1, x2, y2)]
```

### Object Interaction
- **Click**: Select object
- **Drag**: Move object (or pan canvas if empty space)
- **Handles**: Corner/edge handles for resizing
- **Double-click**: Edit text content

### Rendering Pipeline
```python
def on_draw(self, area, context, width, height):
    # 1. Clear background
    context.set_source_rgb(0.95, 0.95, 0.95)
    context.paint()

    # 2. Apply viewport transformation
    context.scale(self.viewport.zoom, self.viewport.zoom)
    context.translate(-self.viewport.offset_x, -self.viewport.offset_y)

    # 3. Get visible objects (culling)
    visible = self.viewport.get_visible_objects(
        self.objects, width, height
    )

    # 4. Render objects by z-index
    for obj in sorted(visible, key=lambda o: o.z_index):
        obj.render(context)

    # 5. Render selection handles if needed
    if self.selected:
        self.render_selection_handles(context)
```

## UI Design (GNOME/Libadwaita Style)

### Main Window Layout
```
┌────────────────────────────────────────┐
│ ☰  Whiteboard        [+▼] 🔍 [-][+] ⚙ │ ← HeaderBar
├────────────────────────────────────────┤
│                                        │
│                                        │
│         Infinite Canvas                │
│                                        │
│                                        │
└────────────────────────────────────────┘
```

### Toolbar Actions
- **☰**: Application menu (New, Open, Save, Export)
- **[+▼]**: Add dropdown (Note, Text, Image)
- **🔍**: Pan/Select tool toggle
- **[-][+]**: Zoom controls
- **⚙**: Settings

### Context Menu (Right-click on object)
- Edit
- Duplicate
- Bring to Front / Send to Back
- Delete

## Implementation Phases

### Phase 1: Foundation (Core Infrastructure)
1. Set up project structure and dependencies
2. Create GtkApplication and main window with HeaderBar
3. Implement basic CanvasView with DrawingArea
4. Implement Viewport class (pan and zoom)
5. Create CanvasObject base class
6. Implement basic rendering loop with viewport transformation

### Phase 2: Object System
1. Implement NoteObject (colored rectangle with text)
2. Implement TextObject (plain text)
3. Implement ImageObject (with Pillow loading)
4. Implement ObjectManager with simple list storage
5. Add object selection (click to select, show handles)
6. Add object dragging (move objects around)
7. Add object resizing (drag corner handles)

### Phase 3: File Storage
1. Design and create SQLite schema
2. Implement BoardStorage class for save/load
3. Implement .wboard ZIP file format
4. Add asset management for images
5. Wire up File → Save/Open with GTK FileDialog
6. Add autosave functionality

### Phase 4: UI Polish
1. Implement toolbar with all actions
2. Add "Add Note" dialog with color picker
3. Add "Add Text" functionality
4. Add "Add Image" with file picker
5. Implement context menu for objects
6. Add keyboard shortcuts (Ctrl+S, Delete, etc.)
7. Apply libadwaita styling

### Phase 5: Performance & UX
1. Implement spatial indexing (quadtree) for large boards
2. Add undo/redo system (command pattern)
3. Optimize rendering (cache surfaces, dirty rectangles)
4. Add visual feedback (hover states, cursor changes)
5. Implement multi-selection (Ctrl+click, drag rectangle)
6. Add grid/snap option (optional)

### Phase 6: Export & Polish
1. Add export to PNG/PDF
2. Add board thumbnails in file manager
3. Write documentation
4. Package as Flatpak
5. Testing and bug fixes

## Performance Optimizations

### Viewport Culling
Only render objects visible in current viewport:
- Reduces draw calls from O(n) to O(visible)
- Essential for infinite canvas with many objects

### Spatial Indexing
Use quadtree for fast spatial queries:
- O(log n) lookup instead of O(n)
- Matters when board has 1000+ objects

### Surface Caching
Cache rendered objects to Cairo surfaces:
- Redraw only when object changes
- Particularly important for text rendering

### Dirty Rectangle Tracking
Only redraw changed portions:
- Track which objects moved/changed
- Request partial redraws via `queue_draw_area()`

## Testing Strategy

### Unit Tests
- Object serialization/deserialization
- Viewport coordinate transformations
- File format loading/saving
- Spatial indexing accuracy

### Integration Tests
- Create board, add objects, save, reload
- Verify asset extraction
- Test with various image formats

### Manual Testing
- Performance test with 500+ objects
- Test on different GNOME versions
- Accessibility testing

## Future Enhancements (Post-MVP)
- Freehand drawing with pen tool
- Shape tools (rectangles, circles, arrows)
- Collaboration features (conflict-free replicated data types)
- Mobile companion app
- Plugin system
- LaTeX equation support
- PDF import (render as images)

## Dependencies Installation

```bash
# Fedora/RHEL
sudo dnf install gtk4 libadwaita python3-gobject python3-pillow

# Ubuntu/Debian
sudo apt install libgtk-4-dev libadwaita-1-dev python3-gi python3-pil

# Python packages
pip install PyGObject Pillow
```

## Project Timeline Estimate

- **Phase 1**: Foundation - Core canvas and viewport
- **Phase 2**: Object system - Notes, text, images working
- **Phase 3**: File storage - Save/load functionality
- **Phase 4**: UI polish - Complete user interface
- **Phase 5**: Performance - Optimization pass
- **Phase 6**: Export & packaging - Ready for release

## Design Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Language | Python | Rapid development, good GTK bindings, sufficient performance |
| UI Framework | GTK4 + libadwaita | Native GNOME integration, modern design |
| Canvas Type | Infinite | Better UX for brainstorming and ideation |
| File Format | ZIP + SQLite | Easy to read/write, standard formats, extensible |
| Rendering | Cairo via DrawingArea | Hardware-accelerated, standard GTK approach |
| Spatial Index | Quadtree | O(log n) queries for large boards |
| Asset Storage | Embedded in ZIP | Self-contained files, easy sharing |

## Open Questions / Future Decisions

1. **Text editing**: Inline editing vs. dialog?
   - Inline is better UX but more complex to implement
   - Start with dialog, add inline later

2. **Note colors**: Predefined palette vs. full picker?
   - Start with palette (6-8 colors)
   - Matches GNOME design guidelines

3. **Image formats**: Support all PIL formats or limit?
   - Support common formats: PNG, JPEG, GIF, WebP
   - Convert to PNG on import for consistency

4. **Maximum zoom**: What are reasonable limits?
   - Min: 10% (0.1x) for overview
   - Max: 400% (4.0x) for detail work

5. **Undo buffer size**: How many actions to keep?
   - Start with 50 actions
   - Make configurable later
