"""
Base editor window for PySide6
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QMessageBox, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from .styles import COLORS, FONTS, SPACING, RADIUS
from .qt_components import NMSButton, NMSPanel
from save_editor import SaveEditor
import json


class EditorWindow(QDialog):
    """Base editor window"""
    
    def __init__(self, parent, save_editor, on_save_callback=None):
        super().__init__(parent)
        self.save_editor = save_editor
        self.on_save_callback = on_save_callback
        self.is_editing = False
        
        self.setWindowTitle("Base Editor")
        self.setGeometry(100, 100, 900, 700)
        
        # Get base data
        self.base_data = self.save_editor.selected_base.copy()
        self.original_json = json.dumps(self.base_data, indent=2, ensure_ascii=False)
        
        self._create_ui()
        self._load_base_data()
    
    def _create_ui(self):
        """Create UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING['lg'])
        layout.setContentsMargins(SPACING['xl'], SPACING['xl'], SPACING['xl'], SPACING['xl'])
        
        # Set background
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {COLORS['bg_primary']}, stop:1 {COLORS['bg_primary_end']});
            }}
        """)
        
        # Header
        header_layout = QHBoxLayout()
        
        base_name = self.base_data.get("Name", "Unknown")
        title = QLabel(f"Editing: {base_name} ◆")
        title.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: {FONTS['heading'][1]}px;
                font-weight: bold;
            }}
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Buttons
        self.copy_btn = NMSButton("📋 Copy", gradient_colors=COLORS['gradient_cyan_violet'])
        self.copy_btn.clicked.connect(self._copy_json)
        header_layout.addWidget(self.copy_btn)
        
        self.edit_btn = NMSButton("✏️ Edit", gradient_colors=COLORS['gradient_cyan_violet'])
        self.edit_btn.clicked.connect(self._toggle_edit)
        header_layout.addWidget(self.edit_btn)
        
        self.save_btn = NMSButton("💾 Save", gradient_colors=COLORS['gradient_cyan_violet'])
        self.save_btn.clicked.connect(self._save_base)
        self.save_btn.setEnabled(False)
        header_layout.addWidget(self.save_btn)
        
        layout.addLayout(header_layout)
        
        # Info panel
        info_panel = NMSPanel()
        info_layout = QVBoxLayout(info_panel)
        info_layout.setContentsMargins(SPACING['md'], SPACING['md'], SPACING['md'], SPACING['md'])
        
        info_text = QLabel(
            "💡 Tip: You can export JSON from djmonkeyuk's base editor using 'Export to NMS' option, "
            "then paste it here after clicking Edit."
        )
        info_text.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_cyan']};
                font-size: {FONTS['small'][1]}px;
            }}
        """)
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_panel)
        
        # JSON editor
        editor_panel = NMSPanel()
        editor_layout = QVBoxLayout(editor_panel)
        editor_layout.setContentsMargins(SPACING['md'], SPACING['md'], SPACING['md'], SPACING['md'])
        
        self.json_text = QTextEdit()
        self.json_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_primary']};
                border: 2px solid {COLORS['border']};
                border-radius: {RADIUS['md']}px;
                font-family: {FONTS['monospace'][0]};
                font-size: {FONTS['monospace'][1]}px;
                padding: 8px;
            }}
            QTextEdit:focus {{
                border-color: {COLORS['border_focus']};
            }}
        """)
        self.json_text.setReadOnly(True)
        editor_layout.addWidget(self.json_text)
        
        layout.addWidget(editor_panel, 1)
        
        # Close button
        close_btn = NMSButton("Close", gradient_colors=COLORS['gradient_cyan_violet'])
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
    
    def _load_base_data(self):
        """Load base data into editor"""
        self.json_text.setPlainText(self.original_json)
    
    def _copy_json(self):
        """Copy JSON to clipboard"""
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.json_text.toPlainText())
        
        # Visual feedback
        original_text = self.copy_btn.text()
        self.copy_btn.setText("✓ Copied!")
        self.copy_btn.setEnabled(False)
        from PySide6.QtCore import QTimer
        QTimer.singleShot(2000, lambda: (
            self.copy_btn.setText(original_text),
            self.copy_btn.setEnabled(True)
        ))
    
    def _toggle_edit(self):
        """Toggle edit mode"""
        if not self.is_editing:
            self.json_text.setReadOnly(False)
            self.edit_btn.setText("🔒 Lock")
            self.save_btn.setEnabled(True)
            self.is_editing = True
        else:
            self.json_text.setReadOnly(True)
            self.edit_btn.setText("✏️ Edit")
            self.save_btn.setEnabled(False)
            self.is_editing = False
    
    def _save_base(self):
        """Save the edited base"""
        if not self.is_editing:
            return
        
        json_str = self.json_text.toPlainText().strip()
        
        try:
            new_base_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Invalid JSON", f"The JSON is invalid:\n{e}")
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Save",
            "Are you sure you want to save this base?\n\n"
            "This will update the base data in memory.\n"
            "You will need to inject it into the save file to make it permanent.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            self.base_data = new_base_data
            self.original_json = json_str
            self.save_editor.selected_base = new_base_data
            self.save_editor.save_selected_base_to_json()
            
            self._load_base_data()
            self._toggle_edit()
            
            if self.on_save_callback:
                self.on_save_callback()
            
            QMessageBox.information(self, "Success", "Base saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save base:\n{e}")

