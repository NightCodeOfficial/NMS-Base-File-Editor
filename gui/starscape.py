"""
Starscape texture generator for NMS-inspired background
"""

import random
import tkinter as tk


class StarscapeCanvas(tk.Canvas):
    """Canvas with starscape texture overlay"""
    
    def __init__(self, parent, star_count=100, **kwargs):
        # Get bg from kwargs or use parent's bg or default
        bg = kwargs.pop('bg', None)
        if bg is None or bg == '':
            # Try to get parent's background, or use a default dark color
            try:
                bg = parent.cget('bg') if hasattr(parent, 'cget') else '#0a0e1a'
            except:
                bg = '#0a0e1a'  # Default dark blue
        
        super().__init__(parent, highlightthickness=0, bg=bg, **kwargs)
        self.star_count = star_count
        self.stars = []
        self.bind('<Configure>', self._draw_stars)
        # Draw initial stars after a short delay to ensure canvas is sized
        self.after(100, self._draw_stars)
    
    def _draw_stars(self, event=None):
        """Draw starscape texture"""
        self.delete('stars')
        
        width = self.winfo_width()
        height = self.winfo_height()
        
        if width <= 1 or height <= 1:
            # Retry if canvas not ready
            self.after(50, self._draw_stars)
            return
        
        # Draw stars with varying brightness and occasional cyan tint
        for _ in range(self.star_count):
            x = random.randint(0, width)
            y = random.randint(0, height)
            size = random.choice([1, 1, 1, 2])  # Mostly small stars, occasional larger
            brightness = random.choice([0.4, 0.6, 0.8, 1.0])  # Varying brightness
            
            # Occasionally use cyan tint for some stars
            use_cyan = random.random() < 0.1  # 10% chance
            
            if use_cyan:
                # Cyan-tinted stars
                r = int(0 * brightness)
                g = int(245 * brightness)
                b = int(212 * brightness)
            else:
                # White stars
                r = g = b = int(255 * brightness)
            
            color = f'#{r:02x}{g:02x}{b:02x}'
            
            if size == 1:
                self.create_oval(x, y, x + size, y + size, fill=color, outline='', tags='stars')
            else:
                self.create_oval(x - 1, y - 1, x + size, y + size, fill=color, outline='', tags='stars')
        
        # Lower stars layer
        self.tag_lower('stars')
    
    def regenerate_stars(self):
        """Regenerate starscape"""
        self._draw_stars()

