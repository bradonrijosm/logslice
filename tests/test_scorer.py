"""Tests for logslice.scorer."""
from __future__ import annotations

import pytest

from logslice.scorer import (
    ScoredLine,
    format_scored,
    score_line,
    score_lines,
    top_scored,
)

WEIGHTS = {"ERROR": 3.0, "WARN": 1.5, "timeout": 2.0}

LINES = [
    "2024-01-01 INFO  service started",
    "2024-01-01 ERROR connection refused",
    "2024-01-01 WARN  timeout reached",
    "2024-01-01 DEBUG nothing interesting",
    "2024-01-01 ERROR timeout on retry",
]


class TestScoreLine:
    def test_no_match_returns_zero(self):
        sl = score_line("INFO all good", WEIGHTS)
        assert sl.score == 0.0
        assert sl.matched_keywords == []

    def test_single_keyword_match(self):
        sl = score_line("ERROR bad thing", WEIGHTS)
        assert sl.score == pytest.approx(3.0)
        assert "ERROR" in sl.matched_keywords

    def test_multiple_keyword_match_accumulates(self):
        sl = score_line("ERROR timeout now", WEIGHTS)
        assert sl.score == pytest.approx(5.0)
        assert set(sl.matched_keywords) == {"ERROR", "timeout"}

    def test_case_insensitive_by_default(self):
        sl = score_line("error occurred", WEIGHTS)
        assert sl.score == pytest.approx(3.0)

    def test_case_sensitive_no_match(self):
        sl = score_line("error occurred", WEIGHTS, case_sensitive=True)
        assert sl.score == 0.0

    def test_line_preserved(self):
        text = "some log line"
        sl = score_line(text, WEIGHTS)
        assert sl.line == text


class TestScoreLines:
    def test_empty_input_returns_empty(self):
        assert score_lines([], WEIGHTS) == []

    def test_returns_scored_line_objects(self):
        results = score_lines(LINES, WEIGHTS)
        assert all(isinstance(r, ScoredLine) for r in results)

    def test_sorted_descending(self):
        results = score_lines(LINES, WEIGHTS)
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_threshold_filters_low_scores(self):
        results = score_lines(LINES, WEIGHTS, threshold=3.0)
        assert all(r.score >= 3.0 for r in results)

    def test_zero_threshold_includes_unmatched(self):
        results = score_lines(LINES, WEIGHTS, threshold=0.0)
        assert len(results) == len(LINES)

    def test_positive_threshold_excludes_unmatched(self):
        results = score_lines(LINES, WEIGHTS, threshold=0.01)
        assert all(r.score > 0 for r in results)


class TestTopScored:
    def test_returns_at_most_n_lines(self):
        results = top_scored(LINES, WEIGHTS, n=2)
        assert len(results) <= 2

    def test_top_1_is_highest_score(self):
        all_results = score_lines(LINES, WEIGHTS, threshold=0.01)
        top = top_scored(LINES, WEIGHTS, n=1)
        assert top[0].score == all_results[0].score

    def test_empty_input_returns_empty(self):
        assert top_scored([], WEIGHTS, n=5) == []


class TestFormatScored:
    def test_score_prefix_present(self):
        sl = ScoredLine(line="some line", score=2.5, matched_keywords=["ERROR"])
        out = format_scored([sl], show_score=True)
        assert "[2.50]" in out[0]

    def test_no_score_prefix_absent(self):
        sl = ScoredLine(line="some line", score=2.5)
        out = format_scored([sl], show_score=False)
        assert "[" not in out[0]

    def test_keywords_shown_when_requested(self):
        sl = ScoredLine(line="line", score=1.0, matched_keywords=["WARN"])
        out = format_scored([sl], show_keywords=True)
        assert "WARN" in out[0]

    def test_empty_input_returns_empty(self):
        assert format_scored([]) == []
