"""Tests for logslice.alerter."""
from __future__ import annotations

import pytest

from logslice.alerter import (
    AlertEvent,
    AlertRule,
    evaluate_rules,
    format_alert,
    run_alerts,
)


LINES = [
    "2024-01-01 00:00:01 INFO  service started",
    "2024-01-01 00:00:02 ERROR disk full",
    "2024-01-01 00:00:03 WARN  memory low",
    "2024-01-01 00:00:04 ERROR connection refused",
    "2024-01-01 00:00:05 INFO  all good",
]


class TestAlertRule:
    def test_matches_simple_pattern(self):
        rule = AlertRule(name="disk", pattern="disk full")
        assert rule.matches(LINES[1])

    def test_no_match_returns_false(self):
        rule = AlertRule(name="oom", pattern="out of memory")
        assert not rule.matches(LINES[0])

    def test_case_insensitive_by_default(self):
        rule = AlertRule(name="err", pattern="error")
        assert rule.matches(LINES[1])

    def test_case_sensitive_no_match(self):
        rule = AlertRule(name="err", pattern="error", case_sensitive=True)
        assert not rule.matches(LINES[1])  # line has "ERROR" uppercase

    def test_level_filter_restricts_match(self):
        rule = AlertRule(name="warn", pattern="memory", level="WARN")
        assert rule.matches(LINES[2])

    def test_level_filter_excludes_wrong_level(self):
        rule = AlertRule(name="warn", pattern="disk", level="WARN")
        assert not rule.matches(LINES[1])  # disk full is ERROR, not WARN


class TestEvaluateRules:
    def test_yields_event_for_each_match(self):
        rules = [AlertRule("err", "ERROR")]
        events = list(evaluate_rules(LINES, rules))
        assert len(events) == 2

    def test_event_contains_rule_name(self):
        rules = [AlertRule("disk", "disk full")]
        events = list(evaluate_rules(LINES, rules))
        assert events[0].rule_name == "disk"

    def test_event_line_number_is_1_based(self):
        rules = [AlertRule("err", "ERROR")]
        events = list(evaluate_rules(LINES, rules))
        assert events[0].line_number == 2

    def test_empty_lines_yields_nothing(self):
        rules = [AlertRule("x", "ERROR")]
        assert list(evaluate_rules([], rules)) == []

    def test_no_rules_yields_nothing(self):
        assert list(evaluate_rules(LINES, [])) == []

    def test_start_offset_applied(self):
        rules = [AlertRule("err", "ERROR")]
        events = list(evaluate_rules(LINES, rules, start=100))
        assert events[0].line_number == 101


def test_format_alert_contains_rule_and_line():
    event = AlertEvent(rule_name="disk", line="disk full", line_number=3)
    result = format_alert(event)
    assert "ALERT:disk" in result
    assert "line 3" in result
    assert "disk full" in result


def test_run_alerts_returns_all_events():
    rules = [AlertRule("err", "ERROR")]
    events = run_alerts(LINES, rules)
    assert len(events) == 2


def test_run_alerts_callback_called_for_each():
    seen: list[AlertEvent] = []
    rules = [AlertRule("err", "ERROR")]
    run_alerts(LINES, rules, callback=seen.append)
    assert len(seen) == 2
