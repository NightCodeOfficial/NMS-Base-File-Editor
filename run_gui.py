#!/usr/bin/env python3
"""
Entry point for the No Man's Sky Save Editor GUI
PySide6 implementation
"""

import sys
from PySide6.QtWidgets import QApplication
from gui.qt_main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

