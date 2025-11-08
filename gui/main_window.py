"""
Main application window for the No Man's Sky Save Editor GUI
NMS-Inspired Explorer theme
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from pathlib import Path
from datetime import datetime

from .styles import COLORS, FONTS, SPACING, RADIUS
from .gradient import GradientFrame
from .starscape import StarscapeCanvas
from .nms_components import NMSButton, NMSPanel, PillToggleButton, NMSLabel
from .components import ModernListbox, StatusBar
from .editor_window import EditorWindow
from save_editor import SaveEditor


class MainWindow:
    """Main application window with NMS-inspired design"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("No Man's Sky Save Editor")
        self.root.geometry("1000x700")
        
        # Create background with gradient and starscape
        self._create_background()
        
        # Initialize SaveEditor
        self.save_editor = SaveEditor()
        
        # State variables
        self.selected_base_index = None
        self.filtered_bases = []
        self.current_base_type_filter = None
        
        # Load save files
        try:
            self.save_editor.load_save_files()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load save files: {e}")
        
        self._create_widgets()
        self._update_save_file_dropdown()
        self._update_status("Ready")
    
    def _create_background(self):
        """Create gradient background with starscape"""
        # Main gradient background
        self._root_gradient = GradientFrame(
            self.root,
            COLORS['bg_primary'],
            COLORS['bg_primary_end'],
            direction='vertical'
        )
        self._root_gradient.pack(fill='both', expand=True)
        
        # Starscape overlay (uses gradient background, stars drawn on top)
        self._starscape = StarscapeCanvas(
            self._root_gradient,
            star_count=150
            # bg will default to parent's background (gradient)
        )
        self._starscape.pack(fill='both', expand=True)
    
    def _create_widgets(self):
        """Create all GUI widgets"""
        # Main container
        main_container = tk.Frame(self._starscape, bg='')
        main_container.pack(fill='both', expand=True, padx=SPACING['xxl'], pady=SPACING['xxl'])
        
        # Header with glowing diamond icon
        header_frame = tk.Frame(main_container, bg='')
        header_frame.pack(fill='x', pady=(0, SPACING['xl']))
        
        # Glowing diamond icon
        diamond_canvas = tk.Canvas(
            header_frame,
            width=32,
            height=32,
            bg='',
            highlightthickness=0
        )
        diamond_canvas.pack(side='left', padx=(0, SPACING['md']))
        
        # Draw diamond with glow
        center_x, center_y = 16, 16
        size = 12
        # Outer glow
        for i in range(3):
            alpha = 0.4 - (i * 0.1)
            glow_color = f'#{int(0 * alpha):02x}{int(245 * alpha):02x}{int(212 * alpha):02x}'
            diamond_canvas.create_polygon(
                center_x, center_y - size - i,
                center_x + size + i, center_y,
                center_x, center_y + size + i,
                center_x - size - i, center_y,
                fill=glow_color, outline='', tags='glow'
            )
        # Diamond shape
        diamond_canvas.create_polygon(
            center_x, center_y - size,
            center_x + size, center_y,
            center_x, center_y + size,
            center_x - size, center_y,
            fill=COLORS['accent_cyan'], outline='', tags='diamond'
        )
        
        # Title
        title_label = NMSLabel(
            header_frame,
            text="No Man's Sky Save Editor",
            style='heading',
            bg='',
            fg=COLORS['text_primary']
        )
        title_label.pack(side='left')
        
        # Main content panel
        self.content_panel = NMSPanel(main_container)
        self.content_panel.pack(fill='both', expand=True)
        
        # Content frame inside panel
        content_frame = tk.Frame(self.content_panel, bg='')
        content_frame.pack(fill='both', expand=True, padx=SPACING['xl'], pady=SPACING['xl'])
        
        # Save file selection section
        self._create_file_section(content_frame)
        
        # Action buttons section
        self._create_action_buttons(content_frame)
        
        # Base type selection section (hidden initially)
        self._create_base_type_section(content_frame)
        
        # Bases list section (hidden initially)
        self._create_bases_section(content_frame)
        
        # Status bar
        self.status_bar = StatusBar(self.root)
        self.status_bar.pack(side='bottom', fill='x')
    
    def _create_file_section(self, parent):
        """Create save file selection section"""
        file_section = tk.Frame(parent, bg='')
        file_section.pack(fill='x', pady=(0, SPACING['xl']))
        
        # Section title
        NMSLabel(
            file_section,
            text="Select Save File:",
            style='subheading',
            bg='',
            fg=COLORS['text_primary']
        ).pack(anchor='w', pady=(0, SPACING['md']))
        
        # Dropdown frame
        dropdown_frame = tk.Frame(file_section, bg='')
        dropdown_frame.pack(fill='x', pady=(0, SPACING['md']))
        
        # Input panel for dropdown
        input_panel = NMSPanel(dropdown_frame)
        input_panel.pack(side='left', fill='x', expand=True, padx=(0, SPACING['md']))
        
        # Dropdown inside panel
        dropdown_container = tk.Frame(input_panel, bg='')
        dropdown_container.pack(fill='both', expand=True, padx=SPACING['md'], pady=SPACING['sm'])
        
        self.save_file_var = tk.StringVar()
        self.save_file_dropdown = ttk.Combobox(
            dropdown_container,
            textvariable=self.save_file_var,
            state='readonly',
            font=FONTS['default'],
            width=50
        )
        self.save_file_dropdown.pack(fill='x')
        
        # Style combobox
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TCombobox',
                       fieldbackground=COLORS['bg_panel'],
                       background=COLORS['bg_panel'],
                       foreground=COLORS['text_primary'],
                       borderwidth=0,
                       relief='flat',
                       padding=8)
        style.map('TCombobox',
             fieldbackground=[('readonly', COLORS['bg_panel'])],
             background=[('readonly', COLORS['bg_panel'])],
             bordercolor=[('focus', COLORS['border_focus']), ('!focus', COLORS['border'])],
             lightcolor=[('focus', COLORS['border_focus'])],
             darkcolor=[('focus', COLORS['border_focus'])])
        
        # Load File button
        self.load_file_btn = NMSButton(
            dropdown_frame,
            text="Load File",
            command=self._load_save_file,
            gradient_colors=COLORS['gradient_cyan_violet']
        )
        self.load_file_btn.pack(side='left')
    
    def _create_action_buttons(self, parent):
        """Create action buttons section"""
        self.action_frame = tk.Frame(parent, bg='')
        self.action_frame.pack(fill='x', pady=(0, SPACING['xl']))
        
        self.edit_base_btn = NMSButton(
            self.action_frame,
            text="Edit Selected Base",
            command=self._open_editor,
            gradient_colors=COLORS['gradient_cyan_violet']
        )
        self.edit_base_btn.pack(side='left', padx=(0, SPACING['md']))
        self._set_button_disabled(self.edit_base_btn, True)
        
        self.inject_base_btn = NMSButton(
            self.action_frame,
            text="Inject Base into Save File",
            command=self._inject_base,
            gradient_colors=COLORS['gradient_cyan_violet']
        )
        self.inject_base_btn.pack(side='left')
        self._set_button_disabled(self.inject_base_btn, True)
    
    def _create_base_type_section(self, parent):
        """Create base type selection section"""
        self.base_type_section = tk.Frame(parent, bg='')
        self.base_type_section.pack(fill='x', pady=(0, SPACING['xl']))
        self.base_type_section.pack_forget()  # Hidden until file is loaded
        
        # Section title
        NMSLabel(
            self.base_type_section,
            text="Select Base Type:",
            style='subheading',
            bg='',
            fg=COLORS['text_primary']
        ).pack(anchor='w', pady=(0, SPACING['md']))
        
        # Toggle buttons frame
        toggle_frame = tk.Frame(self.base_type_section, bg='')
        toggle_frame.pack(fill='x')
        
        self.base_type_var = tk.StringVar(value="both")
        
        # Create pill toggle buttons
        self.corvette_toggle = PillToggleButton(
            toggle_frame,
            text="🚢 Corvettes (PlayerShipBase)",
            variable=self.base_type_var,
            value="PlayerShipBase",
            command=self._on_base_type_changed
        )
        self.corvette_toggle.pack(side='left', padx=(0, SPACING['md']))
        
        self.planetary_toggle = PillToggleButton(
            toggle_frame,
            text="🪐 Planetary Bases (ExternalPlanetBase)",
            variable=self.base_type_var,
            value="ExternalPlanetBase",
            command=self._on_base_type_changed
        )
        self.planetary_toggle.pack(side='left', padx=(0, SPACING['md']))
        
        self.both_toggle = PillToggleButton(
            toggle_frame,
            text="Both",
            variable=self.base_type_var,
            value="both",
            command=self._on_base_type_changed
        )
        self.both_toggle.pack(side='left')
    
    def _create_bases_section(self, parent):
        """Create bases list section"""
        self.bases_section = tk.Frame(parent, bg='')
        self.bases_section.pack(fill='both', expand=True)
        self.bases_section.pack_forget()  # Hidden until base type is selected
        
        # Section title
        NMSLabel(
            self.bases_section,
            text="Select Base:",
            style='subheading',
            bg='',
            fg=COLORS['text_primary']
        ).pack(anchor='w', pady=(0, SPACING['md']))
        
        # Listbox panel
        listbox_panel = NMSPanel(self.bases_section)
        listbox_panel.pack(fill='both', expand=True)
        
        # Listbox container
        listbox_container = tk.Frame(listbox_panel, bg='')
        listbox_container.pack(fill='both', expand=True, padx=SPACING['md'], pady=SPACING['md'])
        
        # Scrollbar
        scrollbar = tk.Scrollbar(listbox_container, bg=COLORS['bg_panel'], troughcolor=COLORS['bg_secondary'])
        scrollbar.pack(side='right', fill='y')
        
        # Listbox
        self.bases_listbox = ModernListbox(listbox_container)
        self.bases_listbox.pack(side='left', fill='both', expand=True)
        self.bases_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.bases_listbox.yview)
        self.bases_listbox.bind('<<ListboxSelect>>', self._on_base_selected)
    
    def _set_button_disabled(self, button, disabled=True):
        """Disable/enable NMS button"""
        if disabled:
            button.config(state='disabled')
            # Draw with disabled appearance
            button.delete('all')
            button.create_rectangle(0, 0, button.winfo_width(), button.winfo_height(),
                                  fill=COLORS['bg_tertiary'], outline=COLORS['border'])
            button.create_text(button.winfo_width() // 2, button.winfo_height() // 2,
                             text=button.text, fill=COLORS['text_muted'], font=FONTS['button'])
        else:
            button.config(state='normal')
            button._draw_button()
    
    def _update_save_file_dropdown(self):
        """Update the save file dropdown with sorted files"""
        if not self.save_editor.save_files:
            return
        
        # Sort by last modified time (descending)
        sorted_files = sorted(
            self.save_editor.save_files,
            key=lambda x: self.save_editor.get_save_file_metadata(x).get('last_saved', ''),
            reverse=True
        )
        
        # Create display strings with last modified time
        display_items = []
        for save_file in sorted_files:
            metadata = self.save_editor.get_save_file_metadata(save_file)
            last_saved = metadata.get('last_saved', 'Unknown')
            display_items.append(f"{save_file} - {last_saved}")
        
        self.save_file_dropdown['values'] = display_items
        if display_items:
            self.save_file_dropdown.current(0)
    
    def _load_save_file(self):
        """Load and decompress the selected save file"""
        selection = self.save_file_dropdown.get()
        if not selection:
            messagebox.showwarning("Warning", "Please select a save file first.")
            return
        
        # Extract filename from display string
        save_file_name = selection.split(' - ')[0]
        
        self._update_status(f"Loading {save_file_name}...", 'info')
        self._set_button_disabled(self.load_file_btn, True)
        self.root.update()
        
        try:
            # Select and decompress the save file
            self.save_editor.select_save_file(save_file_name)
            self.save_editor.decompress_save_file(save_file_name)
            self.save_editor.load_bases()
            
            # Show base type selection
            self.base_type_section.pack(fill='x', pady=(0, SPACING['xl']))
            self._update_status(f"Successfully loaded {save_file_name}", 'success')
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load save file:\n{e}")
            self._update_status(f"Error loading file: {e}", 'error')
        finally:
            self._set_button_disabled(self.load_file_btn, False)
    
    def _on_base_type_changed(self):
        """Handle base type selection change"""
        base_type = self.base_type_var.get()
        self.current_base_type_filter = base_type
        
        if base_type == "both":
            self.filtered_bases = self.save_editor.all_bases
        else:
            self.filtered_bases = self.save_editor.get_bases_by_type(base_type)
        
        # Update bases list
        self._update_bases_list()
        
        # Show bases section
        self.bases_section.pack(fill='both', expand=True)
    
    def _update_bases_list(self):
        """Update the bases listbox with filtered bases"""
        self.bases_listbox.delete(0, tk.END)
        
        for base in self.filtered_bases:
            name = base.get("Name", "Unknown")
            base_type = base.get("BaseType", {}).get("PersistentBaseTypes", "Unknown")
            owner_usn = base.get("Owner", {}).get("USN", "Unknown")
            
            display_text = f"{name} | {base_type} | Owner: {owner_usn}"
            self.bases_listbox.insert(tk.END, display_text)
    
    def _on_base_selected(self, event):
        """Handle base selection from listbox"""
        selection = self.bases_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        self.selected_base_index = index
        
        # Find the actual base in filtered_bases
        selected_base = self.filtered_bases[index]
        base_name = selected_base.get("Name", "Unknown")
        
        # Find the index in all_bases and select it
        try:
            self.save_editor.select_base(base_name)
        except ValueError:
            # If base not found by name, try to find by matching the base object
            for i, base in enumerate(self.save_editor.all_bases):
                if base.get("Name") == base_name:
                    self.save_editor.selected_base = base
                    self.save_editor.selected_base_index = i
                    break
        
        # Enable edit button
        self._set_button_disabled(self.edit_base_btn, False)
        # Keep inject button disabled until base is saved
        self._set_button_disabled(self.inject_base_btn, True)
        self._update_status(f"Selected base: {base_name}", 'info')
    
    def _open_editor(self):
        """Open the base editor window"""
        if self.save_editor.selected_base is None:
            messagebox.showwarning("Warning", "Please select a base first.")
            return
        
        # Open editor window
        editor = EditorWindow(self.root, self.save_editor, self._on_base_saved)
        editor.show()
    
    def _on_base_saved(self):
        """Callback when base is saved in editor"""
        # Update the filtered bases list if needed
        if self.selected_base_index is not None and self.selected_base_index < len(self.filtered_bases):
            self.filtered_bases[self.selected_base_index] = self.save_editor.selected_base
            self._update_bases_list()
        
        # Enable inject button
        self._set_button_disabled(self.inject_base_btn, False)
        self._update_status("Base saved. Ready to inject into save file.", 'success')
    
    def _inject_base(self):
        """Inject the selected base into the save file and recompress"""
        if self.save_editor.selected_base is None:
            messagebox.showwarning("Warning", "No base selected.")
            return
        
        # Confirm action
        result = messagebox.askyesno(
            "Confirm Injection",
            "This will inject the base into the save file and replace the original .hg file.\n\n"
            "A backup will be created before replacement.\n\n"
            "Are you sure you want to continue?",
            icon='warning'
        )
        
        if not result:
            return
        
        self._update_status("Injecting base into save file...", 'info')
        self._set_button_disabled(self.inject_base_btn, True)
        self.root.update()
        
        try:
            # Inject the base
            self.save_editor.inject_selected_base_into_save_file()
            
            # Recompress and replace original file
            original_path = os.path.join(
                self.save_editor.save_file_directory,
                self.save_editor.selected_save_file
            )
            self.save_editor.recompress_save_file(output_path=original_path)
            
            messagebox.showinfo("Success", "Base successfully injected and save file recompressed!")
            self._update_status("Base injected successfully!", 'success')
            
            # Reset state
            self._set_button_disabled(self.inject_base_btn, False)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to inject base:\n{e}")
            self._update_status(f"Error: {e}", 'error')
            self._set_button_disabled(self.inject_base_btn, False)
    
    def _update_status(self, message, status_type='info'):
        """Update status bar"""
        self.status_bar.set_status(message, status_type)
    
    def run(self):
        """Start the GUI main loop"""
        self.root.mainloop()
