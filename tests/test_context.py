"""Tests for logslice.context module."""

import pytest
from logslice.context import extract_context, find_match_indices


LINES = [
    (1, "alpha"),
    (2, "beta"),
    (3, "ERROR: disk full"),
    (4, "gamma"),
    (5, "delta"),
    (6, "ERROR: timeout"),
    (7, "epsilon"),
]


class TestExtractContext:
    def test_empty_lines_returns_empty(self):
        assert extract_context([], [], before=2, after=2) == []

    def test_empty_match_indices_returns_empty(self):
        assert extract_context(LINES, [], before=1, after=1) == []

    def test_match_only_no_context(self):
        result = extract_context(LINES, [2], before=0, after=0)
        assert len(result) == 1
        line_no, text, is_match = result[0]
        assert line_no == 3
        assert is_match is True

    def test_before_context(self):
        result = extract_context(LINES, [2], before=2, after=0)
        line_numbers = [r[0] for r in result]
        assert line_numbers == [1, 2, 3]
        assert result[2][2] is True   # index 2 is the match
        assert result[0][2] is False  # context lines are not matches

    def test_after_context(self):
        result = extract_context(LINES, [2], before=0, after=2)
        line_numbers = [r[0] for r in result]
        assert line_numbers == [3, 4, 5]
        assert result[0][2] is True

    def test_before_and_after_context(self):
        result = extract_context(LINES, [2], before=1, after=1)
        line_numbers = [r[0] for r in result]
        assert line_numbers == [2, 3, 4]

    def test_multiple_matches_overlap_deduplicated(self):
        # Matches at indices 2 and 5 with after=2 — windows overlap at idx 4
        result = extract_context(LINES, [2, 5], before=0, after=2)
        line_numbers = [r[0] for r in result]
        # Should be unique and sorted
        assert line_numbers == sorted(set(line_numbers))
        assert 3 in line_numbers  # match 1
        assert 6 in line_numbers  # match 2

    def test_context_clipped_at_start(self):
        result = extract_context(LINES, [0], before=5, after=0)
        assert result[0][0] == 1  # first available line

    def test_context_clipped_at_end(self):
        result = extract_context(LINES, [6], before=0, after=5)
        assert result[-1][0] == 7  # last available line

    def test_match_flag_preserved_when_overlap(self):
        # index 2 is a match; index 3 is context of match at 2 AND context before match at 5
        result = extract_context(LINES, [2, 5], before=2, after=0)
        by_lineno = {r[0]: r[2] for r in result}
        assert by_lineno[3] is True   # line 3 is a match
        assert by_lineno[6] is True   # line 6 is a match


class TestFindMatchIndices:
    def test_no_matches(self):
        assert find_match_indices(LINES, lambda t: "NOTFOUND" in t) == []

    def test_single_match(self):
        indices = find_match_indices(LINES, lambda t: "disk" in t)
        assert indices == [2]

    def test_multiple_matches(self):
        indices = find_match_indices(LINES, lambda t: "ERROR" in t)
        assert indices == [2, 5]

    def test_all_lines_match(self):
        indices = find_match_indices(LINES, lambda t: len(t) > 0)
        assert indices == list(range(len(LINES)))

    def test_predicate_receives_text_not_tuple(self):
        # Ensure the predicate is called with the text portion, not the full tuple
        seen = []
        find_match_indices(LINES, lambda t: seen.append(t) or False)
        assert all(isinstance(s, str) for s in seen)
