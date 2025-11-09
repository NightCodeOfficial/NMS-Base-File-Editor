"""
Main application window for the No Man's Sky Save Editor GUI
PySide6 implementation with NMS-Inspired Explorer theme
"""

import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QListWidget, QMessageBox,
    QFrame, QScrollArea
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QRect, QTimer
from PySide6.QtGui import (
    QPainter, QLinearGradient, QColor, QPen, QBrush, QFont,
    QPainterPath, QRadialGradient
)
from PySide6.QtWidgets import QGraphicsDropShadowEffect

from .styles import COLORS, FONTS, SPACING, RADIUS
from .qt_components import NMSButton, NMSPanel, PillToggleButton
from .qt_dropdown import DropdownComboBox
from .qt_editor_window import EditorWindow
from .qt_worker import DecompressWorker, InjectWorker, CountComponentsWorker
from .qt_spinner import LoadingSpinner
from save_editor import SaveEditor


class StarscapeWidget(QWidget):
    """Widget with starscape background effect"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.star_count = 150
        self.stars = []
        self._generate_stars()
    
    def _generate_stars(self):
        """Generate star positions"""
        import random
        self.stars = []
        for _ in range(self.star_count):
            self.stars.append({
                'x': random.random(),
                'y': random.random(),
                'size': random.choice([1, 1, 1, 2]),
                'brightness': random.choice([0.4, 0.6, 0.8, 1.0]),
                'cyan': random.random() < 0.1
            })
    
    def paintEvent(self, event):
        """Paint starscape"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        for star in self.stars:
            x = star['x'] * width
            y = star['y'] * height
            size = star['size']
            brightness = star['brightness']
            
            if star['cyan']:
                color = QColor(0, int(245 * brightness), int(212 * brightness))
            else:
                gray = int(255 * brightness)
                color = QColor(gray, gray, gray)
            
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(x), int(y), size, size)


