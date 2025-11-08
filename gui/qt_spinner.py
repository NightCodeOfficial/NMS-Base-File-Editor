"""
Loading spinner widget for status bar
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QColor, QPen, QBrush

from .styles import COLORS


class LoadingSpinner(QWidget):
    """Animated loading spinner"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(16, 16)
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_angle)
        self.hide()
    
    def _update_angle(self):
        """Update rotation angle"""
        self.angle = (self.angle + 10) % 360
        self.update()
    
    def start(self):
        """Start spinning"""
        self.show()
        self.timer.start(30)  # Update every 30ms
    
    def stop(self):
        """Stop spinning"""
        self.timer.stop()
        self.hide()
    
    def paintEvent(self, event):
        """Draw spinner"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw spinning circle segments
        center_x = self.width() / 2
        center_y = self.height() / 2
        radius = min(self.width(), self.height()) / 2 - 2
        
        # Draw 8 segments with varying opacity
        for i in range(8):
            angle = (self.angle + i * 45) % 360
            opacity = 0.2 + (i / 8) * 0.8
            color = QColor(COLORS['accent_cyan'])
            color.setAlphaF(opacity)
            
            pen = QPen(color)
            pen.setWidth(2)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            
            # Draw arc segment
            start_angle = angle - 20
            span_angle = 40
            
            from PySide6.QtCore import QRectF
            rect = QRectF(2, 2, radius * 2, radius * 2)
            painter.drawArc(rect, int(start_angle * 16), int(span_angle * 16))

