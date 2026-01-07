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
- [ ] File save/load (Phase 3)

## Usage

- **Pan**: Click and drag on empty canvas
- **Zoom**: Scroll with mouse wheel
- **Zoom buttons**: Use +/- buttons in toolbar
- **Select**: Click on an object
- **Move**: Drag a selected object

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
