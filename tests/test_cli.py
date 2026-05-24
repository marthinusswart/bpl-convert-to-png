import pytest
import sys
from unittest.mock import patch, MagicMock
from amiga_reader.amiga_reader import main as cli_main

def test_cli_help(capsys):
    """Test that CLI with --help displays usage and exits 0."""
    with patch.object(sys, "argv", ["amiga-reader", "--help"]):
        with pytest.raises(SystemExit) as exc:
            cli_main()
        assert exc.value.code == 0
        
    captured = capsys.readouterr()
    assert "Usage: amiga-reader" in captured.out

def test_cli_invalid_mode(capsys):
    """Test that an invalid mode prints error and exits 1."""
    with patch.object(sys, "argv", ["amiga-reader", "--bad-mode"]):
        with pytest.raises(SystemExit) as exc:
            cli_main()
        assert exc.value.code == 1
        
    captured = capsys.readouterr()
    assert "Invalid mode" in captured.out

def test_cli_display_details_success(create_mock_bpl, create_mock_pal, capsys):
    """Test that --display_details runs successfully and captures details."""
    bpl_path, _, _ = create_mock_bpl(filename="cli_disp.bpl", width=16, height=16, bits=4)
    pal_path, _ = create_mock_pal(filename="cli_disp.pal")
    
    args = [
        "amiga-reader",
        "--display_details",
        "--bpl", bpl_path,
        "--pal", pal_path,
        "--width", "16",
        "--height", "16",
        "--bits", "4"
    ]
    with patch.object(sys, "argv", args):
        cli_main()

    captured = capsys.readouterr()
    assert "Amiga File Analyzer" in captured.out

def test_cli_generate_png_missing_dims(capsys):
    """Test that generating PNG without dimensions exits with 1."""
    args = [
        "amiga-reader",
        "--generate_png",
        "--bpl", "dummy.bpl"
    ]
    with patch.object(sys, "argv", args):
        with pytest.raises(SystemExit) as exc:
            cli_main()
        assert exc.value.code == 1
        
    captured = capsys.readouterr()
    assert "required for --generate_png mode" in captured.out

def test_cli_generate_png_success(create_mock_bpl, create_mock_pal, tmp_path, capsys):
    """Test successful CLI generation of a PNG."""
    bpl_path, _, _ = create_mock_bpl(filename="cli_gen.bpl", width=16, height=16, bits=3)
    pal_path, _ = create_mock_pal(filename="cli_gen.pal")
    
    args = [
        "amiga-reader",
        "--generate_png",
        "--bpl", bpl_path,
        "--pal", pal_path,
        "--width", "16",
        "--height", "16",
        "--bits", "3",
        "--output", str(tmp_path)
    ]
    with patch.object(sys, "argv", args):
        cli_main()
        
    captured = capsys.readouterr()
    assert "PNG generated successfully" in captured.out

@patch("amiga_reader.rich_coverage.main")
def test_cli_coverage(mock_cov_main):
    """Test that 'cov' or 'coverage' subcommands trigger the rich coverage dashboard."""
    with patch.object(sys, "argv", ["amiga-reader", "cov"]):
        with pytest.raises(SystemExit) as exc:
            cli_main()
        assert exc.value.code == 0
    mock_cov_main.assert_called_once()
    
    mock_cov_main.reset_mock()
    with patch.object(sys, "argv", ["amiga-reader", "coverage"]):
        with pytest.raises(SystemExit) as exc:
            cli_main()
        assert exc.value.code == 0
    mock_cov_main.assert_called_once()

def test_cli_invalid_arguments_handling(capsys):
    """Test ValueError handles on non-integer parameters and value checks."""
    # 1. Non-integer width
    with patch.object(sys, "argv", ["amiga-reader", "--display_details", "--width", "invalid"]):
        with pytest.raises(SystemExit) as exc:
            cli_main()
        assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "requires an integer" in captured.out

    # 2. --bits out of bounds
    with patch.object(sys, "argv", ["amiga-reader", "--display_details", "--bits", "0"]):
        with pytest.raises(SystemExit) as exc:
            cli_main()
        assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "must be between 1 and 8" in captured.out

    # 3. --pal-bits invalid
    with patch.object(sys, "argv", ["amiga-reader", "--display_details", "--pal-bits", "16"]):
        with pytest.raises(SystemExit) as exc:
            cli_main()
        assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "--pal-bits must be 12 or 24" in captured.out

    # 4. --scale invalid
    with patch.object(sys, "argv", ["amiga-reader", "--display_details", "--scale", "5"]):
        with pytest.raises(SystemExit) as exc:
            cli_main()
        assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "--scale must be 2, 3, or 4" in captured.out

