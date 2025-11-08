"""
Menu-driven base extraction and replacement tool.
Temporary entry point for testing features.
"""

import json
import os
import time
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import filedialog
from utils import SaveFileManager

# Get the project root directory
_PROJECT_ROOT = Path(__file__).parent
_OUTPUT_DIR = _PROJECT_ROOT / "output"
_OUTPUT_DIR.mkdir(exist_ok=True)


class BaseManager:
    """Manages base extraction and replacement operations using SaveFileManager."""
    
    def __init__(self):
        self.save_manager = SaveFileManager()
        self.extracted_bases = []
        self.base_indices_map = {}  # Maps display index to (master_index, base_data)
    
    @property
    def save_file_json_path(self):
        """Get the current save file path."""
        return self.save_manager.file_path
    
    @property
    def master_save_dict(self):
        """Get the master save dictionary."""
        return self.save_manager._save_data if self.save_manager.is_loaded else None
    
    @property
    def has_changes(self):
        """Check if there are unsaved changes."""
        return self.save_manager.has_changes
    
    def load_save_file(self, file_path: str):
        """Load a save file JSON."""
        try:
            self.save_manager.load(file_path)
            file_name = Path(file_path).name
            print(f"\n✓ Successfully loaded: {file_name}")
            print(f"✓ Found PersistentPlayerBases in save file")
            return True
        except Exception as e:
            print(f"Error loading file: {e}")
            return False
    
    def extract_bases(self, base_types: list):
        """Extract bases of specified types."""
        if not self.save_manager.is_loaded:
            print("Error: No save file loaded")
            return False
        
        # Get bases by type
        extracted = []
        self.base_indices_map = {}
        display_index = 0
        
        # Get all bases and filter
        all_bases = self.save_manager.get_bases()
        for master_index, base in enumerate(all_bases):
            base_type = base.get("BaseType", {}).get("PersistentBaseTypes", "")
            if base_type in base_types:
                extracted.append(base)
                self.base_indices_map[display_index] = (master_index, base)
                display_index += 1
        
        self.extracted_bases = extracted
        
        if not extracted:
            print("\nNo bases found matching the selected types.")
            return False
        
        # Export using SaveFileManager
        try:
            json_file, csv_file = self.save_manager.export_bases(base_types)
            print(f"\n✓ Extracted {len(extracted)} bases")
            print(f"✓ Saved to: {Path(json_file).name}")
            print(f"✓ CSV exported to: {Path(csv_file).name}")
            return True
        except Exception as e:
            print(f"Error exporting bases: {e}")
            return False
    
    def display_bases(self):
        """Display all extracted bases with identifying information."""
        if not self.extracted_bases:
            print("No bases extracted yet.")
            return
        
        print(f"\n{'#':<4} {'Name':<25} {'Type':<22} {'Owner USN':<25} {'GameMode':<12}")
        print("-" * 90)
        
        for display_idx, base in enumerate(self.extracted_bases):
            name = base.get("Name", "Unknown")
            base_type = base.get("BaseType", {}).get("PersistentBaseTypes", "Unknown")
            owner_usn = base.get("Owner", {}).get("USN", "Unknown")
            game_mode = base.get("GameMode", {}).get("PresetGameMode", "Unknown")
            
            # Truncate long names
            if len(name) > 23:
                name = name[:20] + "..."
            if len(owner_usn) > 23:
                owner_usn = owner_usn[:20] + "..."
            
            print(f"{display_idx:<4} {name:<25} {base_type:<22} {owner_usn:<25} {game_mode:<12}")
    
    def get_base_by_display_index(self, display_index: int):
        """Get base data and master index by display index."""
        if display_index not in self.base_indices_map:
            return None, None
        master_index, base_data = self.base_indices_map[display_index]
        return master_index, base_data
    
    def replace_base_in_master(self, master_index: int, new_base_data: dict):
        """Replace a base in the master save file."""
        try:
            self.save_manager.replace_base(master_index, new_base_data)
            print(f"Base at index {master_index} replaced successfully")
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    def save_base_to_file(self, base_data: dict, display_index: int):
        """Save a single base to a JSON file using tkinter file dialog."""
        # Create root window and hide it
        root = tk.Tk()
        root.withdraw()
        
        base_name = base_data.get("Name", "Unknown")
        base_type = base_data.get("BaseType", {}).get("PersistentBaseTypes", "Unknown")
        default_filename = f"base_{base_name}_{base_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        default_filename = default_filename.replace(" ", "_").replace("/", "_")
        
        # Open save dialog
        file_path = filedialog.asksaveasfilename(
            title="Save Base JSON",
            initialdir=str(_OUTPUT_DIR),
            initialfile=default_filename,
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        root.destroy()
        
        if not file_path:
            print("Save cancelled.")
            return None
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(base_data, f, indent=4, ensure_ascii=False)
            print(f"Base saved to: {file_path}")
            return file_path
        except Exception as e:
            print(f"Error saving file: {e}")
            return None
    
    def load_base_from_file(self):
        """Load a base from a JSON file using tkinter file dialog."""
        # Create root window and hide it
        root = tk.Tk()
        root.withdraw()
        
        # Open file dialog
        file_path = filedialog.askopenfilename(
            title="Load Base JSON",
            initialdir=str(_OUTPUT_DIR),
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        root.destroy()
        
        if not file_path:
            print("Load cancelled.")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                base_data = json.load(f)
            print(f"Base loaded from: {file_path}")
            return base_data
        except Exception as e:
            print(f"Error loading base file: {e}")
            return None
    
    def save_changes(self):
        """Save changes to the save file JSON."""
        try:
            self.save_manager.save(create_backup=True)
            print(f"Changes saved to: {self.save_manager.file_path}")
            return True
        except Exception as e:
            print(f"Error saving file: {e}")
            return False


def select_json_file():
    """Select a JSON file using tkinter file dialog."""
    # Create root window and hide it
    root = tk.Tk()
    root.withdraw()
    
    # Open file dialog starting from project root
    file_path = filedialog.askopenfilename(
        title="Select Save File JSON",
        initialdir=str(_PROJECT_ROOT),
        defaultextension=".json",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
    )
    
    root.destroy()
    
    if not file_path:
        print("File selection cancelled.")
        return None
    
    return file_path


def extract_type_menu():
    """Menu to select what to extract."""
    print("\n" + "="*80)
    print("SELECT BASE TYPES TO EXTRACT")
    print("="*80)
    print("1. 🚢 Corvettes (PlayerShipBase)")
    print("2. 🪐 Planetary Bases (ExternalPlanetBase)")
    print("3. Both (Corvettes + Planetary)")
    print("4. Back")
    print()
    
    choice = input("Select option: ").strip()
    
    if choice == "1":
        return ["PlayerShipBase"]
    elif choice == "2":
        return ["ExternalPlanetBase"]
    elif choice == "3":
        return ["PlayerShipBase", "ExternalPlanetBase"]
    elif choice == "4":
        return None
    else:
        print("❌ Invalid option.")
        return None


def base_selection_menu(manager: BaseManager):
    """Menu to select a base by number."""
    if not manager.extracted_bases:
        return None
    
    while True:
        print("\n" + "="*80)
        manager.display_bases()
        print("="*80)
        print("\nEnter base number to select, or 'back' to return to main menu:")
        choice = input("Choice: ").strip().lower()
        
        if choice == "back":
            return None
        
        try:
            display_index = int(choice)
            if 0 <= display_index < len(manager.extracted_bases):
                return display_index
            else:
                print(f"❌ Invalid base number. Please enter 0-{len(manager.extracted_bases)-1}")
                input("Press Enter to continue...")
        except ValueError:
            print("❌ Invalid input. Please enter a number or 'back'")
            input("Press Enter to continue...")


def base_detail_menu(manager: BaseManager, display_index: int):
    """Menu for individual base operations."""
    master_index, base_data = manager.get_base_by_display_index(display_index)
    if master_index is None:
        print("❌ Error: Invalid base index")
        return
    
    base_name = base_data.get("Name", "Unknown")
    base_type = base_data.get("BaseType", {}).get("PersistentBaseTypes", "Unknown")
    owner_usn = base_data.get("Owner", {}).get("USN", "Unknown")
    game_mode = base_data.get("GameMode", {}).get("PresetGameMode", "Unknown")
    num_objects = len(base_data.get("Objects", []))
    
    while True:
        print("\n" + "="*80)
        print(f"BASE DETAILS: {base_name}")
        print("="*80)
        print(f"Type: {base_type}")
        print(f"Owner: {owner_usn}")
        print(f"Game Mode: {game_mode}")
        print(f"Objects: {num_objects}")
        print("="*80)
        print()
        print("1. 💾 Save base JSON to file")
        print("2. 📂 Load base JSON from file (replace this base)")
        print("3. ← Back to base list")
        print()
        
        choice = input("Select option: ").strip()
        
        if choice == "1":
            result = manager.save_base_to_file(base_data, display_index)
            if result:
                print("✓ Base saved successfully!")
            input("\nPress Enter to continue...")
        elif choice == "2":
            new_base_data = manager.load_base_from_file()
            if new_base_data:
                print("\n" + "="*80)
                print("⚠️  REPLACEMENT CONFIRMATION")
                print("="*80)
                print(f"Current base: {base_name} ({base_type})")
                new_name = new_base_data.get("Name", "Unknown")
                new_type = new_base_data.get("BaseType", {}).get("PersistentBaseTypes", "Unknown")
                print(f"New base: {new_name} ({new_type})")
                print("="*80)
                confirm = input("\nReplace base? (yes/no): ").strip().lower()
                if confirm == "yes":
                    if manager.replace_base_in_master(master_index, new_base_data):
                        # Update the extracted bases list
                        manager.extracted_bases[display_index] = new_base_data
                        manager.base_indices_map[display_index] = (master_index, new_base_data)
                        print("✓ Base replaced successfully!")
                        print("⚠️  Remember to save changes to the save file!")
                    else:
                        print("❌ Failed to replace base.")
                else:
                    print("Replacement cancelled.")
                input("\nPress Enter to continue...")
        elif choice == "3":
            break
        else:
            print("❌ Invalid option.")
            input("Press Enter to continue...")


def main_menu(manager: BaseManager):
    """Main menu."""
    while True:
        # Clear screen and show status
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("="*80)
        print("BASE EXTRACTION AND REPLACEMENT")
        print("="*80)
        
        # Status information
        if manager.save_file_json_path:
            file_name = Path(manager.save_file_json_path).name
            print(f"📁 Loaded: {file_name}")
        else:
            print("📁 Loaded: None")
        
        if manager.extracted_bases:
            print(f"📊 Bases extracted: {len(manager.extracted_bases)}")
        else:
            print("📊 Bases extracted: None")
        
        if manager.has_changes:
            print("⚠️  Status: CHANGES PENDING - Save required!")
        else:
            print("✓ Status: No unsaved changes")
        
        print("="*80)
        print()
        
        # Menu options
        print("1. Load save file JSON" + (" [RELOAD]" if manager.save_file_json_path else ""))
        if manager.master_save_dict:
            if not manager.extracted_bases:
                print("2. Extract bases ⚠ REQUIRED")
            else:
                print("2. Re-extract bases (change type selection)")
        else:
            print("2. Extract bases (load file first)")
        
        if manager.extracted_bases:
            print("3. View & Select base")
        else:
            print("3. View & Select base (extract bases first)")
        
        if manager.has_changes:
            print("4. 💾 Save changes to save file JSON [REQUIRED]")
        else:
            print("4. Save changes (no changes to save)")
        
        print("5. Exit")
        print()
        
        choice = input("Select option: ").strip()
        
        if choice == "1":
            file_path = select_json_file()
            if file_path:
                if manager.load_save_file(file_path):
                    # Auto-prompt for extraction if bases not extracted
                    if not manager.extracted_bases and manager.master_save_dict:
                        print("\n" + "="*80)
                        print("Would you like to extract bases now?")
                        print("1. Yes, extract now")
                        print("2. No, do it later")
                        extract_choice = input("\nChoice: ").strip()
                        if extract_choice == "1":
                            base_types = extract_type_menu()
                            if base_types:
                                manager.extract_bases(base_types)
                                time.sleep(1.5)  # Brief pause to show success message
        elif choice == "2":
            if not manager.master_save_dict:
                print("\n❌ Error: Please load a save file first.")
                input("Press Enter to continue...")
                continue
            
            base_types = extract_type_menu()
            if base_types:
                manager.extract_bases(base_types)
                time.sleep(1.5)  # Brief pause to show success message
        elif choice == "3":
            if not manager.extracted_bases:
                print("\n❌ Error: No bases extracted. Please extract bases first.")
                input("Press Enter to continue...")
                continue
            
            display_index = base_selection_menu(manager)
            if display_index is not None:
                base_detail_menu(manager, display_index)
        elif choice == "4":
            if not manager.save_file_json_path:
                print("\n❌ Error: No save file loaded.")
                input("Press Enter to continue...")
                continue
            
            if manager.has_changes:
                print("\n" + "="*80)
                print("⚠️  WARNING: This will overwrite the original file!")
                print(f"File: {manager.save_file_json_path}")
                confirm = input("\nSave changes? (yes/no): ").strip().lower()
                if confirm == "yes":
                    if manager.save_changes():
                        print("✓ Changes saved successfully!")
                    else:
                        print("❌ Failed to save changes.")
                else:
                    print("Save cancelled.")
            else:
                print("\n✓ No changes to save.")
            input("\nPress Enter to continue...")
        elif choice == "5":
            if manager.has_changes:
                print("\n⚠️  You have unsaved changes!")
                confirm = input("Exit anyway? (yes/no): ").strip().lower()
                if confirm != "yes":
                    continue
            print("\nExiting...")
            break
        else:
            print("\n❌ Invalid option.")
            input("Press Enter to continue...")


def main():
    """Entry point."""
    manager = BaseManager()
    main_menu(manager)


if __name__ == "__main__":
    main()