class GradientWidget(QWidget):
    """Widget with gradient background"""
    
    def __init__(self, color1, color2, direction='vertical', parent=None):
        super().__init__(parent)
        self.color1 = QColor(color1)
        self.color2 = QColor(color2)
        self.direction = direction
    
    def paintEvent(self, event):
        """Paint gradient"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if self.direction == 'vertical':
            gradient = QLinearGradient(0, 0, 0, self.height())
        else:
            gradient = QLinearGradient(0, 0, self.width(), 0)
        
        gradient.setColorAt(0, self.color1)
        gradient.setColorAt(1, self.color2)
        
        painter.fillRect(self.rect(), QBrush(gradient))


class MainWindow(QMainWindow):
    """Main application window with NMS-inspired design"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("No Man's Sky Save Editor")
        self.setGeometry(100, 100, 1000, 700)
        
        # Initialize SaveEditor
        self.save_editor = SaveEditor()
        
        # State variables
        self.selected_base_index = None
        self.filtered_bases = []
        self.current_base_type_filter = None
        self.worker = None  # Background worker thread
        self.inject_worker = None  # Background worker for injection
        self.count_worker = None  # Background worker for counting components
        
        # Load save files
        try:
            self.save_editor.load_save_files()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load save files: {e}")
        
        self._create_ui()
        self._update_save_file_dropdown()
        self._update_status("Ready")
    
    def _create_ui(self):
        """Create the UI"""
        # Central widget with gradient background
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Background gradient
        bg_gradient = GradientWidget(
            COLORS['bg_primary'],
            COLORS['bg_primary_end'],
            'vertical'
        )
        bg_layout = QVBoxLayout(central_widget)
        bg_layout.setContentsMargins(0, 0, 0, 0)
        bg_layout.addWidget(bg_gradient)
        
        # Starscape overlay (will be positioned over gradient)
        self.starscape = StarscapeWidget(bg_gradient)
        self.starscape.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        # Main content layout
        main_layout = QVBoxLayout(bg_gradient)
        main_layout.setSpacing(SPACING['xl'])
        main_layout.setContentsMargins(SPACING['xxl'], SPACING['xxl'], SPACING['xxl'], SPACING['xxl'])
        
        # Header
        self._create_header(main_layout)
        
        # Main content panel
        content_panel = NMSPanel()
        main_layout.addWidget(content_panel)
        
        content_layout = QVBoxLayout(content_panel)
        content_layout.setSpacing(SPACING['xl'])
        content_layout.setContentsMargins(SPACING['xl'], SPACING['xl'], SPACING['xl'], SPACING['xl'])
        
        # File selection section
        self._create_file_section(content_layout)
        
        # Action buttons
        self._create_action_buttons(content_layout)
        
        # Separator before base type section (always visible)
        separator_before_base = QFrame()
        separator_before_base.setFrameShape(QFrame.HLine)
        separator_before_base.setFrameShadow(QFrame.Sunken)
        separator_before_base.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['border']};
                max-height: 1px;
            }}
        """)
        content_layout.addWidget(separator_before_base)
        
        # Base type selection (hidden initially)
        self._create_base_type_section(content_layout)
        
        # Bases list (hidden initially)
        self._create_bases_section(content_layout)
        
        # Status bar
        self._create_status_bar()
        
        # Position starscape after layout is done
        self.starscape.raise_()
        self.starscape.setGeometry(bg_gradient.rect())
        
        # Update starscape on resize
        bg_gradient.resizeEvent = lambda e: self.starscape.setGeometry(bg_gradient.rect())
    
    def _create_header(self, parent_layout):
        """Create header with diamond icon"""
        header_layout = QHBoxLayout()
        header_layout.setSpacing(SPACING['md'])
        
        # Diamond icon
        diamond_label = QLabel("◆")
        diamond_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['accent_cyan']};
                font-size: 24px;
                font-weight: bold;
            }}
        """)
        header_layout.addWidget(diamond_label)
        
        # Title
        title_label = QLabel("No Man's Sky Save Editor")
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: {FONTS['heading'][1]}px;
                font-weight: bold;
            }}
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        parent_layout.addLayout(header_layout)
    
    def _create_file_section(self, parent_layout):
        """Create save file selection section"""
        section_layout = QVBoxLayout()
        section_layout.setSpacing(SPACING['md'])
        
        # Section title
        title = QLabel("Select save file")
        title.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: {FONTS['subheading'][1]}px;
                font-weight: bold;
            }}
        """)
        section_layout.addWidget(title)
        
        # Horizontal separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['border']};
                max-height: 1px;
            }}
        """)
        section_layout.addWidget(separator)
        
        # Dropdown and button
        file_layout = QHBoxLayout()
        file_layout.setSpacing(SPACING['md'])
        
        # Dropdown in panel
        dropdown_panel = NMSPanel()
        dropdown_layout = QHBoxLayout(dropdown_panel)
        dropdown_layout.setContentsMargins(SPACING['md'], SPACING['sm'], SPACING['md'], SPACING['sm'])
        
        self.save_file_dropdown = DropdownComboBox()
        dropdown_layout.addWidget(self.save_file_dropdown)
        
        file_layout.addWidget(dropdown_panel, 1)
        
        # Load button
        self.load_file_btn = NMSButton("Load File", gradient_colors=COLORS['gradient_cyan_violet'])
        self.load_file_btn.clicked.connect(self._load_save_file)
        file_layout.addWidget(self.load_file_btn)
        
        section_layout.addLayout(file_layout)
        parent_layout.addLayout(section_layout)
    
    def _create_action_buttons(self, parent_layout):
        """Create action buttons"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(SPACING['md'])
        
        self.edit_base_btn = NMSButton("Edit Selected Base", gradient_colors=COLORS['gradient_cyan_violet'])
        self.edit_base_btn.clicked.connect(self._open_editor)
        self.edit_base_btn.setEnabled(False)
        button_layout.addWidget(self.edit_base_btn)
        
        self.inject_base_btn = NMSButton("Inject Base into Save File", gradient_colors=COLORS['gradient_cyan_violet'])
        self.inject_base_btn.clicked.connect(self._inject_base)
        self.inject_base_btn.setEnabled(False)
        button_layout.addWidget(self.inject_base_btn)
        
        # Add count components button
        self.count_components_btn = NMSButton("Count All Components", gradient_colors=COLORS['gradient_cyan_violet'])
        self.count_components_btn.clicked.connect(self._count_components)
        self.count_components_btn.setEnabled(False)
        button_layout.addWidget(self.count_components_btn)
        
        parent_layout.addLayout(button_layout)
    
    def _create_base_type_section(self, parent_layout):
        """Create base type selection section - simplified"""
        self.base_type_section = QVBoxLayout()
        self.base_type_section.setSpacing(SPACING['md'])
        
        # Section title
        title = QLabel("Select Base")
        title.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: {FONTS['subheading'][1]}px;
                font-weight: bold;
            }}
        """)
        self.base_type_section.addWidget(title)
        
        # Simple button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(SPACING['md'])
        
        self.base_type_var = "both"
        
        # Create simple push buttons - all use same gradient, no special active state
        self.corvette_btn = NMSButton("Corvettes", gradient_colors=COLORS['gradient_cyan_violet'])
        self.corvette_btn.clicked.connect(lambda: self._set_base_type("PlayerShipBase"))
        button_layout.addWidget(self.corvette_btn)
        
        self.planetary_btn = NMSButton("Planetary Bases", gradient_colors=COLORS['gradient_cyan_violet'])
        self.planetary_btn.clicked.connect(lambda: self._set_base_type("ExternalPlanetBase"))
        button_layout.addWidget(self.planetary_btn)
        
        self.both_btn = NMSButton("Both", gradient_colors=COLORS['gradient_cyan_violet'])
        self.both_btn.clicked.connect(lambda: self._set_base_type("both"))
        button_layout.addWidget(self.both_btn)
        
        self.base_type_section.addLayout(button_layout)
        
        # Horizontal separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['border']};
                max-height: 1px;
            }}
        """)
        self.base_type_section.addWidget(separator)
        
        parent_layout.addLayout(self.base_type_section)
        
        # Hide section initially
        for i in range(self.base_type_section.count()):
            item = self.base_type_section.itemAt(i)
            if item.widget():
                item.widget().hide()
            elif item.layout():
                for j in range(item.layout().count()):
                    widget = item.layout().itemAt(j).widget()
                    if widget:
                        widget.setEnabled(False)
    
    def _create_bases_section(self, parent_layout):
        """Create bases list section"""
        self.bases_section = QVBoxLayout()
        self.bases_section.setSpacing(SPACING['md'])
        
        # Section title
        title_layout = QHBoxLayout()
        title_layout.setSpacing(SPACING['sm'])
        
        title = QLabel("SELECT BASE")
        title.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: {FONTS['subheading'][1]}px;
                font-weight: bold;
                letter-spacing: 1px;
            }}
        """)
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        self.bases_section.addLayout(title_layout)
        
        # List in panel
        list_panel = NMSPanel()
        list_layout = QVBoxLayout(list_panel)
        list_layout.setContentsMargins(SPACING['md'], SPACING['md'], SPACING['md'], SPACING['md'])
        
        self.bases_listbox = QListWidget()
        self.bases_listbox.setStyleSheet(f"""
            QListWidget {{
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_primary']};
                border: 2px solid {COLORS['border']};
                border-radius: {RADIUS['md']}px;
                font-size: {FONTS['default'][1]}px;
            }}
            QListWidget::item {{
                padding: 8px;
                border-radius: {RADIUS['sm']}px;
            }}
            QListWidget::item:selected {{
                background-color: {COLORS['selection']};
                color: {COLORS['text_primary']};
            }}
            QListWidget::item:hover {{
                background-color: {COLORS['bg_hover']};
            }}
        """)
        self.bases_listbox.itemClicked.connect(self._on_base_clicked)
        list_layout.addWidget(self.bases_listbox)
        
        self.bases_section.addWidget(list_panel, 1)
        parent_layout.addLayout(self.bases_section, 1)
        # Hide section initially
        for i in range(self.bases_section.count()):
            item = self.bases_section.itemAt(i)
            if item.widget():
                item.widget().hide()
    
    def _create_status_bar(self):
        """Create status bar with loading spinner"""
        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {COLORS['bg_primary']};
                color: {COLORS['text_secondary']};
                border-top: 1px solid {COLORS['border']};
                font-size: {FONTS['small'][1]}px;
                padding: 4px;
            }}
        """)
        
        # Add loading spinner to status bar
        self.loading_spinner = LoadingSpinner()
        self.status_bar.addPermanentWidget(self.loading_spinner)
        
        self.status_bar.showMessage("Ready")
    
    def _update_save_file_dropdown(self):
        """Update save file dropdown"""
        if not self.save_editor.save_files:
            return
        
        sorted_files = sorted(
            self.save_editor.save_files,
            key=lambda x: self.save_editor.get_save_file_metadata(x).get('last_saved', ''),
            reverse=True
        )
        
        self.save_file_dropdown.clear()
        for save_file in sorted_files:
            metadata = self.save_editor.get_save_file_metadata(save_file)
            last_saved = metadata.get('last_saved', 'Unknown')
            self.save_file_dropdown.addItem(f"{save_file} - {last_saved}")
    
    def _load_save_file(self):
        """Load and decompress save file in background thread"""
        selection = self.save_file_dropdown.currentText()
        if not selection:
            QMessageBox.warning(self, "Warning", "Please select a save file first.")
            return
        
        save_file_name = selection.split(' - ')[0]
        
        # Disable buttons during loading
        self.load_file_btn.setEnabled(False)
        if hasattr(self, 'count_components_btn'):
            self.count_components_btn.setEnabled(False)
        self.loading_spinner.start()  # Start spinner
        self._update_status(f"Loading {save_file_name}...")
        
        # Create and start worker thread
        self.worker = DecompressWorker(self.save_editor, save_file_name)
        self.worker.progress.connect(self._update_status)
        self.worker.finished.connect(self._on_decompress_finished)
        self.worker.start()
    
    def _on_decompress_finished(self, success, message):
        """Handle decompression completion"""
        self.load_file_btn.setEnabled(True)
        self.loading_spinner.stop()  # Stop spinner
        
        if success:
            # Show base type section
            for i in range(self.base_type_section.count()):
                item = self.base_type_section.itemAt(i)
                if item.widget():
                    item.widget().show()
                elif item.layout():
                    for j in range(item.layout().count()):
                        widget = item.layout().itemAt(j).widget()
                        if widget:
                            widget.setEnabled(True)
            
            # Enable buttons that require loaded bases
            if hasattr(self, 'count_components_btn'):
                self.count_components_btn.setEnabled(True)
            
            self._update_status(message, 'success')
        else:
            QMessageBox.critical(self, "Error", f"Failed to load save file:\n{message}")
            self._update_status(f"Error: {message}", 'error')
        
        self.worker = None
    
    def _set_base_type(self, base_type):
        """Set base type filter - simplified"""
        self.base_type_var = base_type
        
        # No need to update button styles - they all look the same
        # Filter and display bases
        self._filter_and_display_bases(base_type)
    
    def _filter_and_display_bases(self, base_type):
        """Filter bases and display in list - simplified"""
        try:
            # Check if bases are loaded
            if not hasattr(self.save_editor, 'all_bases') or not self.save_editor.all_bases:
                return
            
            # Filter bases
            if base_type == "both":
                self.filtered_bases = list(self.save_editor.all_bases)
            else:
                self.filtered_bases = []
                for base in self.save_editor.all_bases:
                    if isinstance(base, dict):
                        base_type_obj = base.get("BaseType", {})
                        if isinstance(base_type_obj, dict):
                            if base_type_obj.get("PersistentBaseTypes") == base_type:
                                self.filtered_bases.append(base)
            
            # Update list
            self._populate_bases_list()
            
            # Show section
            for i in range(self.bases_section.count()):
                item = self.bases_section.itemAt(i)
                if item.widget():
                    item.widget().show()
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to filter bases:\n{e}")
            import traceback
            traceback.print_exc()
    
    def _populate_bases_list(self):
        """Populate bases list - simplified"""
        if not hasattr(self, 'bases_listbox') or self.bases_listbox is None:
            return
        
        # Clear list
        self.bases_listbox.clear()
        
        if not self.filtered_bases:
            return
        
        # Get save file name for fallback
        save_file_name = "save file"
        if hasattr(self.save_editor, 'selected_save_file') and self.save_editor.selected_save_file:
            save_file_name = self.save_editor.selected_save_file.replace('.hg', '')
        elif hasattr(self, 'save_file_dropdown') and self.save_file_dropdown.currentText():
            save_file_name = self.save_file_dropdown.currentText().split(' - ')[0].replace('.hg', '')
        
        # Add items
        for i, base in enumerate(self.filtered_bases):
            if not isinstance(base, dict):
                continue
            
            # Get name
            name = base.get("Name") or ""
            if not name:
                base_type_obj = base.get("BaseType", {})
                persistent_type = base_type_obj.get("PersistentBaseTypes", "") if isinstance(base_type_obj, dict) else ""
                if persistent_type == "PlayerShipBase":
                    name = f"Unnamed Corvette {i + 1} from {save_file_name}"
                else:
                    name = f"Unnamed Base {i + 1} from {save_file_name}"
            
            # Get base type
            base_type_obj = base.get("BaseType", {})
            base_type = base_type_obj.get("PersistentBaseTypes", "Unknown") if isinstance(base_type_obj, dict) else "Unknown"
            
            # Get owner
            owner_obj = base.get("Owner", {})
            owner_usn = owner_obj.get("USN", "Unknown") if isinstance(owner_obj, dict) else "Unknown"
            if not owner_usn:
                owner_usn = "Unknown"
            
            # Add item
            item_text = f"{name} | {base_type} | Owner: {owner_usn}"
            
            # Replace "Default" with descriptive name based on base type
            if item_text.startswith("Default |"):
                if base_type == "PlayerShipBase":
                    item_text = item_text.replace("Default |", f"Corvette Base {i + 1} |", 1)
                elif base_type == "ExternalPlanetBase":
                    item_text = item_text.replace("Default |", f"Planetary Base {i + 1} |", 1)
                else:
                    item_text = item_text.replace("Default |", f"Base {i + 1} |", 1)
            
            self.bases_listbox.addItem(item_text)
    
    def _on_base_clicked(self, item):
        """Handle base selection - simplified"""
        try:
            index = self.bases_listbox.row(item)
            if index < 0 or index >= len(self.filtered_bases):
                return
            
            self.selected_base_index = index
            selected_base = self.filtered_bases[index]
            
            # Store selected base
            self.save_editor.selected_base = selected_base
            self.save_editor.selected_base_index = index
            
            # Get name for display
            base_name = selected_base.get("Name") or f"Base {index + 1}"
            
            # Enable buttons
            if hasattr(self, 'edit_base_btn'):
                self.edit_base_btn.setEnabled(True)
            if hasattr(self, 'inject_base_btn'):
                self.inject_base_btn.setEnabled(False)
            
            self._update_status(f"Selected: {base_name}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to select base:\n{e}")
    
    def _open_editor(self):
        """Open base editor window"""
        if self.save_editor.selected_base is None:
            QMessageBox.warning(self, "Warning", "Please select a base first.")
            return
        
        editor = EditorWindow(self, self.save_editor, self._on_base_saved)
        editor.exec()
    
    def _on_base_saved(self):
        """Callback when base is saved"""
        if self.selected_base_index is not None and self.selected_base_index < len(self.filtered_bases):
            self.filtered_bases[self.selected_base_index] = self.save_editor.selected_base
            self._populate_bases_list()  # Refresh the list display
        
        self.inject_base_btn.setEnabled(True)
        self._update_status("Base saved. Ready to inject into save file.", 'success')
    
    def _inject_base(self):
        """Inject base into save file in background thread"""
        if self.save_editor.selected_base is None:
            QMessageBox.warning(self, "Warning", "No base selected.")
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Injection",
            "This will inject the base into the save file and replace the original .hg file.\n\n"
            "A backup will be created before replacement.\n\n"
            "Are you sure you want to continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Disable button and start spinner
        self.inject_base_btn.setEnabled(False)
        self.loading_spinner.start()
        self._update_status("Injecting base into save file...")
        
        # Create and start worker thread
        self.inject_worker = InjectWorker(self.save_editor)
        self.inject_worker.progress.connect(self._update_status)
        self.inject_worker.finished.connect(self._on_inject_finished)
        self.inject_worker.start()
    
    def _on_inject_finished(self, success, message):
        """Handle injection completion"""
        self.loading_spinner.stop()
        self.inject_base_btn.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "Success", message)
            self._update_status("Base injected successfully!", 'success')
            self.inject_base_btn.setEnabled(False)
        else:
            QMessageBox.critical(self, "Error", f"Failed to inject base:\n{message}")
            self._update_status(f"Error: {message}", 'error')
        
        self.inject_worker = None
    
    def _count_components(self):
        """Count components in all bases"""
        if self.save_editor.selected_save_file_dict is None:
            QMessageBox.warning(self, "Warning", "No save file loaded. Please load a save file first.")
            return
        
        if not self.save_editor.all_bases:
            QMessageBox.warning(self, "Warning", "No bases loaded. Please load bases first.")
            return
        
        # Disable button and start spinner
        self.count_components_btn.setEnabled(False)
        self.loading_spinner.start()
        self._update_status("Counting base parts...")
        
        # Create and start worker thread
        self.count_worker = CountComponentsWorker(self.save_editor)
        self.count_worker.progress.connect(self._update_status)
        self.count_worker.finished.connect(self._on_count_finished)
        self.count_worker.start()
    
    def _on_count_finished(self, success, count, message):
        """Handle component counting completion"""
        self.loading_spinner.stop()
        self.count_components_btn.setEnabled(True)
        
        if success:
            QMessageBox.information(
                self, 
                "Component Count", 
                f"Total number of components in all bases:\n\n{count:,}\n\n"
                f"This includes all objects from all bases in the save file."
            )
            self._update_status(f"Counted {count:,} components", 'success')
        else:
            QMessageBox.critical(self, "Error", f"Failed to count components:\n{message}")
            self._update_status(f"Error: {message}", 'error')
        
        self.count_worker = None
    
    def _update_status(self, message, status_type='info'):
        """Update status bar"""
        if status_type in ['success', 'info']:
            color = COLORS['accent_cyan']
        elif status_type == 'warning':
            color = COLORS['warning']
        elif status_type == 'error':
            color = COLORS['error']
        else:
            color = COLORS['text_secondary']
        
        self.status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {COLORS['bg_primary']};
                color: {color};
                border-top: 1px solid {COLORS['border']};
                font-size: {FONTS['small'][1]}px;
                padding: 4px;
            }}
        """)
        self.status_bar.showMessage(message)

