"""
Base editor window for editing base JSON
"""

import tkinter as tk
from tkinter import messagebox
import json

# Try to import pyperclip, fallback to tkinter clipboard if not available
try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False

from .styles import COLORS, FONTS, SPACING, RADIUS
from .components import ModernButton, ModernFrame, ModernLabel


class EditorWindow:
    """Window for editing base JSON"""
    
    def __init__(self, parent, save_editor, on_save_callback=None):
        self.parent = parent
        self.save_editor = save_editor
        self.on_save_callback = on_save_callback
        self.is_editing = False
        
        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title("Base Editor")
        self.window.geometry("900x700")
        
        # Use gradient for window background
        from .gradient import GradientFrame
        self._window_gradient = GradientFrame(
            self.window,
            COLORS['bg_primary'],
            COLORS['bg_primary_end'],
            direction='vertical'
        )
        self._window_gradient.pack(fill='both', expand=True)
        
        # Make window modal
        self.window.transient(parent)
        self.window.grab_set()
        
        # Get base data
        self.base_data = self.save_editor.selected_base.copy()
        self.original_json = json.dumps(self.base_data, indent=2, ensure_ascii=False)
        
        self._create_widgets()
        self._load_base_data()
    
    def _create_widgets(self):
        """Create all widgets in the editor window"""
        # Main container with gradient
        main_container = ModernFrame(
            self._window_gradient,
            gradient=True,
            gradient_colors=(COLORS['bg_secondary'], COLORS['bg_secondary_end']),
            gradient_direction='vertical'
        )
        main_container.pack(fill='both', expand=True, padx=SPACING['xl'], pady=SPACING['xl'])
        
        # Header with teal accent
        header_frame = tk.Frame(main_container._gradient_frame, bg=COLORS['bg_secondary'])
        header_frame.pack(fill='x', pady=(0, SPACING['md']))
        
        base_name = self.base_data.get("Name", "Unknown")
        ModernLabel(
            header_frame,
            text=f"Editing: {base_name}",
            style='heading',
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary']
        ).pack(side='left')
        
        # Teal accent dot
        accent_dot = tk.Label(
            header_frame,
            text="●",
            bg=COLORS['bg_secondary'],
            fg=COLORS['accent_teal'],
            font=('Segoe UI', 8)
        )
        accent_dot.pack(side='left', padx=(SPACING['sm'], 0))
        
        # Button frame
        button_frame = tk.Frame(header_frame, bg=COLORS['bg_secondary'])
        button_frame.pack(side='right')
        
        self.copy_btn = ModernButton(
            button_frame,
            text="📋 Copy",
            command=self._copy_json,
            style='primary'
        )
        self.copy_btn.pack(side='left', padx=(0, SPACING['sm']))
        
        self.edit_btn = ModernButton(
            button_frame,
            text="✏️ Edit",
            command=self._toggle_edit,
            style='primary'
        )
        self.edit_btn.pack(side='left', padx=(0, SPACING['sm']))
        
        self.save_btn = ModernButton(
            button_frame,
            text="💾 Save",
            command=self._save_base,
            style='primary'
        )
        self.save_btn.pack(side='left')
        self.save_btn.set_disabled(True)
        
        # Info note with teal accent
        info_frame = tk.Frame(main_container._gradient_frame, bg=COLORS['bg_tertiary'])
        info_frame.pack(fill='x', pady=(0, SPACING['md']))
        
        # Teal accent border on left
        accent_border = tk.Frame(info_frame, bg=COLORS['accent_teal'], width=4)
        accent_border.pack(side='left', fill='y')
        
        info_text_frame = tk.Frame(info_frame, bg=COLORS['bg_tertiary'])
        info_text_frame.pack(side='left', fill='both', expand=True, padx=SPACING['md'], pady=SPACING['sm'])
        
        info_text = (
            "💡 Tip: You can export JSON from djmonkeyuk's base editor using 'Export to NMS' option, "
            "then paste it here after clicking Edit."
        )
        info_label = ModernLabel(
            info_text_frame,
            text=info_text,
            style='small',
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_teal'],
            wraplength=800,
            justify='left'
        )
        info_label.pack(anchor='w')
        
        # JSON display/edit area
        text_frame = tk.Frame(main_container._gradient_frame, bg=COLORS['bg_secondary'])
        text_frame.pack(fill='both', expand=True)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(text_frame, bg=COLORS['bg_tertiary'], troughcolor=COLORS['bg_secondary'])
        scrollbar.pack(side='right', fill='y')
        
        # Text widget
        self.json_text = tk.Text(
            text_frame,
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary'],
            insertbackground=COLORS['text_primary'],
            selectbackground=COLORS['selection'],
            selectforeground=COLORS['text_primary'],
            relief='flat',
            bd=0,
            font=FONTS['monospace'],
            wrap='none',
            yscrollcommand=scrollbar.set,
            state='disabled'
        )
        self.json_text.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.json_text.yview)
        
        # Close button
        close_frame = tk.Frame(main_container._gradient_frame, bg=COLORS['bg_secondary'])
        close_frame.pack(fill='x', pady=(SPACING['md'], 0))
        
        ModernButton(
            close_frame,
            text="Close",
            command=self.window.destroy,
            style='secondary'
        ).pack(side='right')
    
    def _load_base_data(self):
        """Load base data into the text widget"""
        self.json_text.config(state='normal')
        self.json_text.delete('1.0', tk.END)
        self.json_text.insert('1.0', self.original_json)
        self.json_text.config(state='disabled')
    
    def _copy_json(self):
        """Copy JSON to clipboard"""
        try:
            # Get current text from editor
            current_text = self.json_text.get('1.0', tk.END).strip()
            
            if HAS_PYPERCLIP:
                pyperclip.copy(current_text)
            else:
                # Fallback to tkinter clipboard
                self.window.clipboard_clear()
                self.window.clipboard_append(current_text)
                self.window.update()
            
            # Show temporary feedback
            original_text = self.copy_btn.cget('text')
            self.copy_btn.config(text="✓ Copied!")
            self.window.after(2000, lambda: self.copy_btn.config(text=original_text))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy to clipboard:\n{e}")
    
    def _toggle_edit(self):
        """Toggle edit mode"""
        if not self.is_editing:
            # Enable editing
            self.json_text.config(state='normal')
            self.edit_btn.config(text="🔒 Lock")
            self.save_btn.set_disabled(False)
            self.is_editing = True
        else:
            # Disable editing
            self.json_text.config(state='disabled')
            self.edit_btn.config(text="✏️ Edit")
            self.save_btn.set_disabled(True)
            self.is_editing = False
    
    def _save_base(self):
        """Save the edited base"""
        if not self.is_editing:
            return
        
        # Get JSON from text widget
        json_str = self.json_text.get('1.0', tk.END).strip()
        
        # Validate JSON
        try:
            new_base_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            messagebox.showerror("Invalid JSON", f"The JSON is invalid:\n{e}")
            return
        
        # Confirm save
        result = messagebox.askyesno(
            "Confirm Save",
            "Are you sure you want to save this base?\n\n"
            "This will update the base data in memory.\n"
            "You will need to inject it into the save file to make it permanent.",
            icon='question'
        )
        
        if not result:
            return
        
        try:
            # Update the base data
            self.base_data = new_base_data
            self.original_json = json_str
            
            # Update in save_editor
            self.save_editor.selected_base = new_base_data
            
            # Save to JSON file
            self.save_editor.save_selected_base_to_json()
            
            # Reload display (this will lock editing)
            self._load_base_data()
            self.is_editing = False
            self.edit_btn.config(text="✏️ Edit")
            self.save_btn.set_disabled(True)
            
            # Call callback if provided
            if self.on_save_callback:
                self.on_save_callback()
            
            messagebox.showinfo("Success", "Base saved successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save base:\n{e}")
    
    def show(self):
        """Show the window"""
        self.window.focus_set()
        self.window.wait_window()

