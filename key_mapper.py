#!/usr/bin/env python3
"""
No Man's Sky Key Mapper

Converts obfuscated keys to deobfuscated keys (or vice versa) using
the mapping from MBINCompiler.

Based on mapper.ts by Robert Maupin.
"""

import json
import sys
import os
from typing import Any, Dict, List, Optional
from urllib.request import urlopen
from urllib.error import URLError
from pathlib import Path
from datetime import datetime, timedelta

# Cache settings
CACHE_DIR_NAME = ".nms_mapping_cache"
CACHE_FILE_NAME = "mapping.json"
CACHE_MAX_AGE_DAYS = 7  # Re-download if cache is older than 7 days


def get_cache_path() -> Path:
    """
    Get the path to the cache directory.
    
    Returns:
        Path object for the cache directory
    """
    # Try to use the script's directory first, fallback to user's home directory
    script_dir = Path(__file__).parent
    cache_dir = script_dir / CACHE_DIR_NAME
    
    # Create cache directory if it doesn't exist
    cache_dir.mkdir(exist_ok=True)
    
    return cache_dir / CACHE_FILE_NAME


def is_cache_valid(cache_path: Path, max_age_days: int = CACHE_MAX_AGE_DAYS) -> bool:
    """
    Check if the cached mapping file is valid (exists and not too old).
    
    Args:
        cache_path: Path to the cached mapping file
        max_age_days: Maximum age in days before cache is considered stale
        
    Returns:
        True if cache is valid, False otherwise
    """
    if not cache_path.exists():
        return False
    
    try:
        # Check file modification time
        mod_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
        age = datetime.now() - mod_time
        
        if age > timedelta(days=max_age_days):
            return False
        
        # Also verify it's valid JSON
        with open(cache_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Check if it has the expected structure
            if isinstance(data, dict) and "Mapping" in data:
                return len(data["Mapping"]) > 0
            elif isinstance(data, list):
                return len(data) > 0
        
        return False
    except (OSError, json.JSONDecodeError):
        return False


def load_cached_mapping(cache_path: Path) -> List[Dict[str, str]]:
    """
    Load mapping from cache file.
    
    Args:
        cache_path: Path to the cached mapping file
        
    Returns:
        List of mapping dictionaries
    """
    with open(cache_path, 'r', encoding='utf-8') as f:
        mapping_data = json.load(f)
    
    if isinstance(mapping_data, dict) and "Mapping" in mapping_data:
        return mapping_data["Mapping"]
    elif isinstance(mapping_data, list):
        return mapping_data
    else:
        raise ValueError("Unexpected cached mapping file format")


def save_mapping_to_cache(mapping: List[Dict[str, str]], cache_path: Path):
    """
    Save mapping to cache file.
    
    Args:
        mapping: The mapping data to save
        cache_path: Path where to save the cache
    """
    # Save in the same format as the original (with libMBIN_version if available)
    cache_data = {
        "libMBIN_version": "cached",
        "cached_at": datetime.now().isoformat(),
        "Mapping": mapping
    }
    
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, indent=2, ensure_ascii=False)


