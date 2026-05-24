import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from amiga_reader.tui import FormGroup, AmigaTUIApp, main as tui_main

def test_form_group():
    fg = FormGroup(border_title="Options Block")
    assert fg.border_title == "Options Block"

def test_tui_app_scan_files_nonexistent():
    """Test that scanning is skipped gracefully if the 'bpl' directory does not exist."""
    with patch("pathlib.Path.exists", return_value=False):
        app = AmigaTUIApp()
        assert len(app.bpl_files) == 0
        assert len(app.pal_files) == 0

def test_tui_app_scan_files_success(tmp_path):
    """Test scanning for BPL and PAL files case-insensitively."""
    with patch("amiga_reader.tui.Path") as mock_path_class:
        mock_bpl_dir = MagicMock()
        mock_bpl_dir.exists.return_value = True
        
        mock_bpl1 = MagicMock()
        mock_bpl1.is_file.return_value = True
        mock_bpl1.suffix = ".bpl"
        mock_bpl1.name = "test1.bpl"
        
        mock_bpl2 = MagicMock()
        mock_bpl2.is_file.return_value = True
        mock_bpl2.suffix = ".BPL"
        mock_bpl2.name = "test2.BPL"
        
        mock_pal1 = MagicMock()
        mock_pal1.is_file.return_value = True
        mock_pal1.suffix = ".pal"
        mock_pal1.name = "test1.pal"
        
        mock_pal2 = MagicMock()
        mock_pal2.is_file.return_value = True
        mock_pal2.suffix = ".PAL"
        mock_pal2.name = "test3.PAL"
        
        mock_txt = MagicMock()
        mock_txt.is_file.return_value = True
        mock_txt.suffix = ".txt"
        mock_txt.name = "other.txt"
        
        mock_bpl_dir.iterdir.return_value = [
            mock_bpl1,
            mock_bpl2,
            mock_pal1,
            mock_pal2,
            mock_txt
        ]
        mock_path_class.return_value = mock_bpl_dir
        
        app = AmigaTUIApp()
        assert len(app.bpl_files) == 2
        assert len(app.pal_files) == 2
        assert app.bpl_files[0].name == "test1.bpl"
        assert app.bpl_files[1].name == "test2.BPL"
        assert app.pal_files[0].name == "test1.pal"
        assert app.pal_files[1].name == "test3.PAL"

@patch("pathlib.Path.stat")
def test_tui_app_auto_configure(mock_stat):
    """Test the file-name matching and configuration heuristics."""
    mock_stat.return_value.st_size = 1000
    
    app = AmigaTUIApp()
    app.execution_log = MagicMock()
    app.analysis_log = MagicMock()
    
    app.select_pal = MagicMock()
    app.cb_mask = MagicMock()
    app.select_bits = MagicMock()
    app.cb_interleaved = MagicMock()
    app.cb_overlay = MagicMock()
    app.input_sprite_w = MagicMock()
    app.input_sprite_h = MagicMock()
    app.input_width = MagicMock()
    app.input_height = MagicMock()
    app.info_label = MagicMock()
    app.input_bpl = MagicMock()
    
    app.pal_files = [Path("bpl/pacman_tiles.pal"), Path("bpl/plowman.pal")]
    app.pal_list = MagicMock()
    
    # 1. pacman_tiles heuristic
    app.auto_configure(Path("bpl/pacman_tiles.bpl"))
    assert app.select_pal.value == "bpl/pacman_tiles.pal"
    assert app.cb_mask.value is False
    assert app.cb_overlay.value is True
    
    # 2. alphanumeric heuristic
    app.auto_configure(Path("bpl/alphanumeric.bpl"))
    assert app.cb_overlay.value is True
    
    # 3. pacman-sprite heuristic with 0001
    app.auto_configure(Path("bpl/pacman-sprite-0001.bpl"))
    assert app.input_width.value == "16"
    assert app.input_height.value == "16"
    
    # 4. pacman-sprite heuristic without 0001
    app.auto_configure(Path("bpl/pacman-sprite.bpl"))
    assert app.input_width.value == "32"
    assert app.input_height.value == "256"

@patch("pathlib.Path.stat")
def test_tui_app_auto_configure_more_heuristics(mock_stat):
    """Test additional auto configure heuristics (mask files, plowman_tiles, ValueError)."""
    mock_stat.return_value.st_size = 1000
    app = AmigaTUIApp()
    app.execution_log = MagicMock()
    app.analysis_log = MagicMock()
    
    app.select_pal = MagicMock()
    app.cb_mask = MagicMock()
    app.select_bits = MagicMock()
    app.cb_interleaved = MagicMock()
    app.cb_overlay = MagicMock()
    app.input_sprite_w = MagicMock()
    app.input_sprite_h = MagicMock()
    app.input_width = MagicMock()
    app.input_height = MagicMock()
    app.info_label = MagicMock()
    app.input_bpl = MagicMock()
    
    app.pal_files = [Path("bpl/pacman_tiles.pal"), Path("bpl/plowman.pal")]
    app.pal_list = MagicMock()
    
    # 1. Mask file in stem name
    app.auto_configure(Path("bpl/pacman_tiles_mask.bpl"))
    assert app.cb_mask.value is True
    assert app.select_bits.value == 1
    
    # 2. plowman_tiles heuristic
    app.auto_configure(Path("bpl/plowman_tiles.bpl"))
    assert app.cb_overlay.value is True
    assert app.input_width.value == "320"
    assert app.input_height.value == "320"
    
    # 3. Dimension auto detection fails (mocking reader to raise ValueError)
    with patch("amiga_reader.tui.AmigaBitplaneReader", side_effect=Exception("Detection crashed")):
        app.auto_configure(Path("bpl/unknown_dims.bpl"))
        # Verify log output was recorded
        assert app.execution_log.write.called

