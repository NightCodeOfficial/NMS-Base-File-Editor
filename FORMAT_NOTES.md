# No Man's Sky Save File Format Notes

## File Structure

Based on analysis of `save7.hg`:

### Header (18 bytes)
- **Magic bytes**: `\xe5\xa1\xed\xfe` (bytes 0-3)
- **Version/Length info**: Bytes 4-17 contain version and length information
- The header appears to be: `[magic][version?][length?][padding?]`

### LZ4-Compressed Blocks
- **Discovery**: The save files use **LZ4 compression**, not binary-embedded JSON!
- After the header, the file contains LZ4-compressed blocks
- Each block structure:
  - Magic: `0xfeeda1e5` (4 bytes, little-endian)
  - Compressed size (4 bytes, little-endian)
  - Uncompressed size (4 bytes, little-endian)
  - Padding (4 bytes)
  - LZ4-compressed data

### Decompressed JSON Data
- After decompression, you get **pure JSON** (no binary corruption!)
- Keys are obfuscated using a proprietary algorithm
- The JSON is valid and parseable

## Key Obfuscation

The game obfuscates JSON keys, likely for performance or obfuscation reasons. Examples:

| Obfuscated | Deobfuscated |
|------------|--------------|
| `F2P` | `Version` |
| `8>q` | `Platform` |
| `XTp` | `ActiveContext` |
| `<h0` | `CommonStateData` |
| `Pk4` | `SaveName` |
| `Lg8` | `TotalPlayTime` |
| `kPF` | `UsesThirdPersonCharacterCam` |

The obfuscation appears to be consistent within a game version but may change between versions.

## Compression Format

The save files use LZ4 compression with block-based structure:
- Blocks are decompressed independently
- Each block can be up to 0x80000 (512KB) uncompressed
- The decompressed blocks are concatenated to form the complete JSON
- No binary corruption - the JSON is pure after decompression!

**Note**: Earlier attempts to parse the files as binary-embedded JSON were incorrect. The files must be decompressed first using LZ4.

## Challenges

1. **Key Mapping**: The obfuscation algorithm is proprietary and not publicly documented
2. **Format Changes**: The format may change with game updates
3. **Large Files**: Save files can be 1-2MB+ compressed, several MB uncompressed
4. **Multiple JSON Objects**: Some save files may contain multiple JSON objects concatenated

**Resolved**: The binary corruption issue was actually LZ4 compression. Decompressing first eliminates all binary corruption.

## Recommended Approach

For reliable extraction, use existing tools that have reverse-engineered the format:
- **NomNom**: Comprehensive save editor with full format support
- **NMSBaseJsonEditor**: Base data editor

These tools have:
- Proper binary field handling
- Key deobfuscation algorithms
- Support for multiple game versions

## Research Resources

- [NomNom GitHub](https://github.com/zencq/NomNom) - Study the source code for format details
- [No Man's Sky Modding Wiki](https://nomanssky.fandom.com/wiki/Datamining)
- Game save file locations (Windows): `%USERPROFILE%\AppData\Roaming\HelloGames\NMS`

## Future Improvements

To improve the extraction tool:
1. Reverse engineer the binary field format by analyzing NomNom's code
2. Build a complete key mapping database
3. Handle version-specific format differences
4. Optimize for large files (streaming parser)

