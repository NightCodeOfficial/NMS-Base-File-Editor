"""
Reusable GUI components with modern styling
"""

import tkinter as tk
from tkinter import ttk
from .styles import COLORS, FONTS, SPACING, RADIUS
from .gradient import GradientFrame, create_gradient_frame

class ModernButton(tk.Button):
    """Modern styled button with hover effects and teal accents"""
    
    def __init__(self, parent, text, command=None, style='primary', **kwargs):
        self.style_type = style
        if style == 'primary':
            self.default_bg = COLORS['accent_blue']
            self.hover_bg = COLORS['accent_teal']
            self.hover_fg = COLORS['text_primary']
        elif style == 'teal':
            self.default_bg = COLORS['accent_teal_dark']
            self.hover_bg = COLORS['accent_teal']
            self.hover_fg = COLORS['text_primary']
        else:
            self.default_bg = COLORS['bg_secondary']
            self.hover_bg = COLORS['bg_hover_teal']
            self.hover_fg = COLORS['text_teal']
        
        self.disabled_bg = COLORS['bg_tertiary']
        
        super().__init__(
            parent,
            text=text,
            command=command,
            bg=self.default_bg,
            fg=COLORS['text_primary'],
            font=FONTS['button'],
            relief='flat',
            bd=0,
            padx=SPACING['lg'] + 4,
            pady=SPACING['md'] + 2,
            cursor='hand2',
            activebackground=self.hover_bg,
            activeforeground=self.hover_fg,
            disabledforeground=COLORS['text_muted'],
            highlightthickness=0,
            **kwargs
        )
        
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        self.bind('<Button-1>', self._on_click)
        self.bind('<ButtonRelease-1>', self._on_release)
    
    def _on_enter(self, event):
        if self['state'] != 'disabled':
            self.config(bg=self.hover_bg, fg=self.hover_fg)
    
    def _on_leave(self, event):
        if self['state'] != 'disabled':
            self.config(bg=self.default_bg, fg=COLORS['text_primary'])
    
    def _on_click(self, event):
        if self['state'] != 'disabled':
            # Slight darken on click
            rgb = tuple(max(0, c - 20) for c in self._hex_to_rgb(self.hover_bg))
            darker = self._rgb_to_hex(rgb)
            self.config(bg=darker)
    
    def _on_release(self, event):
        if self['state'] != 'disabled':
            self.config(bg=self.hover_bg)
    
    def _hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _rgb_to_hex(self, rgb):
        return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))
    
    def set_disabled(self, disabled=True):
        state = 'disabled' if disabled else 'normal'
        self.config(state=state)
        if disabled:
            self.config(bg=self.disabled_bg)
        else:
            self.config(bg=self.default_bg)


class ModernFrame(tk.Frame):
    """Modern styled frame with optional gradient"""
    
    def __init__(self, parent, bg=None, gradient=False, gradient_colors=None, **kwargs):
        if gradient and gradient_colors:
            # Use gradient frame instead
            self._is_gradient = True
            color1, color2 = gradient_colors
            self._gradient_frame = GradientFrame(
                parent,
                color1,
                color2,
                direction=kwargs.pop('gradient_direction', 'vertical'),
                **kwargs
            )
        else:
            self._is_gradient = False
            bg = bg or COLORS['bg_secondary']
            super().__init__(
                parent,
                bg=bg,
                **kwargs
            )
    
    def pack(self, *args, **kwargs):
        if self._is_gradient:
            return self._gradient_frame.pack(*args, **kwargs)
        return super().pack(*args, **kwargs)
    
    def grid(self, *args, **kwargs):
        if self._is_gradient:
            return self._gradient_frame.grid(*args, **kwargs)
        return super().grid(*args, **kwargs)
    
    def place(self, *args, **kwargs):
        if self._is_gradient:
            return self._gradient_frame.place(*args, **kwargs)
        return super().place(*args, **kwargs)
    
    def pack_forget(self):
        if self._is_gradient:
            return self._gradient_frame.pack_forget()
        return super().pack_forget()
    
    def __getattr__(self, name):
        # Delegate to gradient frame if it exists and attribute not found
        if self._is_gradient and hasattr(self._gradient_frame, name):
            return getattr(self._gradient_frame, name)
        # If not gradient or attribute not in gradient frame, raise AttributeError
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


class ModernLabel(tk.Label):
    """Modern styled label"""
    
    def __init__(self, parent, text, style='default', **kwargs):
        font = FONTS.get(style, FONTS['default'])
        fg = kwargs.pop('fg', COLORS['text_primary'])
        bg = kwargs.pop('bg', COLORS['bg_secondary'])
        
        super().__init__(
            parent,
            text=text,
            font=font,
            fg=fg,
            bg=bg,
            **kwargs
        )


