"""
NMS-Inspired Explorer components
No Man's Sky-style UI components with gradients, glows, and modern styling
"""

import tkinter as tk
from tkinter import ttk
from .styles import COLORS, FONTS, SPACING, RADIUS
from .gradient import GradientFrame, hex_to_rgb, rgb_to_hex, interpolate_color


class NMSButton(tk.Canvas):
    """NMS-inspired button with gradient, shadow, and glow effects"""
    
    def __init__(self, parent, text, command=None, gradient_colors=None, **kwargs):
        self.command = command
        self.text = text
        self.gradient_colors = gradient_colors or COLORS['gradient_cyan_violet']
        self.is_hovered = False
        self.is_pressed = False
        
        # Calculate button size
        temp_label = tk.Label(parent, text=text, font=FONTS['button'])
        temp_label.update()
        text_width = temp_label.winfo_reqwidth()
        text_height = temp_label.winfo_reqheight()
        temp_label.destroy()
        
        width = kwargs.pop('width', text_width + SPACING['xl'] * 2)
        height = kwargs.pop('height', text_height + SPACING['md'] * 2)
        
        super().__init__(
            parent,
            width=width,
            height=height,
            highlightthickness=0,
            **kwargs
        )
        
        self._draw_button()
        
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        self.bind('<Button-1>', self._on_click)
        self.bind('<ButtonRelease-1>', self._on_release)
        self.bind('<Motion>', lambda e: self.config(cursor='hand2'))
    
    def _draw_button(self):
        """Draw the button with gradient and shadow"""
        self.delete('all')
        
        width = self.winfo_width() or int(self.cget('width'))
        height = self.winfo_height() or int(self.cget('height'))
        
        if width <= 1 or height <= 1:
            return
        
        # Shadow offset
        shadow_offset = 3
        shadow_blur = 4
        
        # Draw shadow (multiple layers for soft shadow)
        for i in range(shadow_blur):
            shadow_alpha = 0.2 - (i * 0.05)
            shadow_color = f'#{int(0 * shadow_alpha):02x}{int(0 * shadow_alpha):02x}{int(0 * shadow_alpha):02x}'
            self.create_oval(
                shadow_offset + i, shadow_offset + i,
                width - shadow_offset - i, height - shadow_offset - i,
                fill=shadow_color, outline='', tags='shadow'
            )
        
        # Draw gradient background
        color1, color2 = self.gradient_colors
        for i in range(height):
            factor = i / height
            color = interpolate_color(color1, color2, factor)
            self.create_line(0, i, width, i, fill=color, tags='gradient')
        
        # Add glow effect if hovered
        if self.is_hovered:
            glow_color = COLORS['glow_cyan']
            for i in range(3):
                alpha = 0.3 - (i * 0.1)
                glow_rgb = hex_to_rgb(glow_color)
                glow_alpha = tuple(int(c * alpha) for c in glow_rgb)
                glow_hex = rgb_to_hex(glow_alpha)
                self.create_rectangle(
                    i, i, width - i, height - i,
                    outline=glow_hex, width=1, tags='glow'
                )
        
        # Draw text
        self.create_text(
            width // 2, height // 2,
            text=self.text,
            fill=COLORS['text_primary'],
            font=FONTS['button'],
            tags='text'
        )
        
        # Lower layers
        self.tag_lower('shadow')
        self.tag_lower('gradient')
        if self.is_hovered:
            self.tag_lower('glow')
        self.tag_raise('text')
    
    def _on_enter(self, event):
        self.is_hovered = True
        self._draw_button()
    
    def _on_leave(self, event):
        self.is_hovered = False
        self.is_pressed = False
        self._draw_button()
    
    def _on_click(self, event):
        self.is_pressed = True
        # Brightness shift on click
        self._draw_button()
        if self.command:
            self.after(100, self.command)  # Small delay for visual feedback
    
    def _on_release(self, event):
        self.is_pressed = False
        self._draw_button()
    
    def configure(self, **kwargs):
        """Override configure to handle text changes"""
        if 'text' in kwargs:
            self.text = kwargs.pop('text')
            self._draw_button()
        return super().configure(**kwargs)
    
    def cget(self, key):
        """Override cget for compatibility"""
        if key == 'text':
            return self.text
        return super().cget(key)


