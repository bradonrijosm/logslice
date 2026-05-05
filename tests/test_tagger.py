"""Tests for logslice.tagger and logslice.tagger_cli."""

from __future__ import annotations

import io
import textwrap

import pytest

from logslice.tagger import (
    TagRule,
    TaggedLine,
    collect_tags,
    filter_by_tag,
    tag_lines,
)
from logslice.tagger_cli import build_tagger_parser, cmd_tag


# ---------------------------------------------------------------------------
# TagRule
# ---------------------------------------------------------------------------

class TestTagRule:
    def test_matches_case_insensitive_by_default(self):
        rule = TagRule(tag="err", pattern="error")
        assert rule.matches("2024-01-01 ERROR: disk full")

    def test_no_match_returns_false(self):
        rule = TagRule(tag="err", pattern="error")
        assert not rule.matches("INFO: all good")

    def test_case_sensitive_no_match(self):
        rule = TagRule(tag="err", pattern="error", case_sensitive=True)
        assert not rule.matches("ERROR: oops")

    def test_case_sensitive_match(self):
        rule = TagRule(tag="err", pattern="error", case_sensitive=True)
        assert rule.matches("error: disk full")


# ---------------------------------------------------------------------------
# TaggedLine
# ---------------------------------------------------------------------------

class TestTaggedLine:
    def test_str_no_tags_returns_plain_line(self):
        tl = TaggedLine(line="plain line")
        assert str(tl) == "plain line"

    def test_str_with_tags_prefixes_labels(self):
        tl = TaggedLine(line="some error", tags=["err"])
        assert str(tl) == "[err] some error"

    def test_multiple_tags_joined(self):
        tl = TaggedLine(line="critical error", tags=["err", "crit"])
        assert str(tl) == "[err,crit] critical error"

    def test_tagged_property_true_when_tags_present(self):
        assert TaggedLine(line="x", tags=["a"]).tagged is True

    def test_tagged_property_false_when_no_tags(self):
        assert TaggedLine(line="x").tagged is False


# ---------------------------------------------------------------------------
# tag_lines
# ---------------------------------------------------------------------------

LINES = [
    "INFO: service started",
    "ERROR: connection refused",
    "WARN: retrying",
    "ERROR: timeout",
    "DEBUG: loop tick",
]

RULES = [
    TagRule(tag="err", pattern="error"),
    TagRule(tag="warn", pattern="warn"),
]


def test_tag_lines_returns_correct_count():
    result = list(tag_lines(LINES, RULES))
    assert len(result) == len(LINES)


def test_tag_lines_applies_multiple_rules():
    result = list(tag_lines(LINES, RULES))
    assert result[1].tags == ["err"]
    assert result[2].tags == ["warn"]


def test_tag_lines_unmatched_line_has_empty_tags():
    result = list(tag_lines(LINES, RULES))
    assert result[0].tags == []


def test_tag_lines_multi_tag_false_stops_at_first():
    rules = [
        TagRule(tag="first", pattern="error"),
        TagRule(tag="second", pattern="error"),
    ]
    result = list(tag_lines(["ERROR: boom"], rules, multi_tag=False))
    assert result[0].tags == ["first"]


# ---------------------------------------------------------------------------
# filter_by_tag / collect_tags
# ---------------------------------------------------------------------------

def test_filter_by_tag_returns_only_matching():
    tagged = list(tag_lines(LINES, RULES))
    errors = list(filter_by_tag(tagged, "err"))
    assert len(errors) == 2
    assert all("err" in tl.tags for tl in errors)


def test_collect_tags_counts_correctly():
    tagged = list(tag_lines(LINES, RULES))
    counts = collect_tags(tagged)
    assert counts["err"] == 2
    assert counts["warn"] == 1


def test_collect_tags_empty_input_returns_empty():
    assert collect_tags([]) == {}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@pytest.fixture()
def log_file(tmp_path):
    p = tmp_path / "test.log"
    p.write_text("\n".join(LINES), encoding="utf-8")
    return str(p)


def _ns(**kwargs):
    defaults = dict(
        file="",
        rules=[],
        filter_tag=None,
        summary=False,
        case_sensitive=False,
    )
    defaults.update(kwargs)
    import argparse
    return argparse.Namespace(**defaults)


def test_build_tagger_parser_returns_parser():
    import argparse
    assert isinstance(build_tagger_parser(), argparse.ArgumentParser)


def test_cmd_tag_outputs_all_lines_no_rules(log_file):
    out = io.StringIO()
    code = cmd_tag(_ns(file=log_file), out=out)
    assert code == 0
    assert out.getvalue().count("\n") == len(LINES)


def test_cmd_tag_invalid_rule_returns_one(log_file):
    out = io.StringIO()
    code = cmd_tag(_ns(file=log_file, rules=["no-colon"]), out=out)
    assert code == 1


def test_cmd_tag_summary_shows_counts(log_file):
    out = io.StringIO()
    code = cmd_tag(_ns(file=log_file, rules=["err:error"], summary=True), out=out)
    assert code == 0
    assert "err: 2" in out.getvalue()


def test_cmd_tag_filter_tag_limits_output(log_file):
    out = io.StringIO()
    code = cmd_tag(
        _ns(file=log_file, rules=["err:error"], filter_tag="err"), out=out
    )
    assert code == 0
    lines = [l for l in out.getvalue().splitlines() if l]
    assert len(lines) == 2


def test_cmd_tag_missing_file_returns_one():
    out = io.StringIO()
    code = cmd_tag(_ns(file="/nonexistent/path.log"), out=out)
    assert code == 1
