"""Tests for logslice.classifier_cli."""

from __future__ import annotations

import io
import json
import textwrap

import pytest

from logslice.classifier_cli import build_classifier_parser, cmd_classify


RULES_JSON = json.dumps([
    {"category": "ERROR", "pattern": "error"},
    {"category": "WARN", "pattern": "warn"},
    {"category": "INFO", "pattern": "info"},
])


@pytest.fixture()
def log_file(tmp_path):
    p = tmp_path / "app.log"
    p.write_text(
        textwrap.dedent("""\
            2024-01-01 ERROR disk full
            2024-01-01 WARN low memory
            2024-01-01 INFO service ok
            2024-01-01 DEBUG verbose
        """),
        encoding="utf-8",
    )
    return p


def _ns(**kwargs):
    defaults = dict(
        logfile=None,
        rules=RULES_JSON,
        default=None,
        unmatched_only=False,
        summary=False,
    )
    defaults.update(kwargs)
    import argparse
    return argparse.Namespace(**defaults)


class TestBuildClassifierParser:
    def test_returns_argument_parser(self):
        import argparse
        assert isinstance(build_classifier_parser(), argparse.ArgumentParser)

    def test_default_default_is_none(self):
        p = build_classifier_parser()
        args = p.parse_args(["file.log", "--rules", "[]"])
        assert args.default is None

    def test_default_summary_is_false(self):
        p = build_classifier_parser()
        args = p.parse_args(["file.log", "--rules", "[]"])
        assert args.summary is False

    def test_default_unmatched_only_is_false(self):
        p = build_classifier_parser()
        args = p.parse_args(["file.log", "--rules", "[]"])
        assert args.unmatched_only is False


class TestCmdClassify:
    def test_returns_zero_on_success(self, log_file):
        out = io.StringIO()
        rc = cmd_classify(_ns(logfile=str(log_file)), out=out)
        assert rc == 0

    def test_prefixes_lines_with_category(self, log_file):
        out = io.StringIO()
        cmd_classify(_ns(logfile=str(log_file)), out=out)
        lines = out.getvalue().splitlines()
        assert lines[0].startswith("[ERROR]")
        assert lines[1].startswith("[WARN]")
        assert lines[2].startswith("[INFO]")

    def test_unmatched_line_gets_question_mark(self, log_file):
        out = io.StringIO()
        cmd_classify(_ns(logfile=str(log_file)), out=out)
        lines = out.getvalue().splitlines()
        assert lines[3].startswith("[?]")

    def test_unmatched_only_filters_matched_lines(self, log_file):
        out = io.StringIO()
        cmd_classify(_ns(logfile=str(log_file), unmatched_only=True), out=out)
        lines = out.getvalue().splitlines()
        assert all(l.startswith("[?]") for l in lines)
        assert len(lines) == 1

    def test_summary_prints_counts(self, log_file):
        out = io.StringIO()
        cmd_classify(_ns(logfile=str(log_file), summary=True), out=out)
        text = out.getvalue()
        assert "ERROR: 1" in text
        assert "WARN: 1" in text
        assert "INFO: 1" in text

    def test_default_label_applied_to_unmatched(self, log_file):
        out = io.StringIO()
        cmd_classify(_ns(logfile=str(log_file), default="OTHER"), out=out)
        lines = out.getvalue().splitlines()
        assert lines[3].startswith("[OTHER]")
