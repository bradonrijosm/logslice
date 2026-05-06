"""Tests for logslice.classifier."""

from __future__ import annotations

import pytest

from logslice.classifier import (
    ClassifiedLine,
    ClassifyRule,
    classify_line,
    classify_lines,
    group_by_category,
)


ERROR_RULE = ClassifyRule(category="ERROR", pattern=r"error")
WARN_RULE = ClassifyRule(category="WARN", pattern=r"warn(ing)?")
INFO_RULE = ClassifyRule(category="INFO", pattern=r"info")

RULES = [ERROR_RULE, WARN_RULE, INFO_RULE]


class TestClassifyRule:
    def test_matches_case_insensitive_by_default(self):
        rule = ClassifyRule(category="X", pattern="error")
        assert rule.matches("2024-01-01 ERROR something broke")

    def test_no_match_returns_false(self):
        assert not ERROR_RULE.matches("everything is fine")

    def test_case_sensitive_no_match(self):
        rule = ClassifyRule(category="X", pattern="ERROR", case_sensitive=True)
        assert not rule.matches("error: disk full")

    def test_case_sensitive_match(self):
        rule = ClassifyRule(category="X", pattern="ERROR", case_sensitive=True)
        assert rule.matches("ERROR: disk full")


class TestClassifyLine:
    def test_first_matching_rule_wins(self):
        cl = classify_line("error warning info", RULES)
        assert cl.category == "ERROR"

    def test_second_rule_matches_when_first_misses(self):
        cl = classify_line("warning: low memory", RULES)
        assert cl.category == "WARN"

    def test_no_match_returns_none_by_default(self):
        cl = classify_line("debug: verbose output", RULES)
        assert cl.category is None

    def test_no_match_uses_default_label(self):
        cl = classify_line("debug: verbose output", RULES, default="OTHER")
        assert cl.category == "OTHER"

    def test_is_classified_true_when_matched(self):
        cl = classify_line("error occurred", RULES)
        assert cl.is_classified

    def test_is_classified_false_when_unmatched(self):
        cl = classify_line("nothing here", RULES)
        assert not cl.is_classified

    def test_line_preserved_in_result(self):
        line = "2024-01-01 INFO service started"
        cl = classify_line(line, RULES)
        assert cl.line == line


class TestClassifyLines:
    def test_yields_one_result_per_line(self):
        lines = ["error here", "info there", "unknown"]
        results = list(classify_lines(lines, RULES))
        assert len(results) == 3

    def test_empty_input_returns_empty(self):
        assert list(classify_lines([], RULES)) == []

    def test_categories_assigned_correctly(self):
        lines = ["error x", "warning y", "info z"]
        cats = [cl.category for cl in classify_lines(lines, RULES)]
        assert cats == ["ERROR", "WARN", "INFO"]


class TestGroupByCategory:
    def test_groups_lines_under_correct_key(self):
        classified = [
            ClassifiedLine(line="a", category="ERROR"),
            ClassifiedLine(line="b", category="ERROR"),
            ClassifiedLine(line="c", category="INFO"),
        ]
        groups = group_by_category(classified)
        assert groups["ERROR"] == ["a", "b"]
        assert groups["INFO"] == ["c"]

    def test_unmatched_lines_under_none_key(self):
        classified = [ClassifiedLine(line="x", category=None)]
        groups = group_by_category(classified)
        assert None in groups
        assert groups[None] == ["x"]

    def test_empty_input_returns_empty_dict(self):
        assert group_by_category([]) == {}
