"""Tests for logslice.correlator and logslice.correlator_cli."""
from __future__ import annotations

import argparse
import io
import textwrap
from pathlib import Path

import pytest

from logslice.correlator import (
    CorrelatedGroup,
    extract_correlation_id,
    group_by_correlation,
    iter_correlated,
)
from logslice.correlator_cli import build_correlator_parser, cmd_correlate


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_LINES = [
    "2024-01-01 00:00:01 INFO  request_id=abc123 starting",
    "2024-01-01 00:00:02 DEBUG request_id=abc123 processing",
    "2024-01-01 00:00:03 INFO  request_id=xyz789 starting",
    "2024-01-01 00:00:04 ERROR request_id=abc123 failed",
    "2024-01-01 00:00:05 INFO  no id here",
]


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    p = tmp_path / "sample.log"
    p.write_text("\n".join(SAMPLE_LINES) + "\n")
    return p


def _ns(**kwargs) -> argparse.Namespace:
    defaults = dict(
        logfile="-",
        correlation_id=None,
        list_ids=False,
        patterns=None,
        case_sensitive=False,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# extract_correlation_id
# ---------------------------------------------------------------------------

class TestExtractCorrelationId:
    def test_request_id_equals(self):
        line = "INFO request_id=abc123 done"
        assert extract_correlation_id(line) == "abc123"

    def test_trace_id_colon(self):
        line = "INFO trace_id: deadbeef handled"
        assert extract_correlation_id(line) == "deadbeef"

    def test_no_id_returns_none(self):
        assert extract_correlation_id("plain log line") is None

    def test_case_insensitive_by_default(self):
        assert extract_correlation_id("REQUEST_ID=UP123") == "UP123"

    def test_custom_pattern(self):
        line = "txn=t-99 processed"
        result = extract_correlation_id(line, patterns=[r"txn=([\w-]+)"])
        assert result == "t-99"


# ---------------------------------------------------------------------------
# group_by_correlation
# ---------------------------------------------------------------------------

class TestGroupByCorrelation:
    def test_groups_by_id(self):
        groups = group_by_correlation(SAMPLE_LINES)
        assert "abc123" in groups
        assert len(groups["abc123"].lines) == 3

    def test_untagged_lines_under_empty_key(self):
        groups = group_by_correlation(SAMPLE_LINES)
        assert "" in groups
        assert len(groups[""].lines) == 1

    def test_empty_input_returns_empty(self):
        assert group_by_correlation([]) == {}

    def test_returns_correlated_group_instances(self):
        groups = group_by_correlation(SAMPLE_LINES)
        for grp in groups.values():
            assert isinstance(grp, CorrelatedGroup)


# ---------------------------------------------------------------------------
# iter_correlated
# ---------------------------------------------------------------------------

class TestIterCorrelated:
    def test_yields_only_matching_lines(self):
        result = list(iter_correlated(SAMPLE_LINES, "abc123"))
        assert len(result) == 3

    def test_yields_nothing_for_unknown_id(self):
        result = list(iter_correlated(SAMPLE_LINES, "nope"))
        assert result == []

    def test_empty_input_yields_nothing(self):
        assert list(iter_correlated([], "abc123")) == []


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

class TestBuildCorrelatorParser:
    def test_returns_argument_parser(self):
        assert isinstance(build_correlator_parser(), argparse.ArgumentParser)

    def test_default_id_is_none(self):
        p = build_correlator_parser()
        ns = p.parse_args(["myfile.log"])
        assert ns.correlation_id is None

    def test_default_list_ids_false(self):
        p = build_correlator_parser()
        ns = p.parse_args(["myfile.log"])
        assert ns.list_ids is False


class TestCmdCorrelate:
    def test_filter_by_id_writes_matching_lines(self, log_file):
        out = io.StringIO()
        ns = _ns(logfile=str(log_file), correlation_id="abc123")
        rc = cmd_correlate(ns, out=out)
        assert rc == 0
        written = out.getvalue().splitlines()
        assert len(written) == 3

    def test_list_ids_shows_counts(self, log_file):
        out = io.StringIO()
        ns = _ns(logfile=str(log_file), list_ids=True)
        rc = cmd_correlate(ns, out=out)
        assert rc == 0
        assert "abc123" in out.getvalue()
        assert "xyz789" in out.getvalue()

    def test_no_flag_returns_nonzero(self, log_file):
        out = io.StringIO()
        ns = _ns(logfile=str(log_file))
        rc = cmd_correlate(ns, out=out)
        assert rc != 0

    def test_unknown_id_writes_nothing(self, log_file):
        out = io.StringIO()
        ns = _ns(logfile=str(log_file), correlation_id="unknown")
        rc = cmd_correlate(ns, out=out)
        assert rc == 0
        assert out.getvalue() == ""
