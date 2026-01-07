# GTK Whiteboard

A native GNOME whiteboard application with infinite canvas support. Basically Miro but local.

Very much not stable and strongly vibed.

![Screenshot](docs/whiteboard-demo-image.png)

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

## Running

```bash
python main.py
```

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
