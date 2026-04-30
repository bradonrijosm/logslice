"""Tests for logslice.stats module."""

import pytest
from logslice.stats import compute_stats, format_stats, _count_levels


SAMPLE_LINES = [
    "2024-01-01 INFO  Service started",
    "2024-01-01 DEBUG Connecting to database",
    "2024-01-01 ERROR Connection refused",
    "2024-01-01 INFO  Service started",  # duplicate
    "2024-01-01 WARN  Retry attempt 1",
]


class TestComputeStats:
    def test_empty_input_returns_zeroed_stats(self):
        stats = compute_stats([])
        assert stats["total_lines"] == 0
        assert stats["unique_lines"] == 0
        assert stats["duplicate_lines"] == 0
        assert stats["avg_line_length"] == 0.0
        assert stats["max_line_length"] == 0
        assert stats["min_line_length"] == 0
        assert stats["level_counts"] == {}

    def test_total_lines_count(self):
        stats = compute_stats(SAMPLE_LINES)
        assert stats["total_lines"] == 5

    def test_unique_lines_count(self):
        stats = compute_stats(SAMPLE_LINES)
        assert stats["unique_lines"] == 4

    def test_duplicate_lines_count(self):
        stats = compute_stats(SAMPLE_LINES)
        assert stats["duplicate_lines"] == 1

    def test_no_duplicates(self):
        lines = ["line one", "line two", "line three"]
        stats = compute_stats(lines)
        assert stats["duplicate_lines"] == 0
        assert stats["unique_lines"] == 3

    def test_avg_line_length(self):
        lines = ["ab", "abcd"]  # lengths 2 and 4 => avg 3.0
        stats = compute_stats(lines)
        assert stats["avg_line_length"] == 3.0

    def test_max_and_min_line_length(self):
        lines = ["short", "a much longer line here"]
        stats = compute_stats(lines)
        assert stats["max_line_length"] == len("a much longer line here")
        assert stats["min_line_length"] == len("short")

    def test_level_counts_populated(self):
        stats = compute_stats(SAMPLE_LINES)
        assert stats["level_counts"].get("ERROR") == 1
        assert stats["level_counts"].get("INFO") == 2
        assert stats["level_counts"].get("DEBUG") == 1

    def test_warning_normalised_to_warn(self):
        lines = ["WARNING something bad happened", "WARN another warning"]
        counts = _count_levels(lines)
        assert counts.get("WARN", 0) == 2
        assert "WARNING" not in counts

    def test_single_line_stats(self):
        lines = ["INFO hello"]
        stats = compute_stats(lines)
        assert stats["total_lines"] == 1
        assert stats["avg_line_length"] == float(len("INFO hello"))

    def test_all_duplicates(self):
        """All identical lines should yield one unique line and n-1 duplicates."""
        lines = ["ERROR same message"] * 4
        stats = compute_stats(lines)
        assert stats["total_lines"] == 4
        assert stats["unique_lines"] == 1
        assert stats["duplicate_lines"] == 3


class TestFormatStats:
    def test_returns_string(self):
        stats = compute_stats(SAMPLE_LINES)
        result = format_stats(stats)
        assert isinstance(result, str)

    def test_contains_header(self):
        stats = compute_stats(SAMPLE_LINES)
        result = format_stats(stats)
        assert "=== Log Statistics ===" in result

    def test_contains_level_counts(self):
        stats = compute_stats(SAMPLE_LINES)
        result = format_stats(stats)
        assert "ERROR" in result
        assert "INFO" in result
