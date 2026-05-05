"""Tests for logslice.sorter."""

import pytest
from logslice.sorter import sort_by_timestamp, sort_lexicographic, stable_sort


LINES_WITH_TS = [
    "2024-03-10 10:05:00 INFO  third event",
    "2024-03-10 09:00:00 ERROR first event",
    "2024-03-10 09:30:00 WARN  second event",
]

LINES_MIXED = [
    "2024-03-10 10:05:00 INFO  third event",
    "no timestamp here",
    "2024-03-10 09:00:00 ERROR first event",
]


class TestSortByTimestamp:
    def test_sorts_ascending_by_default(self):
        result = sort_by_timestamp(LINES_WITH_TS)
        assert result[0].startswith("2024-03-10 09:00")
        assert result[1].startswith("2024-03-10 09:30")
        assert result[2].startswith("2024-03-10 10:05")

    def test_sorts_descending_when_reversed(self):
        result = sort_by_timestamp(LINES_WITH_TS, reverse=True)
        assert result[0].startswith("2024-03-10 10:05")
        assert result[-1].startswith("2024-03-10 09:00")

    def test_empty_input_returns_empty(self):
        assert sort_by_timestamp([]) == []

    def test_single_line_unchanged(self):
        line = "2024-03-10 09:00:00 INFO single"
        assert sort_by_timestamp([line]) == [line]

    def test_untimed_lines_appended_at_end_ascending(self):
        result = sort_by_timestamp(LINES_MIXED, fallback_to_original=True)
        assert result[-1] == "no timestamp here"

    def test_untimed_lines_prepended_when_descending(self):
        result = sort_by_timestamp(LINES_MIXED, reverse=True, fallback_to_original=True)
        assert result[0] == "no timestamp here"

    def test_untimed_lines_dropped_when_fallback_false(self):
        result = sort_by_timestamp(LINES_MIXED, fallback_to_original=False)
        assert "no timestamp here" not in result
        assert len(result) == 2

    def test_all_untimed_fallback_true(self):
        lines = ["no ts", "also no ts"]
        result = sort_by_timestamp(lines, fallback_to_original=True)
        assert result == lines

    def test_all_untimed_fallback_false_returns_empty(self):
        lines = ["no ts", "also no ts"]
        assert sort_by_timestamp(lines, fallback_to_original=False) == []


class TestSortLexicographic:
    def test_sorts_ascending(self):
        lines = ["banana", "apple", "cherry"]
        assert sort_lexicographic(lines) == ["apple", "banana", "cherry"]

    def test_sorts_descending(self):
        lines = ["banana", "apple", "cherry"]
        assert sort_lexicographic(lines, reverse=True) == ["cherry", "banana", "apple"]

    def test_empty_returns_empty(self):
        assert sort_lexicographic([]) == []

    def test_custom_key_function(self):
        lines = ["ERROR something", "INFO detail", "WARN heads-up"]
        result = sort_lexicographic(lines, key=lambda l: l.split()[0])
        assert result[0].startswith("ERROR")
        assert result[1].startswith("INFO")
        assert result[2].startswith("WARN")


class TestStableSort:
    def test_dispatches_to_timestamp(self):
        result = stable_sort(LINES_WITH_TS, by="timestamp")
        assert result[0].startswith("2024-03-10 09:00")

    def test_dispatches_to_lexicographic(self):
        lines = ["c line", "a line", "b line"]
        result = stable_sort(lines, by="lexicographic")
        assert result == ["a line", "b line", "c line"]

    def test_invalid_mode_raises(self):
        with pytest.raises(ValueError, match="Unknown sort mode"):
            stable_sort(["line"], by="invalid")

    def test_reverse_flag_passed_through(self):
        result = stable_sort(LINES_WITH_TS, by="timestamp", reverse=True)
        assert result[0].startswith("2024-03-10 10:05")