class NMSPanel(tk.Canvas):
    """NMS-inspired translucent rounded panel"""
    
    def __init__(self, parent, **kwargs):
        bg = kwargs.pop('bg', COLORS['bg_panel'])
        self.alpha = COLORS['bg_panel_alpha']
        
        super().__init__(
            parent,
            bg=parent.cget('bg') if hasattr(parent, 'cget') else COLORS['bg_primary'],
            highlightthickness=0,
            **kwargs
        )
        
        self.bind('<Configure>', self._draw_panel)
    
    def _draw_panel(self, event=None):
        """Draw rounded translucent panel"""
        self.delete('panel')
        
        width = self.winfo_width()
        height = self.winfo_height()
        
        if width <= 1 or height <= 1:
            return
        
        # Calculate semi-transparent color
        bg_rgb = hex_to_rgb(COLORS['bg_panel'])
        parent_bg = hex_to_rgb(self.cget('bg'))
        
        # Blend with parent background based on alpha
        blended = tuple(
            int(bg_rgb[i] * self.alpha + parent_bg[i] * (1 - self.alpha))
            for i in range(3)
        )
        panel_color = rgb_to_hex(blended)
        
        # Draw rounded rectangle
        radius = RADIUS['lg']
        self.create_rounded_rectangle(
            0, 0, width, height,
            radius=radius,
            fill=panel_color,
            outline=COLORS['border'],
            width=1,
            tags='panel'
        )
        
        self.tag_lower('panel')
    
    def create_rounded_rectangle(self, x1, y1, x2, y2, radius=10, **kwargs):
        """Create a rounded rectangle using arcs and lines"""
        # Create rounded rectangle using create_arc and create_line
        # This is a simplified version - for better results, use create_polygon with calculated points
        fill = kwargs.pop('fill', '')
        outline = kwargs.pop('outline', '')
        width = kwargs.pop('width', 1)
        
        # Draw the rounded rectangle using a polygon approximation
        points = []
        # Top edge
        points.extend([x1 + radius, y1, x2 - radius, y1])
        # Top-right arc
        for i in range(radius + 1):
            angle = (90 - (i * 90 / radius)) * 3.14159 / 180
            points.extend([x2 - radius + radius * (1 - abs(angle - 1.5708) / 1.5708), 
                          y1 + radius - radius * abs(angle - 1.5708) / 1.5708])
        # Right edge
        points.extend([x2, y1 + radius, x2, y2 - radius])
        # Bottom-right arc
        for i in range(radius + 1):
            angle = (0 - (i * 90 / radius)) * 3.14159 / 180
            points.extend([x2 - radius + radius * abs(angle) / 1.5708,
                          y2 - radius + radius * abs(angle) / 1.5708])
        # Bottom edge
        points.extend([x2 - radius, y2, x1 + radius, y2])
        # Bottom-left arc
        for i in range(radius + 1):
            angle = (270 - (i * 90 / radius)) * 3.14159 / 180
            points.extend([x1 + radius - radius * abs(angle - 4.71239) / 1.5708,
                          y2 - radius + radius * abs(angle - 4.71239) / 1.5708])
        # Left edge
        points.extend([x1, y2 - radius, x1, y1 + radius])
        # Top-left arc
        for i in range(radius + 1):
            angle = (180 - (i * 90 / radius)) * 3.14159 / 180
            points.extend([x1 + radius - radius * abs(angle - 3.14159) / 1.5708,
                          y1 + radius - radius * abs(angle - 3.14159) / 1.5708])
        
        # Simplified: use rectangle with rounded corners approximation
        # Draw main rectangle
        if fill:
            self.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=fill, outline='', **kwargs)
            self.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=fill, outline='', **kwargs)
        # Draw corner arcs
        if fill:
            self.create_oval(x1, y1, x1 + radius * 2, y1 + radius * 2, fill=fill, outline='', **kwargs)
            self.create_oval(x2 - radius * 2, y1, x2, y1 + radius * 2, fill=fill, outline='', **kwargs)
            self.create_oval(x1, y2 - radius * 2, x1 + radius * 2, y2, fill=fill, outline='', **kwargs)
            self.create_oval(x2 - radius * 2, y2 - radius * 2, x2, y2, fill=fill, outline='', **kwargs)
        
        # Draw outline
        if outline:
            # Top
            self.create_line(x1 + radius, y1, x2 - radius, y1, fill=outline, width=width, **kwargs)
            # Right
            self.create_line(x2, y1 + radius, x2, y2 - radius, fill=outline, width=width, **kwargs)
            # Bottom
            self.create_line(x2 - radius, y2, x1 + radius, y2, fill=outline, width=width, **kwargs)
            # Left
            self.create_line(x1, y2 - radius, x1, y1 + radius, fill=outline, width=width, **kwargs)
            # Arcs
            self.create_arc(x1, y1, x1 + radius * 2, y1 + radius * 2, start=90, extent=90, 
                          outline=outline, width=width, style='arc', **kwargs)
            self.create_arc(x2 - radius * 2, y1, x2, y1 + radius * 2, start=0, extent=90,
                          outline=outline, width=width, style='arc', **kwargs)
            self.create_arc(x1, y2 - radius * 2, x1 + radius * 2, y2, start=180, extent=90,
                          outline=outline, width=width, style='arc', **kwargs)
            self.create_arc(x2 - radius * 2, y2 - radius * 2, x2, y2, start=270, extent=90,
                          outline=outline, width=width, style='arc', **kwargs)


