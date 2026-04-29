"""Tests for logslice.filter module."""

import pytest

from logslice.filter import (
    filter_by_level,
    filter_by_pattern,
    filter_lines,
)


SAMPLE_LINES = [
    "2024-01-01 10:00:00 DEBUG starting application",
    "2024-01-01 10:00:01 INFO server listening on port 8080",
    "2024-01-01 10:00:05 WARNING disk usage above 80%",
    "2024-01-01 10:00:10 ERROR failed to connect to database",
    "2024-01-01 10:00:11 CRITICAL out of memory",
    "2024-01-01 10:00:12 INFO request completed in 42ms",
    "2024-01-01 10:00:15 ERROR timeout waiting for response",
]


class TestFilterByLevel:
    def test_returns_only_error_lines(self):
        result = list(filter_by_level(SAMPLE_LINES, "error"))
        assert len(result) == 2
        assert all("ERROR" in line for line in result)

    def test_returns_only_info_lines(self):
        result = list(filter_by_level(SAMPLE_LINES, "info"))
        assert len(result) == 2
        assert all("INFO" in line for line in result)

    def test_case_insensitive_level_arg(self):
        result_lower = list(filter_by_level(SAMPLE_LINES, "debug"))
        result_upper = list(filter_by_level(SAMPLE_LINES, "DEBUG"))
        assert result_lower == result_upper

    def test_warning_matches_warn_and_warning(self):
        lines = [
            "2024-01-01 WARN short form",
            "2024-01-01 WARNING long form",
            "2024-01-01 INFO not a warning",
        ]
        result = list(filter_by_level(lines, "warning"))
        assert len(result) == 2

    def test_critical_matches_fatal(self):
        lines = [
            "2024-01-01 FATAL system crash",
            "2024-01-01 CRITICAL memory exhausted",
            "2024-01-01 INFO all good",
        ]
        result = list(filter_by_level(lines, "critical"))
        assert len(result) == 2

    def test_unknown_level_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown log level"):
            list(filter_by_level(SAMPLE_LINES, "verbose"))

    def test_empty_input_returns_empty(self):
        result = list(filter_by_level([], "error"))
        assert result == []


class TestFilterByPattern:
    def test_matches_keyword(self):
        result = list(filter_by_pattern(SAMPLE_LINES, "database"))
        assert len(result) == 1
        assert "database" in result[0]

    def test_case_insensitive_by_default(self):
        result = list(filter_by_pattern(SAMPLE_LINES, "TIMEOUT"))
        assert len(result) == 1

    def test_case_sensitive_no_match(self):
        result = list(filter_by_pattern(SAMPLE_LINES, "TIMEOUT", case_sensitive=True))
        assert len(result) == 0

    def test_regex_pattern(self):
        result = list(filter_by_pattern(SAMPLE_LINES, r"port \d+"))
        assert len(result) == 1
        assert "8080" in result[0]

    def test_empty_input_returns_empty(self):
        result = list(filter_by_pattern([], "anything"))
        assert result == []


class TestFilterLines:
    def test_no_filters_returns_all(self):
        result = list(filter_lines(SAMPLE_LINES))
        assert result == SAMPLE_LINES

    def test_level_filter_only(self):
        result = list(filter_lines(SAMPLE_LINES, level="error"))
        assert len(result) == 2

    def test_pattern_filter_only(self):
        result = list(filter_lines(SAMPLE_LINES, pattern="connect"))
        assert len(result) == 1

    def test_level_and_pattern_combined(self):
        result = list(filter_lines(SAMPLE_LINES, level="error", pattern="timeout"))
        assert len(result) == 1
        assert "timeout" in result[0].lower()

    def test_combined_no_match_returns_empty(self):
        result = list(filter_lines(SAMPLE_LINES, level="debug", pattern="ERROR"))
        assert result == []