@patch("pathlib.Path.stat")
def test_tui_app_list_navigation(mock_stat):
    """Test ListView select changes and highlights for both BPL and PAL lists."""
    mock_stat.return_value.st_size = 1000
    
    app = AmigaTUIApp()
    app.bpl_files = [Path("bpl/test.bpl")]
    app.pal_files = [Path("bpl/test.pal")]
    
    app.execution_log = MagicMock()
    app.analysis_log = MagicMock()
    app.input_bpl = MagicMock()
    app.input_bpl.value = ""
    app.select_pal = MagicMock()
    app.pal_list = MagicMock()
    
    # Test none item in message
    msg_none = MagicMock()
    msg_none.item = None
    app.on_list_view_selected(msg_none)
    
    # Test BPL select message
    item = MagicMock()
    item.id = "bpl_0"
    msg_bpl = MagicMock()
    msg_bpl.item = item
    msg_bpl.list_view = app.file_list = MagicMock()
    
    with patch.object(app, "auto_configure") as mock_auto:
        app.on_list_view_selected(msg_bpl)
        assert app.input_bpl.value == "bpl/test.bpl"
        mock_auto.assert_called_once_with(Path("bpl/test.bpl"))
        
    # Redundant BPL trigger
    with patch.object(app, "auto_configure") as mock_auto:
        app.on_list_view_selected(msg_bpl)
        mock_auto.assert_not_called()
        
    # Test PAL select message
    item_pal = MagicMock()
    item_pal.id = "pal_0"
    msg_pal = MagicMock()
    msg_pal.item = item_pal
    msg_pal.list_view = app.pal_list = MagicMock()
    
    app.select_pal.value = ""
    app.on_list_view_selected(msg_pal)
    assert app.select_pal.value == "bpl/test.pal"
    
    # Redundant PAL trigger
    app.on_list_view_selected(msg_pal)

def test_tui_select_changed_sync():
    """Test synchronisation between select palette dropdown and sidebar lists."""
    app = AmigaTUIApp()
    app.pal_files = [Path("bpl/test1.pal"), Path("bpl/test2.pal")]
    app.select_pal = MagicMock()
    app.pal_list = MagicMock()
    
    event = MagicMock()
    event.select = app.select_pal
    
    # 1. value is None
    event.value = None
    app.on_select_changed(event)
    assert app.pal_list.index is None
    
    # 2. value matches existing file
    event.value = "bpl/test2.pal"
    app.on_select_changed(event)
    assert app.pal_list.index == 1
    
    # 3. value raises ValueError (non-existent file)
    event.value = "bpl/non_existent.pal"
    app.on_select_changed(event)
    assert app.pal_list.index is None

def test_tui_update_info_panel_unknown_dims():
    """Test updating left details panel when dimensions are not auto-detected."""
    app = AmigaTUIApp()
    app.info_label = MagicMock()
    app.cb_mask = MagicMock(value=False)
    app.cb_interleaved = MagicMock(value=True)
    
    app.update_info_panel(Path("bpl/test.bpl"), 1024, None, None, None)
    assert "Dims: Unknown" in app.info_label.update.call_args[0][0]

def test_tui_on_button_pressed_actions():
    """Test button pressing events correctly route actions."""
    app = AmigaTUIApp()
    
    # Analyze (btn-display)
    ev_disp = MagicMock()
    ev_disp.button.id = "btn-display"
    with patch.object(app, "action_display") as mock_disp:
        app.on_button_pressed(ev_disp)
        mock_disp.assert_called_once()
        
    # Convert (btn-convert)
    ev_conv = MagicMock()
    ev_conv.button.id = "btn-convert"
    with patch.object(app, "action_convert") as mock_conv:
        app.on_button_pressed(ev_conv)
        mock_conv.assert_called_once()

