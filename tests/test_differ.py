"""Tests for logslice.differ."""

from __future__ import annotations

import pytest

from logslice.differ import DiffLine, count_changes, diff_lines, format_diff


LINES_A = [
    "2024-01-01 INFO  server started",
    "2024-01-01 INFO  listening on port 8080",
    "2024-01-01 ERROR connection refused",
    "2024-01-01 INFO  shutting down",
]

LINES_B = [
    "2024-01-01 INFO  server started",
    "2024-01-01 INFO  listening on port 9090",  # changed port
    "2024-01-01 WARN  high memory usage",        # replaced error line
    "2024-01-01 INFO  shutting down",
]


class TestDiffLines:
    def test_returns_list_of_diff_lines(self):
        result = diff_lines(LINES_A, LINES_B)
        assert isinstance(result, list)
        assert all(isinstance(d, DiffLine) for d in result)

    def test_identical_inputs_no_changes(self):
        result = diff_lines(LINES_A, LINES_A)
        changes = [d for d in result if d.tag in ("+", "-")]
        assert changes == []

    def test_empty_inputs_returns_empty(self):
        result = diff_lines([], [])
        assert result == []

    def test_detects_removed_line(self):
        a = ["line one", "line two", "line three"]
        b = ["line one", "line three"]
        result = diff_lines(a, b, context=0)
        tags = [d.tag for d in result if d.tag != "@"]
        assert "-" in tags

    def test_detects_added_line(self):
        a = ["line one", "line three"]
        b = ["line one", "line two", "line three"]
        result = diff_lines(a, b, context=0)
        tags = [d.tag for d in result if d.tag != "@"]
        assert "+" in tags

    def test_hunk_header_present(self):
        result = diff_lines(LINES_A, LINES_B)
        headers = [d for d in result if d.tag == "@"]
        assert len(headers) >= 1
        assert headers[0].content.startswith("@@")

    def test_equal_lines_have_both_line_numbers(self):
        result = diff_lines(LINES_A, LINES_B)
        equal_lines = [d for d in result if d.tag == " "]
        for dl in equal_lines:
            assert dl.line_a is not None
            assert dl.line_b is not None

    def test_removed_lines_have_only_line_a(self):
        result = diff_lines(LINES_A, LINES_B)
        removed = [d for d in result if d.tag == "-"]
        for dl in removed:
            assert dl.line_a is not None
            assert dl.line_b is None

    def test_added_lines_have_only_line_b(self):
        result = diff_lines(LINES_A, LINES_B)
        added = [d for d in result if d.tag == "+"]
        for dl in added:
            assert dl.line_a is None
            assert dl.line_b is not None


class TestFormatDiff:
    def test_yields_strings(self):
        diff = diff_lines(LINES_A, LINES_B)
        formatted = list(format_diff(diff))
        assert all(isinstance(line, str) for line in formatted)

    def test_removed_lines_prefixed_with_minus(self):
        diff = diff_lines(LINES_A, LINES_B)
        formatted = list(format_diff(diff, color=False))
        removed = [l for l in formatted if l.startswith("-")]
        assert len(removed) > 0

    def test_added_lines_prefixed_with_plus(self):
        diff = diff_lines(LINES_A, LINES_B)
        formatted = list(format_diff(diff, color=False))
        added = [l for l in formatted if l.startswith("+")]
        assert len(added) > 0

    def test_color_mode_includes_ansi_codes(self):
        diff = diff_lines(LINES_A, LINES_B)
        formatted = list(format_diff(diff, color=True))
        combined = "".join(formatted)
        assert "\033[" in combined

    def test_no_color_no_ansi_codes(self):
        diff = diff_lines(LINES_A, LINES_B)
        formatted = list(format_diff(diff, color=False))
        combined = "".join(formatted)
        assert "\033[" not in combined


class TestCountChanges:
    def test_identical_inputs_zero_changes(self):
        diff = diff_lines(LINES_A, LINES_A)
        added, removed = count_changes(diff)
        assert added == 0
        assert removed == 0

    def test_counts_added_and_removed(self):
        diff = diff_lines(LINES_A, LINES_B)
        added, removed = count_changes(diff)
        assert added > 0
        assert removed > 0

    def test_pure_addition(self):
        a = ["line one", "line three"]
        b = ["line one", "line two", "line three"]
        diff = diff_lines(a, b)
        added, removed = count_changes(diff)
        assert added == 1
        assert removed == 0

    def test_pure_deletion(self):
        a = ["line one", "line two", "line three"]
        b = ["line one", "line three"]
        diff = diff_lines(a, b)
        added, removed = count_changes(diff)
        assert added == 0
        assert removed == 1
