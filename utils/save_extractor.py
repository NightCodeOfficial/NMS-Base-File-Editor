"""
Save File Extractor Utility

Extracts JSON data from No Man's Sky .hg save files.
Based on the decompressor.py script by Robert Maupin.
https://github.com/NMSCD/NMS-Save-Decoder/
"""

import json
import io
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import lz4.block
except ImportError:
    raise ImportError("lz4 module not found. Please install it with: pip install lz4")

# Import key mapping functions (optional)
try:
    from key_mapper import map_keys, get_mapping
    KEY_MAPPER_AVAILABLE = True
except ImportError:
    KEY_MAPPER_AVAILABLE = False


def uint32(data: bytes) -> int:
    """Convert 4 bytes to a little endian unsigned integer."""
    return int.from_bytes(data, byteorder='little', signed=False) & 0xffffffff


def decompress_save_file(data: bytes) -> bytes:
    """
    Decompresses a No Man's Sky save file that uses LZ4 compression.
    
    The format is:
    - LZ4-compressed blocks, each with:
      - Magic: 0xfeeda1e5 (4 bytes)
      - Compressed size (4 bytes)
      - Uncompressed size (4 bytes)
      - Padding (4 bytes)
      - Compressed data
    
    Args:
        data: Raw bytes from the .hg file
        
    Returns:
        Decompressed bytes
    """
    size = len(data)
    din = io.BytesIO(data)
    out = bytearray()
    
    while din.tell() < size:
        magic = uint32(din.read(4))
        if magic != 0xfeeda1e5:
            # If we're not at a block boundary, try to find the next block
            # or we've reached the end
            if din.tell() >= size:
                break
            # Try to find the next block
            remaining = din.read()
            next_block = remaining.find(b'\xe5\xa1\xed\xfe')
            if next_block == -1:
                break
            din.seek(din.tell() - len(remaining) + next_block)
            magic = uint32(din.read(4))
            if magic != 0xfeeda1e5:
                break
        
        compressedSize = uint32(din.read(4))
        uncompressedSize = uint32(din.read(4))
        din.seek(4, 1)  # skip 4 bytes padding
        compressed_data = din.read(compressedSize)
        
        if len(compressed_data) < compressedSize:
            break
        
        try:
            decompressed_block = lz4.block.decompress(compressed_data, uncompressed_size=uncompressedSize)
            out += decompressed_block
        except Exception as e:
            raise ValueError(f"Failed to decompress block: {e}")
    
    return bytes(out)


def extract_json_from_hg(hg_file_path: str) -> Dict[str, Any]:
    """
    Extract JSON from a No Man's Sky .hg save file.
    
    This function:
    1. Reads the .hg file
    2. Decompresses it using LZ4
    3. Parses the JSON (which has obfuscated keys)
    
    Args:
        hg_file_path: Path to the .hg save file
        
    Returns:
        Dictionary containing the parsed JSON data
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file is invalid or can't be decompressed/parsed
    """
    file_path = Path(hg_file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Save file not found: {hg_file_path}")
    
    with open(file_path, 'rb') as f:
        data = f.read()
    
    # Check for minimum file size
    if len(data) < 18:
        raise ValueError("File too short to be a valid save file")
    
    # Decompress the file
    decompressed_data = decompress_save_file(data)
    
    if len(decompressed_data) == 0:
        raise ValueError("Failed to decompress file - might not be a valid save file")
    
    # The decompressed data should be pure JSON
    try:
        json_str = decompressed_data.decode('utf-8')
        
        # Try to parse the JSON
        try:
            data = json.loads(json_str)
            return data
        except json.JSONDecodeError as e:
            # If there's "Extra data", it means we parsed a complete JSON object
            # but there's more data after it. Extract just the first complete object.
            if "Extra data" in str(e):
                # Use JSONDecoder to parse just the first object
                decoder = json.JSONDecoder()
                obj, idx = decoder.raw_decode(json_str)
                return obj
            else:
                # Other JSON errors - try to find the first complete object
                json_start = json_str.find('{')
                if json_start == -1:
                    raise ValueError(f"Could not find JSON in decompressed data: {e}")
                
                # Try to find the matching closing brace
                brace_count = 0
                end_pos = -1
                for i in range(json_start, len(json_str)):
                    if json_str[i] == '{':
                        brace_count += 1
                    elif json_str[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_pos = i + 1
                            break
                
                if end_pos > 0:
                    partial_json = json_str[json_start:end_pos]
                    data = json.loads(partial_json)
                    return data
                else:
                    raise ValueError(f"Could not parse JSON from decompressed data: {e}")
                    
    except UnicodeDecodeError as e:
        raise ValueError(f"Decompressed data is not valid UTF-8: {e}")


def extract_save_file(
    hg_file_path: str,
    apply_key_mapping: bool = True,
    mapping_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extract JSON from a No Man's Sky .hg save file with optional key mapping.
    
    This is the main utility function for extracting save files.
    It handles decompression, JSON parsing, and optional key deobfuscation.
    
    Args:
        hg_file_path: Path to the .hg save file
        apply_key_mapping: If True, attempt to deobfuscate keys using key mapping
        mapping_file: Optional path to a local mapping file. If None, will attempt
                     to download/use cached mapping.
        
    Returns:
        Dictionary containing the parsed JSON data (with deobfuscated keys if mapping was applied)
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file is invalid or can't be decompressed/parsed
        ImportError: If key mapping is requested but key_mapper is not available
    """
    # Extract the JSON data
    data = extract_json_from_hg(hg_file_path)
    
    # Apply key mapping if requested and available
    if apply_key_mapping:
        if not KEY_MAPPER_AVAILABLE:
            raise ImportError(
                "Key mapping requested but key_mapper.py is not available. "
                "Set apply_key_mapping=False to use obfuscated keys."
            )
        
        try:
            mapping = get_mapping(mapping_file)
            data = map_keys(data, mapping)
            print(f"Save file decompressed and key mapping applied successfully")
        except Exception as e:
            raise ValueError(f"Failed to apply key mapping: {e}")
    
    return data

