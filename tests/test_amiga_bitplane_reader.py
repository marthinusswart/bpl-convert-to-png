import pytest
from amiga_reader.amiga_bitplane_reader import AmigaBitplaneReader

def pattern_1(y, x):
    """Custom pixel pattern function returning (color_index, mask_val)."""
    color = (x + y) % 16
    mask = 255 if x % 2 == 0 else 0
    return color, mask

def test_decode_interleaved_no_mask(create_mock_bpl):
    """Test decoding interleaved bitplanes with no mask."""
    width, height, bits = 16, 16, 4
    bpl_path, expected_pixels, _ = create_mock_bpl(
        filename="inter_nomask.bpl",
        width=width,
        height=height,
        bits=bits,
        has_mask=False,
        interleaved=True,
        pattern_fn=pattern_1
    )
    
    reader = AmigaBitplaneReader(bpl_path, width=width, height=height, bits=bits, has_mask=False, interleaved=True)
    pixels, mask = reader.decode_pixels()
    
    assert mask is None
    assert pixels == expected_pixels

def test_decode_interleaved_with_mask(create_mock_bpl):
    """Test decoding interleaved bitplanes with a mask."""
    width, height, bits = 16, 16, 5
    bpl_path, expected_pixels, expected_mask = create_mock_bpl(
        filename="inter_mask.bpl",
        width=width,
        height=height,
        bits=bits,
        has_mask=True,
        interleaved=True,
        pattern_fn=pattern_1
    )
    
    reader = AmigaBitplaneReader(bpl_path, width=width, height=height, bits=bits, has_mask=True, interleaved=True)
    pixels, mask = reader.decode_pixels()
    
    assert pixels == expected_pixels
    assert mask == expected_mask

def test_decode_non_interleaved_no_mask(create_mock_bpl):
    """Test decoding non-interleaved bitplanes with no mask."""
    width, height, bits = 16, 16, 3
    bpl_path, expected_pixels, _ = create_mock_bpl(
        filename="noninter_nomask.bpl",
        width=width,
        height=height,
        bits=bits,
        has_mask=False,
        interleaved=False,
        pattern_fn=pattern_1
    )
    
    reader = AmigaBitplaneReader(bpl_path, width=width, height=height, bits=bits, has_mask=False, interleaved=False)
    pixels, mask = reader.decode_pixels()
    
    assert mask is None
    assert pixels == expected_pixels

def test_decode_non_interleaved_with_mask(create_mock_bpl):
    """Test decoding non-interleaved bitplanes with a mask."""
    width, height, bits = 32, 16, 4
    bpl_path, expected_pixels, expected_mask = create_mock_bpl(
        filename="noninter_mask.bpl",
        width=width,
        height=height,
        bits=bits,
        has_mask=True,
        interleaved=False,
        pattern_fn=pattern_1
    )
    
    reader = AmigaBitplaneReader(bpl_path, width=width, height=height, bits=bits, has_mask=True, interleaved=False)
    pixels, mask = reader.decode_pixels()
    
    assert pixels == expected_pixels
    assert mask == expected_mask

def test_autodetect_dimensions(create_mock_bpl):
    """Test the dimension auto-detection heuristic from file sizes."""
    # Create a 32x32 image with 5 bits (interleaved, no mask)
    # Expected single plane size = ((32+15)//16)*2 = 4 bytes/line * 32 lines = 128 bytes
    # Total expected file size = 128 * 5 = 640 bytes
    width, height, bits = 32, 32, 5
    bpl_path, _, _ = create_mock_bpl(
        filename="autodetect.bpl",
        width=width,
        height=height,
        bits=bits,
        has_mask=False,
        interleaved=True
    )
    
    # Run constructor without width/height
    reader = AmigaBitplaneReader(bpl_path, width=None, height=None, bits=bits, has_mask=False, interleaved=True)
    assert reader.width == 32
    assert reader.height == 32

def test_file_size_mismatch(create_mock_bpl):
    """Test that ValueError is raised if the file size does not match explicit dimensions."""
    width, height, bits = 16, 16, 4
    bpl_path, _, _ = create_mock_bpl(
        filename="mismatch.bpl",
        width=width,
        height=height,
        bits=bits,
        has_mask=False,
        interleaved=True
    )
    
    # Requesting wrong height (17 instead of 16) should raise ValueError
    with pytest.raises(ValueError) as exc:
        AmigaBitplaneReader(bpl_path, width=width, height=17, bits=bits, has_mask=False, interleaved=True)
    assert "File size mismatch" in str(exc.value)

def test_get_summary(create_mock_bpl):
    """Test get_summary output dictionary values."""
    width, height, bits = 16, 16, 5
    bpl_path, _, _ = create_mock_bpl(
        filename="summary.bpl",
        width=width,
        height=height,
        bits=bits,
        has_mask=True,
        interleaved=True
    )
    
    reader = AmigaBitplaneReader(bpl_path, width=width, height=height, bits=bits, has_mask=True, interleaved=True)
    summary = reader.get_summary()
    
    assert summary["width"] == width
    assert summary["height"] == height
    assert summary["depth"] == bits
    assert summary["max_colors"] == 32
    assert summary["has_mask"] is True
    assert summary["interleaved"] is True
    assert summary["bytes_per_line"] == 2
    assert summary["total_planes"] == 10
