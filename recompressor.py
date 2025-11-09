#!/usr/bin/env python3
"""
No Man's Sky Save File Recompressor

Takes a deobfuscated JSON representation of a No Man's Sky save file and
produces a valid .hg file (the game's LZ4-blocked save format).

This module performs the reverse operation of extract_nms_to_save_mapped_json.py:
1. Reverse-maps deobfuscated keys back to obfuscated keys
2. Serializes the JSON compactly
3. Splits into chunks and compresses with LZ4
4. Writes blocks with proper headers to create a valid .hg file
"""

import json
import struct
import os
from pathlib import Path
from typing import Optional, Tuple

try:
    import lz4.block
except ImportError:
    raise ImportError("lz4 module not found. Please install it with: pip install lz4")

try:
    from key_mapper import reverse_map_keys, get_mapping, get_cache_path, load_cached_mapping
except ImportError:
    raise ImportError("key_mapper.py not found. Please ensure it exists in the same directory.")


# Block format constants
BLOCK_MAGIC = 0xFEEDA1E5  # Magic bytes identifying a compressed block
BLOCK_HEADER_SIZE = 16    # Total size of block header (4 + 4 + 4 + 4)
MAX_UNCOMPRESSED_BLOCK_SIZE = 0x80000  # 512 KB (524288 bytes) - maximum uncompressed chunk size


def compress_json_bytes(json_bytes: bytes) -> Tuple[bytes, int]:
    """
    Compress JSON bytes into LZ4 blocks with proper headers.
    
    Splits the input into chunks of up to 512 KB, compresses each chunk,
    and prepends the 16-byte header to each compressed block.
    
    Args:
        json_bytes: The JSON data as UTF-8 encoded bytes
        
    Returns:
        Tuple[bytes, int]: A tuple of (compressed_data, block_count) where:
            - compressed_data: All compressed blocks concatenated together, ready to write to .hg file
            - block_count: Number of compression blocks created
    """
    output = bytearray()
    total_size = len(json_bytes)
    offset = 0
    block_count = 0
    
    # Process the JSON in chunks
    while offset < total_size:
        # Determine chunk size (up to MAX_UNCOMPRESSED_BLOCK_SIZE)
        chunk_size = min(MAX_UNCOMPRESSED_BLOCK_SIZE, total_size - offset)
        uncompressed_chunk = json_bytes[offset:offset + chunk_size]
        
        # Compress the chunk using LZ4
        # store_size=False means we don't include the uncompressed size in the compressed data
        compressed_chunk = lz4.block.compress(uncompressed_chunk, store_size=False)
        compressed_size = len(compressed_chunk)
        
        # Build the 16-byte header for this block
        # Format: [magic (4 LE)] [compressed_size (4 LE)] [uncompressed_size (4 LE)] [padding (4 = 0)]
        header = struct.pack(
            '<IIII',  # Little-endian: 4 unsigned 32-bit integers
            BLOCK_MAGIC,           # Magic bytes: 0xFEEDA1E5
            compressed_size,       # Size of compressed data
            chunk_size,            # Size of uncompressed data
            0                      # Padding (4 bytes of zeros)
        )
        
        # Append header + compressed data to output
        output.extend(header)
        output.extend(compressed_chunk)
        
        offset += chunk_size
        block_count += 1
    
    return bytes(output), block_count


def recompress_save(data: dict, output_path: str, mapping_file: Optional[str] = None) -> None:
    """
    Recompress a No Man's Sky save JSON dictionary into a valid `.hg` file.
    
    Automatically reverse-maps keys, serializes compactly, compresses into
    LZ4 blocks, and writes to the specified path.
    
    Args:
        data: The deobfuscated JSON dictionary (with readable keys like "Version", "Platform", etc.)
        output_path: Path where the .hg file should be written
        mapping_file: Optional path to local mapping file. If None, downloads from GitHub.
        
    Raises:
        ImportError: If required modules (lz4, key_mapper) are not available
        IOError: If file operations fail
        ValueError: If data is invalid or compression fails
    """
    # Step 1: Get the key mapping
    print("Loading key mapping...")
    
    # If no mapping file specified, check for cached mapping first
    if mapping_file is None:
        cache_path = get_cache_path()
        if cache_path.exists():
            try:
                print(f"Using cached mapping from: {cache_path}")
                mapping = load_cached_mapping(cache_path)
                print(f"Loaded {len(mapping)} mapping entries from cache.")
            except Exception as e:
                print(f"Warning: Failed to load cached mapping ({e}), downloading fresh copy...")
                mapping = get_mapping(mapping_file, use_cache=True)
                print(f"Downloaded {len(mapping)} mapping entries.")
        else:
            print("No cached mapping found, downloading from GitHub...")
            mapping = get_mapping(mapping_file, use_cache=True)
            print(f"Downloaded {len(mapping)} mapping entries.")
    else:
        # Use the specified mapping file
        mapping = get_mapping(mapping_file, use_cache=True)
        print(f"Loaded {len(mapping)} mapping entries.")
    
    # Step 2: Reverse-map keys (deobfuscated -> obfuscated)
    print("Reverse-mapping keys...")
    obfuscated_data = reverse_map_keys(data, mapping)
    print("✓ Keys reverse-mapped successfully.")
    
    # Step 3: Serialize to compact JSON
    print("Serializing JSON...")
    json_str = json.dumps(obfuscated_data, separators=(",", ":"), ensure_ascii=False)
    json_bytes = json_str.encode('utf-8')  # UTF-8 encoding, no BOM
    print(f"Serialized JSON size: {len(json_bytes):,} bytes ({len(json_bytes) / 1024 / 1024:.2f} MB)")
    
    # Step 4: Compress into LZ4 blocks
    print("Compressing into LZ4 blocks...")
    compressed_data, block_count = compress_json_bytes(json_bytes)
    compressed_size = len(compressed_data)
    print(f"Compressed to {compressed_size:,} bytes ({compressed_size / 1024 / 1024:.2f} MB)")
    print(f"Created {block_count} compression block(s)")
    
    # Step 5: Write to temporary file first, then rename (atomic operation)
    temp_path = output_path + ".tmp"
    print(f"Writing to temporary file: {temp_path}")
    
    try:
        with open(temp_path, 'wb') as f:
            f.write(compressed_data)
        
        # Rename temp file to final output (atomic on most filesystems)
        os.replace(temp_path, output_path)
        print(f"✓ Successfully wrote .hg file: {output_path}")
        print(f"  Blocks: {block_count}")
        print(f"  Compressed size: {compressed_size:,} bytes")
        print(f"  Original size: {len(json_bytes):,} bytes")
        print(f"  Compression ratio: {len(json_bytes) / compressed_size:.2f}x")
        
    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        raise IOError(f"Failed to write output file: {e}") from e

