import pytest
import sys
from unittest.mock import patch, MagicMock
from amiga_reader.rich_coverage import generate_rich_report, main as cov_main

def test_rich_coverage_missing_db(capsys):
    """Test that rich coverage prints a descriptive error and exits 1 if coverage db fails to load."""
    with patch("coverage.Coverage", side_effect=Exception("No DB")):
        with pytest.raises(SystemExit) as exc:
            generate_rich_report()
        assert exc.value.code == 1
        
    captured = capsys.readouterr()
    assert "Could not load coverage database" in captured.out

def test_rich_coverage_no_data(capsys):
    """Test that rich coverage prints a message and exits 1 if data is empty."""
    mock_cov = MagicMock()
    mock_cov.get_data.return_value = None  # No database data
    
    with patch("coverage.Coverage", return_value=mock_cov):
        with pytest.raises(SystemExit) as exc:
            generate_rich_report()
        assert exc.value.code == 1
        
    captured = capsys.readouterr()
    assert "No coverage data found in the .coverage database" in captured.out

def test_rich_coverage_success(capsys):
    """Test successful coverage report generation with mocked coverage stats."""
    mock_cov = MagicMock()
    
    # Mock database data
    mock_data = MagicMock()
    mock_data.measured_files.return_value = [
        "/path/src/amiga_reader/amiga_palette_reader.py",
        "/path/src/other/ignored.py" # Cover filter branch
    ]
    mock_cov.get_data.return_value = mock_data
    
    # Mock analysis numbers
    mock_numbers = MagicMock()
    mock_numbers.n_statements = 50
    mock_numbers.n_missing = 5
    mock_numbers.n_branches = 10
    mock_numbers.n_missing_branches = 2
    mock_numbers.n_partial_branches = 1
    mock_numbers.pc_covered = 90.0
    
    mock_analysis = MagicMock()
    mock_analysis.numbers = mock_numbers
    mock_cov._analyze.return_value = mock_analysis
    mock_cov.analysis2.return_value = (None, None, None, None, "10-12, 15")
    
    with patch("coverage.Coverage", return_value=mock_cov), \
         patch("os.path.relpath", side_effect=["src/amiga_reader/amiga_palette_reader.py", "src/other/ignored.py", "src/amiga_reader/amiga_palette_reader.py"]):
        generate_rich_report()
        
    captured = capsys.readouterr()
    assert "Amiga Reader - Colorized Test Coverage Report" in captured.out
    assert "Code Coverage Metrics" in captured.out
    assert "amiga_pal" in captured.out
    assert "50" in captured.out
    assert "90.0%" in captured.out
    assert "10-12, 15" in captured.out

def test_rich_coverage_edge_cases(capsys):
    """Test various coverage report edge cases (100% cover, under 90% cover, no stmts/branches, and exceptions)."""
    mock_cov = MagicMock()
    
    mock_data = MagicMock()
    # 2 files to cover duplicates and different coverages
    mock_data.measured_files.return_value = [
        "/path/src/amiga_reader/file1.py",
        "/path/src/amiga_reader/file2.py",
        "/path/src/amiga_reader/file3.py"
    ]
    mock_cov.get_data.return_value = mock_data
    
    # File 1: 100% coverage
    n1 = MagicMock(n_statements=10, n_missing=0, n_branches=0, n_missing_branches=0, n_partial_branches=0, pc_covered=100.0)
    # File 2: 80% coverage
    n2 = MagicMock(n_statements=10, n_missing=2, n_branches=0, n_missing_branches=0, n_partial_branches=0, pc_covered=80.0)
    # File 3: Exception raise to cover except block
    
    mock_cov._analyze.side_effect = [
        MagicMock(numbers=n1),
        MagicMock(numbers=n2),
        Exception("Crash during analysis")
    ]
    mock_cov.analysis2.return_value = (None, None, None, None, "")
    
    with patch("coverage.Coverage", return_value=mock_cov), \
         patch("os.path.relpath", side_effect=["src/amiga_reader/file1.py", "src/amiga_reader/file2.py", "src/amiga_reader/file3.py"]):
        generate_rich_report()
        
    captured = capsys.readouterr()
    assert "100.0%" in captured.out
    assert "80.0%" in captured.out

def test_rich_coverage_zero_statements(capsys):
    """Test coverage report output when total statements and branches are zero."""
    mock_cov = MagicMock()
    mock_data = MagicMock()
    mock_data.measured_files.return_value = ["/path/src/amiga_reader/empty.py"]
    mock_cov.get_data.return_value = mock_data
    
    n_empty = MagicMock(n_statements=0, n_missing=0, n_branches=0, n_missing_branches=0, n_partial_branches=0, pc_covered=100.0)
    mock_cov._analyze.return_value = MagicMock(numbers=n_empty)
    mock_cov.analysis2.return_value = (None, None, None, None, "")
    
    with patch("coverage.Coverage", return_value=mock_cov), \
         patch("os.path.relpath", return_value="src/amiga_reader/empty.py"):
        generate_rich_report()
        
    captured = capsys.readouterr()
    assert "TOTAL" in captured.out

def test_rich_coverage_main_execution():
    """Test that main() executes generate_rich_report."""
    with patch("amiga_reader.rich_coverage.generate_rich_report") as mock_gen:
        cov_main()
        mock_gen.assert_called_once()
