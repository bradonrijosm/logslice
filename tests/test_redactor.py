"""Tests for logslice.redactor."""

from __future__ import annotations

import pytest

from logslice.redactor import (
    DEFAULT_RULES,
    RedactRule,
    count_redactions,
    redact_line,
    redact_lines,
)


class TestRedactRule:
    def test_basic_substitution(self):
        rule = RedactRule("secret", r"password=\S+", "[PWD]")
        assert rule.apply("user password=hunter2 logged in") == "user [PWD] logged in"

    def test_case_insensitive_by_default(self):
        rule = RedactRule("word", r"secret")
        assert rule.apply("SECRET value") == "[REDACTED] value"

    def test_case_sensitive_no_match(self):
        rule = RedactRule("word", r"secret", case_sensitive=True)
        assert rule.apply("SECRET value") == "SECRET value"

    def test_case_sensitive_match(self):
        rule = RedactRule("word", r"secret", case_sensitive=True)
        assert rule.apply("secret value") == "[REDACTED] value"

    def test_multiple_occurrences_replaced(self):
        rule = RedactRule("num", r"\d+", "#")
        assert rule.apply("a=1 b=2 c=3") == "a=# b=# c=#"

    def test_custom_replacement(self):
        rule = RedactRule("ip", r"\d{1,3}(?:\.\d{1,3}){3}", "<IP>")
        assert rule.apply("connected from 192.168.1.1") == "connected from <IP>"


class TestRedactLine:
    def test_no_match_returns_original(self):
        line = "ordinary log line with no sensitive data"
        assert redact_line(line, rules=[]) == line

    def test_ssn_redacted(self):
        line = "user ssn is 123-45-6789 on record"
        result = redact_line(line, rules=DEFAULT_RULES)
        assert "123-45-6789" not in result
        assert "[SSN]" in result

    def test_jwt_redacted(self):
        token = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        line = f"Authorization: Bearer {token}"
        result = redact_line(line, rules=DEFAULT_RULES)
        assert token not in result
        assert "[JWT]" in result

    def test_multiple_rules_applied_in_order(self):
        rule_a = RedactRule("a", r"foo", "BAR")
        rule_b = RedactRule("b", r"BAR", "BAZ")
        assert redact_line("foo", rules=[rule_a, rule_b]) == "BAZ"

    def test_empty_rules_list_returns_line_unchanged(self):
        line = "some 123-45-6789 line"
        assert redact_line(line, rules=[]) == line


class TestRedactLines:
    def test_yields_same_count(self):
        lines = ["line one", "line two", "line three"]
        result = list(redact_lines(lines, rules=[]))
        assert len(result) == 3

    def test_all_lines_processed(self):
        rule = RedactRule("num", r"\d+", "#")
        lines = ["error 404", "code 200", "no digits here"]
        result = list(redact_lines(lines, rules=[rule]))
        assert result == ["error #", "code #", "no digits here"]

    def test_empty_input_yields_nothing(self):
        assert list(redact_lines([], rules=DEFAULT_RULES)) == []


class TestCountRedactions:
    def test_counts_zero_when_no_matches(self):
        counts = count_redactions(["nothing sensitive here"], rules=DEFAULT_RULES)
        assert all(v == 0 for v in counts.values())

    def test_counts_ssn_occurrences(self):
        lines = ["ssn: 111-22-3333", "another 444-55-6666 here"]
        rule = RedactRule("ssn", r"\b\d{3}-\d{2}-\d{4}\b", "[SSN]")
        counts = count_redactions(lines, rules=[rule])
        assert counts["ssn"] == 2

    def test_returns_dict_keyed_by_rule_name(self):
        rule = RedactRule("x", r"x")
        counts = count_redactions(["xxx"], rules=[rule])
        assert "x" in counts
        assert counts["x"] == 3
