"""Tests for logslice.rate_analyzer and logslice.rate_analyzer_cli."""
from __future__ import annotations

import io
import json
import textwrap
from pathlib import Path
from types import SimpleNamespace

import pytest

from logslice.rate_analyzer import (
    RateBucket,
    RateReport,
    _bucket_key,
    analyze_rate,
    format_rate_report,
)
from logslice.rate_analyzer_cli import build_rate_parser, cmd_rate


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

LINES_WITH_TS = [
    "2024-01-15T10:00:05 INFO  request started",
    "2024-01-15T10:00:30 INFO  request ended",
    "2024-01-15T10:01:10 ERROR timeout",
    "2024-01-15T10:01:45 WARN  retrying",
    "2024-01-15T10:02:05 INFO  ok",
]

LINES_NO_TS = [
    "no timestamp here",
    "another plain line",
]


# ---------------------------------------------------------------------------
# analyze_rate
# ---------------------------------------------------------------------------

class TestAnalyzeRate:
    def test_empty_input_returns_empty_report(self):
        r = analyze_rate([])
        assert r.total_lines == 0
        assert r.buckets == []
        assert r.peak_bucket is None

    def test_total_lines_counted(self):
        r = analyze_rate(LINES_WITH_TS, window_seconds=60)
        assert r.total_lines == 5

    def test_lines_grouped_into_minute_buckets(self):
        r = analyze_rate(LINES_WITH_TS, window_seconds=60)
        # 10:00 bucket → 2 lines, 10:01 → 2 lines, 10:02 → 1 line
        counts = {b.key: b.count for b in r.buckets}
        assert sum(counts.values()) == 5
        assert len(counts) == 3

    def test_peak_bucket_has_highest_count(self):
        r = analyze_rate(LINES_WITH_TS, window_seconds=60)
        assert r.peak_bucket is not None
        assert r.peak_bucket.count == max(b.count for b in r.buckets)

    def test_lines_without_timestamp_grouped_under_no_timestamp(self):
        r = analyze_rate(LINES_NO_TS, window_seconds=60)
        keys = [b.key for b in r.buckets]
        assert "(no-timestamp)" in keys

    def test_average_rate_computed(self):
        r = analyze_rate(LINES_WITH_TS, window_seconds=60)
        assert r.average_rate == pytest.approx(5 / 3, rel=1e-3)

    def test_include_lines_populates_bucket_lines(self):
        r = analyze_rate(LINES_WITH_TS, window_seconds=60, include_lines=True)
        total_stored = sum(len(b.lines) for b in r.buckets)
        assert total_stored == 5

    def test_include_lines_false_bucket_lines_empty(self):
        r = analyze_rate(LINES_WITH_TS, window_seconds=60, include_lines=False)
        for b in r.buckets:
            assert b.lines == []

    def test_window_seconds_stored_in_report(self):
        r = analyze_rate(LINES_WITH_TS, window_seconds=30)
        assert r.window_seconds == 30


# ---------------------------------------------------------------------------
# format_rate_report
# ---------------------------------------------------------------------------

class TestFormatRateReport:
    def test_contains_total_lines(self):
        r = analyze_rate(LINES_WITH_TS, window_seconds=60)
        text = format_rate_report(r)
        assert "5" in text

    def test_contains_peak_bucket_key(self):
        r = analyze_rate(LINES_WITH_TS, window_seconds=60)
        text = format_rate_report(r)
        assert r.peak_bucket.key in text

    def test_empty_report_no_crash(self):
        r = analyze_rate([], window_seconds=60)
        text = format_rate_report(r)
        assert "0" in text


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    p = tmp_path / "sample.log"
    p.write_text("\n".join(LINES_WITH_TS), encoding="utf-8")
    return p


def _ns(**kwargs):
    defaults = dict(file="-", window=60, include_lines=False, json=False)
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class TestBuildRateParser:
    def test_returns_argument_parser(self):
        import argparse
        assert isinstance(build_rate_parser(), argparse.ArgumentParser)

    def test_default_window_is_60(self):
        p = build_rate_parser()
        ns = p.parse_args(["-"])
        assert ns.window == 60

    def test_default_json_is_false(self):
        p = build_rate_parser()
        ns = p.parse_args(["-"])
        assert ns.json is False


class TestCmdRate:
    def test_returns_zero_on_success(self, log_file):
        out = io.StringIO()
        rc = cmd_rate(_ns(file=str(log_file)), out=out)
        assert rc == 0

    def test_text_output_contains_total(self, log_file):
        out = io.StringIO()
        cmd_rate(_ns(file=str(log_file)), out=out)
        assert "5" in out.getvalue()

    def test_json_output_is_valid_json(self, log_file):
        out = io.StringIO()
        cmd_rate(_ns(file=str(log_file), json=True), out=out)
        data = json.loads(out.getvalue())
        assert data["total_lines"] == 5

    def test_json_contains_buckets(self, log_file):
        out = io.StringIO()
        cmd_rate(_ns(file=str(log_file), json=True), out=out)
        data = json.loads(out.getvalue())
        assert isinstance(data["buckets"], list)
        assert len(data["buckets"]) > 0
