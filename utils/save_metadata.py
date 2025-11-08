"""
Save File Metadata Extractor

Extracts basic metadata from No Man's Sky .hg save files without fully
decompressing them. This allows quick inspection of save files.
"""

import json
import os
import io
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any
import re

try:
    import lz4.block
except ImportError:
    raise ImportError("lz4 module not found. Please install it with: pip install lz4")

try:
    from key_mapper import get_mapping, map_keys, get_cache_path, load_cached_mapping
    KEY_MAPPER_AVAILABLE = True
except ImportError:
    KEY_MAPPER_AVAILABLE = False


def uint32(data: bytes) -> int:
    """Convert 4 bytes to a little endian unsigned integer."""
    return int.from_bytes(data, byteorder='little', signed=False) & 0xffffffff


def decompress_first_block(data: bytes, max_bytes: Optional[int] = None) -> bytes:
    """
    Decompress only the first block (or enough blocks to get max_bytes) from a .hg file.
    
    Args:
        data: The raw .hg file data
        max_bytes: Maximum number of bytes to decompress. If None, decompresses first block only.
        
    Returns:
        Decompressed bytes from the first block(s)
    """
    size = len(data)
    din = io.BytesIO(data)
    out = bytearray()
    
    # Read first block
    if din.tell() >= size:
        return bytes(out)
    
    magic = uint32(din.read(4))
    if magic != 0xfeeda1e5:
        # Try to find the first block
        remaining = din.read()
        next_block = remaining.find(b'\xe5\xa1\xed\xfe')
        if next_block == -1:
            return bytes(out)
        din.seek(next_block)
        magic = uint32(din.read(4))
        if magic != 0xfeeda1e5:
            return bytes(out)
    
    compressedSize = uint32(din.read(4))
    uncompressedSize = uint32(din.read(4))
    din.seek(4, 1)  # skip 4 bytes padding
    compressed_data = din.read(compressedSize)
    
    if len(compressed_data) < compressedSize:
        return bytes(out)
    
    try:
        decompressed_block = lz4.block.decompress(compressed_data, uncompressed_size=uncompressedSize)
        
        # If max_bytes is specified and we need more, decompress additional blocks
        if max_bytes is None:
            return decompressed_block
        
        out.extend(decompressed_block)
        
        # Continue decompressing blocks until we have enough data
        while len(out) < max_bytes and din.tell() < size:
            magic = uint32(din.read(4))
            if magic != 0xfeeda1e5:
                break
            
            compressedSize = uint32(din.read(4))
            uncompressedSize = uint32(din.read(4))
            din.seek(4, 1)  # skip padding
            compressed_data = din.read(compressedSize)
            
            if len(compressed_data) < compressedSize:
                break
            
            try:
                decompressed_block = lz4.block.decompress(compressed_data, uncompressed_size=uncompressedSize)
                out.extend(decompressed_block)
            except Exception:
                break
        
        # Return only up to max_bytes
        return bytes(out[:max_bytes])
        
    except Exception as e:
        return bytes(out)


