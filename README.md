# No Man's Sky Base Modifier


![Save Tool Screenshot](images/save%20tool.png)


A Python-based save file editor for No Man's Sky that allows you to extract, view, edit, and inject base data (including Corvettes and Planetary Bases) from your save files. The tool features a modern GUI built with PySide6 and provides a comprehensive API for programmatic save file manipulation.

## Overview

This tool enables you to:
- **Decompress** No Man's Sky save files (`.hg` format) into readable JSON
- **Extract** individual bases (Corvettes and Planetary Bases) from save files
- **Edit** base data using a built-in JSON editor
- **Inject** modified bases back into save files
- **Recompress** save files back to `.hg` format for use in-game
- **Automatically backup** original files before any modifications

The save files use LZ4 compression and obfuscated JSON keys. This tool handles decompression, key deobfuscation (using mappings from MBINCompiler), and provides a user-friendly interface for base management.

## Features

- **GUI Application**: Modern, NMS-inspired interface built with PySide6
- **API Support**: Programmatic access via `SaveEditor` class in `save_editor.py`
- **Automatic Backups**: Original save files are backed up before any modifications
- **Base Filtering**: Filter bases by type (Corvettes, Planetary Bases, or Both)
- **JSON Editor**: Built-in editor for viewing and modifying base data
- **Key Mapping**: Automatic deobfuscation of save file keys using cached mappings

## Prerequisites

- Python 3.8 or higher
- Windows (Linux support is planned but not yet implemented)
- No Man's Sky installed (to access save files)

## Installation

1. **Clone or download this repository**

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   - **Windows:**
     ```bash
     .\venv\Scripts\activate
     ```
   - **Linux/Mac:**
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies:**
   ```bash
   pip install PySide6 lz4
   ```
   
   Note: If you have a `requirements.txt` file, you can use:
   ```bash
   pip install -r requirements.txt
   ```

## How to Use

### Using the GUI

**[IMPORTANT]** ALWAYS MANUALLY BACK UP YOUR SAVE FILE BEFORE ANY EDITS!!!

1. **Launch the application:**
   ```bash
   python run_gui.py
   ```

2. **Select a save file:**
   - The dropdown will automatically detect save files from your default No Man's Sky save directory.
   - By default, the last save file you loaded in-game will be selected.
   - You can choose a different save file from the dropdown.

3. **Load the save file:**
   - Click the "Load File" button.
   - The save file will be decompressed and parsed into JSON.
   - Watch the progress bar at the bottom — once complete, the base type selection buttons will become active.

4. **Select a base type:**
   - Choose **Corvettes** to view only freighter bases.
   - Choose **Planetary Bases** to view only planet bases.
   - Choose **Both** to view all bases.

5. **Select a base:**
   - Click on a base name in the **Select Base** section.
   - The base data will be displayed in the JSON editor.

6. **Open the editor:**
   - Click **Edit Selected Base** to open the editor.

7. **Export and edit base data:**
   - Click the **Copy** button in the editor to copy the base data.
   - Paste this data into djmonkeyuk's base editor ([Nexus Mods link](https://www.nexusmods.com/nomanssky/mods/2598)):
     1. In djmonkeyuk's base builder, click the top left icon → “Import base from NMS”.
     2. Paste the copied JSON.
     
        ![import to base editor](images/import%20from%20nms%201.png)
     3. Make your edits in the base builder.
     
        ![example edits](images/example%20of%20imported%20ship.png)
     4. To export, go to the top left menu → "Export to NMS" → Copy.
     
        ![export from base editor](images/copy%20to%20clipboard.png)


8. **Apply changes in the save editor:**
   - Click the **pencil icon** in the editor.
   - Use `Ctrl+A`, `Ctrl+V` to paste your edited base/ship data.
   - Click **Save**.

9. **Save changes:**
   - After making edits, you can inject the base back into the save file.
   - The tool will create backups before making any changes.


### Using the API

The `SaveEditor` class in `save_editor.py` provides programmatic access to all functionality:

```python
from save_editor import SaveEditor

# Initialize the editor
editor = SaveEditor()

# Load save files
editor.load_save_files()

# Select and decompress a save file
editor.select_save_file("save7.hg")
editor.decompress_save_file("save7.hg")

# Load bases
editor.load_bases()

# Get bases by type
corvettes = editor.get_bases_by_type("PlayerShipBase")
planetary_bases = editor.get_bases_by_type("ExternalPlanetBase")

# Select a specific base
editor.select_base("My Base Name")

# Save base to JSON file
editor.save_selected_base_to_json("output/my_base.json")

# Load base from JSON
editor.load_selected_base_from_json("output/my_base.json")

# Inject base back into save file
editor.inject_selected_base_into_save_file()

# Recompress save file
editor.recompress_save_file("output/modified_save.hg")
```


## Important Notes

- **Backups**: The tool automatically creates backups before any modifications. Original save files are backed up to `backups/save files/`, and bases are backed up to `backups/bases/`.

- **Save File Format**: No Man's Sky save files use LZ4 compression and obfuscated JSON keys. This tool handles both automatically.

- **Core Logic**: The driving logic of this project is stored in `save_editor.py`. This module contains all the function calls for decompressing saves, finding bases, injecting JSON code, etc., and can be used as a standalone API.

- **GUI**: The GUI (`gui/` directory) serves as a wrapper around `save_editor.py`.

- **Disclaimer**: While I did write most of the core logic, the gui was created with heavy AI assistance.

- **Metadata Extraction**: The metadata extraction feature is currently under development and may need improvements.

## Troubleshooting

- **Save files not detected**: Ensure No Man's Sky is installed and you have save files in the default directory
- **Decompression errors**: Make sure you have the `lz4` package installed
- **Key mapping errors**: The tool will attempt to download key mappings automatically. If this fails, check your internet connection

## Contributing

Contributions are welcome! This project was created in spare time over two days, so there's definitely room for improvement. Areas that need work:

- Linux support (currently Windows-focused)
- Metadata extraction improvements
- Better error handling and validation
- Logging


Feel free to reach out with improvements, bug reports, or feature requests.

## Credits & Acknowledgments

This project builds upon the excellent work of the No Man's Sky modding community. Special thanks to:

### Save File Decompression
- **Robert Maupin** - Original author of the save file decompressor and key mapper
  - [NMS-Save-Decoder](https://github.com/NMSCD/NMS-Save-Decoder/) - The original Python script for decompressing No Man's Sky save files
  - This project's `utils/save_extractor.py` and `key_mapper.py` are based on Robert Maupin's work

### Key Mapping
- **monkeyman192** - Creator of MBINCompiler
  - [MBINCompiler](https://github.com/monkeyman192/MBINCompiler) - Provides the key mapping files used for deobfuscating save file keys
  - This project uses MBINCompiler's mapping.json to convert obfuscated keys to readable format

### Base Editor
- **djmonkeyuk** - Creator of the No Man's Sky Base Editor
  - [Base Editor on Nexus Mods](https://www.nexusmods.com/nomanssky/mods/2598) - A powerful visual base editor that works seamlessly with this tool
  - Users can export base JSON from this tool, edit it in djmonkeyuk's editor, and import it back

Without these foundational projects, this tool would not have been possible. Thank you to all the contributors in the No Man's Sky modding community!

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

© 2025 NightCodeOfficial. This software is provided “as is,” without warranty of any kind.
