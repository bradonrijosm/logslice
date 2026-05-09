"""Tests for logslice.extractor."""
from __future__ import annotations

import pytest

from logslice.extractor import (
    ExtractRule,
    ExtractedLine,
    extract_fields,
    format_extracted,
)


class TestExtractRule:
    def test_extracts_first_group(self):
        rule = ExtractRule(name="ip", pattern=r"(\d+\.\d+\.\d+\.\d+)")
        assert rule.extract("client 192.168.1.1 connected") == "192.168.1.1"

    def test_no_match_returns_none(self):
        rule = ExtractRule(name="ip", pattern=r"(\d+\.\d+\.\d+\.\d+)")
        assert rule.extract("no address here") is None

    def test_case_insensitive_match(self):
        rule = ExtractRule(name="level", pattern=r"(error)", case_sensitive=False)
        assert rule.extract("ERROR occurred") == "ERROR"

    def test_case_sensitive_no_match(self):
        rule = ExtractRule(name="level", pattern=r"(error)", case_sensitive=True)
        assert rule.extract("ERROR occurred") is None

    def test_no_group_returns_full_match(self):
        rule = ExtractRule(name="word", pattern=r"\bFOO\b")
        assert rule.extract("line FOO bar") == "FOO"


class TestExtractFields:
    def _lines(self):
        return [
            "2024-01-01 ERROR 192.168.0.1 something failed",
            "2024-01-02 INFO  10.0.0.5 all good",
        ]

    def _rules(self):
        return [
            ExtractRule("level", r"(ERROR|INFO|WARN)", case_sensitive=False),
            ExtractRule("ip", r"(\d+\.\d+\.\d+\.\d+)"),
        ]

    def test_yields_extracted_line_objects(self):
        result = list(extract_fields(self._lines(), self._rules()))
        assert all(isinstance(r, ExtractedLine) for r in result)

    def test_correct_field_values(self):
        result = list(extract_fields(self._lines(), self._rules()))
        assert result[0].fields["level"] == "ERROR"
        assert result[0].fields["ip"] == "192.168.0.1"

    def test_missing_field_is_none(self):
        lines = ["no ip here"]
        rules = [ExtractRule("ip", r"(\d+\.\d+\.\d+\.\d+)")]
        result = list(extract_fields(lines, rules))
        assert result[0].fields["ip"] is None

    def test_has_field_true_when_matched(self):
        lines = ["192.168.1.1 ok"]
        rules = [ExtractRule("ip", r"(\d+\.\d+\.\d+\.\d+)")]
        result = list(extract_fields(lines, rules))
        assert result[0].has_field("ip") is True

    def test_has_field_false_when_missing(self):
        lines = ["no address"]
        rules = [ExtractRule("ip", r"(\d+\.\d+\.\d+\.\d+)")]
        result = list(extract_fields(lines, rules))
        assert result[0].has_field("ip") is False

    def test_empty_input_yields_nothing(self):
        result = list(extract_fields([], [ExtractRule("x", r"(x)")]))
        assert result == []

    def test_trailing_newline_stripped_from_line(self):
        lines = ["hello world\n"]
        rules = [ExtractRule("w", r"(world)")]
        result = list(extract_fields(lines, rules))
        assert result[0].line == "hello world"


class TestFormatExtracted:
    def _make(self, fields):
        return ExtractedLine(line="x", fields=fields)

    def test_tab_separated_by_default(self):
        el = self._make({"a": "foo", "b": "bar"})
        rows = list(format_extracted([el]))
        assert rows == ["foo\tbar"]

    def test_missing_replaced_with_placeholder(self):
        el = self._make({"a": None, "b": "bar"})
        rows = list(format_extracted([el], missing="N/A"))
        assert rows == ["N/A\tbar"]

    def test_custom_separator(self):
        el = self._make({"a": "1", "b": "2"})
        rows = list(format_extracted([el], separator="|"))
        assert rows == ["1|2"]

    def test_empty_input_yields_nothing(self):
        assert list(format_extracted([])) == []
