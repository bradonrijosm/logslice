"""Tests for logslice.timeline."""

from __future__ import annotations

import pytest

from logslice.timeline import (
    TimelineBucket,
    Timeline,
    _bucket_label,
    build_timeline,
    format_timeline,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

LINE_A = "2024-01-15 10:01:00 INFO  request received"
LINE_B = "2024-01-15 10:01:45 DEBUG processing"
LINE_C = "2024-01-15 10:02:10 ERROR something failed"
LINE_NO_TS = "no timestamp here"


# ---------------------------------------------------------------------------
# _bucket_label
# ---------------------------------------------------------------------------

class TestBucketLabel:
    def test_minute_bucket_format(self):
        import datetime
        ts = datetime.datetime(2024, 3, 5, 14, 37, 22).timestamp()
        label = _bucket_label(ts, 60)
        assert label == "2024-03-05 14:37"

    def test_hour_bucket_format(self):
        import datetime
        ts = datetime.datetime(2024, 3, 5, 14, 37, 22).timestamp()
        label = _bucket_label(ts, 3600)
        assert label == "2024-03-05 14:00"

    def test_day_bucket_format(self):
        import datetime
        ts = datetime.datetime(2024, 3, 5, 14, 37, 22).timestamp()
        label = _bucket_label(ts, 86400)
        assert label == "2024-03-05"


# ---------------------------------------------------------------------------
# build_timeline
# ---------------------------------------------------------------------------

class TestBuildTimeline:
    def test_empty_input_returns_empty_timeline(self):
        tl = build_timeline([])
        assert tl.buckets == {}
        assert tl.untimed == []

    def test_untimed_lines_collected(self):
        tl = build_timeline([LINE_NO_TS, LINE_NO_TS])
        assert len(tl.untimed) == 2
        assert tl.buckets == {}

    def test_same_minute_merged_into_one_bucket(self):
        tl = build_timeline([LINE_A, LINE_B])
        assert len(tl.buckets) == 1
        bucket = list(tl.buckets.values())[0]
        assert bucket.count == 2

    def test_different_minutes_create_separate_buckets(self):
        tl = build_timeline([LINE_A, LINE_C])
        assert len(tl.buckets) == 2

    def test_keep_lines_stores_originals(self):
        tl = build_timeline([LINE_A, LINE_B], keep_lines=True)
        bucket = list(tl.buckets.values())[0]
        assert LINE_A in bucket.lines
        assert LINE_B in bucket.lines

    def test_keep_lines_false_stores_nothing(self):
        tl = build_timeline([LINE_A], keep_lines=False)
        bucket = list(tl.buckets.values())[0]
        assert bucket.lines == []

    def test_invalid_bucket_seconds_raises(self):
        with pytest.raises(ValueError):
            build_timeline([], bucket_seconds=0)

    def test_ordered_buckets_are_sorted(self):
        tl = build_timeline([LINE_C, LINE_A])
        labels = [b.label for b in tl.ordered_buckets()]
        assert labels == sorted(labels)

    def test_bucket_seconds_stored(self):
        tl = build_timeline([], bucket_seconds=300)
        assert tl.bucket_seconds == 300


# ---------------------------------------------------------------------------
# format_timeline
# ---------------------------------------------------------------------------

class TestFormatTimeline:
    def test_no_buckets_returns_placeholder(self):
        tl = Timeline(bucket_seconds=60)
        result = format_timeline(tl)
        assert "no timestamped" in result

    def test_output_contains_bucket_label(self):
        tl = build_timeline([LINE_A])
        result = format_timeline(tl)
        assert "2024-01-15 10:01" in result

    def test_output_contains_count(self):
        tl = build_timeline([LINE_A, LINE_B])
        result = format_timeline(tl)
        assert "2" in result

    def test_untimed_line_mentioned(self):
        tl = build_timeline([LINE_A, LINE_NO_TS])
        result = format_timeline(tl)
        assert "untimed" in result

    def test_bar_width_respected(self):
        tl = build_timeline([LINE_A])
        result = format_timeline(tl, bar_width=10)
        # bar is enclosed in brackets; total chars inside should equal 10
        start = result.index("[")
        end = result.index("]")
        assert end - start - 1 == 10
