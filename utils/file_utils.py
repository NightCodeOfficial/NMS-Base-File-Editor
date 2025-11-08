import os
import platform
import json
from datetime import datetime
from pathlib import Path

# Get the project root directory (parent of utils directory)
_PROJECT_ROOT = Path(__file__).parent.parent
SETTINGS_DIR = _PROJECT_ROOT / "settings"
FILE_SETTINGS_PATH = SETTINGS_DIR / "file_settings.json"


def _ensure_settings_dir():
    """Ensure the settings directory exists."""
    SETTINGS_DIR.mkdir(exist_ok=True)


def _load_file_settings() -> dict:
    """Load file settings from JSON file."""
    _ensure_settings_dir()
    if FILE_SETTINGS_PATH.exists():
        try:
            with open(FILE_SETTINGS_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def _save_file_settings(settings: dict):
    """Save file settings to JSON file."""
    _ensure_settings_dir()
    settings["last_updated"] = datetime.now().isoformat()
    with open(FILE_SETTINGS_PATH, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


def _update_file_settings(**updates):
    """Update file settings with new values."""
    settings = _load_file_settings()
    settings.update(updates)
    _save_file_settings(settings)


def get_current_user()->str:
    user = os.getlogin()
    _update_file_settings(current_user=user, user_last_accessed=datetime.now().isoformat())
    return user


def get_operating_system()->str:
    os_name = platform.system()
    _update_file_settings(operating_system=os_name, os_last_accessed=datetime.now().isoformat())
    return os_name


def save_json_file(json_data: dict, file_path: str):
    '''
    Save a dictionary to a json file.
    '''
    with open(file_path, 'w') as f:
        json.dump(json_data, f, indent=4)


def get_default_save_directory()->str:
    if get_operating_system() == "Windows":
        nms_roaming_directory = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "HelloGames", "NMS")
        # The save directory should be one more directory down from the roaming directory with the name st_xxxxxxxx
        # where xxxxxxxx is the steam id of the user.
        # I will just use any number as a wildcardfor the steam id for now.
        
        # Check if the save directory exists by searching which directories are within the roaming directory and contain the string "st_"
        for directory in os.listdir(nms_roaming_directory):
            if "st_" in directory:
                save_directory = os.path.join(nms_roaming_directory, directory)
                print(f"Save directory found: {save_directory}")
                _update_file_settings(
                    default_save_directory=save_directory,
                    save_directory_last_accessed=datetime.now().isoformat()
                )
                return save_directory
        print("No save directory found")
        _update_file_settings(
            default_save_directory=None,
            save_directory_last_accessed=datetime.now().isoformat()
        )
        return None
    else:
        print("Operating systems other than Windows are not supported yet")
        print("Please contact the developer with your save directory to add support for your operating system")
        _update_file_settings(
            default_save_directory=None,
            save_directory_last_accessed=datetime.now().isoformat()
        )
        return None


def get_all_save_files(save_directory)->list[str]:
    '''
    Get all save files from the save directory.
    returns a list of strings of the save file names.
    '''
    if save_directory is None:
        _update_file_settings(
            save_files=[],
            save_files_last_accessed=datetime.now().isoformat()
        )
        return []
    
    files = [file for file in os.listdir(save_directory) if file.startswith("save") and file.endswith(".hg")]
    _update_file_settings(
        save_files=files,
        save_files_count=len(files),
        save_files_last_accessed=datetime.now().isoformat(),
        save_directory_used=save_directory
    )
    return files
