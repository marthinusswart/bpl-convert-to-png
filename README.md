# Amiga BPL/PAL File Analyzer & PNG Converter

A Python tool to read, analyze, and convert Amiga format `.bpl` (bitplane) and `.pal` (palette) files created by `kingcon.exe` to PNG images.

## Features

- **Bitplane Analysis**: Automatically detects image dimensions, bitplane depth, and mask presence
- **Palette Display**: Shows all colors in the palette with RGB values, hex codes, and visual previews
- **PNG Generation**: Converts BPL/PAL files to PNG format with transparency support
- **Colorful Output**: Uses the `rich` library for beautiful, colorful console output
- **Flexible Input**: Accepts base filename or individual file paths

## Installation

1. Create a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

The tool supports two modes of operation:

### Mode 1: Display Details (`--display_details`)

Analyzes and displays information about the BPL and PAL files.

**Using base filename (recommended):**

```bash
python amiga_reader.py --display_details assets/packman_tiles
```

This will automatically look for `assets/packman_tiles.bpl` and `assets/packman_tiles.pal`.

**Specifying individual files:**

```bash
python amiga_reader.py --display_details --bpl assets/packman_tiles.bpl --pal assets/packman_tiles.pal
```

### Mode 2: Generate PNG (`--generate_png`)

Converts BPL and PAL files to a PNG image with transparency support.

**Using base filename (recommended):**

```bash
python amiga_reader.py --generate_png assets/packman_tiles
```

This will create `assets/packman_tiles.png`.

**Specifying individual files with custom output:**

```bash
python amiga_reader.py --generate_png --bpl assets/packman_tiles.bpl --pal assets/packman_tiles.pal --output output.png
```

## Output Information

The analyzer provides:

### Bitplane (.bpl) Information

- File path and size
- BOB (Blitter Object) dimensions in pixels
- Bitplane depth (number of bitplanes)
- Maximum colors supported
- Mask presence detection

### Palette (.pal) Information

- File path and size
- Number of colors in palette
- Complete color table with:
  - Color index
  - RGB values
  - Hexadecimal color codes
  - Visual color preview blocks

## File Formats

### Bitplane (.bpl) Format

Amiga bitplane format stores pixel data in separate planes, where each plane represents one bit of the pixel's color index. The format supports:

- Widths: 16, 32, 64, 128, 160, 256, 320, 352, 640 pixels (multiples of 16)
- Depths: 1-8 bitplanes (supporting 2-256 colors)
- Optional mask plane for transparency

### Palette (.pal) Format

Palette files store color information, typically:

- 2 bytes per color (12-bit RGB: 0RGB format)
- 4 bytes per color (24-bit RGB with padding)
- Common palette sizes: 2, 4, 8, 16, 32, 64, 128, or 256 colors

## Example Output

```
╭────────────────────────────────────────────╮
│ Amiga File Analyzer                        │
│ Reading BPL and PAL files from kingcon.exe │
╰────────────────────────────────────────────╯

         Bitplane (.bpl) Information
╭────────────────┬──────────────────────────╮
│ Property       │ Value                    │
├────────────────┼──────────────────────────┤
│ File Path      │ assets/packman_tiles.bpl │
│ File Size      │ 128,000 bytes            │
│ BOB Dimensions │ 320 x 400 pixels         │
│ Bitplane Depth │ 7 planes                 │
│ Max Colors     │ 128 colors               │
│ Mask Present   │ ✓ Yes                    │
╰────────────────┴──────────────────────────╯
```

## Classes

### `AmigaPaletteReader`

Reads and parses Amiga palette files, supporting both 12-bit and 24-bit color formats.

### `AmigaBitplaneReader`

Analyzes bitplane files to determine dimensions, depth, and mask presence using intelligent dimension detection. Includes pixel decoding for PNG generation.

### `AmigaFileAnalyzer`

Main analyzer class that coordinates reading and displaying information from both file types with colorful console output. Supports two modes:

- **display mode**: Shows detailed file analysis
- **generate mode**: Creates PNG images from BPL/PAL data

# Examples

- **details**: python amiga_reader.py --display_details assets/packman_tiles --width 320 --height 320 --mask true
- **generate**: python amiga_reader.py --generate_png assets/packman_tiles --width 320 --height 320 --mask --sprite_width 16 --sprite_height 16
