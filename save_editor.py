from utils import *
import json
import os
import shutil
from pathlib import Path
from datetime import datetime


# This class will be used to edit the save file and the bases in the save file
# It will hold the underlying logic to drive both gui and cli functionality 
class SaveEditor:
    '''
    A class to edit the save file and the bases in the save file
    It holds the underlying logic to drive both gui and cli functionality.
    '''


    def __init__(self):
        # Get the project directory (where this script is located)
        self.project_directory = Path(__file__).parent
        
        # Get the default save directory in windows
        self.save_file_directory = get_default_save_directory()

        #  all save file names in the chosen directory will be loaded into this list
        self.save_files = []

        # Get the save file metadata for each save file in the save_files list
        # NEEDS TO BE FIXED
        self.save_file_metadata = {}

        # the currently selected save file
        self.selected_save_file = None

        # the dictionary version of the currently selected save file taken from decompressing the save file
        self.selected_save_file_dict = None

        # the currently selected base type
        # either PlayerShipBase or ExternalPlanetBase
        self.selected_base_type = None

        # a list of all basess that are of the selected base type
        self.selected_base_type_bases = []
        # the currently selected base
        # This is what will be edited when the user selects a base to edit
        self.selected_base = None
        
        # the path to PersistentPlayerBases in the save file dictionary
        # stored as a list of keys/indices to navigate to the bases array
        self.bases_path = None
        # all bases loaded from the save file
        # this is the list of all bases in PersistentPlayerBases
        self.all_bases = []
        # the index of the currently selected base in the all_bases list
        self.selected_base_index = None
        # path to the backup of the original save file (.hg)
        self.original_save_file_backup_path = None

        # the UID of the owner of the save file
        self.save_file_owner_uid = None

    def load_save_files(self, save_file_directory: str = None):
        '''
        Load all save files from the save file directory.
        '''
        if save_file_directory is None:
            save_file_directory = self.save_file_directory
        else:
            self.save_file_directory = save_file_directory
        self.save_files = get_all_save_files(save_file_directory)

        #################################
        # UPDATE THE METADATA FUNTION IT DOES NOT WORK CORRECTLY!!!!
        #################################

        # update the save_file_metadata dictionary with the metadata for each save file
        for save_file in self.save_files:
            full_save_file_path = os.path.join(save_file_directory, save_file)
            self.save_file_metadata[save_file] = get_save_metadata(full_save_file_path)
        
    def select_save_file(self, save_file_name: str):
        '''
        Select a save file from the save files list.
        '''
        self.selected_save_file = save_file_name

    def get_save_file_metadata(self, save_file_name: str):
        '''
        Get the metadata for a save file.
        '''
        # Ensure the file name exists as a key in the save_file_metadata dictionary
        if save_file_name not in self.save_file_metadata:
            raise ValueError(f"Save file {save_file_name} not found")
        return self.save_file_metadata[save_file_name]

    def decompress_save_file(self, save_file_name: str, apply_key_mapping: bool = True):
        '''
        Decompress the save file into self.selected_save_file_dict
        Creates a backup of the original .hg file before decompressing.
        
        Args:
            save_file_name: Name of the save file to decompress
            apply_key_mapping: If True, deobfuscate keys using key mapping (default: True)
        '''
        # Ensure the file name exists as a key in the save_file_metadata dictionary
        if save_file_name not in self.save_files:
            raise ValueError(f"Save file {save_file_name} not found")
        
        full_save_file_path = os.path.join(self.save_file_directory, save_file_name)
        
        # Backup the original .hg file before decompressing
        backups_dir = self.project_directory / "backups" / "save files"
        if not backups_dir.exists():
            backups_dir.mkdir(parents=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"{Path(save_file_name).stem}_backup_{timestamp}.hg"
        self.original_save_file_backup_path = str(backups_dir / backup_filename)
        shutil.copy2(full_save_file_path, self.original_save_file_backup_path)
        print(f"Original save file backed up to: {self.original_save_file_backup_path}")
        
        self.selected_save_file_dict = extract_save_file(full_save_file_path, apply_key_mapping=apply_key_mapping)

        # save the decompressed save file to a json file in project directory backups\decompressed files directory
        # make the decompressed files directory if it doesn't exist
        decompressed_dir = self.project_directory / "backups" / "decompressed files"
        if not decompressed_dir.exists():
            decompressed_dir.mkdir(parents=True)
        backup_save_file_path = decompressed_dir / f"{save_file_name} - decompressed.json"
        save_json_file(self.selected_save_file_dict, str(backup_save_file_path))
        print(f"Decompressed save file saved to {backup_save_file_path}")

        return self.selected_save_file_dict
        
    def select_base_type(self, base_type: str):
        '''
        Select a base type from the selected save file. Must be either PlayerShipBase or ExternalPlanetBase.
        '''
        if base_type not in ["PlayerShipBase", "ExternalPlanetBase"]:
            raise ValueError(f"Invalid base type: {base_type}")
        self.selected_base_type = base_type


    def process_bases(self, save_file_json_path: str):
        '''
        An example function for processing basses from the prototype of this project.
        '''
        print(f"Processing save file: {save_file_json_path}")
        with open(save_file_json_path, 'r', encoding='utf-8') as f:
            save_file_dict = json.load(f)

        


        # Filter the base values to only corvettes
        print("Filtering base values to only corvettes")
        base_values = filter_base_by_type(base_values, "PlayerShipBase")


        # Save the base values to a json file
        with open("output/bases.json", "w", encoding='utf-8') as f:
            json.dump(base_values, f, indent=4, ensure_ascii=False)

        print(f"{len(base_values)} bases saved to output/bases.json")


        print("Exporting bases to csv")
        export_bases_to_csv(base_values, "output/bases_overview.csv")


    def load_bases(self):
        '''
        Load all bases from the selected save file and store them in self.all_bases.
        Also stores the path to PersistentPlayerBases for later use.
        '''
        if self.selected_save_file_dict is None:
            raise ValueError("No save file decompressed. Please decompress a save file first.")
        
        # Returns a generator of tuples (path, value)
        base_keys = list(find_key_recursively(self.selected_save_file_dict, "PersistentPlayerBases"))
        
        if not base_keys:
            raise ValueError("Could not find PersistentPlayerBases in save file")
        
        base_path, base_values = base_keys[0]
        self.bases_path = base_path
        self.all_bases = base_values
        
        print(f"Found bases at: {' > '.join(base_path)}")
        print(f"Number of corvettes: {get_number_of_bases_by_type(base_values, 'PlayerShipBase')}")
        print(f"Number of planetary bases: {get_number_of_bases_by_type(base_values, 'ExternalPlanetBase')}")
        print(f"Total bases loaded: {len(base_values)}")

    def get_bases_by_type(self, base_type: str):
        '''
        Get all bases of the specified base type.
        
        Args:
            base_type: The base type to filter by (e.g., "PlayerShipBase", "ExternalPlanetBase")
            
        Returns:
            List of base dictionaries matching the type
            
        Raises:
            ValueError: If no save file is decompressed or no bases are loaded
        '''
        if self.selected_save_file_dict is None:
            raise ValueError("No save file decompressed. Please decompress a save file first.")
        if not self.all_bases:
            raise ValueError("No bases loaded. Please call load_bases() first.")
        
        return filter_base_by_type(self.all_bases, base_type)
        
    def select_base(self, base_name: str):
        '''
        Select a base by name from the loaded bases.
        
        Args:
            base_name: The name of the base to select (string)
            
        Raises:
            ValueError: If no bases are loaded or base name not found
        '''
        if not self.all_bases:
            raise ValueError("No bases loaded. Please call load_bases() first.")
        
        # Search for the base by name
        for index, base in enumerate(self.all_bases):
            if base.get("Name", "") == base_name:
                self.selected_base = base
                self.selected_base_index = index
                print(f"Selected base: {base_name} (index: {index})")
                return base
        
        # If we get here, the base was not found
        raise ValueError(f"Base with name '{base_name}' not found in loaded bases")
    
    def get_selected_base_component_count(self):
        '''
        Get the component count (number of objects) from the currently selected base.
        Uses recursive key search to find the "Objects" key in the base structure.
        
        Returns:
            int: The number of components/objects in the selected base, or 0 if not found
            
        '''
        return self.get_numer_of_components_from_base(self.selected_base)


    def get_numer_of_components_from_base(self, base: dict):
        '''
        Get the number of components from a base. Will return 0 if the base does not have an Objects key.
        Args:
            base: The base to get the number of components from
        
        Returns:
            int: The number of components in the base
        
        Raises:
            ValueError: If no base is selected
        '''
        # First try direct access (most common case)
        if "Objects" in base:
            objects = base["Objects"]
            if isinstance(objects, list):
                return len(objects)
            else:
                return 0
        
        else:
            # This is the search that will likely run.
            # Recursively search for the Objects key in the selected base
            objects_keys = list(find_key_recursively(base, "Objects"))
            
            if objects_keys:
                # Get the first occurrence of Objects
                path, objects_value = objects_keys[0]
                if isinstance(objects_value, list):
                    return len(objects_value)
                else:
                    return 0
        
        # If the key isn't found after both searches, return 0
        return 0

    def get_save_owner_uid(self):
        '''
        Get the UID of the owner of the save file.

        returns:
            str: The UID of the owner of the save file
            None: If the UID is not found
        '''
        # It seems to be reliable to search "UsedDiscoveryOwnersV2" for the "UID" key across saves
        if self.selected_save_file_dict is None:
            raise ValueError("No save file decompressed. Please decompress a save file first.")
        used_discovery_owners_v2 = find_key_recursively(self.selected_save_file_dict, "UsedDiscoveryOwnersV2")
        if not used_discovery_owners_v2:
            raise ValueError("Could not find UsedDiscoveryOwnersV2 in save file")
        used_discovery_owners_v2_value = (list(used_discovery_owners_v2))[0]
        used_discovery_sub_dict = used_discovery_owners_v2_value[1][0]

        # Debug print the used_discovery_sub_dict
        # print(used_discovery_sub_dict)
        
        # Now that we found the UsedDiscoveryOwnersV2 key, we need to check if the "UID" key is in the value
        if "UID" in used_discovery_sub_dict:
            return used_discovery_sub_dict["UID"]
        else:
            return None
    
    def get_number_of_components_for_all_bases_in_save_file(self):
        '''
        Get the number of components for all bases in the save file.
        Helpful for check if you're approaching the max number of components in the save file.
        '''

        # Make sure a save dict is loaded first
        if self.selected_save_file_dict is None:
            raise ValueError("No save file decompressed. Please decompress a save file first.")

        # Make sure bases are loaded 
        if not self.all_bases:
            raise ValueError("No bases loaded. Make sure to load bases before fetching part count.")
        
        # Get the number of components for all bases
        # Slow proof of concept functionality right now. I will optomize this later.
        total_components = 0
        for base in self.all_bases:
            total_components += self.get_numer_of_components_from_base(base)

        return total_components

    def get_uid_from_base(self, base: dict):
        '''
        Get the UID from a base.
        returns:
            str: The UID of the base
            None: If the UID is not found
        '''
        uid_generator = find_key_recursively(base, "UID")
        if not uid_generator:
            return None
        try:
            uid_list = list(uid_generator)
            isolated_uid = uid_list[0][1]
            return isolated_uid
        except IndexError:
            return None

    def get_num_components_save_file_owner(self):
        '''
        Get the number of components for the owner of the save file.
        '''
        # Make sure a save dict is loaded first
        if self.selected_save_file_dict is None:
            raise ValueError("No save file decompressed. Please decompress a save file first.")
        # first get the owner uid
        owner_uid = self.get_save_owner_uid()
        if owner_uid is None:
            raise ValueError("Could not find owner UID in save file")
        self.save_file_owner_uid = owner_uid
        # Now go through a similar process to get_number_of_components_for_all_bases_in_save_file 
        # but filter the bases by the owner uid
        total_components = 0
        for base in self.all_bases:
            uid = self.get_uid_from_base(base)
            if uid == owner_uid:
                total_components += self.get_numer_of_components_from_base(base)
        return total_components
        
    
    def save_selected_base_to_json(self, output_path: str = None):
        '''
        Save the currently selected base to a JSON file.
        Creates a backup of the existing file if it already exists.
        
        Args:
            output_path: Optional path to save the base JSON file.
                        If None, saves to project_directory/output/bases/
        
        Raises:
            ValueError: If no base is selected
        '''
        if self.selected_base is None:
            raise ValueError("No base selected. Please select a base first using select_base().")
        
        # If no output path provided, use default location
        if output_path is None:
            output_dir = self.project_directory / "output" / "bases"
            if not output_dir.exists():
                output_dir.mkdir(parents=True)
            
            base_name = self.selected_base.get("Name", "unnamed_base")
            # Sanitize base name for filename
            safe_name = "".join(c for c in base_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_')
            output_path = str(output_dir / f"{safe_name}.json")
        
        # Create backup if file already exists
        if os.path.exists(output_path):
            from datetime import datetime
            backups_dir = self.project_directory / "backups" / "bases"
            if not backups_dir.exists():
                backups_dir.mkdir(parents=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{Path(output_path).stem}_backup_{timestamp}.json"
            backup_path = str(backups_dir / backup_filename)
            shutil.copy2(output_path, backup_path)
            print(f"Backup created: {backup_path}")
        
        # Save the base to JSON file
        save_json_file(self.selected_base, output_path)
        print(f"Selected base saved to: {output_path}")
        return output_path
    
    def load_selected_base_from_json(self, json_file_path: str):
        '''
        Load a base from a JSON file and set it as the selected base.
        This does not inject it into the save file - use inject_base_into_save_file() for that.
        
        Args:
            json_file_path: Path to the JSON file containing the base data
            
        Raises:
            FileNotFoundError: If the JSON file doesn't exist
            ValueError: If the JSON file is invalid
        '''
        if not os.path.exists(json_file_path):
            raise FileNotFoundError(f"Base JSON file not found: {json_file_path}")
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                base_data = json.load(f)
            
            # Validate that it looks like a base (has Name and BaseType)
            if not isinstance(base_data, dict):
                raise ValueError("Base JSON file must contain a dictionary")
            
            self.selected_base = base_data
            self.selected_base_index = None  # Reset index since this is a new base
            print(f"Base loaded from: {json_file_path}")
            print(f"Base name: {base_data.get('Name', 'Unknown')}")
            return base_data
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON file: {e}")
    
    def inject_selected_base_into_save_file(self):
        '''
        Inject the currently selected base back into the master selected_save_file_dict.
        This replaces the base at the selected_base_index with the current selected_base data.
        Creates a backup of the original base before replacing it.
        
        Raises:
            ValueError: If no save file is loaded, no bases are loaded, or no base is selected
        '''
        if self.selected_save_file_dict is None:
            raise ValueError("No save file decompressed. Please decompress a save file first.")
        
        if not self.all_bases:
            raise ValueError("No bases loaded. Please call load_bases() first.")
        
        if self.selected_base is None:
            raise ValueError("No base selected. Please select a base first using select_base().")
        
        if self.selected_base_index is None:
            raise ValueError("No base index available. Please select a base first using select_base().")
        
        # Backup the original base before replacing it
        original_base = self.all_bases[self.selected_base_index]
        base_name = original_base.get("Name", "Unknown")
        
        backups_dir = self.project_directory / "backups" / "bases"
        if not backups_dir.exists():
            backups_dir.mkdir(parents=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # Sanitize base name for filename
        safe_name = "".join(c for c in base_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_name = safe_name.replace(' ', '_')
        backup_filename = f"{safe_name}_backup_{timestamp}.json"
        base_backup_path = str(backups_dir / backup_filename)
        save_json_file(original_base, base_backup_path)
        print(f"Original base backed up to: {base_backup_path}")
        
        # Navigate to the PersistentPlayerBases array in the save file dictionary
        # This follows the same pattern as SaveFileManager._get_bases_array()
        current = self.selected_save_file_dict
        for key in self.bases_path[:-1]:
            if key.startswith("[") and key.endswith("]"):
                # List index - format is "[0]"
                idx = int(key[1:-1])
                current = current[idx]
            else:
                # Dict key
                current = current[key]
        
        # Replace the base at the selected index
        bases_array = current[self.bases_path[-1]]
        bases_array[self.selected_base_index] = self.selected_base
        
        # Also update our local copy to keep it in sync
        self.all_bases[self.selected_base_index] = self.selected_base
        
        print(f"Base injected into save file at index {self.selected_base_index}")
        return self.selected_base_index
    
    def recompress_save_file(self, output_path: str = None, mapping_file: str = None):
        '''
        Recompress the selected_save_file_dict back into a .hg file.
        This will reverse-map the keys, serialize to JSON, compress with LZ4, and write to file.
        If the output path is the same as the original save file, creates a backup first.
        
        Args:
            output_path: Optional path for the output .hg file.
                        If None, saves to project_directory/output/ with the original filename.
            mapping_file: Optional path to local mapping file. If None, uses cached or downloads from GitHub.
            
        Raises:
            ValueError: If no save file is decompressed
            ImportError: If required modules (lz4, key_mapper) are not available
        '''
        if self.selected_save_file_dict is None:
            raise ValueError("No save file decompressed. Please decompress a save file first.")
        
        # Import recompressor function
        try:
            from recompressor import recompress_save
        except ImportError:
            raise ImportError("recompressor.py not found. Please ensure it exists in the project directory.")
        
        # If no output path provided, use default location
        if output_path is None:
            output_dir = self.project_directory / "output"
            if not output_dir.exists():
                output_dir.mkdir()
            
            if self.selected_save_file:
                # Use the original save file name but in output directory
                output_path = str(output_dir / self.selected_save_file)
            else:
                # Generate a default name
                output_path = str(output_dir / "recompressed_save.hg")
        
        # Ensure output path ends with .hg
        if not output_path.endswith('.hg'):
            output_path += '.hg'
        
        # If output path is the same as the original save file, backup it first
        original_save_file_path = None
        if self.selected_save_file:
            original_save_file_path = os.path.join(self.save_file_directory, self.selected_save_file)
            if os.path.abspath(output_path) == os.path.abspath(original_save_file_path):
                # We're overwriting the original file, create a backup
                backups_dir = self.project_directory / "backups" / "save files"
                if not backups_dir.exists():
                    backups_dir.mkdir(parents=True)
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_filename = f"{Path(self.selected_save_file).stem}_before_recompress_{timestamp}.hg"
                backup_path = str(backups_dir / backup_filename)
                shutil.copy2(original_save_file_path, backup_path)
                print(f"Original save file backed up before recompression to: {backup_path}")
        
        # Recompress the save file
        print(f"Recompressing save file to: {output_path}")
        recompress_save(self.selected_save_file_dict, output_path, mapping_file)
        print(f"Save file successfully recompressed to: {output_path}")
        return output_path

