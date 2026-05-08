"""Tests for logslice.dispatcher and logslice.dispatcher_cli."""
from __future__ import annotations

import argparse
from io import StringIO
from typing import List

import pytest

from logslice.dispatcher import (
    DispatchRule,
    DispatchedLine,
    dispatch_line,
    dispatch_lines,
    group_by_channel,
    channel_summary,
)
from logslice.dispatcher_cli import build_dispatcher_parser, _parse_rules, cmd_dispatch


# ---------------------------------------------------------------------------
# DispatchRule
# ---------------------------------------------------------------------------

class TestDispatchRule:
    def test_matches_case_insensitive_by_default(self):
        rule = DispatchRule(channel="errors", pattern="error")
        assert rule.matches("2024-01-01 ERROR something bad")

    def test_no_match_returns_false(self):
        rule = DispatchRule(channel="errors", pattern="error")
        assert not rule.matches("2024-01-01 INFO all good")

    def test_case_sensitive_no_match(self):
        rule = DispatchRule(channel="errors", pattern="error", case_sensitive=True)
        assert not rule.matches("ERROR uppercase")

    def test_case_sensitive_match(self):
        rule = DispatchRule(channel="errors", pattern="error", case_sensitive=True)
        assert rule.matches("error lowercase")


# ---------------------------------------------------------------------------
# dispatch_line
# ---------------------------------------------------------------------------

def _rules() -> List[DispatchRule]:
    return [
        DispatchRule(channel="errors", pattern="error"),
        DispatchRule(channel="warnings", pattern="warn"),
    ]


def test_dispatch_line_first_match_wins():
    line = "ERROR and WARN in same line"
    result = dispatch_line(line, _rules())
    assert result.channel == "errors"
    assert result.rule_index == 0


def test_dispatch_line_falls_through_to_default():
    result = dispatch_line("INFO nothing special", _rules())
    assert result.channel == "default"
    assert result.rule_index is None


def test_dispatch_line_custom_default_channel():
    result = dispatch_line("INFO nothing", _rules(), default_channel="misc")
    assert result.channel == "misc"


def test_dispatch_lines_yields_all():
    lines = ["ERROR bad", "WARN ok", "INFO fine"]
    results = list(dispatch_lines(lines, _rules()))
    assert len(results) == 3
    assert results[0].channel == "errors"
    assert results[1].channel == "warnings"
    assert results[2].channel == "default"


# ---------------------------------------------------------------------------
# group_by_channel / channel_summary
# ---------------------------------------------------------------------------

def test_group_by_channel_keys():
    dispatched = [
        DispatchedLine(line="a", channel="errors"),
        DispatchedLine(line="b", channel="errors"),
        DispatchedLine(line="c", channel="default"),
    ]
    groups = group_by_channel(dispatched)
    assert set(groups.keys()) == {"errors", "default"}
    assert groups["errors"] == ["a", "b"]


def test_channel_summary_sorted_descending():
    groups = {"errors": ["a", "b", "c"], "warnings": ["x"], "default": ["p", "q"]}
    summary = channel_summary(groups)
    counts = [count for _, count in summary]
    assert counts == sorted(counts, reverse=True)


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def test_build_dispatcher_parser_returns_parser():
    assert isinstance(build_dispatcher_parser(), argparse.ArgumentParser)


def test_default_channel_is_default():
    ns = build_dispatcher_parser().parse_args(["/dev/null"])
    assert ns.default_channel == "default"


def test_parse_rules_valid():
    rules = _parse_rules(["errors:error", "warnings:warn"], case_sensitive=False)
    assert rules[0].channel == "errors"
    assert rules[1].pattern == "warn"


def test_parse_rules_invalid_raises():
    with pytest.raises(ValueError):
        _parse_rules(["no-colon-here"], case_sensitive=False)


def test_cmd_dispatch_missing_file(tmp_path):
    ns = argparse.Namespace(
        logfile=str(tmp_path / "nonexistent.log"),
        rules=[],
        default_channel="default",
        case_sensitive=False,
        summary=False,
    )
    assert cmd_dispatch(ns) == 1


def test_cmd_dispatch_summary(tmp_path):
    log = tmp_path / "app.log"
    log.write_text("ERROR bad\nINFO ok\nERROR again\n")
    ns = argparse.Namespace(
        logfile=str(log),
        rules=["errors:error"],
        default_channel="default",
        case_sensitive=False,
        summary=True,
    )
    assert cmd_dispatch(ns) == 0
