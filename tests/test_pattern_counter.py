"""Tests for logslice.pattern_counter and logslice.pattern_counter_cli."""
from __future__ import annotations

import io
import textwrap
from pathlib import Path

import pytest

from logslice.pattern_counter import (
    PatternCount,
    count_pattern,
    count_patterns,
    format_pattern_counts,
)
from logslice.pattern_counter_cli import build_pattern_counter_parser, cmd_count


LINES = [
    "2024-01-01 ERROR something went wrong\n",
    "2024-01-01 INFO  all good\n",
    "2024-01-01 ERROR another error here\n",
    "2024-01-01 WARN  disk space low\n",
    "2024-01-01 ERROR third error\n",
    "2024-01-01 INFO  startup complete\n",
]


class TestCountPattern:
    def test_counts_matching_lines(self):
        result = count_pattern(LINES, r"ERROR")
        assert result.count == 3

    def test_zero_for_no_match(self):
        result = count_pattern(LINES, r"CRITICAL")
        assert result.count == 0

    def test_case_insensitive_by_default(self):
        result = count_pattern(LINES, r"error")
        assert result.count == 3

    def test_case_sensitive_no_match(self):
        result = count_pattern(LINES, r"error", case_sensitive=True)
        assert result.count == 0

    def test_samples_capped_at_max(self):
        result = count_pattern(LINES, r"ERROR", max_samples=2)
        assert len(result.sample_lines) == 2

    def test_samples_contain_stripped_lines(self):
        result = count_pattern(LINES, r"ERROR", max_samples=5)
        for s in result.sample_lines:
            assert not s.endswith("\n")

    def test_pattern_stored_on_result(self):
        result = count_pattern(LINES, r"INFO")
        assert result.pattern == r"INFO"


class TestCountPatterns:
    def test_returns_dict_keyed_by_pattern(self):
        results = count_patterns(LINES, [r"ERROR", r"INFO"])
        assert set(results.keys()) == {r"ERROR", r"INFO"}

    def test_counts_are_correct(self):
        results = count_patterns(LINES, [r"ERROR", r"INFO"])
        assert results[r"ERROR"].count == 3
        assert results[r"INFO"].count == 2

    def test_empty_patterns_returns_empty_dict(self):
        results = count_patterns(LINES, [])
        assert results == {}

    def test_empty_lines_all_zero(self):
        results = count_patterns([], [r"ERROR", r"INFO"])
        assert results[r"ERROR"].count == 0
        assert results[r"INFO"].count == 0


class TestFormatPatternCounts:
    def test_no_patterns_returns_message(self):
        assert format_pattern_counts({}) == "No patterns specified."

    def test_contains_pattern_and_count(self):
        results = count_patterns(LINES, [r"ERROR"])
        output = format_pattern_counts(results)
        assert "ERROR" in output
        assert "3" in output

    def test_no_samples_hides_sample_lines(self):
        results = count_patterns(LINES, [r"ERROR"])
        output = format_pattern_counts(results, show_samples=False)
        assert "sample:" not in output


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    p = tmp_path / "test.log"
    p.write_text("".join(LINES), encoding="utf-8")
    return p


class TestCmdCount:
    def _ns(self, log_file, patterns, **kwargs):
        defaults = dict(
            file=str(log_file),
            patterns=patterns,
            case_sensitive=False,
            max_samples=3,
            no_samples=False,
        )
        defaults.update(kwargs)
        import argparse
        return argparse.Namespace(**defaults)

    def test_returns_zero_on_success(self, log_file):
        ns = self._ns(log_file, [r"ERROR"])
        assert cmd_count(ns, out=io.StringIO(), err=io.StringIO()) == 0

    def test_output_contains_count(self, log_file):
        ns = self._ns(log_file, [r"ERROR"])
        out = io.StringIO()
        cmd_count(ns, out=out, err=io.StringIO())
        assert "3" in out.getvalue()

    def test_returns_two_when_no_patterns(self, log_file):
        ns = self._ns(log_file, [])
        assert cmd_count(ns, out=io.StringIO(), err=io.StringIO()) == 2

    def test_returns_one_for_missing_file(self, tmp_path):
        import argparse
        ns = argparse.Namespace(
            file=str(tmp_path / "missing.log"),
            patterns=[r"ERROR"],
            case_sensitive=False,
            max_samples=3,
            no_samples=False,
        )
        assert cmd_count(ns, out=io.StringIO(), err=io.StringIO()) == 1


def test_build_pattern_counter_parser_returns_parser():
    import argparse
    p = build_pattern_counter_parser()
    assert isinstance(p, argparse.ArgumentParser)


def test_default_case_sensitive_is_false():
    p = build_pattern_counter_parser()
    ns = p.parse_args(["some.log"])
    assert ns.case_sensitive is False


def test_default_max_samples_is_3():
    p = build_pattern_counter_parser()
    ns = p.parse_args(["some.log"])
    assert ns.max_samples == 3
