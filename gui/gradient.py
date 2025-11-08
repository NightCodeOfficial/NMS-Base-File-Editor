"""
Gradient utilities for tkinter
Since tkinter doesn't support native gradients, we use canvas-based solutions
"""

import tkinter as tk


def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    """Convert RGB tuple to hex color"""
    return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))


def interpolate_color(color1, color2, factor):
    """Interpolate between two colors"""
    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)
    r = rgb1[0] + (rgb2[0] - rgb1[0]) * factor
    g = rgb1[1] + (rgb2[1] - rgb1[1]) * factor
    b = rgb1[2] + (rgb2[2] - rgb1[2]) * factor
    return rgb_to_hex((r, g, b))


class GradientFrame(tk.Canvas):
    """Frame with gradient background"""
    
    def __init__(self, parent, color1, color2, direction='vertical', **kwargs):
        # Remove bg from kwargs as we'll handle it
        bg = kwargs.pop('bg', None)
        width = kwargs.pop('width', None)
        height = kwargs.pop('height', None)
        
        super().__init__(parent, highlightthickness=0, **kwargs)
        
        self.color1 = color1
        self.color2 = color2
        self.direction = direction
        
        self.bind('<Configure>', self._draw_gradient)
        
        # Store widgets to be placed on this gradient frame
        self._widgets = []
    
    def _draw_gradient(self, event=None):
        """Draw the gradient"""
        self.delete('gradient')
        
        width = self.winfo_width()
        height = self.winfo_height()
        
        if width <= 1 or height <= 1:
            return
        
        if self.direction == 'vertical':
            # Vertical gradient
            for i in range(height):
                factor = i / height
                color = interpolate_color(self.color1, self.color2, factor)
                self.create_line(0, i, width, i, fill=color, tags='gradient')
        else:
            # Horizontal gradient
            for i in range(width):
                factor = i / width
                color = interpolate_color(self.color1, self.color2, factor)
                self.create_line(i, 0, i, height, fill=color, tags='gradient')
        
        # Lower gradient layer
        self.tag_lower('gradient')
    
    def pack_widget(self, widget, **kwargs):
        """Pack a widget on this gradient frame"""
        self._widgets.append(widget)
        widget.pack(**kwargs)
        self.update_idletasks()
        self._draw_gradient()
    
    def grid_widget(self, widget, **kwargs):
        """Grid a widget on this gradient frame"""
        self._widgets.append(widget)
        widget.grid(**kwargs)
        self.update_idletasks()
        self._draw_gradient()


def create_gradient_frame(parent, color1, color2, direction='vertical', **kwargs):
    """Create a gradient frame"""
    return GradientFrame(parent, color1, color2, direction, **kwargs)