def process_json_string_to_valid_json(json_str: str) -> str:
    """
    Process a JSON string to make it valid.
    """
    # The decompressed json string is very likely to not be a valid json
    # It will be in json format, but like not have all its {} closed and will be cut off at the end.
    # We first need to determine if the json string is valid.
    # If not, continue to process it to make it valid.
    # To process, I will cut off the last invalid key/value pair and then add enough } to close the json string.
    # Example of the end of the json string:
    # "eK9": false,
    # "WQX": true,
    # "fH8": "",
    # "xDJ":
    # In this case, I would cut off the "xDJ": then detect how many } are needed to close the json string.
    # I would then add the necessary } to close the json string.

    # First, I need to determine if the json string is valid.
    try:
        json.loads(json_str)
        return json_str
    except json.JSONDecodeError:
        # Try to parse as much as possible from the start using raw_decode
        # This will parse the maximum valid prefix of the JSON string
        decoder = json.JSONDecoder()
        try:
            obj, idx = decoder.raw_decode(json_str)
            # If we successfully parsed something, return it as valid JSON
            # Validate that the dumped JSON is actually valid
            result = json.dumps(obj, ensure_ascii=False)
            json.loads(result)  # Validate it
            return result
        except (json.JSONDecodeError, ValueError, TypeError):
            # If raw_decode fails completely, we need to manually fix the JSON
            # by removing incomplete trailing content and closing structures
            truncated = json_str.rstrip()
            
            # Remove incomplete trailing key/value pairs
            # Pattern 1: Incomplete key with colon: "key":
            truncated = re.sub(r'[,:\s]*"[^"]*"\s*:\s*$', '', truncated)
            # Pattern 2: Incomplete key without colon: "key"
            truncated = re.sub(r'[,:\s]*"[^"]*"\s*$', '', truncated)
            # Pattern 3: Incomplete key without closing quote: "key
            truncated = re.sub(r'[,:\s]*"[^"]*$', '', truncated)
            
            # Remove trailing comma or colon
            truncated = truncated.rstrip().rstrip(',').rstrip(':').rstrip()
            
            # Remove any trailing incomplete structures by working backwards
            # Keep removing characters until we find a valid ending point
            while truncated:
                last_char = truncated[-1]
                
                # If we end with comma or colon, remove it
                if last_char in ',:':
                    truncated = truncated[:-1].rstrip()
                    continue
                
                # If we end with a quote, check if it's a complete string
                if last_char == '"':
                    # Try to find matching opening quote (handling escaped quotes)
                    quote_pos = len(truncated) - 1
                    escaped = False
                    found_match = False
                    for i in range(quote_pos - 1, -1, -1):
                        if truncated[i] == '\\':
                            escaped = not escaped
                            continue
                        if truncated[i] == '"' and not escaped:
                            found_match = True
                            break
                        escaped = False
                    
                    if not found_match:
                        # Incomplete string, remove it
                        truncated = truncated[:quote_pos].rstrip().rstrip(':').rstrip(',').rstrip()
                        continue
                
                # If we get here, we have a potentially valid ending point
                break
            
            # Count unmatched braces and brackets
            open_braces = truncated.count('{') - truncated.count('}')
            open_brackets = truncated.count('[') - truncated.count(']')
            
            # Remove any trailing comma before adding closing braces
            truncated = truncated.rstrip().rstrip(',')
            
            # Add closing brackets first (inner structures), then braces (outer structures)
            fixed = truncated + (']' * max(0, open_brackets)) + ('}' * max(0, open_braces))
            
            # Validate the result
            try:
                json.loads(fixed)
                return fixed
            except json.JSONDecodeError:
                # If still invalid, try a more aggressive approach:
                # Find the last complete structure and truncate there
                last_brace = truncated.rfind('}')
                last_bracket = truncated.rfind(']')
                last_valid_pos = max(last_brace, last_bracket)
                
                if last_valid_pos >= 0:
                    # Truncate to the last complete structure
                    truncated = truncated[:last_valid_pos + 1]
                    open_braces = truncated.count('{') - truncated.count('}')
                    open_brackets = truncated.count('[') - truncated.count(']')
                    fixed = truncated + (']' * max(0, open_brackets)) + ('}' * max(0, open_braces))
                else:
                    # No complete structures found, just close what we have
                    fixed = truncated + (']' * max(0, open_brackets)) + ('}' * max(0, open_braces))
                
                # Validate the final result before returning
                try:
                    json.loads(fixed)
                    return fixed
                except json.JSONDecodeError:
                    # If still invalid, return empty object as last resort
                    return "{}"
        


