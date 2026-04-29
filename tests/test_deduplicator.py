"""Tests for logslice.deduplicator."""

import pytest
from logslice.deduplicator import deduplicate_lines, count_duplicates


LINES = [
    (1, "INFO  server started"),
    (2, "DEBUG connection accepted"),
    (3, "INFO  server started"),
    (4, "ERROR disk full"),
    (5, "DEBUG connection accepted"),
    (6, "ERROR disk full"),
]

CONSECUTIVE_LINES = [
    (1, "INFO  heartbeat"),
    (2, "INFO  heartbeat"),
    (3, "INFO  heartbeat"),
    (4, "ERROR disk full"),
    (5, "INFO  heartbeat"),
]


class TestDeduplicateGlobal:
    def test_removes_all_duplicates(self):
        result = list(deduplicate_lines(iter(LINES)))
        texts = [t for _, t in result]
        assert len(texts) == len(set(texts))

    def test_keeps_first_occurrence(self):
        result = list(deduplicate_lines(iter(LINES)))
        assert result[0] == (1, "INFO  server started")
        assert result[1] == (2, "DEBUG connection accepted")

    def test_empty_input_returns_empty(self):
        assert list(deduplicate_lines(iter([]))) == []

    def test_no_duplicates_unchanged(self):
        unique = [(1, "a"), (2, "b"), (3, "c")]
        assert list(deduplicate_lines(iter(unique))) == unique

    def test_all_same_returns_one(self):
        same = [(i, "same line") for i in range(1, 6)]
        result = list(deduplicate_lines(iter(same)))
        assert result == [(1, "same line")]

    def test_preserves_original_line_numbers(self):
        """Ensure line numbers from first occurrence are preserved, not renumbered."""
        result = list(deduplicate_lines(iter(LINES)))
        line_numbers = [n for n, _ in result]
        assert line_numbers == [1, 2, 4]


class TestDeduplicateConsecutive:
    def test_collapses_consecutive_repeats(self):
        result = list(deduplicate_lines(iter(CONSECUTIVE_LINES), consecutive_only=True))
        texts = [t for _, t in result]
        assert texts == ["INFO  heartbeat", "ERROR disk full", "INFO  heartbeat"]

    def test_non_consecutive_duplicates_kept(self):
        result = list(deduplicate_lines(iter(LINES), consecutive_only=True))
        assert len(result) == len(LINES)  # no consecutive dupes in LINES

    def test_empty_input_returns_empty(self):
        assert list(deduplicate_lines(iter([]), consecutive_only=True)) == []

    def test_single_line_returned(self):
        result = list(deduplicate_lines(iter([(1, "only")]), consecutive_only=True))
        assert result == [(1, "only")]

    def test_preserves_first_line_number_in_run(self):
        """Ensure the line number of the first line in a consecutive run is kept."""
        result = list(deduplicate_lines(iter(CONSECUTIVE_LINES), consecutive_only=True))
        line_numbers = [n for n, _ in result]
        assert line_numbers == [1, 4, 5]


class TestCountDuplicates:
    def test_global_count(self):
        assert count_duplicates(iter(LINES)) == 2

    def test_consecutive_count(self):
        assert count_duplicates(iter(CONSECUTIVE_LINES), consecutive_only=True) == 2

    def test_no_duplicates_returns_zero(self):
        unique = [(1, "a"), (2, "b")]
        assert count_duplicates(iter(unique)) == 0

    def test_empty_returns_zero(self):
        assert count_duplicates(iter([])) == 0