class ModernEntry(tk.Entry):
    """Modern styled entry field with teal focus"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary'],
            insertbackground=COLORS['accent_teal'],
            selectbackground=COLORS['selection_teal'],
            selectforeground=COLORS['text_primary'],
            relief='flat',
            bd=0,
            font=FONTS['default'],
            highlightthickness=2,
            highlightbackground=COLORS['border'],
            highlightcolor=COLORS['border_focus_teal'],
            **kwargs
        )
        
        self.bind('<FocusIn>', self._on_focus_in)
        self.bind('<FocusOut>', self._on_focus_out)
    
    def _on_focus_in(self, event):
        self.config(highlightbackground=COLORS['border_focus_teal'])
    
    def _on_focus_out(self, event):
        self.config(highlightbackground=COLORS['border'])


class ModernText(tk.Text):
    """Modern styled text widget with teal cursor"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary'],
            insertbackground=COLORS['accent_teal'],
            selectbackground=COLORS['selection_teal'],
            selectforeground=COLORS['text_primary'],
            relief='flat',
            bd=0,
            font=FONTS['monospace'],
            highlightthickness=2,
            highlightbackground=COLORS['border'],
            highlightcolor=COLORS['border_focus_teal'],
            wrap='none',
            **kwargs
        )
        
        self.bind('<FocusIn>', self._on_focus_in)
        self.bind('<FocusOut>', self._on_focus_out)
    
    def _on_focus_in(self, event):
        self.config(highlightbackground=COLORS['border_focus_teal'])
    
    def _on_focus_out(self, event):
        self.config(highlightbackground=COLORS['border'])


class ModernListbox(tk.Listbox):
    """Modern styled listbox with teal selection highlights"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary'],
            selectbackground=COLORS['selection_teal'],
            selectforeground=COLORS['text_primary'],
            relief='flat',
            bd=0,
            font=FONTS['default'],
            highlightthickness=2,
            highlightbackground=COLORS['border'],
            highlightcolor=COLORS['border_teal'],
            activestyle='none',
            **kwargs
        )
        
        # Bind selection events for better UX
        self.bind('<Button-1>', self._on_click)
        self.bind('<Motion>', self._on_motion)
    
    def _on_click(self, event):
        # Add subtle animation effect
        pass
    
    def _on_motion(self, event):
        # Could add hover effects here
        pass


class StatusBar(tk.Frame):
    """Status bar at bottom left showing current operation with gradient"""
    
    def __init__(self, parent):
        # Use gradient for status bar
        self._gradient_frame = GradientFrame(
            parent,
            COLORS['bg_primary'],
            COLORS['bg_primary_end'],
            direction='horizontal',
            height=32
        )
        self._gradient_frame.pack_propagate(False)
        
        # Add subtle teal accent line at top
        self._accent_line = self._gradient_frame.create_line(
            0, 0, 0, 0, fill=COLORS['accent_teal'], width=2, tags='accent'
        )
        
        self.status_label = tk.Label(
            self._gradient_frame,
            text="Ready",
            bg=COLORS['bg_primary'],
            fg=COLORS['text_secondary'],
            font=FONTS['small'],
            anchor='w',
            padx=SPACING['md']
        )
        self.status_label.pack(side='left', fill='both', expand=True)
        
        self._gradient_frame.bind('<Configure>', self._update_accent_line)
    
    def _update_accent_line(self, event=None):
        """Update the accent line position"""
        width = self._gradient_frame.winfo_width()
        if width > 0:
            self._gradient_frame.coords('accent', 0, 0, width, 0)
    
    def pack(self, *args, **kwargs):
        return self._gradient_frame.pack(*args, **kwargs)
    
    def set_status(self, message, status_type='info'):
        """Update status message with optional color coding"""
        color_map = {
            'info': COLORS.get('text_secondary', '#b8bcc8'),
            'success': COLORS.get('success', '#00f5d4'),
            'warning': COLORS.get('warning', '#ffb86c'),
            'error': COLORS.get('error', '#ff4e6d'),
        }
        # Use cyan for success/info in NMS theme
        if status_type in ['success', 'info']:
            color = COLORS.get('accent_cyan', '#00f5d4')
        else:
            color = color_map.get(status_type, COLORS.get('text_secondary', '#b8bcc8'))
        self.status_label.config(text=message, fg=color)

