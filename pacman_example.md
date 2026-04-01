## Deep Dive: Pac-Man Tiles Memory Layout

Let's break down exactly how the Amiga structures the `.bpl` file when you run this command:

```bash
..\..\tools\kingcon.exe pacman_tiles.png pacman_tiles -Interleaved -Format=5 -RawPalette -Mask
```

To understand the final 128,000-byte file, we need to build it up step-by-step.

### Bitplane 0-4

A `320x320` image requires **40 bytes per scanline** (`320 pixels / 8 bits per byte = 40 bytes`). 
If we were exporting a 5-bitplane image (32 colors) with no mask, the interleaved file layout would look like this:

```text
[=== SCANLINE 0 ===]
+------------------------+
| 1. Plane 0 (40 bytes)  |
+------------------------+
| 2. Plane 1 (40 bytes)  |
+------------------------+
| 3. Plane 2 (40 bytes)  |
+------------------------+
| 4. Plane 3 (40 bytes)  |
+------------------------+
| 5. Plane 4 (40 bytes)  |
+------------------------+

[=== SCANLINE 1 ===]
+------------------------+
| 1. Plane 0 (40 bytes)  |
+------------------------+
| 2. Plane 1 (40 bytes)  |
+------------------------+
| 3. Plane 2 (40 bytes)  |
+------------------------+
| 4. Plane 3 (40 bytes)  |
+------------------------+
| 5. Plane 4 (40 bytes)  |
+------------------------+

... (Repeats for all 320 scanlines) ...
```
*Running Total: 40 bytes × 320 lines = 12,800 bytes*

### Bitplanes with Mask

When you supply the -Mask flag along with -Interleaved, KingCon does something very specific: it duplicates the 40-byte mask and weaves it immediately after every single color plane.

For our 5-bitplane image, this means 5 identical mask blocks are added per scanline, doubling the size of the file:

```text
[=== SCANLINE 0 ===]
+------------------------+
| 1. Plane 0 (40 bytes)  |
+------------------------+
| 2. Mask (40 bytes)     |
+------------------------+
| 3. Plane 1 (40 bytes)  |
+------------------------+
| 4. Mask (40 bytes)     |
+------------------------+
| 5. Plane 2 (40 bytes)  |
+------------------------+
| 6. Mask (40 bytes)     |
+------------------------+
| 7. Plane 3 (40 bytes)  |
+------------------------+
| 8. Mask (40 bytes)     |
+------------------------+
| 9. Plane 4 (40 bytes)  |
+------------------------+
|10. Mask (40 bytes)     |
+------------------------+

[=== SCANLINE 1 ===]
+------------------------+
| 1. Plane 0 (40 bytes)  |
+------------------------+
| 2. Mask (40 bytes)     |
+------------------------+

... (Repeats for all 320 scanlines) ...

Running Total: 400 bytes × 320 lines = 128,000 bytes