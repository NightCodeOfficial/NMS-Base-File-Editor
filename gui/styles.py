"""
NMS-Inspired Explorer theme styling
No Man's Sky-inspired sci-fi interface
"""

# Color scheme - NMS Settings Menu style (purple/blue to red/orange gradient)
COLORS = {
    # Background colors - purple/blue to red/orange gradient (like NMS settings)
    'bg_primary': '#1a0f2e',      # Deep purple-blue (top of gradient)
    'bg_primary_end': '#2d1a0f',  # Warm red-orange (bottom of gradient)
    'bg_panel': '#0f0f1a',        # Dark translucent panel color
    'bg_panel_alpha': 0.85,       # Panel opacity (85%)
    'bg_secondary': '#151520',    # Slightly lighter for panels
    'bg_tertiary': '#1a1a28',     # Even lighter
    'bg_hover': '#1f1f2f',        # Hover state
    'bg_selected': '#2a2a3a',     # Selected option background (dark blue-grey)
    
    # NMS Settings Menu accent colors
    'accent_cyan': '#4a9eff',     # Soft blue (like NMS UI)
    'accent_cyan_dark': '#3a7ecc', # Darker blue
    'accent_orange': '#ff8c42',   # Warm orange
    'accent_orange_dark': '#cc6f35', # Darker orange
    'accent_white': '#ffffff',     # Pure white for text
    
    # Gradient combinations for buttons (subtle, matching NMS style)
    'gradient_cyan_violet': ('#4a9eff', '#7a6aff'),  # Soft blue to violet
    'gradient_pink_blue': ('#ff6a9e', '#4a9eff'),   # Pink to blue
    'gradient_active': ('#4a9eff', '#6a8aff'),      # Active toggle gradient (subtle)
    
    # Text colors (NMS settings menu style)
    'text_primary': '#ffffff',     # Primary text (white)
    'text_secondary': '#cccccc',   # Secondary text (light gray)
    'text_muted': '#888888',       # Muted text (gray)
    'text_cyan': '#4a9eff',        # Blue text
    'text_selected': '#ffffff',    # Selected text (white)
    
    # Status colors
    'success': '#4a9eff',          # Success (blue)
    'warning': '#ff8c42',          # Warning (orange)
    'error': '#ff4a4a',            # Error (red)
    'info': '#4a9eff',             # Info (blue)
    
    # Border colors
    'border': '#2a2a3a',           # Default border
    'border_light': '#3a3a4a',     # Light border
    'border_cyan': '#4a9eff',      # Blue border
    'border_focus': '#4a9eff',     # Focus border (blue)
    
    # Selection (NMS settings menu style - dark blue-grey box)
    'selection': '#2a2a3a',        # Selection color (dark blue-grey)
    'selection_hover': '#3a3a4a',  # Selection hover (lighter)
    
    # Glow effects
    'glow_cyan': '#00f5d4',
    'glow_pink': '#ff4ecd',
    'glow_orange': '#ffb86c',
}

# Fonts - Modern sans-serif
FONTS = {
    'default': ('Segoe UI', 11),
    'heading': ('Segoe UI', 18, 'bold'),
    'subheading': ('Segoe UI', 13, 'bold'),
    'monospace': ('Consolas', 11),
    'small': ('Segoe UI', 10),
    'button': ('Segoe UI', 11, 'bold'),
}

# Spacing - NMS-inspired generous spacing
SPACING = {
    'xs': 4,
    'sm': 8,
    'md': 12,
    'lg': 16,
    'xl': 24,
    'xxl': 32,
}

# Border radius - Rounded corners
RADIUS = {
    'sm': 6,
    'md': 10,
    'lg': 12,
    'xl': 15,
    'pill': 20,  # For pill-style buttons
}

# Shadows
SHADOWS = {
    'sm': '0 2px 4px rgba(0, 0, 0, 0.3)',
    'md': '0 4px 8px rgba(0, 0, 0, 0.4)',
    'lg': '0 8px 16px rgba(0, 0, 0, 0.5)',
    'glow_cyan': '0 0 10px rgba(0, 245, 212, 0.5)',
    'glow_pink': '0 0 10px rgba(255, 78, 205, 0.5)',
}
