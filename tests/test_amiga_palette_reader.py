import pytest
import tempfile
import struct
import os
from amiga_reader.amiga_palette_reader import AmigaPaletteReader

def test_12bit_palette_parsing():
    """Test that a 12-bit Amiga palette is decoded into correct 8-bit RGB values."""
    # Create a dummy 12-bit palette file with 2 colors:
    # Color 0: Black (0x0000) -> (0, 0, 0)
    # Color 1: White (0x0FFF) -> (255, 255, 255)
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(struct.pack(">H", 0x0000))
        tmp.write(struct.pack(">H", 0x0FFF))
        tmp_path = tmp.name

    try:
        reader = AmigaPaletteReader(tmp_path, bits=12)
        
        assert reader.num_colors == 2
        
        # Verify Black
        assert reader.colors[0] == (0, 0, 0)
        
        # Verify White (0xF * 17 = 255 for each channel)
        assert reader.colors[1] == (255, 255, 255)
    finally:
        os.unlink(tmp_path)