def fetch_mapping(use_cache: bool = True) -> List[Dict[str, str]]:
    """
    Fetch the latest key mapping from MBINCompiler GitHub releases.
    
    Args:
        use_cache: If True, check cache first and save downloaded mapping to cache
        
    Returns:
        List of mapping dictionaries with 'Key' and 'Value' fields
    """
    cache_path = get_cache_path()
    
    # Check cache first if enabled
    if use_cache and is_cache_valid(cache_path):
        print("Using cached mapping file...")
        try:
            mapping = load_cached_mapping(cache_path)
            print(f"Loaded {len(mapping)} entries from cache.")
            return mapping
        except Exception as e:
            print(f"Warning: Failed to load cache ({e}), downloading fresh copy...")
            # Continue to download
    
    # Download from GitHub
    mapping_url = (
        "https://github.com/monkeyman192/MBINCompiler/releases/latest/download/mapping.json"
    )
    
    print("Downloading mapping from GitHub...")
    try:
        with urlopen(mapping_url, timeout=10) as response:
            mapping_data = json.loads(response.read().decode('utf-8'))
        
        # The mapping file has structure: {"libMBIN_version": "...", "Mapping": [...]}
        if isinstance(mapping_data, dict) and "Mapping" in mapping_data:
            mapping = mapping_data["Mapping"]
            print(f"Success! Downloaded mapping with {len(mapping)} entries.")
        elif isinstance(mapping_data, list):
            # Sometimes it might be just a list
            mapping = mapping_data
            print(f"Success! Downloaded mapping with {len(mapping)} entries.")
        else:
            raise ValueError("Unexpected mapping file format")
        
        # Save to cache if enabled
        if use_cache:
            try:
                save_mapping_to_cache(mapping, cache_path)
                print(f"Cached mapping to {cache_path}")
            except Exception as e:
                print(f"Warning: Failed to save cache ({e}), but continuing...")
        
        return mapping
            
    except URLError as e:
        # If download fails, try to use cache even if it's old
        if use_cache and cache_path.exists():
            print(f"Warning: Download failed ({e}), trying to use cached mapping (may be outdated)...")
            try:
                mapping = load_cached_mapping(cache_path)
                print(f"Using cached mapping with {len(mapping)} entries (may be outdated).")
                return mapping
            except Exception:
                pass
        raise ConnectionError(f"Failed to download mapping: {e}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse mapping JSON: {e}")


def load_mapping_from_file(mapping_file: str) -> List[Dict[str, str]]:
    """
    Load key mapping from a local JSON file.
    
    Args:
        mapping_file: Path to the mapping JSON file
        
    Returns:
        List of mapping dictionaries
    """
    with open(mapping_file, 'r', encoding='utf-8') as f:
        mapping_data = json.load(f)
    
    if isinstance(mapping_data, dict) and "Mapping" in mapping_data:
        return mapping_data["Mapping"]
    elif isinstance(mapping_data, list):
        return mapping_data
    else:
        raise ValueError("Unexpected mapping file format")


def map_keys(json_obj: Any, mapping: List[Dict[str, str]]) -> Any:
    """
    Recursively map obfuscated keys to deobfuscated keys.
    
    Args:
        json_obj: The JSON object to map (can be dict, list, or primitive)
        mapping: List of mapping dictionaries with 'Key' (obfuscated) and 'Value' (deobfuscated)
        
    Returns:
        New object with mapped keys
    """
    if isinstance(json_obj, list):
        return [map_keys(item, mapping) for item in json_obj]
    elif isinstance(json_obj, dict):
        new_json = {}
        # Create a lookup dictionary for faster searching
        key_map = {m["Key"]: m["Value"] for m in mapping}
        
        for key, value in json_obj.items():
            # Look up the mapped key
            mapped_key = key_map.get(key)
            if mapped_key:
                new_json[mapped_key] = map_keys(value, mapping)
            else:
                # Keep original key if no mapping found
                new_json[key] = map_keys(value, mapping)
        return new_json
    else:
        # Primitive value (string, number, bool, None) - return as-is
        return json_obj


def reverse_map_keys(json_obj: Any, mapping: List[Dict[str, str]]) -> Any:
    """
    Recursively map deobfuscated keys back to obfuscated keys.
    
    Args:
        json_obj: The JSON object to reverse map
        mapping: List of mapping dictionaries with 'Key' (obfuscated) and 'Value' (deobfuscated)
        
    Returns:
        New object with reverse-mapped keys
    """
    if isinstance(json_obj, list):
        return [reverse_map_keys(item, mapping) for item in json_obj]
    elif isinstance(json_obj, dict):
        new_json = {}
        # Create a reverse lookup dictionary
        value_map = {m["Value"]: m["Key"] for m in mapping}
        
        for key, value in json_obj.items():
            # Look up the original obfuscated key
            original_key = value_map.get(key)
            if original_key:
                new_json[original_key] = reverse_map_keys(value, mapping)
            else:
                # Keep original key if no reverse mapping found
                new_json[key] = reverse_map_keys(value, mapping)
        return new_json
    else:
        # Primitive value - return as-is
        return json_obj