def extract_metadata_from_partial_json(json_str: str, use_key_mapping: bool = True) -> Dict[str, Any]:
    """
    Extract metadata from a partial JSON string.
    
    Tries to extract key fields even if the JSON is incomplete.
    Can use key mapping to deobfuscate keys if available.
    
    Args:
        json_str: Partial JSON string (may be incomplete)
        use_key_mapping: If True and key_mapper is available, deobfuscate keys first
        
    Returns:
        Dictionary with metadata fields
    """
    metadata = {
        "version": None,
        "platform": None,
        "active_context": None,
        "save_name": None,
        "is_expedition": False,
        "expedition_type": None
    }
    
    # Try to get key mapping if available
    mapping = None
    if use_key_mapping and KEY_MAPPER_AVAILABLE:
        try:
            # Try to use cached mapping first
            cache_path = get_cache_path()
            if cache_path.exists():
                mapping = load_cached_mapping(cache_path)
            else:
                mapping = get_mapping(None, use_cache=True)
        except Exception:
            # If mapping fails, continue without it
            mapping = None

    # Save the json string to a file for debugging
    if not os.path.exists("debug_json"):
        os.makedirs("debug_json")
    with open(f"debug_json/debug_json_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
        f.write(json_str)
    
    try:
        json_str = process_json_string_to_valid_json(json_str)
        # dump the json string to a file json file but dump using write instead of json library
        with open(f"debug_json/debug_json_{datetime.now().strftime('%Y%m%d_%H%M%S')}_processed.json", "w") as f:
            f.write(json_str)
        # print(f"Processed JSON string: {json_str}")
        # Try to parse the JSON
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            # If the processed JSON is still invalid, log the error and try to fix it one more time
            print(f"JSON decode error after processing: {e}")
            print(f"Error at position: {e.pos if hasattr(e, 'pos') else 'unknown'}")
            # Try one more time with a fresh attempt
            json_str = process_json_string_to_valid_json(json_str)
            data = json.loads(json_str)
        # Debug print removed - was printing: print(f"Data: {data}")
        
        # Deobfuscate keys if mapping is available
        if mapping:
            try:
                data = map_keys(data, mapping)
            except Exception:
                # If mapping fails, continue with obfuscated keys
                pass
        
        # Extract top-level fields (try both deobfuscated and obfuscated keys)
        metadata["version"] = data.get("Version") or data.get("F2P")
        metadata["platform"] = data.get("Platform") or data.get("8>q")
        metadata["active_context"] = data.get("ActiveContext") or data.get("XTp")
        metadata["save_summary"] = data.get("SaveSummary") or data.get("n:R")
        # print("THIS WAS ACCESSED")
        
        # Check if it's an expedition save
        # Look for ExpeditionContext key (obfuscated: "2YS" or deobfuscated: "ExpeditionContext")
        has_expedition_context = "ExpeditionContext" in data or "2YS" in data
        
        if metadata["active_context"] == "Season" or has_expedition_context:
            metadata["is_expedition"] = True
            metadata["expedition_type"] = "Expedition"
        elif metadata["active_context"] == "Main":
            metadata["is_expedition"] = False
            metadata["expedition_type"] = "Normal"
        else:
            # Could be other types
            if has_expedition_context:
                metadata["is_expedition"] = True
                metadata["expedition_type"] = "Expedition"
            else:
                metadata["is_expedition"] = False
                metadata["expedition_type"] = metadata["active_context"] or "Unknown"
        
        # Extract SaveName from CommonStateData (try both obfuscated and deobfuscated)
        common_state_key = "CommonStateData" if "CommonStateData" in data else "<h0"
        if common_state_key in data and isinstance(data[common_state_key], dict):
            save_name_key = "SaveName" if "SaveName" in data[common_state_key] else "Pk4"
            metadata["save_name"] = data[common_state_key].get(save_name_key, "")
        
       
        # Also store all top-level keys for inspection
        metadata["top_level_keys"] = list(data.keys())[:50]  # First 50 keys
        
        # Look for the "@eC" field which might be save slot (seen in partial JSON)
        # It can be at top level or nested in CommonStateData/SeasonStateData
        def find_nested_key(obj, key, path=""):
            """Recursively search for a key in nested dict/list structures."""
            if isinstance(obj, dict):
                if key in obj:
                    return obj[key], path
                for k, v in obj.items():
                    result = find_nested_key(v, key, f"{path}.{k}" if path else k)
                    if result:
                        return result
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    result = find_nested_key(item, key, f"{path}[{i}]" if path else f"[{i}]")
                    if result:
                        return result
            return None
        
        eC_result = find_nested_key(data, "@eC")
        if eC_result:
            eC_value, eC_path = eC_result
            metadata["@eC_value"] = eC_value
            metadata["@eC_path"] = eC_path
            if isinstance(eC_value, list) and len(eC_value) > 0:
                if isinstance(eC_value[0], (int, float)) and 1 <= eC_value[0] <= 15:
                    metadata["detected_save_slot"] = int(eC_value[0])
        
    except json.JSONDecodeError:
        # JSON might be incomplete, try to extract fields manually
        # Look for key patterns in the string (both obfuscated and deobfuscated)
        import re
        print("METADATA EXCEPTION SECTION ACCESSED")
        
        # Try to find Version (obfuscated: "F2P" or deobfuscated: "Version")
        version_match = re.search(r'"(?:Version|F2P)"\s*:\s*(\d+)', json_str)
        if version_match:
            metadata["version"] = int(version_match.group(1))
        
        # Try to find Platform (obfuscated: "8>q" or deobfuscated: "Platform")
        platform_match = re.search(r'"(?:Platform|8>q)"\s*:\s*"([^"]+)"', json_str)
        if platform_match:
            metadata["platform"] = platform_match.group(1)
        
        # Try to find ActiveContext (obfuscated: "XTp" or deobfuscated: "ActiveContext")
        context_match = re.search(r'"(?:ActiveContext|XTp)"\s*:\s*"([^"]+)"', json_str)
        if context_match:
            metadata["active_context"] = context_match.group(1)
        
        # Check for ExpeditionContext (obfuscated: "2YS" or deobfuscated: "ExpeditionContext")
        has_expedition = bool(re.search(r'"(?:ExpeditionContext|2YS)"\s*:', json_str))
        
        if metadata["active_context"] == "Season" or has_expedition:
            metadata["is_expedition"] = True
            metadata["expedition_type"] = "Expedition"
        elif metadata["active_context"] == "Main":
            metadata["is_expedition"] = False
            metadata["expedition_type"] = "Normal"
        else:
            if has_expedition:
                metadata["is_expedition"] = True
                metadata["expedition_type"] = "Expedition"
            else:
                metadata["is_expedition"] = False
                metadata["expedition_type"] = metadata["active_context"] or "Unknown"
        
        # Try to find SaveName (obfuscated: "Pk4" or deobfuscated: "SaveName")
        save_name_match = re.search(r'"(?:SaveName|Pk4)"\s*:\s*"([^"]*)"', json_str)
        if save_name_match:
            metadata["save_name"] = save_name_match.group(1)
    
    return metadata


def save_metadata_to_json(hg_file_path: str, output_path: str) -> str:
    """
    Extract metadata from a save file and save it to a JSON file for inspection.
    
    Args:
        hg_file_path: Path to the .hg save file
        output_path: Path where to save the JSON file
        
    Returns:
        Path to the saved JSON file
    """
    metadata = get_save_metadata(hg_file_path)
    
    # Also include the raw partial JSON for inspection
    try:
        with open(hg_file_path, 'rb') as f:
            data = f.read()
        decompressed_data = decompress_first_block(data, max_bytes=50000)  # 50KB for inspection
        json_str = decompressed_data.decode('utf-8')
        
        # Try to parse and include structured data (more complete)
        try:
            # Try to parse a larger chunk
            parse_length = min(50000, len(json_str))
            partial_json = json.loads(json_str[:parse_length] if len(json_str) > parse_length else json_str)
            metadata["partial_json_sample"] = partial_json
            metadata["partial_json_length"] = parse_length
        except json.JSONDecodeError:
            # If parsing fails, try to extract just the first object
            try:
                decoder = json.JSONDecoder()
                obj, idx = decoder.raw_decode(json_str)
                metadata["partial_json_sample"] = obj
                metadata["partial_json_length"] = idx
            except:
                # If all parsing fails, include as string
                metadata["partial_json_sample"] = json_str[:10000]  # First 10000 chars
                metadata["partial_json_error"] = "Could not parse as JSON"
    except Exception as e:
        metadata["partial_json_error"] = str(e)
    
    # Save to JSON file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    return output_path




def get_save_metadata(hg_file_path: str) -> Dict[str, Any]:
    """
    Extract metadata from a No Man's Sky .hg save file without fully decompressing it.
    
    This function:
    1. Decompresses only the first block(s) of the .hg file
    2. Extracts key metadata fields from the partial JSON
    3. Attempts to detect save slot from the file data
    4. Gets file modification time
    
    Args:
        hg_file_path: Path to the .hg save file
        
    Returns:
        Dictionary containing:
            - version: Game version number
            - platform: Platform string (e.g., "Win|Final")
            - active_context: Active context ("Main", "Season", etc.)
            - save_name: Save name from CommonStateData
            - is_expedition: Boolean indicating if this is an expedition save
            - expedition_type: "Expedition" or "Normal" or other
            - save_slot: Save slot number (detected from file or filename, may be None)
            - save_slot_from_filename: Save slot number extracted from filename (may be inaccurate)
            - detected_save_slot: Save slot detected from file data (if found)
            - last_saved: File modification time as ISO string
            - last_saved_timestamp: File modification time as Unix timestamp
            - file_path: Path to the save file
            - file_size: Size of the .hg file in bytes
    """
    file_path = Path(hg_file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Save file not found: {hg_file_path}")
    
    # Get file metadata
    stat = file_path.stat()
    file_size = stat.st_size
    last_saved_timestamp = stat.st_mtime

    # convert last saved timestamp to ISO format
    last_saved = datetime.fromtimestamp(last_saved_timestamp).isoformat()
    
    
    # Read and partially decompress the file
    with open(hg_file_path, 'rb') as f:
        data = f.read()
    
    # Decompress enough to get metadata (first ~10KB should be enough)
    # The metadata fields are at the top of the JSON
    decompressed_data = decompress_first_block(data, max_bytes=10240)  # 10KB should be plenty
    
    if len(decompressed_data) == 0:
        raise ValueError("Failed to decompress file - might not be a valid save file")
    
    # Convert to string and extract metadata
    try:
        json_str = decompressed_data.decode('utf-8')
    except UnicodeDecodeError:
        raise ValueError("Decompressed data is not valid UTF-8")
    
    metadata = extract_metadata_from_partial_json(json_str, use_key_mapping=True)
    
    # Add file-specific metadata
    # Use detected save slot if found, otherwise fall back to filename
    detected_slot = metadata.get("detected_save_slot")
    metadata["save_slot"] = detected_slot if detected_slot is not None else None
    metadata["last_saved"] = last_saved
    metadata["last_saved_timestamp"] = last_saved_timestamp
    metadata["file_path"] = str(file_path)
    metadata["file_size"] = file_size
    
    return metadata


def get_save_metadata_summary(hg_file_path: str) -> str:
    """
    Get a human-readable summary of save file metadata.
    
    Args:
        hg_file_path: Path to the .hg save file
        
    Returns:
        Formatted string summary
    """
    try:
        meta = get_save_metadata(hg_file_path)
        
        slot_info = str(meta['save_slot']) if meta['save_slot'] is not None else 'Unknown'
        if meta['save_slot_from_filename'] is not None and meta['save_slot'] != meta['save_slot_from_filename']:
            slot_info += f" (filename suggests {meta['save_slot_from_filename']}, may be inaccurate)"
        
        lines = [
            f"Save File: {Path(hg_file_path).name}",
            f"  Slot: {slot_info}",
            f"  Type: {meta['expedition_type'] or 'Unknown'}",
            f"  Save Name: {meta['save_name'] or '(empty)'}",
            f"  Version: {meta['version'] or 'Unknown'}",
            f"  Platform: {meta['platform'] or 'Unknown'}",
            f"  Last Saved: {meta['last_saved']}",
            f"  File Size: {meta['file_size']:,} bytes"
        ]
        
        return "\n".join(lines)
    except Exception as e:
        return f"Error reading save file: {e}"

