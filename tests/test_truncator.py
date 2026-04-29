"""Tests for logslice.truncator module."""

import pytest
from logslice.truncator import (
    truncate_line,
    truncate_lines,
    cap_lines,
    truncate_and_cap,
    DEFAULT_MAX_LINE_LENGTH,
    DEFAULT_TRUNCATION_MARKER,
)


class TestTruncateLine:
    def test_short_line_unchanged(self):
        line = "short line"
        result, was_truncated = truncate_line(line, max_length=50)
        assert result == line
        assert was_truncated is False

    def test_long_line_is_truncated(self):
        line = "a" * 300
        result, was_truncated = truncate_line(line, max_length=100)
        assert was_truncated is True
        assert result.endswith(DEFAULT_TRUNCATION_MARKER)
        assert len(result) == 100 + len(DEFAULT_TRUNCATION_MARKER)

    def test_exact_length_not_truncated(self):
        line = "x" * DEFAULT_MAX_LINE_LENGTH
        result, was_truncated = truncate_line(line)
        assert was_truncated is False
        assert result == line

    def test_custom_marker(self):
        line = "hello world extra content"
        result, was_truncated = truncate_line(line, max_length=5, marker=">>>")
        assert result == "hello>>>"
        assert was_truncated is True

    def test_invalid_max_length_raises(self):
        with pytest.raises(ValueError):
            truncate_line("some line", max_length=0)


class TestTruncateLines:
    def test_no_long_lines(self):
        lines = ["short", "also short"]
        result, count = truncate_lines(lines, max_length=50)
        assert result == lines
        assert count == 0

    def test_counts_truncated_lines(self):
        lines = ["a" * 300, "b" * 10, "c" * 250]
        result, count = truncate_lines(lines, max_length=100)
        assert count == 2
        assert len(result) == 3

    def test_empty_list_returns_empty(self):
        result, count = truncate_lines([])
        assert result == []
        assert count == 0


class TestCapLines:
    def test_no_cap_returns_all(self):
        lines = ["a", "b", "c"]
        result, was_capped = cap_lines(lines, max_lines=None)
        assert result == lines
        assert was_capped is False

    def test_cap_limits_output(self):
        lines = list(range(10))
        result, was_capped = cap_lines(lines, max_lines=5)
        assert result == list(range(5))
        assert was_capped is True

    def test_cap_equal_to_length_not_capped(self):
        lines = ["x", "y", "z"]
        result, was_capped = cap_lines(lines, max_lines=3)
        assert result == lines
        assert was_capped is False

    def test_zero_or_negative_max_lines_returns_all(self):
        lines = ["a", "b"]
        result, was_capped = cap_lines(lines, max_lines=0)
        assert result == lines
        assert was_capped is False


class TestTruncateAndCap:
    def test_combined_truncation_and_cap(self):
        lines = ["a" * 300] * 20
        result, truncated_count, was_capped = truncate_and_cap(
            lines, max_length=100, max_lines=10
        )
        assert len(result) == 10
        assert truncated_count == 10
        assert was_capped is True

    def test_no_truncation_no_cap(self):
        lines = ["short", "lines"]
        result, truncated_count, was_capped = truncate_and_cap(lines, max_length=200)
        assert result == lines
        assert truncated_count == 0
        assert was_capped is False
