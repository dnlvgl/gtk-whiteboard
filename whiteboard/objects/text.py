"""
Text object implementation
"""

import json
from whiteboard.canvas.objects import CanvasObject


class TextObject(CanvasObject):
    """
    A plain text object
    """

    def __init__(self, x, y, width=300, height=50, text='', font_size=16):
        super().__init__(x, y, width, height)
        self.text = text
        self.font_size = font_size
        self.font_family = 'Sans'
        self.color = (0, 0, 0)
        self.padding = 5

        # Text wrap cache
        self._wrapped_lines = None
        self._wrap_text = None
        self._wrap_width = None
        self._wrap_font_size = None

    def _invalidate_wrap_cache(self):
        self._wrapped_lines = None

    def render(self, context):
        context.save()

        # Draw background if selected or hovered
        if self.selected:
            context.set_source_rgba(0.9, 0.95, 1.0, 0.3)
            context.rectangle(self.x, self.y, self.width, self.height)
            context.fill()

            context.set_source_rgb(0.2, 0.6, 1.0)
            context.set_line_width(1)
            context.rectangle(self.x, self.y, self.width, self.height)
            context.stroke()
        elif self.hovered:
            context.set_source_rgba(0.2, 0.6, 1.0, 0.08)
            context.rectangle(self.x, self.y, self.width, self.height)
            context.fill()

            context.set_source_rgba(0.2, 0.6, 1.0, 0.4)
            context.set_line_width(1)
            context.rectangle(self.x, self.y, self.width, self.height)
            context.stroke()

        # Draw text
        if self.text:
            context.set_source_rgb(*self.color)
            context.select_font_face(self.font_family, 0, 0)
            context.set_font_size(self.font_size)

            max_width = self.width - 2 * self.padding

            # Use cached wrapped lines if inputs haven't changed
            if (self._wrapped_lines is not None and
                    self._wrap_text == self.text and
                    self._wrap_width == max_width and
                    self._wrap_font_size == self.font_size):
                lines = self._wrapped_lines
            else:
                words = self.text.split()
                lines = []
                current_line = []

                for word in words:
                    test_line = ' '.join(current_line + [word])
                    extents = context.text_extents(test_line)

                    if extents.width <= max_width:
                        current_line.append(word)
                    else:
                        if current_line:
                            lines.append(' '.join(current_line))
                            current_line = [word]
                        else:
                            lines.append(word)

                if current_line:
                    lines.append(' '.join(current_line))

                self._wrapped_lines = lines
                self._wrap_text = self.text
                self._wrap_width = max_width
                self._wrap_font_size = self.font_size

            # Render lines
            y_offset = self.y + self.padding + self.font_size
            for line in lines:
                if y_offset > self.y + self.height - self.padding:
                    break
                context.move_to(self.x + self.padding, y_offset)
                context.show_text(line)
                y_offset += self.font_size * 1.5

        context.restore()

    def get_type(self):
        return 'text'

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.get_type(),
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'z_index': self.z_index,
            'data': json.dumps({
                'text': self.text,
                'font_family': self.font_family,
                'font_size': self.font_size,
                'color': '#{:02x}{:02x}{:02x}'.format(
                    int(self.color[0] * 255),
                    int(self.color[1] * 255),
                    int(self.color[2] * 255)
                )
            })
        }

    @classmethod
    def from_dict(cls, data):
        obj_data = json.loads(data['data'])
        text_obj = cls(
            x=data['x'],
            y=data['y'],
            width=data['width'],
            height=data['height'],
            text=obj_data.get('text', ''),
            font_size=obj_data.get('font_size', 16)
        )
        text_obj.id = data['id']
        text_obj.z_index = data['z_index']
        text_obj.font_family = obj_data.get('font_family', 'Sans')

        # Parse color from hex
        color_hex = obj_data.get('color', '#000000')
        if color_hex.startswith('#'):
            r = int(color_hex[1:3], 16) / 255.0
            g = int(color_hex[3:5], 16) / 255.0
            b = int(color_hex[5:7], 16) / 255.0
            text_obj.color = (r, g, b)

        return text_obj