def test_tui_get_form_values_validation():
    """Test full form validation constraints (missing BPL, non-int sizes, invalid overlay)."""
    app = AmigaTUIApp()
    app.execution_log = MagicMock()
    
    # Initialize inputs
    app.input_bpl = MagicMock()
    app.select_pal = MagicMock()
    app.input_width = MagicMock()
    app.input_height = MagicMock()
    app.select_bits = MagicMock()
    app.cb_mask = MagicMock()
    app.cb_interleaved = MagicMock()
    app.select_pal_bits = MagicMock()
    app.select_scale = MagicMock()
    app.cb_overlay = MagicMock()
    app.input_sprite_w = MagicMock()
    app.input_sprite_h = MagicMock()
    app.cb_gen_mask = MagicMock()
    app.input_output_dir = MagicMock()
    
    # 1. BPL file is empty
    app.input_bpl.value = ""
    assert app.get_form_values() is None
    
    # 2. Dimensions not integers
    app.input_bpl.value = "bpl/test.bpl"
    app.input_width.value = "invalid"
    app.input_height.value = "16"
    assert app.get_form_values() is None
    
    # 3. Invalid overlay dimensions
    app.input_width.value = "16"
    app.cb_overlay.value = True
    app.input_sprite_w.value = "invalid"
    app.input_sprite_h.value = "16"
    
    values = app.get_form_values()
    assert values is not None
    # Invalid overlay should log warning and return None for overlay sprite dims
    assert values["sprite_width"] is None
    assert app.execution_log.write.called

def test_tui_actions_edge_cases():
    """Test action_convert and action_display edge cases (form values empty, converter success/failure, exceptions)."""
    app = AmigaTUIApp()
    app.execution_log = MagicMock()
    app.analysis_log = MagicMock()
    
    # 1. Form values empty in convert
    with patch.object(app, "get_form_values", return_value=None):
        app.action_convert()
        app.action_display()
        assert not app.execution_log.write.called
        
    # 2. Form values valid
    valid_form = {
        "bpl_file": "bpl/test.bpl",
        "pal_file": "bpl/test.pal",
        "width": 16,
        "height": 16,
        "bits": 5,
        "has_mask": True,
        "interleaved": True,
        "pal_bits": 12,
        "scale": 3,
        "sprite_width": 16,
        "sprite_height": 16,
        "gen_mask": True,
        "output_dir": "converted"
    }
    
    # 3. Convert finishes successfully
    with patch.object(app, "get_form_values", return_value=valid_form), \
         patch("amiga_reader.tui.AmigaFileAnalyzer") as mock_analyzer:
        mock_inst = MagicMock()
        mock_inst.generate_png.return_value = "converted/test.png"
        mock_analyzer.return_value = mock_inst
        
        app.action_convert()
        assert "SUCCESS" in app.execution_log.write.call_args[0][0]
        
    # 4. Convert finishes with None path
    with patch.object(app, "get_form_values", return_value=valid_form), \
         patch("amiga_reader.tui.AmigaFileAnalyzer") as mock_analyzer:
        mock_inst = MagicMock()
        mock_inst.generate_png.return_value = None
        mock_analyzer.return_value = mock_inst
        
        app.action_convert()
        assert "no file was written" in app.execution_log.write.call_args[0][0]

    # 5. Convert raises Exception
    with patch.object(app, "get_form_values", return_value=valid_form), \
         patch("amiga_reader.tui.AmigaFileAnalyzer", side_effect=Exception("Failed completely")):
        app.action_convert()
        all_lines = [call[0][0] for call in app.execution_log.write.call_args_list]
        assert any("CRITICAL ERROR" in line for line in all_lines)

    # 6. Display raises Exception
    with patch.object(app, "get_form_values", return_value=valid_form), \
         patch("amiga_reader.tui.AmigaFileAnalyzer", side_effect=Exception("Analyzer fail")):
        app.action_display()
        all_lines = [call[0][0] for call in app.analysis_log.write.call_args_list]
        assert any("CRITICAL ERROR" in line for line in all_lines)

@pytest.mark.asyncio
async def test_tui_action_quit():
    app = AmigaTUIApp()
    app.execution_log = MagicMock()
    with patch.object(app, "exit") as mock_exit:
        await app.action_quit()
        mock_exit.assert_called_once()

def test_tui_main():
    with patch("amiga_reader.tui.AmigaTUIApp.run") as mock_run:
        tui_main()
        mock_run.assert_called_once()

@pytest.mark.asyncio
async def test_tui_integration(create_mock_bpl, create_mock_pal):
    """Test full integration of the Textual App in virtual terminal."""
    bpl_path, _, _ = create_mock_bpl(filename="tui_test.bpl", width=16, height=16, bits=5)
    pal_path, _ = create_mock_pal(filename="tui_test.pal")
    
    app = AmigaTUIApp()
    app.bpl_files = [Path(bpl_path)]
    app.pal_files = [Path(pal_path)]
    
    async with app.run_test() as pilot:
        assert app.title == "Amiga BPL Converter TUI"
        
        app.file_list.index = 0
        await pilot.pause()
        
        assert app.input_bpl.value == str(bpl_path)
        assert app.input_width.value == "16"
        assert app.input_height.value == "16"
        assert app.select_pal.value == str(pal_path)
        
        await pilot.press("d")
        await pilot.pause()
        assert len(app.analysis_log.lines) > 0
        
        with patch("amiga_reader.tui.AmigaFileAnalyzer") as mock_analyzer:
            mock_inst = MagicMock()
            mock_inst.generate_png.return_value = "converted/tui_test.png"
            mock_analyzer.return_value = mock_inst
            
            await pilot.press("c")
            await pilot.pause()
            mock_inst.generate_png.assert_called_once()
