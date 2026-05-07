"""Tests for logslice.timeline_cli."""

from __future__ import annotations

import io
import textwrap
from pathlib import Path

import pytest

from logslice.timeline_cli import build_timeline_parser, cmd_timeline


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    p = tmp_path / "sample.log"
    p.write_text(
        textwrap.dedent("""\
            2024-01-15 10:01:00 INFO  request received
            2024-01-15 10:01:45 DEBUG processing
            2024-01-15 10:02:10 ERROR something failed
            no timestamp here
        """)
    )
    return p


def _ns(**kwargs):
    defaults = dict(file=None, bucket=60, bar_width=40, keep_lines=False)
    defaults.update(kwargs)
    import argparse
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# build_timeline_parser
# ---------------------------------------------------------------------------

class TestBuildTimelineParser:
    def test_returns_argument_parser(self):
        import argparse
        p = build_timeline_parser()
        assert isinstance(p, argparse.ArgumentParser)

    def test_default_bucket_is_60(self):
        p = build_timeline_parser()
        ns = p.parse_args(["somefile.log"])
        assert ns.bucket == 60

    def test_default_bar_width_is_40(self):
        p = build_timeline_parser()
        ns = p.parse_args(["somefile.log"])
        assert ns.bar_width == 40

    def test_default_keep_lines_is_false(self):
        p = build_timeline_parser()
        ns = p.parse_args(["somefile.log"])
        assert ns.keep_lines is False

    def test_bucket_flag_parsed(self):
        p = build_timeline_parser()
        ns = p.parse_args(["f.log", "--bucket", "300"])
        assert ns.bucket == 300

    def test_keep_lines_flag_parsed(self):
        p = build_timeline_parser()
        ns = p.parse_args(["f.log", "--keep-lines"])
        assert ns.keep_lines is True


# ---------------------------------------------------------------------------
# cmd_timeline
# ---------------------------------------------------------------------------

class TestCmdTimeline:
    def test_returns_zero_on_success(self, log_file):
        ns = _ns(file=str(log_file))
        assert cmd_timeline(ns) == 0

    def test_returns_one_on_missing_file(self):
        ns = _ns(file="/nonexistent/file.log")
        assert cmd_timeline(ns) == 1

    def test_output_contains_bucket_label(self, log_file):
        ns = _ns(file=str(log_file))
        out = io.StringIO()
        cmd_timeline(ns, out=out)
        assert "2024-01-15" in out.getvalue()

    def test_output_contains_hash_bars(self, log_file):
        ns = _ns(file=str(log_file))
        out = io.StringIO()
        cmd_timeline(ns, out=out)
        assert "#" in out.getvalue()

    def test_custom_bucket_changes_grouping(self, log_file):
        ns_narrow = _ns(file=str(log_file), bucket=60)
        ns_wide = _ns(file=str(log_file), bucket=3600)
        out_narrow = io.StringIO()
        out_wide = io.StringIO()
        cmd_timeline(ns_narrow, out=out_narrow)
        cmd_timeline(ns_wide, out=out_wide)
        # wider bucket merges all three timestamped lines into one row
        assert out_wide.getvalue().count("[") < out_narrow.getvalue().count("[")
