"""Tests for logslice.diff_cli."""

from __future__ import annotations

import argparse
import textwrap
from pathlib import Path

import pytest

from logslice.diff_cli import build_diff_parser, cmd_diff


@pytest.fixture()
def log_pair(tmp_path: Path):
    """Return (path_a, path_b) for two small log files."""
    file_a = tmp_path / "a.log"
    file_b = tmp_path / "b.log"
    file_a.write_text(
        textwrap.dedent("""\
        2024-01-01 INFO  start
        2024-01-01 ERROR boom
        2024-01-01 INFO  end
        """),
        encoding="utf-8",
    )
    file_b.write_text(
        textwrap.dedent("""\
        2024-01-01 INFO  start
        2024-01-01 WARN  almost boom
        2024-01-01 INFO  end
        """),
        encoding="utf-8",
    )
    return str(file_a), str(file_b)


def _ns(**kwargs) -> argparse.Namespace:
    defaults = dict(file_a="a.log", file_b="b.log", context=3, color=False, summary=False)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestBuildDiffParser:
    def test_returns_argument_parser(self):
        parser = build_diff_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    def test_default_context_is_3(self):
        parser = build_diff_parser()
        args = parser.parse_args(["a.log", "b.log"])
        assert args.context == 3

    def test_default_color_is_false(self):
        parser = build_diff_parser()
        args = parser.parse_args(["a.log", "b.log"])
        assert args.color is False

    def test_default_summary_is_false(self):
        parser = build_diff_parser()
        args = parser.parse_args(["a.log", "b.log"])
        assert args.summary is False

    def test_context_flag_parsed(self):
        parser = build_diff_parser()
        args = parser.parse_args(["a.log", "b.log", "-c", "5"])
        assert args.context == 5

    def test_color_flag_parsed(self):
        parser = build_diff_parser()
        args = parser.parse_args(["a.log", "b.log", "--color"])
        assert args.color is True

    def test_summary_flag_parsed(self):
        parser = build_diff_parser()
        args = parser.parse_args(["a.log", "b.log", "--summary"])
        assert args.summary is True


class TestCmdDiff:
    def test_returns_zero_for_identical_files(self, tmp_path):
        f = tmp_path / "same.log"
        f.write_text("line one\nline two\n", encoding="utf-8")
        ns = _ns(file_a=str(f), file_b=str(f))
        assert cmd_diff(ns) == 0

    def test_returns_one_for_different_files(self, log_pair, capsys):
        file_a, file_b = log_pair
        ns = _ns(file_a=file_a, file_b=file_b)
        code = cmd_diff(ns)
        assert code == 1

    def test_prints_summary_line(self, log_pair, capsys):
        file_a, file_b = log_pair
        ns = _ns(file_a=file_a, file_b=file_b)
        cmd_diff(ns)
        out = capsys.readouterr().out
        assert "lines added" in out
        assert "lines removed" in out

    def test_missing_file_returns_one(self, capsys):
        ns = _ns(file_a="/no/such/file_a.log", file_b="/no/such/file_b.log")
        code = cmd_diff(ns)
        assert code == 1
        err = capsys.readouterr().err
        assert "error reading file" in err

    def test_summary_flag_suppresses_diff_body(self, log_pair, capsys):
        file_a, file_b = log_pair
        ns = _ns(file_a=file_a, file_b=file_b, summary=True)
        cmd_diff(ns)
        out = capsys.readouterr().out
        # The diff body lines start with +/- but summary-only output should
        # not contain hunk headers starting with @@.
        assert "@@" not in out
