"""Tests for logslice.labeler."""

from __future__ import annotations

import io
import textwrap
from argparse import Namespace
from pathlib import Path

import pytest

from logslice.labeler import LabelRule, LabeledLine, label_line, label_lines, first_label
from logslice.labeler_cli import build_labeler_parser, cmd_label, _parse_rules


# ---------------------------------------------------------------------------
# LabelRule
# ---------------------------------------------------------------------------

class TestLabelRule:
    def test_matches_case_insensitive_by_default(self):
        rule = LabelRule(label="err", pattern="error")
        assert rule.matches("2024-01-01 ERROR something broke")

    def test_no_match_returns_false(self):
        rule = LabelRule(label="err", pattern="error")
        assert not rule.matches("INFO all good")

    def test_case_sensitive_no_match(self):
        rule = LabelRule(label="err", pattern="error", case_sensitive=True)
        assert not rule.matches("ERROR uppercase")

    def test_case_sensitive_match(self):
        rule = LabelRule(label="err", pattern="error", case_sensitive=True)
        assert rule.matches("error lowercase")


# ---------------------------------------------------------------------------
# LabeledLine
# ---------------------------------------------------------------------------

class TestLabeledLine:
    def test_is_labeled_true_when_labels_present(self):
        ll = LabeledLine(line="some line\n", labels=["err"])
        assert ll.is_labeled

    def test_is_labeled_false_when_no_labels(self):
        ll = LabeledLine(line="some line\n", labels=[])
        assert not ll.is_labeled

    def test_formatted_with_labels(self):
        ll = LabeledLine(line="msg", labels=["err", "crit"])
        assert ll.formatted() == "[err]|[crit] msg"

    def test_formatted_without_labels_returns_line(self):
        ll = LabeledLine(line="msg", labels=[])
        assert ll.formatted() == "msg"

    def test_formatted_custom_separator(self):
        ll = LabeledLine(line="msg", labels=["warn"])
        assert ll.formatted(separator=" >> ") == "[warn] >> msg"


# ---------------------------------------------------------------------------
# label_line / label_lines
# ---------------------------------------------------------------------------

def test_label_line_multiple_rules():
    rules = [
        LabelRule("err", "error"),
        LabelRule("slow", r"latency|timeout"),
    ]
    ll = label_line("ERROR timeout exceeded", rules)
    assert "err" in ll.labels
    assert "slow" in ll.labels


def test_label_lines_yields_all_by_default():
    rules = [LabelRule("err", "error")]
    lines = ["INFO ok\n", "ERROR bad\n"]
    results = list(label_lines(lines, rules))
    assert len(results) == 2


def test_label_lines_labeled_only_filters():
    rules = [LabelRule("err", "error")]
    lines = ["INFO ok\n", "ERROR bad\n"]
    results = list(label_lines(lines, rules, labeled_only=True))
    assert len(results) == 1
    assert results[0].labels == ["err"]


def test_first_label_returns_first():
    ll = LabeledLine(line="x", labels=["a", "b"])
    assert first_label(ll) == "a"


def test_first_label_default_when_empty():
    ll = LabeledLine(line="x", labels=[])
    assert first_label(ll, default="unknown") == "unknown"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    p = tmp_path / "app.log"
    p.write_text(textwrap.dedent("""\
        INFO  service started
        ERROR disk full
        WARN  latency spike
    """))
    return p


def _ns(**kwargs):
    defaults = dict(logfile="", rules=[], case_sensitive=False, labeled_only=False, separator=" ")
    defaults.update(kwargs)
    return Namespace(**defaults)


class TestBuildLabelerParser:
    def test_returns_argument_parser(self):
        p = build_labeler_parser()
        assert p is not None

    def test_default_labeled_only_is_false(self):
        p = build_labeler_parser()
        ns = p.parse_args(["somefile"])
        assert ns.labeled_only is False

    def test_default_separator_is_space(self):
        p = build_labeler_parser()
        ns = p.parse_args(["somefile"])
        assert ns.separator == " "


class TestCmdLabel:
    def test_returns_zero_on_success(self, log_file):
        ns = _ns(logfile=str(log_file), rules=["err:error"])
        assert cmd_label(ns, out=io.StringIO()) == 0

    def test_output_contains_label(self, log_file):
        ns = _ns(logfile=str(log_file), rules=["err:error"])
        out = io.StringIO()
        cmd_label(ns, out=out)
        assert "[err]" in out.getvalue()

    def test_labeled_only_excludes_unmatched(self, log_file):
        ns = _ns(logfile=str(log_file), rules=["err:error"], labeled_only=True)
        out = io.StringIO()
        cmd_label(ns, out=out)
        lines = [l for l in out.getvalue().splitlines() if l]
        assert all("[err]" in l for l in lines)

    def test_bad_rule_returns_one(self, log_file):
        ns = _ns(logfile=str(log_file), rules=["no-colon-here"])
        assert cmd_label(ns, out=io.StringIO()) == 1

    def test_missing_file_returns_one(self):
        ns = _ns(logfile="/nonexistent/path.log", rules=[])
        assert cmd_label(ns, out=io.StringIO()) == 1


def test_parse_rules_creates_label_rules():
    rules = _parse_rules(["err:error", "warn:warning"], case_sensitive=False)
    assert len(rules) == 2
    assert rules[0].label == "err"
    assert rules[1].label == "warn"
