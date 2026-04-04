#!/bin/sh
set -e

# Get the directory where the script is located and change to it.
# This makes all relative paths (like for venv and assets) work correctly.
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd -- "$SCRIPT_DIR"

# Per README.md, the virtual environment is named 'venv'.
# If yours is named '.venv', change the path below.
VENV_PYTHON="./.venv/bin/python"

# Check if the python executable exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo "Error: Python virtual environment not found at $(pwd)/.venv" >&2
    echo "Please run 'python3 -m venv .venv' in the project root first." >&2
    exit 1
fi

echo "Running Amiga BPL to PNG conversion..."

"$VENV_PYTHON" amiga_reader.py --generate_png bpl/pacman_tiles --output converted --no-interleaved --width 320 --height 320 --scale 3 --sprite_width 16 --sprite_height 16

echo "✓ Conversion complete. Output is in the 'converted' directory."