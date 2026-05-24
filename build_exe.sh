#!/bin/sh
set -e

# Get the directory where the script is located and change to it.
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd -- "$SCRIPT_DIR"

VENV_PYTHON="./.venv/bin/python"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "Error: Python virtual environment not found at $(pwd)/.venv" >&2
    echo "Please make sure your virtual environment is initialized in .venv" >&2
    exit 1
fi

"$VENV_PYTHON" build_exe.py
