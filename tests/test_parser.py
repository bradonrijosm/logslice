"""Tests for logslice.parser timestamp extraction and parsing."""

import pytest
from datetime import datetime

from logslice.parser import extract_timestamp, parse_datetime_arg


class TestExtractTimestamp:
    def test_iso8601_T_separator(self):
        line = "2024-01-15T13:45:00 INFO Server started"
        result = extract_timestamp(line)
        assert result == datetime(2024, 1, 15, 13, 45, 0)

    def test_iso8601_space_separator(self):
        line = "2024-01-15 08:30:00 ERROR Disk full"
        result = extract_timestamp(line)
        assert result == datetime(2024, 1, 15, 8, 30, 0)

    def test_apache_format(self):
        line = '192.168.1.1 - - [15/Jan/2024:13:45:00 +0000] "GET / HTTP/1.1" 200'
        result = extract_timestamp(line)
        assert result == datetime(2024, 1, 15, 13, 45, 0)

    def test_no_timestamp_returns_none(self):
        line = "This line has no timestamp at all."
        result = extract_timestamp(line)
        assert result is None

    def test_empty_line_returns_none(self):
        assert extract_timestamp("") is None

    def test_timestamp_in_middle_of_line(self):
        line = "[app] 2024-03-20T09:00:00 [DEBUG] connection established"
        result = extract_timestamp(line)
        assert result == datetime(2024, 3, 20, 9, 0, 0)


class TestParseDatetimeArg:
    def test_full_iso_T(self):
        assert parse_datetime_arg("2024-01-15T13:45:00") == datetime(2024, 1, 15, 13, 45, 0)

    def test_full_iso_space(self):
        assert parse_datetime_arg("2024-01-15 13:45:00") == datetime(2024, 1, 15, 13, 45, 0)

    def test_date_only(self):
        assert parse_datetime_arg("2024-01-15") == datetime(2024, 1, 15, 0, 0, 0)

    def test_without_seconds(self):
        assert parse_datetime_arg("2024-01-15T13:45") == datetime(2024, 1, 15, 13, 45, 0)

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="Cannot parse datetime"):
            parse_datetime_arg("not-a-date")
