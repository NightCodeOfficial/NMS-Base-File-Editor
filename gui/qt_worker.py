"""
Background worker thread for file operations
"""

from PySide6.QtCore import QThread, Signal


class DecompressWorker(QThread):
    """Worker thread for decompressing save files"""
    
    finished = Signal(bool, str)  # success, message
    progress = Signal(str)  # status message
    
    def __init__(self, save_editor, save_file_name):
        super().__init__()
        self.save_editor = save_editor
        self.save_file_name = save_file_name
    
    def run(self):
        """Run decompression in background"""
        try:
            self.progress.emit(f"Selecting save file...")
            self.save_editor.select_save_file(self.save_file_name)
            
            self.progress.emit(f"Decompressing {self.save_file_name}...")
            self.save_editor.decompress_save_file(self.save_file_name)
            
            self.progress.emit(f"Loading bases...")
            self.save_editor.load_bases()
            
            self.finished.emit(True, f"Successfully loaded {self.save_file_name}")
        except Exception as e:
            self.finished.emit(False, str(e))


class InjectWorker(QThread):
    """Worker thread for injecting base and recompressing save file"""
    
    finished = Signal(bool, str)  # success, message
    progress = Signal(str)  # status message
    
    def __init__(self, save_editor):
        super().__init__()
        self.save_editor = save_editor
    
    def run(self):
        """Run injection and recompression in background"""
        try:
            self.progress.emit("Injecting base into save file...")
            self.save_editor.inject_selected_base_into_save_file()
            
            self.progress.emit("Recompressing save file...")
            original_path = f"{self.save_editor.save_file_directory}/{self.save_editor.selected_save_file}"
            self.save_editor.recompress_save_file(output_path=original_path)
            
            self.finished.emit(True, "Base successfully injected and save file recompressed!")
        except Exception as e:
            self.finished.emit(False, str(e))


class CountComponentsWorker(QThread):
    """Worker thread for counting components in all bases"""
    
    finished = Signal(bool, int, str)  # success, count, message
    progress = Signal(str)  # status message
    
    def __init__(self, save_editor):
        super().__init__()
        self.save_editor = save_editor
    
    def run(self):
        """Run component counting in background"""
        try:
            self.progress.emit("Counting base parts...")
            total_components = self.save_editor.get_number_of_components_for_all_bases_in_save_file()
            self.finished.emit(True, total_components, f"Total components: {total_components}")
        except Exception as e:
            self.finished.emit(False, 0, str(e))