class PillToggleButton(tk.Canvas):
    """Pill-style toggle button for base type selection"""
    
    def __init__(self, parent, text, variable, value, command=None, **kwargs):
        self.text = text
        self.variable = variable
        self.value = value
        self.command = command
        self.is_active = False
        
        # Calculate size
        temp_label = tk.Label(parent, text=text, font=FONTS['default'])
        temp_label.update()
        text_width = temp_label.winfo_reqwidth()
        text_height = temp_label.winfo_reqheight()
        temp_label.destroy()
        
        width = kwargs.pop('width', text_width + SPACING['xl'])
        height = kwargs.pop('height', text_height + SPACING['sm'])
        
        super().__init__(
            parent,
            width=width,
            height=height,
            highlightthickness=0,
            **kwargs
        )
        
        # Check initial state
        self._check_state()
        self._draw_button()
        
        # Monitor variable changes
        self.variable.trace_add('write', lambda *args: self._check_state())
        
        self.bind('<Button-1>', self._on_click)
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        self.bind('<Motion>', lambda e: self.config(cursor='hand2'))
    
    def _check_state(self):
        """Check if this button should be active"""
        new_state = self.variable.get() == self.value
        if new_state != self.is_active:
            self.is_active = new_state
            self._draw_button()
    
    def _draw_button(self):
        """Draw the pill button"""
        self.delete('all')
        
        width = self.winfo_width() or int(self.cget('width'))
        height = self.winfo_height() or int(self.cget('height'))
        
        if width <= 1 or height <= 1:
            return
        
        radius = RADIUS['pill']
        
        if self.is_active:
            # Active: gradient background
            color1, color2 = COLORS['gradient_active']
            for i in range(height):
                factor = i / height
                color = interpolate_color(color1, color2, factor)
                self.create_line(0, i, width, i, fill=color, tags='bg')
            
            # Add shadow for active state
            shadow_offset = 2
            for i in range(2):
                shadow_alpha = 0.15 - (i * 0.05)
                shadow_color = f'#{int(0 * shadow_alpha):02x}{int(0 * shadow_alpha):02x}{int(0 * shadow_alpha):02x}'
                self.create_oval(
                    shadow_offset + i, shadow_offset + i,
                    width - shadow_offset - i, height - shadow_offset - i,
                    fill=shadow_color, outline='', tags='shadow'
                )
            
            text_color = COLORS['text_primary']
        else:
            # Inactive: dark translucent
            bg_rgb = hex_to_rgb(COLORS['bg_panel'])
            parent_bg = hex_to_rgb(self.master.cget('bg') if hasattr(self.master, 'cget') else COLORS['bg_primary'])
            blended = tuple(
                int(bg_rgb[i] * 0.8 + parent_bg[i] * 0.2)
                for i in range(3)
            )
            panel_color = rgb_to_hex(blended)
            
            self.create_rounded_rectangle(
                0, 0, width, height,
                radius=radius,
                fill=panel_color,
                outline=COLORS['border'],
                width=1,
                tags='bg'
            )
            
            text_color = COLORS['text_secondary']
        
        # Draw text
        self.create_text(
            width // 2, height // 2,
            text=self.text,
            fill=text_color,
            font=FONTS['default'],
            tags='text'
        )
        
        # Layer order
        self.tag_lower('shadow')
        self.tag_lower('bg')
        self.tag_raise('text')
    
    def create_rounded_rectangle(self, x1, y1, x2, y2, radius=10, **kwargs):
        """Create a rounded rectangle using arcs and rectangles"""
        fill = kwargs.pop('fill', '')
        outline = kwargs.pop('outline', '')
        width = kwargs.pop('width', 1)
        
        # Draw main rectangle
        if fill:
            self.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=fill, outline='', **kwargs)
            self.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=fill, outline='', **kwargs)
        # Draw corner arcs
        if fill:
            self.create_oval(x1, y1, x1 + radius * 2, y1 + radius * 2, fill=fill, outline='', **kwargs)
            self.create_oval(x2 - radius * 2, y1, x2, y1 + radius * 2, fill=fill, outline='', **kwargs)
            self.create_oval(x1, y2 - radius * 2, x1 + radius * 2, y2, fill=fill, outline='', **kwargs)
            self.create_oval(x2 - radius * 2, y2 - radius * 2, x2, y2, fill=fill, outline='', **kwargs)
        
        # Draw outline
        if outline:
            # Top
            self.create_line(x1 + radius, y1, x2 - radius, y1, fill=outline, width=width, **kwargs)
            # Right
            self.create_line(x2, y1 + radius, x2, y2 - radius, fill=outline, width=width, **kwargs)
            # Bottom
            self.create_line(x2 - radius, y2, x1 + radius, y2, fill=outline, width=width, **kwargs)
            # Left
            self.create_line(x1, y2 - radius, x1, y1 + radius, fill=outline, width=width, **kwargs)
            # Arcs
            self.create_arc(x1, y1, x1 + radius * 2, y1 + radius * 2, start=90, extent=90, 
                          outline=outline, width=width, style='arc', **kwargs)
            self.create_arc(x2 - radius * 2, y1, x2, y1 + radius * 2, start=0, extent=90,
                          outline=outline, width=width, style='arc', **kwargs)
            self.create_arc(x1, y2 - radius * 2, x1 + radius * 2, y2, start=180, extent=90,
                          outline=outline, width=width, style='arc', **kwargs)
            self.create_arc(x2 - radius * 2, y2 - radius * 2, x2, y2, start=270, extent=90,
                          outline=outline, width=width, style='arc', **kwargs)
    
    def _on_click(self, event):
        if not self.is_active:
            self.variable.set(self.value)
            if self.command:
                self.command()
    
    def _on_enter(self, event):
        if not self.is_active:
            # Slight brightness on hover
            pass
    
    def _on_leave(self, event):
        pass


class NMSLabel(tk.Label):
    """NMS-inspired label with modern typography"""
    
    def __init__(self, parent, text, style='default', **kwargs):
        font = FONTS.get(style, FONTS['default'])
        fg = kwargs.pop('fg', COLORS['text_primary'])
        bg = kwargs.pop('bg', COLORS['bg_primary'])
        
        super().__init__(
            parent,
            text=text,
            font=font,
            fg=fg,
            bg=bg,
            **kwargs
        )

