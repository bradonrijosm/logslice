"""Tests for logslice.merger."""

import os
import tempfile
import pytest

from logslice.merger import merge_logs, merge_log_files


SOURCE_A = [
    "2024-01-01 08:00:00 INFO  service-a started",
    "2024-01-01 08:02:00 INFO  service-a ready",
    "2024-01-01 08:05:00 ERROR service-a failed",
]

SOURCE_B = [
    "2024-01-01 08:01:00 INFO  service-b started",
    "2024-01-01 08:03:00 WARN  service-b slow",
    "2024-01-01 08:06:00 INFO  service-b done",
]

NO_TIMESTAMP_LINES = [
    "no timestamp here",
    "also no timestamp",
]


class TestMergeLogs:
    def test_empty_sources_yields_nothing(self):
        result = list(merge_logs([]))
        assert result == []

    def test_single_source_yields_all_lines(self):
        result = list(merge_logs([("a", iter(SOURCE_A))]))
        assert result == SOURCE_A

    def test_two_sources_interleaved_by_timestamp(self):
        result = list(merge_logs([("a", iter(SOURCE_A)), ("b", iter(SOURCE_B))]))
        assert len(result) == 6
        # First line should be from source A (08:00)
        assert "service-a started" in result[0]
        # Second line should be from source B (08:01)
        assert "service-b started" in result[1]
        # Third line from A (08:02)
        assert "service-a ready" in result[2]
        # Fourth from B (08:03)
        assert "service-b slow" in result[3]

    def test_all_lines_present_after_merge(self):
        result = list(merge_logs([("a", iter(SOURCE_A)), ("b", iter(SOURCE_B))]))
        for line in SOURCE_A + SOURCE_B:
            assert line in result

    def test_lines_without_timestamps_sorted_last(self):
        mixed = SOURCE_A[:1] + NO_TIMESTAMP_LINES
        result = list(merge_logs([("a", iter(mixed)), ("b", iter([]))]))
        # Timestamped line should come first
        assert "service-a started" in result[0]
        # Non-timestamped lines at the end
        assert result[-2:] == NO_TIMESTAMP_LINES

    def test_empty_one_source_returns_other(self):
        result = list(merge_logs([("a", iter(SOURCE_A)), ("b", iter([]))]))
        assert result == SOURCE_A

    def test_single_line_sources(self):
        result = list(merge_logs([
            ("a", iter(["2024-01-01 09:00:00 INFO  alpha"])),
            ("b", iter(["2024-01-01 08:00:00 INFO  beta"])),
        ]))
        assert result[0].endswith("beta")
        assert result[1].endswith("alpha")


class TestMergeLogFiles:
    def _write_temp(self, lines):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False)
        f.write("\n".join(lines) + "\n")
        f.close()
        return f.name

    def test_merges_two_files(self):
        path_a = self._write_temp(SOURCE_A)
        path_b = self._write_temp(SOURCE_B)
        try:
            result = list(merge_log_files([path_a, path_b]))
            assert len(result) == 6
            for line in SOURCE_A + SOURCE_B:
                assert any(line.strip() in r for r in result)
        finally:
            os.unlink(path_a)
            os.unlink(path_b)

    def test_single_file_returns_all_lines(self):
        path_a = self._write_temp(SOURCE_A)
        try:
            result = [l.rstrip("\n") for l in merge_log_files([path_a])]
            assert result == SOURCE_A
        finally:
            os.unlink(path_a)
