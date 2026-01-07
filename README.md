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
- [ ] File save/load (Phase 3)

## Usage

### Navigation
- **Pan**: Click and drag on empty canvas
- **Zoom**: Scroll with mouse wheel, or use +/- buttons in toolbar

### Object Creation
- **Add objects**: Click the + button → choose Note/Text/Image

### Object Manipulation
- **Select**: Click on an object
- **Move**: Drag a selected object
- **Resize**: Drag the corner handles of a selected object
- **Edit text**: Double-click on a note or text object
- **Delete**: Select object and press Delete or Backspace
- **Duplicate**: Select object and press Ctrl+D
- **Z-order**: Menu → Object → Bring to Front / Send to Back

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
