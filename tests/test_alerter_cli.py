"""Tests for logslice.alerter_cli."""
from __future__ import annotations

import io
from pathlib import Path

import pytest

from logslice.alerter_cli import build_alerter_parser, cmd_alert


LOG_CONTENT = "\n".join([
    "2024-01-01 00:00:01 INFO  service started",
    "2024-01-01 00:00:02 ERROR disk full",
    "2024-01-01 00:00:03 WARN  memory low",
    "2024-01-01 00:00:04 ERROR connection refused",
])


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    p = tmp_path / "app.log"
    p.write_text(LOG_CONTENT, encoding="utf-8")
    return p


def _ns(log_file, rules=None, level=None, case_sensitive=False, count_only=False):
    parser = build_alerter_parser()
    argv = [str(log_file)]
    for r in (rules or []):
        argv += ["--rule", r]
    if level:
        argv += ["--level", level]
    if case_sensitive:
        argv.append("--case-sensitive")
    if count_only:
        argv.append("--count-only")
    return parser.parse_args(argv)


class TestBuildAlerterParser:
    def test_returns_argument_parser(self):
        import argparse
        assert isinstance(build_alerter_parser(), argparse.ArgumentParser)

    def test_default_level_is_none(self, log_file):
        ns = _ns(log_file, rules=["x:pattern"])
        assert ns.level is None

    def test_default_case_sensitive_false(self, log_file):
        ns = _ns(log_file, rules=["x:pattern"])
        assert ns.case_sensitive is False

    def test_default_count_only_false(self, log_file):
        ns = _ns(log_file, rules=["x:pattern"])
        assert ns.count_only is False


class TestCmdAlert:
    def test_returns_zero_on_success(self, log_file):
        ns = _ns(log_file, rules=["err:ERROR"])
        assert cmd_alert(ns, out=io.StringIO()) == 0

    def test_returns_one_when_no_rules(self, log_file):
        ns = _ns(log_file)
        assert cmd_alert(ns, out=io.StringIO()) == 1

    def test_returns_one_for_malformed_rule(self, log_file):
        ns = _ns(log_file, rules=["badformat"])
        assert cmd_alert(ns, out=io.StringIO()) == 1

    def test_output_contains_alert_tag(self, log_file):
        out = io.StringIO()
        ns = _ns(log_file, rules=["err:ERROR"])
        cmd_alert(ns, out=out)
        assert "[ALERT:err]" in out.getvalue()

    def test_count_only_prints_number(self, log_file):
        out = io.StringIO()
        ns = _ns(log_file, rules=["err:ERROR"], count_only=True)
        cmd_alert(ns, out=out)
        assert out.getvalue().strip() == "2"

    def test_level_filter_restricts_output(self, log_file):
        out = io.StringIO()
        ns = _ns(log_file, rules=["warn:memory"], level="WARN", count_only=True)
        cmd_alert(ns, out=out)
        assert out.getvalue().strip() == "1"