def test_cli_mask_arguments(create_mock_bpl, capsys):
    """Test --mask parameter options: flag, true, false, yes, no."""
    bpl_path, _, _ = create_mock_bpl(filename="cli_mask.bpl", width=16, height=16, bits=4)
    
    # --mask false
    args1 = ["amiga-reader", "--display_details", "--bpl", bpl_path, "--mask", "false", "--width", "16", "--height", "16", "--bits", "4"]
    with patch.object(sys, "argv", args1):
        cli_main()
    captured = capsys.readouterr()
    assert "✗ No" in captured.out

    # --mask no
    args2 = ["amiga-reader", "--display_details", "--bpl", bpl_path, "--mask", "no", "--width", "16", "--height", "16", "--bits", "4"]
    with patch.object(sys, "argv", args2):
        cli_main()
    captured = capsys.readouterr()
    assert "✗ No" in captured.out

def test_cli_display_details_mismatched_dims(capsys):
    """Test display details fails when only one of width/height is provided."""
    args = ["amiga-reader", "--display_details", "--width", "320"]
    with patch.object(sys, "argv", args):
        with pytest.raises(SystemExit) as exc:
            cli_main()
        assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "Please provide both --width and --height" in captured.out

def test_cli_missing_base_name(capsys):
    """Test display details fails when base name is missing."""
    args = ["amiga-reader", "--display_details", "--width", "320", "--height", "320"]
    # No base name argument supplied (third position starts with -- or is empty)
    with patch.object(sys, "argv", args):
        with pytest.raises(SystemExit) as exc:
            cli_main()
        assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "Missing base name or --bpl file path" in captured.out

def test_cli_base_name_resolution(create_mock_bpl, tmp_path, capsys):
    """Test base name resolution when PAL file does or does not exist."""
    # Write a bpl file without writing a pal file
    bpl_path = tmp_path / "base_test.bpl"
    bpl_path.touch()
    
    # We execute using the resolved base_name "base_test"
    args = ["amiga-reader", "--display_details", str(tmp_path / "base_test"), "--width", "16", "--height", "16", "--bits", "1"]
    with patch.object(sys, "argv", args):
        cli_main()
    captured = capsys.readouterr()
    assert "Palette (.pal) Information" not in captured.out

def test_cli_error_blocks_handling(create_mock_bpl, capsys):
    """Test file not found and general exceptions handling blocks."""
    # 1. File not found
    args1 = ["amiga-reader", "--display_details", "--bpl", "missing.bpl", "--width", "16", "--height", "16"]
    with patch.object(sys, "argv", args1):
        with pytest.raises(SystemExit) as exc:
            cli_main()
        assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.out

    # 2. General exception during analyzer execution
    bpl_path, _, _ = create_mock_bpl(filename="cli_crash.bpl")
    args2 = ["amiga-reader", "--display_details", "--bpl", bpl_path, "--width", "16", "--height", "16"]
    with patch.object(sys, "argv", args2), \
         patch("amiga_reader.amiga_file_analyzer.AmigaFileAnalyzer.display_summary", side_effect=Exception("Analyzer crash")):
        with pytest.raises(SystemExit) as exc:
            cli_main()
        assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "Analyzer crash" in captured.out

def test_cli_tui_launcher(capsys):
    """Test launching TUI when less than 2 arguments are provided."""
    # Successful launch
    with patch.object(sys, "argv", ["amiga-reader"]), \
         patch("amiga_reader.tui.AmigaTUIApp.run") as mock_run:
        with pytest.raises(SystemExit) as exc:
            cli_main()
        assert exc.value.code == 0
    mock_run.assert_called_once()

    # Exception during launch
    with patch.object(sys, "argv", ["amiga-reader"]), \
         patch("amiga_reader.tui.AmigaTUIApp.run", side_effect=Exception("Failed to boot")):
        with pytest.raises(SystemExit) as exc:
            cli_main()
        assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "Error launching TUI" in captured.out
