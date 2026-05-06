"""Tests for logslice.summarizer and logslice.summarizer_cli."""
from __future__ import annotations

import json
import textwrap
from io import StringIO
from pathlib import Path
from types import SimpleNamespace

import pytest

from logslice.summarizer import SummaryReport, summarize_lines, format_summary_report
from logslice.summarizer_cli import build_summarizer_parser, cmd_summarize


SAMPLE_LINES = [
    "2024-01-01 10:00:00 INFO  server started",
    "2024-01-01 10:01:00 ERROR disk full",
    "2024-01-01 10:02:00 INFO  server started",
    "2024-01-01 10:03:00 WARN  high memory",
    "2024-01-01 10:04:00 ERROR disk full",
    "2024-01-01 10:05:00 INFO  request ok",
]


class TestSummarizeLines:
    def test_total_lines(self):
        r = summarize_lines(SAMPLE_LINES)
        assert r.total_lines == 6

    def test_unique_lines(self):
        r = summarize_lines(SAMPLE_LINES)
        assert r.unique_lines == 4

    def test_duplicate_lines(self):
        r = summarize_lines(SAMPLE_LINES)
        assert r.duplicate_lines == 2

    def test_level_counts_include_error(self):
        r = summarize_lines(SAMPLE_LINES)
        assert r.level_counts.get("ERROR", 0) == 2

    def test_first_and_last_timestamp(self):
        r = summarize_lines(SAMPLE_LINES)
        assert r.first_timestamp is not None
        assert r.last_timestamp is not None
        assert r.first_timestamp <= r.last_timestamp

    def test_top_lines_respects_n(self):
        r = summarize_lines(SAMPLE_LINES, top_n=2)
        assert len(r.top_lines) <= 2

    def test_empty_input(self):
        r = summarize_lines([])
        assert r.total_lines == 0
        assert r.first_timestamp is None
        assert r.last_timestamp is None


class TestFormatSummaryReport:
    def test_contains_total(self):
        r = summarize_lines(SAMPLE_LINES)
        text = format_summary_report(r)
        assert "Total lines" in text

    def test_contains_level_section(self):
        r = summarize_lines(SAMPLE_LINES)
        text = format_summary_report(r)
        assert "ERROR" in text

    def test_contains_top_repeated(self):
        r = summarize_lines(SAMPLE_LINES)
        text = format_summary_report(r)
        assert "Top repeated" in text


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    p = tmp_path / "test.log"
    p.write_text("\n".join(SAMPLE_LINES), encoding="utf-8")
    return p


def _ns(**kwargs):
    defaults = {"top": 5, "json": False}
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class TestCmdSummarize:
    def test_returns_zero_on_success(self, log_file):
        ns = _ns(file=str(log_file))
        assert cmd_summarize(ns, out=StringIO()) == 0

    def test_returns_one_for_missing_file(self, tmp_path):
        ns = _ns(file=str(tmp_path / "missing.log"))
        assert cmd_summarize(ns, out=StringIO()) == 1

    def test_text_output_contains_summary_header(self, log_file):
        ns = _ns(file=str(log_file))
        buf = StringIO()
        cmd_summarize(ns, out=buf)
        assert "Log Summary" in buf.getvalue()

    def test_json_output_is_valid_json(self, log_file):
        ns = _ns(file=str(log_file), json=True)
        buf = StringIO()
        cmd_summarize(ns, out=buf)
        data = json.loads(buf.getvalue())
        assert "total_lines" in data
        assert "level_counts" in data

    def test_json_top_lines_length(self, log_file):
        ns = _ns(file=str(log_file), top=2, json=True)
        buf = StringIO()
        cmd_summarize(ns, out=buf)
        data = json.loads(buf.getvalue())
        assert len(data["top_lines"]) <= 2


class TestBuildSummarizerParser:
    def test_returns_argument_parser(self):
        p = build_summarizer_parser()
        assert p is not None

    def test_default_top_is_five(self):
        p = build_summarizer_parser()
        ns = p.parse_args(["somefile.log"])
        assert ns.top == 5

    def test_default_json_is_false(self):
        p = build_summarizer_parser()
        ns = p.parse_args(["somefile.log"])
        assert ns.json is False