def is_mapped(json_obj: dict) -> bool:
    """
    Check if a JSON object is already mapped (has deobfuscated keys).
    
    Args:
        json_obj: The JSON object to check
        
    Returns:
        True if the object appears to be mapped (has "Version" key), False otherwise
    """
    return "Version" in json_obj


def get_mapping(mapping_file: Optional[str] = None, use_cache: bool = True) -> List[Dict[str, str]]:
    """
    Get the key mapping from file or download from GitHub (with caching).
    
    Args:
        mapping_file: Optional path to local mapping file. If None, downloads from GitHub.
        use_cache: If True, use cache for downloaded mappings (only applies when downloading)
        
    Returns:
        List of mapping dictionaries
    """
    if mapping_file and os.path.exists(mapping_file):
        return load_mapping_from_file(mapping_file)
    else:
        return fetch_mapping(use_cache=use_cache)


def clear_cache():
    """Clear the cached mapping file."""
    cache_path = get_cache_path()
    if cache_path.exists():
        cache_path.unlink()
        print(f"Cache cleared: {cache_path}")
        return True
    else:
        print("No cache file to clear.")
        return False


def main():
    """Standalone mapper tool (for testing/manual use)"""
    if len(sys.argv) < 2:
        print("No Man's Sky Key Mapper")
        print("=" * 50)
        print("\nUsage: python key_mapper.py <input.json> [mapping.json] [--no-cache] [--clear-cache]")
        print("\nOptions:")
        print("  --no-cache       Don't use cache (always download fresh)")
        print("  --clear-cache    Clear the cached mapping file")
        print("\nExample:")
        print("  python key_mapper.py obfuscated.json")
        print("  python key_mapper.py obfuscated.json custom_mapping.json")
        print("  python key_mapper.py --clear-cache")
        print("\nIf mapping.json is not provided, it will be downloaded from GitHub.")
        print("Mapping files are cached for 7 days to avoid repeated downloads.")
        sys.exit(1)
    
    # Parse arguments
    args = sys.argv[1:]
    input_file = None
    mapping_file = None
    use_cache = True
    clear_cache_flag = False
    
    i = 0
    while i < len(args):
        if args[i] == "--no-cache":
            use_cache = False
        elif args[i] == "--clear-cache":
            clear_cache_flag = True
        elif not input_file and args[i] != "--no-cache" and args[i] != "--clear-cache":
            input_file = args[i]
        elif not mapping_file and args[i] != "--no-cache" and args[i] != "--clear-cache":
            mapping_file = args[i]
        i += 1
    
    # Handle clear cache option
    if clear_cache_flag:
        clear_cache()
        if not input_file:
            sys.exit(0)
    
    if not input_file:
        print("Error: No input file specified")
        sys.exit(1)
    
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found")
        sys.exit(1)
    
    print(f"Loading JSON from: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        try:
            file_json = json.load(f)
        except json.JSONDecodeError:
            # Try removing last character (sometimes there's trailing data)
            with open(input_file, 'r', encoding='utf-8') as f2:
                content = f2.read()
                file_json = json.loads(content[:-1])
    
    # Check if already mapped
    is_already_mapped = isinstance(file_json, dict) and is_mapped(file_json)
    
    print(f"JSON is {'already mapped' if is_already_mapped else 'obfuscated'}")
    print("Loading mapping...")
    
    mapping = get_mapping(mapping_file, use_cache=use_cache)
    
    # Apply appropriate mapping function
    mapping_function = reverse_map_keys if is_already_mapped else map_keys
    direction = "reverse-mapping" if is_already_mapped else "mapping"
    
    print(f"{direction.capitalize()} keys...")
    mapped_save = mapping_function(file_json, mapping)
    
    # Write back to file
    indent = None if is_already_mapped else 2  # Minify when compressing (reverse mapping)
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(mapped_save, f, indent=indent, ensure_ascii=False)
    
    print("Done!")


if __name__ == "__main__":
    main()

