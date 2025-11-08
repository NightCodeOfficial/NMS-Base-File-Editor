"""
Custom dropdown with visible chevron indicator
"""

from PySide6.QtWidgets import QComboBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPolygonF
from PySide6.QtCore import QPointF

from .styles import COLORS, RADIUS


class DropdownComboBox(QComboBox):
    """ComboBox with custom chevron indicator"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['text_primary']};
                border: 2px solid {COLORS['border']};
                border-radius: {RADIUS['md']}px;
                padding: 8px 32px 8px 8px;
                font-size: 11px;
            }}
            QComboBox:hover {{
                border-color: {COLORS['border_cyan']};
            }}
            QComboBox:focus {{
                border-color: {COLORS['border_focus']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
                background-color: transparent;
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['text_primary']};
                selection-background-color: {COLORS['selection']};
                border: 1px solid {COLORS['border']};
                border-radius: {RADIUS['md']}px;
                padding: 4px;
            }}
        """)
    
    def paintEvent(self, event):
        """Custom paint with chevron indicator"""
        super().paintEvent(event)
        
        # Draw chevron indicator
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Position chevron on the right side
        width = self.width()
        height = self.height()
        chevron_size = 8
        chevron_x = width - 20
        chevron_y = height / 2
        
        # Draw downward triangle (chevron)
        chevron_color = QColor(COLORS['text_secondary'])
        if self.underMouse() or self.hasFocus():
            chevron_color = QColor(COLORS['accent_cyan'])
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(chevron_color))
        
        # Create triangle points
        points = QPolygonF([
            QPointF(chevron_x - chevron_size/2, chevron_y - chevron_size/3),
            QPointF(chevron_x + chevron_size/2, chevron_y - chevron_size/3),
            QPointF(chevron_x, chevron_y + chevron_size/3)
        ])
        
        painter.drawPolygon(points)

