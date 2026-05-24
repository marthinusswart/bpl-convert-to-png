import pytest
from pathlib import Path
from PIL import Image
from amiga_reader.amiga_palette_reader import AmigaPaletteReader
from amiga_reader.amiga_bitplane_reader import AmigaBitplaneReader
from amiga_reader.amiga_png_creator import AmigaPngCreator

def test_generate_png_success(create_mock_bpl, create_mock_pal, tmp_path):
    """Test generating a simple standard PNG with a palette."""
    bpl_path, _, _ = create_mock_bpl(filename="test_png.bpl", width=16, height=16, bits=3)
    pal_path, _ = create_mock_pal(filename="test_png.pal", bits=12)
    
    bpl_reader = AmigaBitplaneReader(bpl_path, width=16, height=16, bits=3, interleaved=True)
    pal_reader = AmigaPaletteReader(pal_path, bits=12)
    
    output_dir = tmp_path / "output"
    creator = AmigaPngCreator(
        bpl_reader=bpl_reader,
        pal_reader=pal_reader,
        output_dir=str(output_dir)
    )
    
    png_path = creator.generate_png()
    assert png_path is not None
    assert Path(png_path).exists()
    
    # Check that PNG matches dimensions
    with Image.open(png_path) as img:
        assert img.size == (16, 16)
        assert img.mode == "RGBA"

def test_generate_png_no_bpl_or_pal(create_mock_bpl, create_mock_pal):
    """Test behavior when BPL or PAL readers are missing."""
    bpl_path, _, _ = create_mock_bpl(filename="test_err.bpl", width=16, height=16, bits=2)
    pal_path, _ = create_mock_pal(filename="test_err.pal")
    
    bpl_reader = AmigaBitplaneReader(bpl_path, width=16, height=16, bits=2)
    pal_reader = AmigaPaletteReader(pal_path)
    
    # 1. No BPL reader
    creator_no_bpl = AmigaPngCreator(bpl_reader=None, pal_reader=pal_reader)
    assert creator_no_bpl.generate_png() is None
    
    # 2. No PAL reader
    creator_no_pal = AmigaPngCreator(bpl_reader=bpl_reader, pal_reader=None)
    assert creator_no_pal.generate_png() is None

def test_generate_png_with_scaling(create_mock_bpl, create_mock_pal, tmp_path):
    """Test generating a PNG scaled up using NEAREST interpolation."""
    bpl_path, _, _ = create_mock_bpl(filename="test_scale.bpl", width=16, height=16, bits=3)
    pal_path, _ = create_mock_pal(filename="test_scale.pal")
    
    bpl_reader = AmigaBitplaneReader(bpl_path, width=16, height=16, bits=3)
    pal_reader = AmigaPaletteReader(pal_path)
    
    creator = AmigaPngCreator(
        bpl_reader=bpl_reader,
        pal_reader=pal_reader,
        scale=3,
        output_dir=str(tmp_path)
    )
    
    png_path = creator.generate_png()
    assert png_path is not None
    
    with Image.open(png_path) as img:
        assert img.size == (48, 48)  # 16 * 3 = 48

def test_generate_png_with_overlay(create_mock_bpl, create_mock_pal, tmp_path):
    """Test generating a PNG with tile labels overlay."""
    bpl_path, _, _ = create_mock_bpl(filename="test_overlay.bpl", width=32, height=16, bits=3)
    pal_path, _ = create_mock_pal(filename="test_overlay.pal")
    
    bpl_reader = AmigaBitplaneReader(bpl_path, width=32, height=16, bits=3)
    pal_reader = AmigaPaletteReader(pal_path)
    
    creator = AmigaPngCreator(
        bpl_reader=bpl_reader,
        pal_reader=pal_reader,
        sprite_width=16,
        sprite_height=16,
        output_dir=str(tmp_path)
    )
    
    png_path = creator.generate_png()
    assert png_path is not None
    
    with Image.open(png_path) as img:
        assert img.size == (32, 16)

def test_generate_mask_png(create_mock_bpl, tmp_path):
    """Test generating a separate black/white mask PNG from mask plane."""
    bpl_path, _, _ = create_mock_bpl(filename="test_mask.bpl", width=16, height=16, bits=3, has_mask=True)
    
    bpl_reader = AmigaBitplaneReader(bpl_path, width=16, height=16, bits=3, has_mask=True)
    
    creator = AmigaPngCreator(
        bpl_reader=bpl_reader,
        output_dir=str(tmp_path)
    )
    
    mask_path = creator.generate_mask_png()
    assert mask_path is not None
    assert Path(mask_path).exists()
    assert str(mask_path).endswith("_mask.png")
    
    with Image.open(mask_path) as img:
        assert img.size == (16, 16)
        assert img.mode == "L"

def test_generate_mask_png_missing(create_mock_bpl):
    """Test that mask generation skips appropriately when BPL has no mask or is missing."""
    # 1. BPL has no mask
    bpl_path_nomask, _, _ = create_mock_bpl(filename="test_nomask_gen.bpl", width=16, height=16, bits=2, has_mask=False)
    bpl_reader_nomask = AmigaBitplaneReader(bpl_path_nomask, width=16, height=16, bits=2, has_mask=False)
    
    creator1 = AmigaPngCreator(bpl_reader=bpl_reader_nomask)
    assert creator1.generate_mask_png() is None
    
    # 2. No BPL reader
    creator2 = AmigaPngCreator(bpl_reader=None)
    assert creator2.generate_mask_png() is None
