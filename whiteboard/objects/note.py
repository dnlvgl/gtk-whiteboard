"""
Note object implementation
"""

import json
from whiteboard.canvas.objects import CanvasObject


class NoteObject(CanvasObject):
    """
    A colored sticky note with text
    """

    # Predefined color palette
    COLORS = {
        'yellow': (1.0, 0.92, 0.23),
        'orange': (1.0, 0.6, 0.0),
        'blue': (0.5, 0.7, 1.0),
        'green': (0.5, 0.9, 0.5),
        'purple': (0.7, 0.5, 1.0),
    }

    def __init__(self, x, y, width=200, height=200, text='', color='yellow'):
        super().__init__(x, y, width, height)
        self.text = text
        self.color_name = color
        self.color = self.COLORS.get(color, self.COLORS['yellow'])
        self.font_size = 14
        self.padding = 10

        # Text wrap cache
        self._wrapped_lines = None
        self._wrap_text = None
        self._wrap_width = None
        self._wrap_font_size = None

    def _invalidate_wrap_cache(self):
        self._wrapped_lines = None

    def render(self, context):
        context.save()

        # Shadow
        context.set_source_rgba(0, 0, 0, 0.2)
        context.rectangle(self.x + 3, self.y + 3, self.width, self.height)
        context.fill()

        # Background
        context.set_source_rgb(*self.color)
        context.rectangle(self.x, self.y, self.width, self.height)
        context.fill()

        # Border
        if self.selected:
            context.set_source_rgb(0.2, 0.6, 1.0)
            context.set_line_width(3)
        elif self.hovered:
            context.set_source_rgba(0.2, 0.6, 1.0, 0.5)
            context.set_line_width(2)
        else:
            context.set_source_rgba(*self.color, 0.5)
            context.set_line_width(1)
        context.rectangle(self.x, self.y, self.width, self.height)
        context.stroke()

        # Draw text
        if self.text:
            context.set_source_rgb(0, 0, 0)
            context.select_font_face('Sans', 0, 0)
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
        return 'note'

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
                'color': self.color_name,
                'font_size': self.font_size
            })
        }

    @classmethod
    def from_dict(cls, data):
        obj_data = json.loads(data['data'])
        note = cls(
            x=data['x'],
            y=data['y'],
            width=data['width'],
            height=data['height'],
            text=obj_data.get('text', ''),
            color=obj_data.get('color', 'yellow')
        )
        note.id = data['id']
        note.z_index = data['z_index']
        note.font_size = obj_data.get('font_size', 14)
        return note
