import pytest
from pathlib import Path
from amiga_reader.amiga_file_analyzer import AmigaFileAnalyzer

def test_display_summary(create_mock_bpl, create_mock_pal, capsys):
    """Test that display_summary outputs correct details for both BPL and PAL."""
    bpl_path, _, _ = create_mock_bpl(filename="analyzer.bpl", width=16, height=16, bits=4, has_mask=True)
    pal_path, _ = create_mock_pal(filename="analyzer.pal")
    
    analyzer = AmigaFileAnalyzer(
        bpl_file=bpl_path,
        pal_file=pal_path,
        mode="display",
        width=16,
        height=16,
        bits=4,
        has_mask=True,
        interleaved=True,
        pal_bits=12
    )
    
    analyzer.display_summary()
    
    # Capture standard output and verify console printed summaries
    captured = capsys.readouterr()
    assert "Amiga File Analyzer" in captured.out
    assert "Bitplane (.bpl) Information" in captured.out
    assert "Palette (.pal) Information" in captured.out
    assert "Color Palette" in captured.out
    assert "16 x 16 pixels" in captured.out
    assert "4 planes" in captured.out

def test_generate_png_from_analyzer(create_mock_bpl, create_mock_pal, tmp_path):
    """Test that generate_png successfully delegates to AmigaPngCreator and generates files."""
    bpl_path, _, _ = create_mock_bpl(filename="analyzer_gen.bpl", width=16, height=16, bits=3, has_mask=True)
    pal_path, _ = create_mock_pal(filename="analyzer_gen.pal")
    
    analyzer = AmigaFileAnalyzer(
        bpl_file=bpl_path,
        pal_file=pal_path,
        mode="generate",
        width=16,
        height=16,
        bits=3,
        has_mask=True,
        interleaved=True,
        pal_bits=12,
        gen_mask=True,
        output_dir=str(tmp_path)
    )
    
    png_path = analyzer.generate_png()
    assert png_path is not None
    assert Path(png_path).exists()
    
    # Verify that mask file was also generated because gen_mask=True
    mask_path = tmp_path / "analyzer_gen_mask.png"
    assert mask_path.exists()
