import pytest
import os
from amiga_reader.amiga_palette_reader import AmigaPaletteReader

def test_12bit_palette_parsing(create_mock_pal):
    """Test that a 12-bit Amiga palette is decoded into correct 8-bit RGB values."""
    colors = [
        (0, 0, 0),        # Black -> 0x0000
        (255, 255, 255),  # White -> 0x0FFF
        (170, 85, 0)      # Brownish -> 0x0A50 (10*17=170, 5*17=85, 0*17=0)
    ]
    pal_path, expected_colors = create_mock_pal(bits=12, colors=colors)
    
    reader = AmigaPaletteReader(pal_path, bits=12)
    assert reader.num_colors == len(colors)
    assert reader.colors[0] == colors[0]
    assert reader.colors[1] == colors[1]
    assert reader.colors[2] == colors[2]

def test_24bit_palette_parsing(create_mock_pal):
    """Test that a 24-bit palette is decoded correctly."""
    colors = [
        (12, 34, 56),
        (78, 90, 12),
        (255, 128, 64)
    ]
    pal_path, expected_colors = create_mock_pal(bits=24, colors=colors)
    
    reader = AmigaPaletteReader(pal_path, bits=24)
    assert reader.num_colors == len(colors)
    assert reader.colors[0] == colors[0]
    assert reader.colors[1] == colors[1]
    assert reader.colors[2] == colors[2]

def test_invalid_file_size(tmp_path):
    """Test that ValueError is raised on invalid file sizes."""
    # Write 3 bytes (invalid for 12-bit which requires multiple of 2)
    bad_12bit = tmp_path / "bad12.pal"
    bad_12bit.write_bytes(b"\x00\x00\x00")
    
    with pytest.raises(ValueError) as exc:
        AmigaPaletteReader(bad_12bit, bits=12)
    assert "not a multiple of 2" in str(exc.value)
    
    # Write 5 bytes (invalid for 24-bit which requires multiple of 4)
    bad_24bit = tmp_path / "bad24.pal"
    bad_24bit.write_bytes(b"\x00\x00\x00\x00\x00")
    
    with pytest.raises(ValueError) as exc:
        AmigaPaletteReader(bad_24bit, bits=24)
    assert "not a multiple of 4" in str(exc.value)

def test_get_summary(create_mock_pal):
    """Test that get_summary returns the correct metadata dict."""
    pal_path, colors = create_mock_pal(bits=12)
    reader = AmigaPaletteReader(pal_path, bits=12)
    
    summary = reader.get_summary()
    assert summary["num_colors"] == len(colors)
    assert summary["file_size"] == os.path.getsize(pal_path)
    assert summary["colors"] == colors
    assert summary["bits"] == 12

def test_missing_file():
    """Test that FileNotFoundError is raised if the palette file is missing."""
    with pytest.raises(FileNotFoundError):
        AmigaPaletteReader("non_existent_palette.pal")