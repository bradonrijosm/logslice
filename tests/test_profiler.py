"""Tests for logslice.profiler."""

from __future__ import annotations

import pytest

from logslice.profiler import ProfileResult, format_profile, profile_lines


LINES_60S = [
    "2024-01-15 10:00:05 INFO  request started",
    "2024-01-15 10:00:30 INFO  processing",
    "2024-01-15 10:01:10 ERROR timeout",
    "2024-01-15 10:02:45 WARN  retry",
    "no timestamp here at all",
]


class TestProfileLines:
    def test_total_lines_counted(self):
        result = profile_lines(LINES_60S, bucket_size_seconds=60)
        assert result.total_lines == 5

    def test_timestamped_lines_counted(self):
        result = profile_lines(LINES_60S, bucket_size_seconds=60)
        assert result.timestamped_lines == 4

    def test_buckets_are_non_empty(self):
        result = profile_lines(LINES_60S, bucket_size_seconds=60)
        assert len(result.buckets) >= 1

    def test_two_lines_in_same_minute_bucket(self):
        result = profile_lines(LINES_60S, bucket_size_seconds=60)
        assert any(v == 2 for v in result.buckets.values())

    def test_peak_bucket_has_highest_count(self):
        result = profile_lines(LINES_60S, bucket_size_seconds=60)
        assert result.peak_count == max(result.buckets.values())

    def test_empty_input_returns_zeroed_result(self):
        result = profile_lines([], bucket_size_seconds=60)
        assert result.total_lines == 0
        assert result.timestamped_lines == 0
        assert result.buckets == {}
        assert result.peak_bucket is None

    def test_all_untimstamped_lines(self):
        result = profile_lines(["no ts", "also no ts"], bucket_size_seconds=60)
        assert result.timestamped_lines == 0
        assert result.buckets == {}

    def test_invalid_bucket_size_raises(self):
        with pytest.raises(ValueError):
            profile_lines(LINES_60S, bucket_size_seconds=0)

    def test_bucket_size_respected(self):
        result_60 = profile_lines(LINES_60S, bucket_size_seconds=60)
        result_3600 = profile_lines(LINES_60S, bucket_size_seconds=3600)
        assert len(result_60.buckets) >= len(result_3600.buckets)

    def test_bucket_size_stored_in_result(self):
        result = profile_lines(LINES_60S, bucket_size_seconds=120)
        assert result.bucket_size_seconds == 120


class TestFormatProfile:
    def test_no_timestamps_returns_notice(self):
        result = ProfileResult(bucket_size_seconds=60)
        output = format_profile(result)
        assert "No timestamped" in output

    def test_output_contains_peak_label(self):
        result = profile_lines(LINES_60S, bucket_size_seconds=60)
        output = format_profile(result)
        assert result.peak_bucket in output

    def test_output_contains_total_lines(self):
        result = profile_lines(LINES_60S, bucket_size_seconds=60)
        output = format_profile(result)
        assert str(result.total_lines) in output

    def test_bar_width_respected(self):
        result = profile_lines(LINES_60S, bucket_size_seconds=60)
        output = format_profile(result, bar_width=10)
        # bars are composed of '#'; max bar must not exceed 10 hashes
        max_bar = max(line.count("#") for line in output.splitlines())
        assert max_bar <= 10
