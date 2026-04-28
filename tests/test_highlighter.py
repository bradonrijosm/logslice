"""Tests for logslice.highlighter."""

import pytest
from logslice.highlighter import (
    highlight_keywords,
    highlight_lines,
    ANSI_YELLOW,
    ANSI_RED,
    ANSI_RESET,
)


class TestHighlightKeywords:
    def test_empty_keywords_returns_original(self):
        line = "2024-01-01 ERROR something went wrong"
        assert highlight_keywords(line, []) == line

    def test_single_keyword_wrapped(self):
        result = highlight_keywords("ERROR occurred", ["ERROR"])
        assert f"{ANSI_YELLOW}ERROR{ANSI_RESET}" in result

    def test_case_insensitive_by_default(self):
        result = highlight_keywords("error occurred", ["ERROR"])
        assert f"{ANSI_YELLOW}error{ANSI_RESET}" in result

    def test_case_sensitive_no_match(self):
        result = highlight_keywords("error occurred", ["ERROR"], case_sensitive=True)
        assert ANSI_YELLOW not in result
        assert result == "error occurred"

    def test_case_sensitive_match(self):
        result = highlight_keywords("ERROR occurred", ["ERROR"], case_sensitive=True)
        assert f"{ANSI_YELLOW}ERROR{ANSI_RESET}" in result

    def test_multiple_keywords(self):
        result = highlight_keywords("ERROR and WARN both present", ["ERROR", "WARN"])
        assert f"{ANSI_YELLOW}ERROR{ANSI_RESET}" in result
        assert f"{ANSI_YELLOW}WARN{ANSI_RESET}" in result

    def test_red_color(self):
        result = highlight_keywords("CRITICAL failure", ["CRITICAL"], color="red")
        assert f"{ANSI_RED}CRITICAL{ANSI_RESET}" in result

    def test_unknown_color_defaults_to_yellow(self):
        result = highlight_keywords("INFO message", ["INFO"], color="blue")
        assert f"{ANSI_YELLOW}INFO{ANSI_RESET}" in result

    def test_keyword_with_regex_special_chars(self):
        result = highlight_keywords("rate: 100.0%", ["100.0%"])
        assert f"{ANSI_YELLOW}100.0%{ANSI_RESET}" in result

    def test_multiple_occurrences_all_highlighted(self):
        result = highlight_keywords("foo bar foo", ["foo"])
        assert result.count(f"{ANSI_YELLOW}foo{ANSI_RESET}") == 2


class TestHighlightLines:
    def test_empty_list_returns_empty(self):
        assert highlight_lines([], ["ERROR"]) == []

    def test_all_lines_processed(self):
        lines = ["ERROR here", "INFO there", "ERROR again"]
        result = highlight_lines(lines, ["ERROR"])
        assert len(result) == 3
        assert f"{ANSI_YELLOW}ERROR{ANSI_RESET}" in result[0]
        assert f"{ANSI_YELLOW}ERROR{ANSI_RESET}" in result[2]
        assert ANSI_YELLOW not in result[1]

    def test_no_keywords_returns_unchanged(self):
        lines = ["line one", "line two"]
        assert highlight_lines(lines, []) == lines
