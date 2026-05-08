"""Tests for logslice.transformer."""

from __future__ import annotations

import pytest

from logslice.transformer import (
    TransformRule,
    TransformedLine,
    apply_transforms,
    transform_line,
    transform_lines,
)


# ---------------------------------------------------------------------------
# TransformRule
# ---------------------------------------------------------------------------

class TestTransformRule:
    def test_basic_substitution(self):
        rule = TransformRule(pattern=r"foo", replacement="bar")
        assert rule.apply("foo baz") == "bar baz"

    def test_case_insensitive_by_default(self):
        rule = TransformRule(pattern=r"error", replacement="ERR")
        assert rule.apply("ERROR occurred") == "ERR occurred"

    def test_case_sensitive_no_match(self):
        rule = TransformRule(pattern=r"error", replacement="ERR", case_sensitive=True)
        assert rule.apply("ERROR occurred") == "ERROR occurred"

    def test_case_sensitive_match(self):
        rule = TransformRule(pattern=r"error", replacement="ERR", case_sensitive=True)
        assert rule.apply("error occurred") == "ERR occurred"

    def test_matches_returns_true(self):
        rule = TransformRule(pattern=r"\d+", replacement="NUM")
        assert rule.matches("line 42")

    def test_matches_returns_false(self):
        rule = TransformRule(pattern=r"\d+", replacement="NUM")
        assert not rule.matches("no digits here")

    def test_label_stored(self):
        rule = TransformRule(pattern=r"x", replacement="y", label="my-rule")
        assert rule.label == "my-rule"


# ---------------------------------------------------------------------------
# transform_line
# ---------------------------------------------------------------------------

def test_transform_line_no_rules_unchanged():
    tl = transform_line("hello world", [])
    assert tl.result == "hello world"
    assert not tl.changed
    assert tl.applied == []


def test_transform_line_single_rule_applied():
    rule = TransformRule(pattern=r"world", replacement="earth")
    tl = transform_line("hello world", [rule])
    assert tl.result == "hello earth"
    assert tl.changed
    assert len(tl.applied) == 1


def test_transform_line_rules_applied_in_order():
    r1 = TransformRule(pattern=r"foo", replacement="bar", label="r1")
    r2 = TransformRule(pattern=r"bar", replacement="baz", label="r2")
    tl = transform_line("foo", [r1, r2])
    assert tl.result == "baz"
    assert tl.applied == ["r1", "r2"]


def test_transform_line_non_matching_rule_not_in_applied():
    r1 = TransformRule(pattern=r"xyz", replacement="ABC", label="r1")
    tl = transform_line("hello", [r1])
    assert tl.applied == []


# ---------------------------------------------------------------------------
# transform_lines
# ---------------------------------------------------------------------------

def test_transform_lines_yields_one_per_input():
    rules = [TransformRule(pattern=r"a", replacement="A")]
    results = list(transform_lines(["aaa", "bbb", "aXb"], rules))
    assert len(results) == 3
    assert all(isinstance(r, TransformedLine) for r in results)


# ---------------------------------------------------------------------------
# apply_transforms
# ---------------------------------------------------------------------------

def test_apply_transforms_returns_strings():
    rules = [TransformRule(pattern=r"\d+", replacement="NUM")]
    out = list(apply_transforms(["line 1", "line 2"], rules))
    assert out == ["line NUM", "line NUM"]


def test_apply_transforms_changed_only_skips_unchanged():
    rules = [TransformRule(pattern=r"\d+", replacement="NUM")]
    out = list(apply_transforms(["no digits", "line 99"], rules, changed_only=True))
    assert out == ["line NUM"]


def test_apply_transforms_empty_input_returns_empty():
    out = list(apply_transforms([], []))
    assert out == []
