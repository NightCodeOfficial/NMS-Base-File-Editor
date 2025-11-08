"""
PySide6 NMS-Inspired components
"""

from PySide6.QtWidgets import QPushButton, QWidget, QFrame
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import (
    QPainter, QLinearGradient, QColor, QPen, QBrush, QFont,
    QPainterPath
)
from PySide6.QtWidgets import QGraphicsDropShadowEffect

from .styles import COLORS, FONTS, SPACING, RADIUS


class NMSButton(QPushButton):
    """NMS-inspired button with gradient and shadow"""
    
    def __init__(self, text, gradient_colors=None, parent=None):
        super().__init__(text, parent)
        self.gradient_colors = gradient_colors or COLORS['gradient_cyan_violet']
        self._setup_button()
    
    def _setup_button(self):
        """Setup button styling"""
        self.setMinimumHeight(40)
        self.setFont(QFont(FONTS['button'][0], FONTS['button'][1], QFont.Bold))
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)
        
        # Hover animation
        self._hover_animation = QPropertyAnimation(self, b"geometry")
        self._hover_animation.setDuration(150)
        self._hover_animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def paintEvent(self, event):
        """Custom paint with gradient"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        
        # Create gradient (horizontal for NMS style)
        gradient = QLinearGradient(0, 0, rect.width(), 0)
        color1 = QColor(self.gradient_colors[0])
        color2 = QColor(self.gradient_colors[1])
        
        # Brighten gradient on hover
        if self.underMouse() and self.isEnabled():
            color1 = color1.lighter(110)
            color2 = color2.lighter(110)
        
        gradient.setColorAt(0, color1)
        gradient.setColorAt(1, color2)
        
        # Draw rounded rectangle with gradient
        path = QPainterPath()
        path.addRoundedRect(rect, RADIUS['md'], RADIUS['md'])
        
        if not self.isEnabled():
            # Disabled state
            painter.fillPath(path, QBrush(QColor(COLORS['bg_tertiary'])))
            painter.setPen(QPen(QColor(COLORS['text_muted'])))
        else:
            painter.fillPath(path, QBrush(gradient))
            painter.setPen(QPen(QColor(255, 255, 255, 0)))  # No border
        
        # Draw text
        painter.setPen(QPen(QColor(COLORS['text_primary'])))
        painter.setFont(self.font())
        painter.drawText(rect, Qt.AlignCenter, self.text())
    
    def enterEvent(self, event):
        """Hover effect"""
        if self.isEnabled():
            # Brighten shadow on hover
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(12)
            shadow.setColor(QColor(0, 0, 0, 150))
            shadow.setOffset(0, 4)
            self.setGraphicsEffect(shadow)
            # Trigger repaint to show hover effect
            self.update()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Leave hover"""
        if self.isEnabled():
            # Reset shadow
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(8)
            shadow.setColor(QColor(0, 0, 0, 100))
            shadow.setOffset(0, 3)
            self.setGraphicsEffect(shadow)
            # Trigger repaint
            self.update()
        super().leaveEvent(event)


class NMSPanel(QFrame):
    """NMS-inspired translucent rounded panel"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self._setup_panel()
    
    def _setup_panel(self):
        """Setup panel styling"""
        self.setFrameShape(QFrame.NoFrame)
    
    def paintEvent(self, event):
        """Custom paint with rounded corners and transparency"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        
        # Create semi-transparent background
        bg_color = QColor(COLORS['bg_panel'])
        bg_color.setAlphaF(COLORS['bg_panel_alpha'])
        
        # Draw rounded rectangle
        path = QPainterPath()
        path.addRoundedRect(rect, RADIUS['lg'], RADIUS['lg'])
        
        painter.fillPath(path, QBrush(bg_color))
        
        # Draw border
        pen = QPen(QColor(COLORS['border']))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawPath(path)


class PillToggleButton(QPushButton):
    """Pill-style toggle button with hover effects"""
    
    def __init__(self, text, value, parent=None):
        super().__init__(text, parent)
        self.value = value
        self.setCheckable(True)
        self.setMinimumHeight(36)
        self.setFont(QFont(FONTS['default'][0], FONTS['default'][1]))
        self._is_hovered = False
        self._setup_toggle()
    
    def _setup_toggle(self):
        """Setup toggle styling"""
        # Add shadow for active state
        self._shadow = QGraphicsDropShadowEffect()
        self._shadow.setBlurRadius(4)
        self._shadow.setColor(QColor(0, 0, 0, 80))
        self._shadow.setOffset(0, 2)
    
    def enterEvent(self, event):
        """Hover enter"""
        self._is_hovered = True
        self.update()  # Trigger repaint
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Hover leave"""
        self._is_hovered = False
        self.update()  # Trigger repaint
        super().leaveEvent(event)
    
    def paintEvent(self, event):
        """Custom paint with gradient when active and hover effects"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        path = QPainterPath()
        path.addRoundedRect(rect, RADIUS['pill'], RADIUS['pill'])
        
        if self.isChecked():
            # Active: gradient background
            gradient = QLinearGradient(0, 0, rect.width(), 0)
            color1 = QColor(COLORS['gradient_active'][0])
            color2 = QColor(COLORS['gradient_active'][1])
            # Brighten on hover
            if self._is_hovered:
                color1 = color1.lighter(110)
                color2 = color2.lighter(110)
            gradient.setColorAt(0, color1)
            gradient.setColorAt(1, color2)
            painter.fillPath(path, QBrush(gradient))
            self.setGraphicsEffect(self._shadow)
            text_color = QColor(COLORS['text_primary'])
        else:
            # Inactive: translucent background
            bg_color = QColor(COLORS['bg_panel'])
            if self._is_hovered:
                # Brighten on hover
                bg_color.setAlphaF(0.8)
            else:
                bg_color.setAlphaF(0.6)
            painter.fillPath(path, QBrush(bg_color))
            self.setGraphicsEffect(None)
            
            # Border - highlight on hover
            border_color = COLORS['border_cyan'] if self._is_hovered else COLORS['border']
            pen = QPen(QColor(border_color))
            pen.setWidth(1 if not self._is_hovered else 2)
            painter.setPen(pen)
            painter.drawPath(path)
            
            text_color = QColor(COLORS['text_primary'] if self._is_hovered else COLORS['text_secondary'])
        
        # Draw text
        painter.setPen(QPen(text_color))
        painter.setFont(self.font())
        painter.drawText(rect, Qt.AlignCenter, self.text())

