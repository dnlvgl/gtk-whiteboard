# Whiteboard

A native GNOME whiteboard application with infinite canvas support.

## Features

- Infinite canvas with pan and zoom
- Add notes, text, and images
- Move and resize objects
- Native GTK4/libadwaita UI

## Installation

### System Dependencies

**Fedora:**
```bash
sudo dnf install gtk4 libadwaita python3-gobject python3-pillow
```

**Ubuntu/Debian:**
```bash
sudo apt install libgtk-4-dev libadwaita-1-dev python3-gi python3-pil
```

### Python Dependencies

```bash
pip install -r requirements.txt
```

## Running

```bash
python main.py
```

## Development Status

**Phase 1 (Foundation) - COMPLETED ✓**
- [x] Basic application structure
- [x] Infinite canvas with pan and zoom
- [x] Viewport management
- [x] Object creation (notes, text, images)
- [x] Object selection and movement

**Phase 2 (Object Interaction) - COMPLETED ✓**
- [x] Object resizing with drag handles
- [x] Text editing (double-click to edit)
- [x] Delete objects (Delete/Backspace key)
- [x] Duplicate objects (Ctrl+D)
- [x] Z-order control (bring to front / send to back)
- [x] Cursor feedback for interactions

**Phase 3 (File Storage) - COMPLETED ✓**
- [x] SQLite database schema
- [x] .wboard file format (ZIP with SQLite + assets)
- [x] Save boards to file (Ctrl+S)
- [x] Load boards from file (Ctrl+O)
- [x] Image asset management

**Phase 4 (UI Polish) - COMPLETED ✓**
- [x] Color picker dialog for notes
- [x] Right-click context menu
- [x] Save confirmation on quit/new
- [x] Modified state tracking (* in title)
- [x] Enhanced visual feedback

## Usage

### Navigation
- **Pan**: Click and drag on empty canvas
- **Zoom**: Scroll with mouse wheel, or use +/- buttons in toolbar

### Object Creation
- **Add note**: Click + button → Add Note → Choose color
- **Add text**: Click + button → Add Text
- **Add image**: Click + button → Add Image → Select file

### Object Manipulation
- **Select**: Click on an object
- **Move**: Drag a selected object
- **Resize**: Drag the corner handles of a selected object
- **Edit text**: Double-click on a note or text object
- **Delete**: Select object and press Delete or Backspace, or right-click → Delete
- **Duplicate**: Select object and press Ctrl+D, or right-click → Duplicate
- **Z-order**: Menu → Object, or right-click → Bring to Front / Send to Back
- **Context menu**: Right-click on any object for quick actions

### File Operations
- **New board**: Ctrl+N or Menu → New
- **Open board**: Ctrl+O or Menu → Open
- **Save board**: Ctrl+S or Menu → Save
- **Save as**: Menu → Save (when no file is open)

## Project Structure

```
whiteboard/
├── main.py                 # Entry point
├── whiteboard/
│   ├── app.py             # GtkApplication
│   ├── window.py          # Main window
│   └── canvas/
│       ├── canvas_view.py # Canvas widget
│       ├── viewport.py    # Viewport management
│       └── objects.py     # Object base class
```
