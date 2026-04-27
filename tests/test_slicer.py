"""Tests for logslice.slicer time-range filtering."""

import os
import tempfile
from datetime import datetime

import pytest

from logslice.slicer import slice_log, count_lines

SAMPLE_LINES = [
    "2024-01-15T07:00:00 DEBUG early morning init",
    "2024-01-15T08:00:00 INFO  service started",
    "2024-01-15T09:30:00 WARN  memory usage high",
    "2024-01-15T12:00:00 ERROR database timeout",
    "2024-01-15T17:59:00 INFO  backup completed",
    "2024-01-15T23:00:00 DEBUG nightly cleanup",
    "no timestamp line",
]


@pytest.fixture()
def log_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as fh:
        fh.write("\n".join(SAMPLE_LINES) + "\n")
        path = fh.name
    yield path
    os.unlink(path)


class TestSliceLog:
    def test_no_bounds_returns_all_lines(self, log_file):
        result = list(slice_log(log_file))
        assert len(result) == len(SAMPLE_LINES)

    def test_start_only(self, log_file):
        start = datetime(2024, 1, 15, 9, 0, 0)
        result = list(slice_log(log_file, start=start))
        assert all("07:00" not in l and "08:00" not in l for l in result)
        assert any("09:30" in l for l in result)

    def test_end_only(self, log_file):
        end = datetime(2024, 1, 15, 9, 0, 0)
        result = list(slice_log(log_file, end=end))
        assert len(result) == 2  # 07:00 and 08:00

    def test_start_and_end(self, log_file):
        start = datetime(2024, 1, 15, 8, 0, 0)
        end = datetime(2024, 1, 15, 12, 0, 0)
        result = list(slice_log(log_file, start=start, end=end))
        assert len(result) == 3  # 08:00, 09:30, 12:00

    def test_lines_without_timestamps_are_skipped(self, log_file):
        start = datetime(2024, 1, 15, 0, 0, 0)
        end = datetime(2024, 1, 15, 23, 59, 59)
        result = list(slice_log(log_file, start=start, end=end))
        assert not any("no timestamp" in l for l in result)

    def test_empty_range_returns_nothing(self, log_file):
        start = datetime(2025, 1, 1, 0, 0, 0)
        end = datetime(2025, 1, 1, 1, 0, 0)
        result = list(slice_log(log_file, start=start, end=end))
        assert result == []

    def test_file_not_found_raises(self):
        with pytest.raises(FileNotFoundError):
            list(slice_log("/nonexistent/path/file.log"))


class TestCountLines:
    def test_count_with_range(self, log_file):
        start = datetime(2024, 1, 15, 8, 0, 0)
        end = datetime(2024, 1, 15, 12, 0, 0)
        assert count_lines(log_file, start=start, end=end) == 3

    def test_count_no_bounds(self, log_file):
        assert count_lines(log_file) == len(SAMPLE_LINES)
