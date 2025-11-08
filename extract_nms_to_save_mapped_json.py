#!/usr/bin/env python3
"""
No Man's Sky Save File Extractor with Key Mapping

Based on the decompressor.py script by Robert Maupin.
https://github.com/NMSCD/NMS-Save-Decoder/

Includes key mapping functionality from mapper.ts to automatically
deobfuscate keys using the MBINCompiler mapping.
"""

import json
import sys
import os
import io
from pathlib import Path

try:
    import lz4.block
except ImportError:
    print("Error: lz4 module not found. Please install it with: pip install lz4")
    sys.exit(1)

# Import key mapping functions
try:
    from key_mapper import map_keys, get_mapping
except ImportError:
    print("Warning: key_mapper.py not found. Key mapping will be disabled.")
    map_keys = None
    get_mapping = None


def uint32(data: bytes) -> int:
    """Convert 4 bytes to a little endian unsigned integer."""
    return int.from_bytes(data, byteorder='little', signed=False) & 0xffffffff


def decompress_save_file(data):
    """
    Decompresses a No Man's Sky save file that uses LZ4 compression.
    
    The format is:
    - Header (18 bytes) with magic bytes
    - LZ4-compressed blocks, each with:
      - Magic: 0xfeeda1e5 (4 bytes)
      - Compressed size (4 bytes)
      - Uncompressed size (4 bytes)
      - Padding (4 bytes)
      - Compressed data
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
            print(f"Warning: Failed to decompress block: {e}")
            break
    
    return bytes(out)


def extract_json_from_hg(hg_file_path):
    """
    Extract JSON from a No Man's Sky .hg save file.
    
    This function:
    1. Reads the .hg file
    2. Decompresses it using LZ4
    3. Parses the JSON (which has obfuscated keys)
    """
    with open(hg_file_path, 'rb') as f:
        data = f.read()
    
    # Check for header magic bytes
    if len(data) < 18:
        raise ValueError("File too short to be a valid save file")
    
    # The header is 18 bytes, but the LZ4 blocks start after it
    # Actually, looking at the decompressor, it seems the blocks might start at the beginning
    # Let's try decompressing from the start
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


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("No Man's Sky Save File Extractor with Key Mapping")
        print("=" * 60)
        print("\nUsage: python extract_nms_save_improved.py <input.hg> [output.json] [--no-map] [--mapping mapping.json]")
        print("\nOptions:")
        print("  --no-map          Don't apply key mapping (output obfuscated keys)")
        print("  --mapping FILE    Use a local mapping file instead of downloading")
        print("\nExample:")
        print("  python extract_nms_save_improved.py sources/save7.hg save7_extracted.json")
        print("  python extract_nms_save_improved.py sources/save7.hg output.json --no-map")
        print("  python extract_nms_save_improved.py sources/save7.hg output.json --mapping mapping.json")
        sys.exit(1)
    
    # Parse arguments
    args = sys.argv[1:]
    input_file = None
    output_file = None
    apply_mapping = True
    mapping_file = None
    
    i = 0
    while i < len(args):
        if args[i] == "--no-map":
            apply_mapping = False
        elif args[i] == "--mapping" and i + 1 < len(args):
            mapping_file = args[i + 1]
            i += 1
        elif not input_file:
            input_file = args[i]
        elif not output_file:
            output_file = args[i]
        i += 1
    
    if not input_file:
        print("Error: No input file specified")
        sys.exit(1)
    
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found")
        sys.exit(1)
    
    # Determine output file
    if not output_file:
        input_path = Path(input_file)
        output_file = str(input_path.parent / f"{input_path.stem}_extracted.json")
    
    print(f"Extracting JSON from: {input_file}")
    print(f"Output: {output_file}")
    print("Decompressing and parsing...")
    
    try:
        data = extract_json_from_hg(input_file)
        
        # Apply key mapping if requested and available
        if apply_mapping and map_keys and get_mapping:
            print("Applying key mapping...")
            try:
                mapping = get_mapping(mapping_file)
                data = map_keys(data, mapping)
                print("✓ Keys successfully deobfuscated!")
            except Exception as e:
                print(f"Warning: Failed to apply key mapping: {e}")
                print("  Continuing with obfuscated keys...")
        elif apply_mapping:
            print("Warning: Key mapping not available (key_mapper.py not found)")
            print("  Output will contain obfuscated keys")
        
        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Successfully extracted JSON!")
        print(f"  File: {output_file}")
        print(f"  Top-level keys: {', '.join(list(data.keys())[:10])}")
        
        if apply_mapping and map_keys and get_mapping:
            print("\n" + "=" * 60)
            print("SUCCESS:")
            print("=" * 60)
            print("• Keys have been DEOBFUSCATED")
            print("  (e.g., 'Version', 'Platform', 'ActiveContext')")
        else:
            print("\n" + "=" * 60)
            print("NOTE:")
            print("=" * 60)
            print("• The extracted JSON contains OBFUSCATED keys")
            print("  (e.g., 'F2P' instead of 'Version', '8>q' instead of 'Platform')")
            print("• Use --no-map to disable key mapping, or ensure key_mapper.py is available")
        
        print("• Always backup your save files before modifying them")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

