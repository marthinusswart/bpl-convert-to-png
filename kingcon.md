# KingCon — How It Works: PNG to Amiga BPL Conversion

KingCon V1.2, written by Soren Hannibal/Lemon, is a command-line tool that converts
standard image files (PNG, BMP, TGA, GIF, etc.) into Amiga hardware-compatible raw binary
formats. It uses the [FreeImage](https://freeimage.sourceforge.io/) library for image
loading and relies on big-endian output to match Amiga memory layout.

---

## Table of Contents

1. [Build & Installation](#build--installation)
2. [Command Syntax](#command-syntax)
3. [The Full Conversion Pipeline](#the-full-conversion-pipeline)
4. [Bitplane Format Deep Dive](#bitplane-format-deep-dive)
   - [Non-Interleaved Layout](#non-interleaved-layout)
   - [Interleaved Layout](#interleaved-layout)
   - [Mask Plane in Interleaved Mode](#mask-plane-in-interleaved-mode)
5. [Color / Palette Handling](#color--palette-handling)
   - [Palettization](#palettization)
   - [12-Bit Color Quantization](#12-bit-color-quantization)
   - [Extra Half-Brite (EHB)](#extra-half-brite-ehb)
6. [Mask Extraction](#mask-extraction)
7. [Output File Reference](#output-file-reference)
   - [.BPL — Bitplane Data](#bpl--bitplane-data)
   - [.PAL — Raw Palette](#pal--raw-palette)
   - [.COP — Copper Palette](#cop--copper-palette)
   - [.BOB — Blitter Object List](#bob--blitter-object-list)
   - [.FAR — Font ASCII Remap Table](#far--font-ascii-remap-table)
   - [\_preview.TGA — Preview Image](#_previewtga--preview-image)
8. [Conversion Modes](#conversion-modes)
9. [Transforms: Flip, Rotate, Trim](#transforms-flip-rotate-trim)
10. [Complete Option Reference](#complete-option-reference)
11. [Asset Conversion List Files](#asset-conversion-list-files)
12. [Common Recipes](#common-recipes)

---

## Build & Installation

**Dependencies:** FreeImage library.

```bash
# macOS
brew install freeimage

# Build
make all
```

The Makefile uses `g++` with `-lfreeimage`. The resulting binary is `kingcon`.

---

## Command Syntax

```
kingcon <sourcefile> <destfile_base> -Format=<N> [mode] [options...]
```

or, for batch processing:

```
kingcon @assetconversionlistfile
```

- `sourcefile` — input image (any format FreeImage supports: PNG, BMP, TGA, GIF, etc.)
- `destfile_base` — output base name **without extension** (KingCon appends the correct extension)
- `Format` — determines output format and number of bitplanes (see below)
- Options may use either `-` prefix and either short or long name, e.g. `-I` or `-Interleaved`

---

## The Full Conversion Pipeline

This describes every step KingCon executes when you run, for example:

```bash
kingcon tiles.png tiles -Format=4 -Interleaved -Mask -RawPalette
```

### Step 1 — Load Source Image

KingCon calls FreeImage's `GenericLoader`. FreeImage auto-detects the file format by
signature or extension. Virtually any common image format works.

### Step 2 — Vertical Flip

FreeImage stores bitmaps **bottom-to-top** (origin at lower-left). KingCon immediately
calls `FreeImage_FlipVertical` so that row 0 corresponds to the **top** of the image —
matching Amiga scanline conventions.

### Step 3 — Build the Cutout List

Depending on mode (see [Conversion Modes](#conversion-modes)), a list of rectangular
regions (`Cutout` structs) is assembled. In SingleFrame mode this is just the whole
image (or the sub-region specified by `-X/-Y/-W/-H`).

### Step 4 — Convert to Palettized / 32-bit

For formats that require palettized input (BPL, Sprite, Attached Sprite, VFT):

1. **If the image is already 8-bit indexed AND uses ≤ 2ⁿ colors** (n = numBitplanes):
   A _lossless_ palettization path runs. Every unique 12-bit quantized color is mapped
   to a palette index. If the source had a palette, its ordering is preserved.

2. **If the image has more colors than allowed** (or is 24/32-bit):
   KingCon warns and runs FreeImage's `FIQ_NNQUANT` color quantizer
   (`FreeImage_ColorQuantizeEx`) to force the palette down to `2^numBitplanes` entries.
   The top-left pixel's color is used as a hint for the background/mask color.

3. **Palette index 0 is always the background color.** After quantization, KingCon
   scans and swaps palette entries so that index 0 contains the background/mask color.

> **Important:** The source PNG should ideally already be palettized to the correct
> depth (e.g., 4-bit/16-color for `-Format=4`) to avoid lossy quantization.

### Step 5 — Extract Mask Bitmap

KingCon creates a separate grayscale mask bitmap (8 bits per pixel, 0 = transparent,
255 = opaque):

| Source Format    | Mask Rule                                                                          |
| ---------------- | ---------------------------------------------------------------------------------- |
| 8-bit palettized | Pixels whose color index equals `maskColorIndex` (default 0) → 0; all others → 255 |
| 32-bit RGBA      | Alpha channel → mask (non-zero alpha = opaque)                                     |
| 24-bit RGB       | Pixels matching the top-left pixel's color → 0; all others → 255                   |

This mask is used both for bitplane encoding and for Bob/font cutout detection.

### Step 6 — Apply Transforms

Before encoding, optional transforms are applied **to the source bitmap**:

- `-FlipX` — `FreeImage_FlipHorizontal`
- `-Rotate=2` (180°) — vertical + horizontal flip
- `-Rotate=1` or `-Rotate=3` (90° CW / 270°) — manual pixel-by-pixel rotation into a
  new bitmap; palette is copied across; the image is re-flipped afterwards.

Cutout coordinates and anchor points are adjusted to match the transformed image.

### Step 7 — Trim (optional)

With `-Trim`, each cutout's bounding box is shrunk from each of its 4 edges until a
non-mask pixel is found. Anchor offsets are adjusted accordingly.

### Step 8 — Allocate Conversion Buffers

`PrepareCutout` computes the buffer size and allocates memory for each cutout's output
bitplane data:

```
widthBytes = ceil((cutout.width + 15) / 16) * 2   // Amiga: width rounded up to 16-bit word
bufferSize = widthBytes * cutout.height * (numBitplanes + numMaskPlanes)
```

Where `numMaskPlanes`:

- Non-interleaved with mask: `1`
- Interleaved with mask: `numBitplanes` (mask duplicated per color plane)
- No mask: `0`

### Step 9 — Encode Bitplane Data (`PerformCutout`)

This is the core conversion. For every pixel `(x, y)` of the cutout:

```cpp
colorIndex = sourcePixel(x, y);       // 8-bit palette index
bitFlag = 1 << ((x & 7) ^ 7);         // Amiga MSB-first bit ordering within a byte

for (j = 0; j < numBitplanes; j++) {
    if (colorIndex & (1 << j))
        destPtr[j * perPlaneOffset + x/8] |= bitFlag;
}
if (mask[x][y] != 0) {
    for (j = 0; j < numMaskPlanes; j++)
        destPtr[maskPlaneOffset + j * perPlaneOffset + x/8] |= bitFlag;
}
```

`perPlaneOffset`, `perLineOffset`, and `maskPlaneOffset` differ between interleaved and
non-interleaved modes (see [Bitplane Format Deep Dive](#bitplane-format-deep-dive)).

If `-InvertMask` is set, all bytes in the mask planes are bitwise-inverted after
encoding each scanline.

### Step 10 — Save Files

- `.BPL` — all cutout buffers written sequentially
- `.PAL` / `.COP` — palette written if `-RawPalette` / `-CopperPalette` was requested
- `.BOB` — anchor/dimension table if in Bob or font mode
- `.FAR` — ASCII remap table if in font mode
- `_preview.TGA` — a composite preview image showing all cutouts

---

## Bitplane Format Deep Dive

Amiga hardware uses **planar graphics**: each bit of a pixel's color index comes from a
separate memory region (a "bitplane"). For an N-bitplane image, a pixel at position `x`
in scanline `y` has its color index assembled bit-by-bit from N planes.

Bit ordering within a byte is **MSB-first** (most significant bit = leftmost pixel):

```
Byte value:  1000 0000 = pixel 0 (x=0) set, pixels 1–7 clear
Byte value:  0000 0001 = pixel 7 (x=7) set
```

KingCon enforces Amiga width alignment: `widthBytes = ceil(width / 16) * 2`.

### Non-Interleaved Layout

The default layout (without `-Interleaved`) stores all scanlines of plane 0, then all
scanlines of plane 1, etc.:

```
File layout:
  [plane0: height × widthBytes bytes]
  [plane1: height × widthBytes bytes]
  ...
  [planeN-1: height × widthBytes bytes]
  [mask: height × widthBytes bytes]   ← if -Mask
```

Offsets within the buffer:

- `perPlaneOffset = widthBytes × height`
- `perLineOffset = widthBytes`
- `maskPlaneOffset = perPlaneOffset × numBitplanes`

To read pixel (x, y) from plane j:

```
byte = buffer[j * perPlaneOffset + y * widthBytes + x/8]
bit  = (byte >> (7 - (x % 8))) & 1
```

### Interleaved Layout

With `-Interleaved`, all planes of scanline 0 are stored together, then all planes of
scanline 1, etc. This is the format Amiga blitter routines expect for fast copying:

```
Scanline 0: [plane0: widthBytes][plane1: widthBytes]...[planeN-1: widthBytes]
Scanline 1: [plane0: widthBytes][plane1: widthBytes]...[planeN-1: widthBytes]
...
```

Offsets:

- `perLineOffset = widthBytes × numBitplanes`
- `perPlaneOffset = widthBytes`
- No mask: `maskPlaneOffset = perPlaneOffset × numBitplanes`

File size formula:

```
fileSize = widthBytes × height × numBitplanes
```

### Mask Plane in Interleaved Mode

With both `-Interleaved` and `-Mask`, the mask is **duplicated once per color plane**
and interleaved immediately after each color plane:

```
Scanline 0: [plane0: widthBytes][mask: widthBytes][plane1: widthBytes][mask: widthBytes]...
Scanline 1: [plane0: widthBytes][mask: widthBytes][plane1: widthBytes][mask: widthBytes]...
```

Offsets:

- `perPlaneOffset = widthBytes × 2` (color plane + paired mask = 2 × widthBytes)
- `perLineOffset  = widthBytes × numBitplanes × 2`
- `maskPlaneOffset = widthBytes` (immediately follows each color plane)

File size formula:

```
fileSize = widthBytes × height × numBitplanes × 2
```

> **Note:** The mask is identical (duplicated) for each color plane pair. All N mask
> copies carry the same data. The Amiga blitter uses one mask, but the interleaved
> layout requires them to be interleaved per-plane.

---

## Color / Palette Handling

### Palettization

KingCon quantizes all colors to **12-bit Amiga precision** during palette building:

```cpp
// 8-bit channel → 4-bit: divide by 16 (truncate)
result = ((r / 16) << 8) | ((g / 16) << 4) | (b / 16);
```

And back to 8-bit for display/comparison:

```cpp
// 4-bit → 8-bit: multiply by 17
r8 = ((word >> 8) & 0x0F) * 17;
```

The palette is stored internally as 12-bit `unsigned short` values in the format
`0x0RGB` (4 bits each for R, G, B; top nibble ignored).

### 12-Bit Color Quantization

When a lossless palettization is impossible (too many colors), KingCon:

1. Converts the image to 24-bit
2. Runs FreeImage's `FIQ_NNQUANT` (Wu's quantizer) to reduce to `2^numBitplanes` colors
3. Ensures the background/mask color stays at index 0

### Extra Half-Brite (EHB)

With `-Format=e` (EHB), the palette has 32 standard colors (indices 0–31) and 32 half-
brightness duplicates (indices 32–63). KingCon computes the half-brite value as:

```cpp
halfBrite = (color & 0xeee) >> 1;
```

This truncates the least significant bit of each 4-bit channel and halves the result.

---

## Mask Extraction

The mask bitmap is an 8-bit grayscale image where:

- `0` = transparent (mask color / background)
- `255` = opaque

Three source modes:

| Source Format         | Mask Logic                                                                  |
| --------------------- | --------------------------------------------------------------------------- |
| 8-bit indexed         | `maskColorIndex` (default 0) → transparent                                  |
| 32-bit RGBA           | `alpha != 0` → opaque                                                       |
| 24-bit RGB (no alpha) | Top-left pixel color → transparent (Bob/font modes require RGBA or indexed) |

---

## Output File Reference

### .BPL — Bitplane Data

Raw binary, big-endian. Width must be a multiple of 16 bits (2 bytes). All data is
written directly from the conversion buffer with no header.

For a single frame (non-Bob, non-anim) command, total plane count (`totalPlanes`):

| Mode                       | totalPlanes        |
| -------------------------- | ------------------ |
| No mask, non-interleaved   | `numBitplanes`     |
| With mask, non-interleaved | `numBitplanes + 1` |
| No mask, interleaved       | `numBitplanes`     |
| With mask, interleaved     | `numBitplanes × 2` |

```
fileSize = widthBytes × height × totalPlanes
```

### .PAL — Raw Palette

Raw binary, big-endian. Written from the bitmap's FreeImage palette array.

**12-bit format** (`-RawPalette`): 2 bytes per color, format `0x0RGB`:

```
Byte 0:  0000 RRRR
Byte 1:  GGGG BBBB
```

**24-bit format** (`-RawPalette24`): 4 bytes per color, format `0x00RRGGBB`:

```
Byte 0:  0x00
Byte 1:  RR (8-bit red)
Byte 2:  GG (8-bit green)
Byte 3:  BB (8-bit blue)
```

Color count = `2 ^ numBitplanes`. For EHB, only 32 colors (half the full 64) are saved.
For sprites, color 0 is not saved (reserved for transparency).

### .COP — Copper Palette

Copper-list ready pairs of 16-bit words (big-endian):

```
[COLOR_REG_ADDR][12-bit color value]
```

Where `COLOR_REG_ADDR = 0x180 + (colorIndex × 2)`. Copper register addresses for
colors start at `$DFF180`. With `-LineColors`, a per-scanline copper list is generated
with `COPWAIT` instructions (`$xxE1 $FFFE` / `$xy07 $FFFE`) between each line.

### .BOB — Blitter Object List

Written in Bob and font modes. One record per cutout (big-endian):

```c
struct Bob {
    uint16_t widthInWords;  // width / 2 (words per scanline per plane)
    uint16_t height;        // height in pixels
    uint16_t width;         // width in pixels
    uint32_t offset;        // byte offset into the .BPL data for this BOB
    int16_t  anchorX;       // anchor point X (from bounding box left edge)
    int16_t  anchorY;       // anchor point Y (from bounding box top edge)
};
```

Anchor points are encoded in the source image as a single-pixel deviation on the bottom
(anchorX) and left (anchorY) edges of each bounding box.

### .FAR — Font ASCII Remap Table

Written in font modes. 256-byte lookup table mapping ASCII codes to font glyph indices.
`0xFF` means the character is not present. Case-insensitive mapping is automatic (if
only `A` is present, `a` maps to the same glyph and vice versa).

### \_preview.TGA — Preview Image

A TGA image with all cutouts arranged in a grid (approximately √N columns and rows).
Each cutout is outlined in green; anchor dots appear in white on the bottom and left
edges. A small 6×6 hardcoded numeric font labels each cutout. Background color:
`0x102030` (dark blue-grey). Generated unconditionally on every run.

---

## Conversion Modes

### Single Frame (default)

Converts the entire source image (or the region specified by `-X/-Y/-W/-H`) as one
cutout.

### Animation (`-Anim[=N]`)

Finds the trailing decimal number in the source filename and increments it for each
subsequent frame (e.g., `sprite001.png`, `sprite002.png`, …). All frames must be the
**same size and use the same palette**. Outputs one `.BPL` with all frame data
concatenated and one `.BOB` with per-frame offsets.

### Bob (`-Bob=N`)

Expects the source image to contain exactly N BOBs, each surrounded by a solid-colored
**bounding box** with:

- A **single different-colored pixel** on the **bottom** edge → `anchorX` position
- A **single different-colored pixel** on the **left** edge → `anchorY` position

KingCon scans the mask bitmap for non-empty rectangular regions, then validates and
strips the bounding boxes. Outputs a `.BPL` with all BOBs concatenated and a `.BOB`
table with per-BOB offsets, widths, heights, and anchors.

### Monospace Font (`-MonospaceFont "..."`)

Requires `-Width=W` and `-Height=H`. Cuts glyphs from a grid at fixed cell size W×H,
reading characters from the provided string left-to-right, top-to-bottom. Outputs a
`.BPL`, `.BOB`, and `.FAR`.

### Proportional Font (`-ProportionalFont "..."`)

Uses Bob cutout detection to find variable-width glyphs from each row of text. Requires
`-Height=H`. Outputs `.BPL`, `.BOB`, and `.FAR`.

---

## Transforms: Flip, Rotate, Trim

All transforms are applied **after** palettization but **before** bitplane encoding.

| Option      | Effect                                                                           |
| ----------- | -------------------------------------------------------------------------------- |
| `-FlipX`    | Mirror image horizontally; adjusts cutout X and anchorX                          |
| `-Rotate=1` | 90° clockwise; swaps width/height; adjusts anchorX/anchorY                       |
| `-Rotate=2` | 180°; equivalent to FlipX + FlipY                                                |
| `-Rotate=3` | 270° clockwise                                                                   |
| `-Trim`     | Shrink each cutout's bounding box until non-mask pixels are found on all 4 sides |

`-AddWord` (`-AW`) inserts an extra 16-bit word at the right edge of each scanline per
plane. This is used to pad blitter operations that read one word ahead.

---

## Complete Option Reference

| Short        | Long                 | Parameter                                            | Description                                    |
| ------------ | -------------------- | ---------------------------------------------------- | ---------------------------------------------- |
| `-F`         | `-Format`            | `1`–`8`, `c`, `s[16/32/64]`, `a[16/32/64]`, `v`, `e` | Output format and number of color bitplanes    |
| `-A`         | `-Anim`              | `[=numFrames]`                                       | Animation mode                                 |
| `-B`         | `-Bob`               | `=numBobs`                                           | Bob cutout mode                                |
| `-N`         | `-MonospaceFont`     | `"chars"`                                            | Monospace font mode                            |
| `-P`         | `-ProportionalFont`  | `"chars"`                                            | Proportional font mode                         |
| `-G`         | `-Gap`               | `=pixels`                                            | Gap between font lines (font modes only)       |
| `-X`         | `-Left`              | `=x`                                                 | Start X (not Bob mode)                         |
| `-Y`         | `-Top`               | `=y`                                                 | Start Y, 0=top (not Bob mode)                  |
| `-W`         | `-Width`             | `=w`                                                 | Width override                                 |
| `-H`         | `-Height`            | `=h`                                                 | Height override                                |
| `-I`         | `-Interleaved`       | —                                                    | Interleaved bitplane layout (BPL only)         |
| `-M`         | `-Mask`              | `[=colorIdx]`                                        | Add mask plane; default mask color = index 0   |
| `-IM`        | `-InvertMask`        | —                                                    | Invert the mask bits                           |
| `-RP`        | `-RawPalette`        | —                                                    | Save 12-bit raw palette (.PAL)                 |
| `-RP24`      | `-RawPalette24`      | —                                                    | Save 24-bit raw palette (.PAL)                 |
| `-C`         | `-CopperPalette`     | `[=colorStartIdx]`                                   | Save copper-list palette (.COP)                |
| `-L`         | `-LineColors`        | `[=maxChanges]`                                      | Per-scanline color cycling copper list         |
| `-DW`        | `-DoubleCopperWaits` | —                                                    | Always emit 2 COPWAIT per line (for line 256+) |
| `-T`         | `-Trim`              | —                                                    | Trim bounding box to non-mask pixels           |
| `-AW`        | `-AddWord`           | —                                                    | Insert extra blitter word per scanline         |
| `-PM`        | `-PreviewMaskColor0` | —                                                    | Use color 0 as mask in preview image           |
| `-FX`        | `-FlipX`             | —                                                    | Mirror horizontally                            |
| `-R`         | `-Rotate`            | `=1\|2\|3`                                           | Rotate (1=90°CW, 2=180°, 3=270°CW)             |
| `-SX`        | `-SpriteX`           | `=n`                                                 | Sprite control word X position (default `$81`) |
| `-SY`        | `-SpriteY`           | `=n`                                                 | Sprite control word Y position (default `$2C`) |
| `-FTMain`    | `-FileTypeMain`      | `=type`                                              | Output main file as text (see below)           |
| `-FTPalette` | `-FileTypePalette`   | `=type`                                              | Output palette file as text                    |
| `-FTBob`     | `-FileTypeBob`       | `=type`                                              | Output BOB file as text                        |
| `-FTFont`    | `-FileTypeFont`      | `=type`                                              | Output font file as text                       |

**FileType values:** `uchar`, `ushort`, `0xuchar`, `0xushort`, `dc.b`, `dc.w`
(produce `_UChar.INL`, `_UShort.INL`, `_dcb.i`, or `_dcw.i` assembly-include files instead of raw binary)

**Format values:**

| Value       | Description                            | Output Extension |
| ----------- | -------------------------------------- | ---------------- |
| `1`–`8`     | N-bitplane format                      | `.BPL`           |
| `c`         | Chunky (not yet implemented)           | `.CHK`           |
| `s` / `s16` | 16-pixel sprite                        | `.SPR`           |
| `s32`       | 32-pixel sprite                        | `.S32`           |
| `s64`       | 64-pixel sprite                        | `.S64`           |
| `a` / `a16` | Attached sprite (15-color)             | `.ASP`           |
| `a32`       | 32-pixel attached sprite               | `.A32`           |
| `a64`       | 64-pixel attached sprite               | `.A64`           |
| `v`         | Vertical fill table                    | `.VFT`           |
| `e`         | Extra Half-Brite (6 planes, 64 colors) | `.EHB`           |

---

## Asset Conversion List Files

```
kingcon @list.txt
```

The file is a plain ASCII (single-byte) text file. Each non-empty, non-comment line
contains one complete set of kingcon arguments (without the leading `kingcon` binary
name):

```
// This is a comment
tiles.png   tiles  -Format=4 -Interleaved -Mask -RawPalette
font.png    font   -Format=4 -MonospaceFont "ABCDEFGHIJKLMNOPQRSTUVWXYZ" -Width=8 -Height=8
```

List files can reference other list files (`@nested.txt`) up to 5 levels deep.

---

## Common Recipes

### Single image — 4 bitplanes (16 colors), interleaved, with mask and palette

```bash
kingcon sprite.png sprite -Format=4 -Interleaved -Mask -RawPalette
```

Output:

- `sprite.BPL` — interleaved bitplane data with embedded mask planes
- `sprite.PAL` — 16 × 2 bytes = 32 bytes of raw 12-bit palette
- `sprite_preview.TGA` — preview image

File size formula for `sprite.BPL`:

```
fileSize = ceil(width/16)*2 × height × 4 (planes) × 2 (+mask) bytes
```

### Animation sequence (frames `anim001.png` … `anim010.png`), 5 bitplanes

```bash
kingcon anim001.png anim -Format=5 -Interleaved -Anim=10 -Mask -RawPalette
```

### Bob sheet with 8 bobs, 4 bitplanes

```bash
kingcon bobs.png bobs -Format=4 -Bob=8 -Mask -RawPalette
```

### Monospace font, 16 characters, 8×8 pixels, 2 bitplanes

```bash
kingcon font.png font -Format=2 -MonospaceFont "0123456789ABCDEF" -Width=8 -Height=8
```

### Extra Half-Brite (64 colors from 32 palette entries)

```bash
kingcon scene.png scene -Format=e -Interleaved -RawPalette
```

### Packman tiles example (this project)

```bash
kingcon packman_tiles.png assets/packman_tiles -Format=5 -Interleaved -Mask -RawPalette
```

Produces `packman_tiles.BPL` (5 bitplanes × 2 for mask = 10 plane-rows per scanline)
and `packman_tiles.PAL` (32 colors × 2 bytes = 64 bytes).

---

## Byte Ordering Note

All multi-byte values in KingCon output are **big-endian** (Motorola byte order), as
required by the Amiga's 68000 processor. KingCon uses `htons()` / `htonl()` explicitly
when writing palette values, BOB structs, copper lists, sprite control words, and fill
table offsets.

---

## Source Code Notes

KingCon is a single-file C++ program (`kingcon.cpp`, ~3600 lines) with the following
key classes and structures:

| Symbol                         | Role                                                           |
| ------------------------------ | -------------------------------------------------------------- |
| `CFormatSaver`                 | Abstract base class for all output format writers              |
| `CBitplaneFormatSaver`         | Writes `.BPL`; handles interleaved/non-interleaved/mask        |
| `CSpriteFormatSaver`           | Writes `.SPR`/`.S32`/`.S64` with hardware sprite control words |
| `CAttachedSpriteFormatSaver`   | Extends sprite saver for 15-color attached sprites             |
| `CVerticalFillTableSaver`      | Writes `.VFT` run-length encoded vertical column data          |
| `CChunkyFormatSaver`           | Stub — chunky format not yet implemented                       |
| `Bob` (struct)                 | 14-byte packed record stored in `.BOB` files                   |
| `Cutout` (struct)              | Internal working region extracted from source image            |
| `SourceImage` (struct)         | Holds the FreeImage bitmap + mask bitmap + line color table    |
| `Image` (struct)               | All conversion parameters (format, mode, options)              |
| `ConvertImage()`               | Top-level orchestrator of the full pipeline                    |
| `AttemptLosslessPalletizing()` | 12-bit lossless palette reduction                              |
| `ExtractMaskBitmap()`          | Builds the per-pixel opacity mask                              |
| `BuildCutoutList()`            | Determines cutout regions for all modes                        |
| `SaveFiles()`                  | Writes all output files                                        |
| `SavePreviewImage()`           | Writes the `_preview.TGA` composite                            |

# How does KingCon know to create the correct masks without the sprite size?
It actually doesn't need to know about your sprites at all! Here is how the magic works:

Global Mask Generation: When you pass the -Mask flag, KingCon looks at the entire 320x320 image. By default, it looks for Palette Index 0 (your background color). Every single pixel in the 320x320 image that matches the background color gets a 0 (transparent) in the mask plane. Every other pixel gets a 1 (opaque).
Interleaved Storage: Because you used -Interleaved -Mask, KingCon weaves this massive 320x320 mask directly into the Amiga bitplane data. Every single scanline of your 320x320 image will contain the color data immediately followed by the mask data for that exact line.
How the Amiga uses it: On the Amiga, programmers use the Blitter chip to draw graphics. When they want to draw tile (1, 2), they tell the Blitter: "Go to X=16, Y=32 in this big 320x320 image, grab a 16x16 block of pixels, and grab the mask that is interleaved right next to it."
Because the mask is generated perfectly for the entire sheet, any 16x16 chunk you cut out of it will naturally have the exact correct mask attached to it!

What about your Python script?
Your Python script works the exact same way as the Amiga! It will decode the entire 320x320 image (and its perfect mask) into one big PNG.

Then, because you pass --sprite_width 16 --sprite_height 16 to amiga_reader.py, your Python code will simply draw lines and numbers over top of that decoded image to show you exactly where the 16x16 boundaries are.

# This will now work perfectly!
python amiga_reader.py --generate_png assets/packman_tiles --width 320 --height 320 --mask --sprite_width 16 --sprite_height 16

---

