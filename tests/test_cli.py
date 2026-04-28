"""Tests for the CLI argument parsing and main entry point."""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from io import StringIO

from logslice.cli import build_parser, main


SAMPLE_LOG = """2024-01-15 08:00:00 INFO Server started
2024-01-15 08:05:00 INFO Request received
2024-01-15 09:00:00 WARNING High memory usage
2024-01-15 10:00:00 ERROR Disk full
2024-01-15 11:00:00 INFO Cleanup complete
"""


@pytest.fixture
def log_file(tmp_path):
    """Create a temporary log file for testing."""
    path = tmp_path / "test.log"
    path.write_text(SAMPLE_LOG)
    return str(path)


class TestBuildParser:
    """Tests for the argument parser construction."""

    def test_parser_returns_namespace(self):
        parser = build_parser()
        args = parser.parse_args(["somefile.log"])
        assert args.file == "somefile.log"

    def test_default_start_is_none(self):
        parser = build_parser()
        args = parser.parse_args(["somefile.log"])
        assert args.start is None

    def test_default_end_is_none(self):
        parser = build_parser()
        args = parser.parse_args(["somefile.log"])
        assert args.end is None

    def test_start_argument_parsed(self):
        parser = build_parser()
        args = parser.parse_args(["somefile.log", "--start", "2024-01-15 08:00:00"])
        assert args.start == "2024-01-15 08:00:00"

    def test_end_argument_parsed(self):
        parser = build_parser()
        args = parser.parse_args(["somefile.log", "--end", "2024-01-15 10:00:00"])
        assert args.end == "2024-01-15 10:00:00"

    def test_line_numbers_flag_default_false(self):
        parser = build_parser()
        args = parser.parse_args(["somefile.log"])
        assert args.line_numbers is False

    def test_line_numbers_flag_enabled(self):
        parser = build_parser()
        args = parser.parse_args(["somefile.log", "--line-numbers"])
        assert args.line_numbers is True

    def test_summary_flag_default_false(self):
        parser = build_parser()
        args = parser.parse_args(["somefile.log"])
        assert args.summary is False

    def test_summary_flag_enabled(self):
        parser = build_parser()
        args = parser.parse_args(["somefile.log", "--summary"])
        assert args.summary is True


class TestMain:
    """Integration tests for the main CLI entry point."""

    def test_main_no_bounds_outputs_all_lines(self, log_file, capsys):
        with patch("sys.argv", ["logslice", log_file]):
            main()
        captured = capsys.readouterr()
        assert "Server started" in captured.out
        assert "Cleanup complete" in captured.out

    def test_main_with_start_filters_output(self, log_file, capsys):
        with patch("sys.argv", ["logslice", log_file, "--start", "2024-01-15 09:00:00"]):
            main()
        captured = capsys.readouterr()
        assert "Server started" not in captured.out
        assert "High memory usage" in captured.out
        assert "Disk full" in captured.out

    def test_main_with_end_filters_output(self, log_file, capsys):
        with patch("sys.argv", ["logslice", log_file, "--end", "2024-01-15 08:30:00"]):
            main()
        captured = capsys.readouterr()
        assert "Server started" in captured.out
        assert "Request received" in captured.out
        assert "High memory usage" not in captured.out

    def test_main_with_start_and_end(self, log_file, capsys):
        with patch("sys.argv", [
            "logslice", log_file,
            "--start", "2024-01-15 08:30:00",
            "--end", "2024-01-15 10:30:00"
        ]):
            main()
        captured = capsys.readouterr()
        assert "Server started" not in captured.out
        assert "High memory usage" in captured.out
        assert "Disk full" in captured.out
        assert "Cleanup complete" not in captured.out

    def test_main_with_summary_flag(self, log_file, capsys):
        with patch("sys.argv", ["logslice", log_file, "--summary"]):
            main()
        captured = capsys.readouterr()
        assert "lines" in captured.out.lower() or "matched" in captured.out.lower()

    def test_main_with_line_numbers(self, log_file, capsys):
        with patch("sys.argv", ["logslice", log_file, "--line-numbers"]):
            main()
        captured = capsys.readouterr()
        # Line numbers should appear as numeric prefixes
        assert "1:" in captured.out or "1 " in captured.out

    def test_main_invalid_file_exits(self, capsys):
        with patch("sys.argv", ["logslice", "/nonexistent/path/file.log"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
        assert exc_info.value.code != 0

    def test_main_invalid_start_date_exits(self, log_file, capsys):
        with patch("sys.argv", ["logslice", log_file, "--start", "not-a-date"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
        assert exc_info.value.code != 0
