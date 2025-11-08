"""
Save File Manager - Modular class for managing No Man's Sky save file JSON operations.
"""

import json
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

from .base_or_corvette_detection import find_key_recursively


class SaveFileManager:
    """
    Manages No Man's Sky save file JSON operations.
    
    Provides intuitive methods for:
    - Loading save files
    - Fetching bases
    - Filtering by base type
    - Editing/replacing bases
    - Saving changes
    """
    
    def __init__(self, file_path: Optional[str] = None):
        """
        Initialize SaveFileManager.
        
        Args:
            file_path: Optional path to save file JSON. If provided, will load automatically.
        """
        self._save_data: Optional[Dict[str, Any]] = None
        self._file_path: Optional[str] = None
        self._base_path: Optional[List[str]] = None
        self._has_changes: bool = False
        self._backup_path: Optional[str] = None
        
        if file_path:
            self.load(file_path)
    
    @property
    def file_path(self) -> Optional[str]:
        """Get the current file path."""
        return self._file_path
    
    @property
    def has_changes(self) -> bool:
        """Check if there are unsaved changes."""
        return self._has_changes
    
    @property
    def is_loaded(self) -> bool:
        """Check if a save file is loaded."""
        return self._save_data is not None
    
    @property
    def base_path(self) -> Optional[List[str]]:
        """Get the path to PersistentPlayerBases in the save file."""
        return self._base_path
    
    def load(self, file_path: str) -> bool:
        """
        Load a save file JSON.
        
        Args:
            file_path: Path to the save file JSON.
            
        Returns:
            True if loaded successfully, False otherwise.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self._save_data = json.load(f)
            
            # Find PersistentPlayerBases location
            base_keys = list(find_key_recursively(self._save_data, "PersistentPlayerBases"))
            if not base_keys:
                raise ValueError("Could not find PersistentPlayerBases in save file")
            
            self._base_path, _ = base_keys[0]
            self._file_path = file_path
            self._has_changes = False
            return True
        except Exception as e:
            raise RuntimeError(f"Error loading file: {e}")
    
    def _get_bases_array(self) -> List[Dict[str, Any]]:
        """Get the PersistentPlayerBases array from the save data."""
        if not self._save_data or not self._base_path:
            raise ValueError("No save file loaded")
        
        # Navigate to the PersistentPlayerBases array
        current = self._save_data
        for key in self._base_path[:-1]:
            if key.startswith("[") and key.endswith("]"):
                # List index - format is "[0]"
                idx = int(key[1:-1])
                current = current[idx]
            else:
                # Dict key
                current = current[key]
        
        # Get the PersistentPlayerBases array (last element in path)
        return current[self._base_path[-1]]
    
    def get_bases(self) -> List[Dict[str, Any]]:
        """
        Get all bases from the save file.
        
        Returns:
            List of all base dictionaries.
        """
        return self._get_bases_array().copy()
    
    def get_base_types(self) -> List[str]:
        """
        Get all unique base types in the save file.
        
        Returns:
            List of unique base type strings.
        """
        bases = self.get_bases()
        types = set()
        for base in bases:
            base_type = base.get("BaseType", {}).get("PersistentBaseTypes", "")
            if base_type:
                types.add(base_type)
        return sorted(list(types))
    
    def get_bases_by_type(self, base_type: str) -> List[Dict[str, Any]]:
        """
        Get all bases of a specific type.
        
        Args:
            base_type: The base type to filter by (e.g., "PlayerShipBase", "ExternalPlanetBase").
            
        Returns:
            List of base dictionaries matching the type.
        """
        bases = self.get_bases()
        return [
            base for base in bases
            if base.get("BaseType", {}).get("PersistentBaseTypes", "") == base_type
        ]
    
    def get_base_by_index(self, index: int) -> Optional[Dict[str, Any]]:
        """
        Get a base by its index in the save file.
        
        Args:
            index: The index of the base in the PersistentPlayerBases array.
            
        Returns:
            Base dictionary if found, None otherwise.
        """
        bases_array = self._get_bases_array()
        if 0 <= index < len(bases_array):
            return bases_array[index].copy()
        return None
    
    def find_base_index(self, base_data: Dict[str, Any]) -> Optional[int]:
        """
        Find the index of a base in the save file.
        
        Uses base name and type to identify the base.
        
        Args:
            base_data: The base dictionary to find.
            
        Returns:
            Index of the base if found, None otherwise.
        """
        bases_array = self._get_bases_array()
        base_name = base_data.get("Name", "")
        base_type = base_data.get("BaseType", {}).get("PersistentBaseTypes", "")
        
        for idx, base in enumerate(bases_array):
            if (base.get("Name", "") == base_name and
                base.get("BaseType", {}).get("PersistentBaseTypes", "") == base_type):
                return idx
        return None
    
    def replace_base(self, index: int, new_base_data: Dict[str, Any]) -> bool:
        """
        Replace a base at the given index with new base data.
        
        Args:
            index: The index of the base to replace.
            new_base_data: The new base dictionary.
            
        Returns:
            True if successful, False otherwise.
        """
        bases_array = self._get_bases_array()
        
        if index < 0 or index >= len(bases_array):
            raise IndexError(f"Index {index} out of range (array has {len(bases_array)} bases)")
        
        bases_array[index] = new_base_data
        self._has_changes = True
        return True
    
    def add_base(self, base_data: Dict[str, Any]) -> int:
        """
        Add a new base to the save file.
        
        Args:
            base_data: The base dictionary to add.
            
        Returns:
            The index of the newly added base.
        """
        bases_array = self._get_bases_array()
        bases_array.append(base_data)
        self._has_changes = True
        return len(bases_array) - 1
    
    def remove_base(self, index: int) -> bool:
        """
        Remove a base from the save file.
        
        Args:
            index: The index of the base to remove.
            
        Returns:
            True if successful, False otherwise.
        """
        bases_array = self._get_bases_array()
        
        if index < 0 or index >= len(bases_array):
            raise IndexError(f"Index {index} out of range (array has {len(bases_array)} bases)")
        
        bases_array.pop(index)
        self._has_changes = True
        return True
    
    def get_base_count(self) -> int:
        """
        Get the total number of bases in the save file.
        
        Returns:
            Number of bases.
        """
        return len(self._get_bases_array())
    
    def get_base_count_by_type(self, base_type: str) -> int:
        """
        Get the count of bases of a specific type.
        
        Args:
            base_type: The base type to count.
            
        Returns:
            Number of bases of the specified type.
        """
        return len(self.get_bases_by_type(base_type))
    
    def create_backup(self, backup_dir: Optional[str] = None) -> str:
        """
        Create a backup of the current save file.
        
        Args:
            backup_dir: Directory to save backup. Defaults to "backups/save files".
            
        Returns:
            Path to the backup file.
        """
        if not self._file_path:
            raise ValueError("No save file loaded")
        
        if backup_dir is None:
            backup_dir = Path("backups") / "save files"
        else:
            backup_dir = Path(backup_dir)
        
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"{Path(self._file_path).stem}_backup_{timestamp}.json"
        self._backup_path = str(backup_dir / backup_filename)
        
        shutil.copy2(self._file_path, self._backup_path)
        return self._backup_path
    
    def save(self, file_path: Optional[str] = None, create_backup: bool = True) -> bool:
        """
        Save changes to the save file.
        
        Args:
            file_path: Path to save to. If None, saves to the original file.
            create_backup: Whether to create a backup before saving.
            
        Returns:
            True if successful, False otherwise.
        """
        if not self._save_data:
            raise ValueError("No save file loaded")
        
        save_path = file_path or self._file_path
        if not save_path:
            raise ValueError("No file path specified")
        
        # Create backup if requested and not already created
        if create_backup and not self._backup_path:
            self.create_backup()
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self._save_data, f, indent=2, ensure_ascii=False)
            
            self._has_changes = False
            if file_path and file_path != self._file_path:
                self._file_path = file_path
            return True
        except Exception as e:
            raise RuntimeError(f"Error saving file: {e}")
    
    def export_bases(self, base_types: Optional[List[str]] = None, 
                    output_dir: Optional[str] = None) -> Tuple[str, str]:
        """
        Export bases to JSON and CSV files.
        
        Args:
            base_types: List of base types to export. If None, exports all bases.
            output_dir: Directory to save exported files. Defaults to "output".
            
        Returns:
            Tuple of (json_file_path, csv_file_path).
        """
        from .base_or_corvette_detection import export_bases_to_csv
        
        if output_dir is None:
            output_dir = Path("output")
        else:
            output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        # Get bases to export
        if base_types:
            bases = []
            for base_type in base_types:
                bases.extend(self.get_bases_by_type(base_type))
        else:
            bases = self.get_bases()
        
        # Save to JSON
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_file = output_dir / f"extracted_bases_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(bases, f, indent=4, ensure_ascii=False)
        
        # Export to CSV
        csv_file = output_dir / f"bases_overview_{timestamp}.csv"
        export_bases_to_csv(bases, str(csv_file))
        
        return str(json_file), str(csv_file)

