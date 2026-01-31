"""
Image object implementation
"""

import json
from whiteboard.canvas.objects import CanvasObject

import gi
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import GdkPixbuf


class ImageObject(CanvasObject):
    """
    An image object that displays a raster image
    """

    def __init__(self, x, y, width=None, height=None, image_path=None):
        """
        Initialize an image object

        Args:
            x: X position
            y: Y position
            width: Image width (None to use original)
            height: Image height (None to use original)
            image_path: Path to image file
        """
        self.image_path = image_path
        self.pixbuf = None
        self.original_width = 0
        self.original_height = 0

        # Load image
        if image_path:
            try:
                self.pixbuf = GdkPixbuf.Pixbuf.new_from_file(image_path)
                self.original_width = self.pixbuf.get_width()
                self.original_height = self.pixbuf.get_height()
            except Exception as e:
                print(f'Error loading image: {e}')

        # Set dimensions
        if width is None:
            width = self.original_width
        if height is None:
            height = self.original_height

        super().__init__(x, y, width, height)

    def render(self, context):
        """
        Render the image using Cairo

        Args:
            context: Cairo context
        """
        if not self.pixbuf:
            # Draw placeholder if image failed to load
            context.save()
            context.set_source_rgb(0.8, 0.8, 0.8)
            context.rectangle(self.x, self.y, self.width, self.height)
            context.fill()

            context.set_source_rgb(0.5, 0.5, 0.5)
            context.set_line_width(2)
            context.rectangle(self.x, self.y, self.width, self.height)
            context.stroke()

            # Draw X
            context.move_to(self.x, self.y)
            context.line_to(self.x + self.width, self.y + self.height)
            context.move_to(self.x + self.width, self.y)
            context.line_to(self.x, self.y + self.height)
            context.stroke()

            context.restore()
            return

        context.save()

        # Scale context to fit image into object bounds
        scale_x = self.width / self.original_width
        scale_y = self.height / self.original_height

        context.translate(self.x, self.y)
        context.scale(scale_x, scale_y)

        # Draw image using Gdk
        from gi.repository import Gdk
        Gdk.cairo_set_source_pixbuf(context, self.pixbuf, 0, 0)
        context.paint()

        context.restore()

        # Draw border if selected or hovered
        if self.selected:
            context.set_source_rgb(0.2, 0.6, 1.0)
            context.set_line_width(2)
            context.rectangle(self.x, self.y, self.width, self.height)
            context.stroke()
        elif self.hovered:
            context.set_source_rgba(0.2, 0.6, 1.0, 0.5)
            context.set_line_width(2)
            context.rectangle(self.x, self.y, self.width, self.height)
            context.stroke()

    def get_type(self):
        """Get object type identifier"""
        return 'image'

    def to_dict(self):
        """Serialize to dictionary"""
        return {
            'id': self.id,
            'type': self.get_type(),
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'z_index': self.z_index,
            'data': json.dumps({
                'asset_path': self.image_path,
                'original_width': self.original_width,
                'original_height': self.original_height
            })
        }

    @classmethod
    def from_dict(cls, data):
        """Deserialize from dictionary"""
        obj_data = json.loads(data['data'])
        image = cls(
            x=data['x'],
            y=data['y'],
            width=data['width'],
            height=data['height'],
            image_path=obj_data.get('asset_path')
        )
        image.id = data['id']
        image.z_index = data['z_index']
        return image
