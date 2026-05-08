"""Tests for logslice.transformer_cli."""

from __future__ import annotations

import io
import pytest

from logslice.transformer_cli import (
    _parse_rules,
    build_transformer_parser,
    cmd_transform,
)


@pytest.fixture()
def log_file(tmp_path):
    p = tmp_path / "sample.log"
    p.write_text(
        "2024-01-01 ERROR something failed\n"
        "2024-01-01 INFO  all good\n"
        "2024-01-01 ERROR another failure\n"
    )
    return str(p)


def _ns(**kwargs):
    defaults = dict(file="", rules=[], case_sensitive=False, changed_only=False)
    defaults.update(kwargs)
    import argparse
    return argparse.Namespace(**defaults)


class TestBuildTransformerParser:
    def test_returns_argument_parser(self):
        import argparse
        assert isinstance(build_transformer_parser(), argparse.ArgumentParser)

    def test_default_rules_is_empty(self):
        p = build_transformer_parser()
        ns = p.parse_args(["/dev/null"])
        assert ns.rules == []

    def test_default_case_sensitive_is_false(self):
        p = build_transformer_parser()
        ns = p.parse_args(["/dev/null"])
        assert ns.case_sensitive is False

    def test_default_changed_only_is_false(self):
        p = build_transformer_parser()
        ns = p.parse_args(["/dev/null"])
        assert ns.changed_only is False


class TestParseRules:
    def test_valid_rule_parsed(self):
        rules = _parse_rules(["foo=bar"], case_sensitive=False)
        assert len(rules) == 1
        assert rules[0].pattern == "foo"
        assert rules[0].replacement == "bar"

    def test_invalid_rule_raises(self):
        with pytest.raises(ValueError):
            _parse_rules(["no-equals"], case_sensitive=False)

    def test_multiple_rules(self):
        rules = _parse_rules(["a=A", "b=B"], case_sensitive=False)
        assert len(rules) == 2

    def test_case_sensitive_propagated(self):
        rules = _parse_rules(["x=y"], case_sensitive=True)
        assert rules[0].case_sensitive is True


class TestCmdTransform:
    def test_returns_zero_on_success(self, log_file):
        ns = _ns(file=log_file, rules=["ERROR=ERR"])
        assert cmd_transform(ns, out=io.StringIO()) == 0

    def test_replaces_pattern_in_output(self, log_file):
        out = io.StringIO()
        ns = _ns(file=log_file, rules=["ERROR=ERR"])
        cmd_transform(ns, out=out)
        content = out.getvalue()
        assert "ERR" in content
        assert "ERROR" not in content

    def test_unchanged_lines_present_by_default(self, log_file):
        out = io.StringIO()
        ns = _ns(file=log_file, rules=["ERROR=ERR"])
        cmd_transform(ns, out=out)
        lines = out.getvalue().splitlines()
        assert len(lines) == 3

    def test_changed_only_filters_unchanged(self, log_file):
        out = io.StringIO()
        ns = _ns(file=log_file, rules=["ERROR=ERR"], changed_only=True)
        cmd_transform(ns, out=out)
        lines = out.getvalue().splitlines()
        assert len(lines) == 2

    def test_no_rules_output_equals_input(self, log_file):
        out = io.StringIO()
        ns = _ns(file=log_file)
        cmd_transform(ns, out=out)
        with open(log_file) as fh:
            original = fh.read().splitlines()
        assert out.getvalue().splitlines() == original
