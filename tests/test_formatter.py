"""Tests for logslice.formatter."""

import io
import pytest

from logslice.formatter import format_lines, format_summary, format_no_match


SAMPLE_LINES = [
    "2024-01-01 00:00:01 INFO  Starting up\n",
    "2024-01-01 00:00:02 DEBUG Loaded config\n",
    "2024-01-01 00:00:03 ERROR Something failed\n",
]


class TestFormatLines:
    def test_writes_all_lines(self):
        buf = io.StringIO()
        count = format_lines(SAMPLE_LINES, output=buf)
        assert count == 3
        assert buf.getvalue() == "".join(SAMPLE_LINES)

    def test_returns_zero_for_empty(self):
        buf = io.StringIO()
        count = format_lines([], output=buf)
        assert count == 0
        assert buf.getvalue() == ""

    def test_prefix_line_numbers(self):
        buf = io.StringIO()
        count = format_lines(SAMPLE_LINES, output=buf, prefix_line_numbers=True)
        assert count == 3
        lines = buf.getvalue().splitlines()
        assert lines[0].startswith("     1  ")
        assert lines[1].startswith("     2  ")
        assert lines[2].startswith("     3  ")

    def test_prefix_line_numbers_custom_start(self):
        buf = io.StringIO()
        format_lines(SAMPLE_LINES[:1], output=buf, prefix_line_numbers=True, start_line=42)
        assert buf.getvalue().startswith("    42  ")

    def test_adds_newline_if_missing(self):
        buf = io.StringIO()
        format_lines(["no newline at end"], output=buf)
        assert buf.getvalue().endswith("\n")

    def test_does_not_double_newline(self):
        buf = io.StringIO()
        format_lines(["already has newline\n"], output=buf)
        assert buf.getvalue().count("\n") == 1


class TestFormatSummary:
    def test_with_total(self):
        buf = io.StringIO()
        format_summary(50, total=200, output=buf)
        assert "50 of 200" in buf.getvalue()
        assert "25.0%" in buf.getvalue()

    def test_without_total(self):
        buf = io.StringIO()
        format_summary(7, output=buf)
        assert "7 lines matched" in buf.getvalue()

    def test_zero_total_no_division_error(self):
        buf = io.StringIO()
        format_summary(0, total=0, output=buf)
        assert "0.0%" in buf.getvalue()


class TestFormatNoMatch:
    def test_emits_warning(self):
        buf = io.StringIO()
        format_no_match(output=buf)
        assert "Warning" in buf.getvalue()
        assert "no lines matched" in buf.getvalue()
