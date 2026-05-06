"""Tests for logslice.throttler."""

from __future__ import annotations

import pytest

from logslice.throttler import bucket_lines, count_throttled

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Two timestamps that fall in the same 60-second bucket (same minute)
SAME_BUCKET = [
    "2024-01-15 10:00:01 INFO  request start",
    "2024-01-15 10:00:15 INFO  request mid",
    "2024-01-15 10:00:45 INFO  request end",
]

# Two timestamps in adjacent 60-second buckets
DIFF_BUCKET = [
    "2024-01-15 10:00:01 INFO  first bucket",
    "2024-01-15 10:01:05 INFO  second bucket",
]

NO_TS_LINES = [
    "plain log line without timestamp",
    "another plain line",
]


# ---------------------------------------------------------------------------
# bucket_lines
# ---------------------------------------------------------------------------

class TestBucketLines:
    def test_no_lines_yields_nothing(self):
        assert list(bucket_lines([], max_per_bucket=1)) == []

    def test_lines_without_timestamp_always_pass_through(self):
        result = list(bucket_lines(NO_TS_LINES, max_per_bucket=1))
        assert result == NO_TS_LINES

    def test_max_one_keeps_first_line_per_bucket(self):
        result = list(bucket_lines(SAME_BUCKET, bucket_seconds=60, max_per_bucket=1))
        assert len(result) == 1
        assert result[0] == SAME_BUCKET[0]

    def test_max_two_keeps_two_lines_per_bucket(self):
        result = list(bucket_lines(SAME_BUCKET, bucket_seconds=60, max_per_bucket=2))
        assert len(result) == 2

    def test_max_larger_than_bucket_keeps_all(self):
        result = list(bucket_lines(SAME_BUCKET, bucket_seconds=60, max_per_bucket=100))
        assert result == SAME_BUCKET

    def test_different_buckets_each_get_own_quota(self):
        result = list(bucket_lines(DIFF_BUCKET, bucket_seconds=60, max_per_bucket=1))
        assert result == DIFF_BUCKET

    def test_invalid_bucket_seconds_raises(self):
        with pytest.raises(ValueError):
            list(bucket_lines(SAME_BUCKET, bucket_seconds=0))

    def test_invalid_max_per_bucket_raises(self):
        with pytest.raises(ValueError):
            list(bucket_lines(SAME_BUCKET, max_per_bucket=0))

    def test_returns_iterator(self):
        import types
        result = bucket_lines(SAME_BUCKET)
        assert isinstance(result, types.GeneratorType)


# ---------------------------------------------------------------------------
# count_throttled
# ---------------------------------------------------------------------------

class TestCountThrottled:
    def test_empty_input_returns_zeros(self):
        kept, dropped = count_throttled([], max_per_bucket=5)
        assert kept == 0 and dropped == 0

    def test_all_kept_when_under_limit(self):
        kept, dropped = count_throttled(SAME_BUCKET, bucket_seconds=60, max_per_bucket=10)
        assert kept == 3
        assert dropped == 0

    def test_excess_lines_counted_as_dropped(self):
        kept, dropped = count_throttled(SAME_BUCKET, bucket_seconds=60, max_per_bucket=1)
        assert kept == 1
        assert dropped == 2

    def test_no_ts_lines_always_kept(self):
        kept, dropped = count_throttled(NO_TS_LINES, max_per_bucket=1)
        assert kept == len(NO_TS_LINES)
        assert dropped == 0

    def test_kept_plus_dropped_equals_total(self):
        lines = SAME_BUCKET + DIFF_BUCKET
        kept, dropped = count_throttled(lines, bucket_seconds=60, max_per_bucket=2)
        assert kept + dropped == len(lines)
