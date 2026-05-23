#!/bin/sh
set -e

# Get the directory where the script is located and change to it.
# This makes all relative paths (like for venv and assets) work correctly.
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd -- "$SCRIPT_DIR"

AMIGA_READER="./dist/amiga-reader"

# Check if the standalone executable exists
if [ ! -f "$AMIGA_READER" ]; then
    echo "Error: amiga-reader executable not found at $AMIGA_READER" >&2
    echo "Please run 'python build_exe.py' in the project root first." >&2
    exit 1
fi

"$AMIGA_READER" --generate_png bpl/plowman_tiles --output converted --no-interleaved --width 320 --height 320 --scale 3 --sprite_width 16 --sprite_height 16
"$AMIGA_READER" --generate_png bpl/plowman_tiles_mask --palette bpl/plowman_tiles.pal --output converted --no-interleaved --width 320 --height 320 --bits 1 --scale 3 --sprite_width 16 --sprite_height 16
"$AMIGA_READER" --generate_png bpl/alphanumeric --palette bpl/plowman_tiles.pal --output converted --no-interleaved --width 160 --height 160 --scale 4 --sprite_width 8 --sprite_height 8

echo "✓ Conversion complete. Output is in the 'converted' directory."
