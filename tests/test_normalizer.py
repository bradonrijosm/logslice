"""Tests for logslice.normalizer."""

from __future__ import annotations

import pytest

from logslice.normalizer import (
    collapse_whitespace,
    normalize_line,
    normalize_lines,
    redact_hex_addresses,
    redact_uuids,
    strip_trailing_whitespace,
)


class TestStripTrailingWhitespace:
    def test_removes_trailing_spaces(self):
        assert strip_trailing_whitespace("hello   ") == "hello"

    def test_removes_newline(self):
        assert strip_trailing_whitespace("hello\n") == "hello"

    def test_removes_crlf(self):
        assert strip_trailing_whitespace("hello\r\n") == "hello"

    def test_no_trailing_unchanged(self):
        assert strip_trailing_whitespace("hello") == "hello"

    def test_empty_string_unchanged(self):
        assert strip_trailing_whitespace("") == ""


class TestCollapseWhitespace:
    def test_collapses_double_space(self):
        assert collapse_whitespace("a  b") == "a b"

    def test_collapses_many_spaces(self):
        assert collapse_whitespace("a     b") == "a b"

    def test_single_space_unchanged(self):
        assert collapse_whitespace("a b") == "a b"

    def test_empty_unchanged(self):
        assert collapse_whitespace("") == ""


class TestRedactUuids:
    def test_replaces_uuid(self):
        line = "request id=550e8400-e29b-41d4-a716-446655440000 done"
        result = redact_uuids(line)
        assert "<UUID>" in result
        assert "550e8400" not in result

    def test_custom_placeholder(self):
        line = "id=550e8400-e29b-41d4-a716-446655440000"
        assert redact_uuids(line, placeholder="[ID]") == "id=[ID]"

    def test_no_uuid_unchanged(self):
        line = "no uuid here"
        assert redact_uuids(line) == "no uuid here"


class TestRedactHexAddresses:
    def test_replaces_hex_addr(self):
        line = "segfault at 0xdeadbeef in module"
        result = redact_hex_addresses(line)
        assert "<ADDR>" in result
        assert "0xdeadbeef" not in result

    def test_custom_placeholder(self):
        line = "ptr=0x1a2b3c"
        assert redact_hex_addresses(line, placeholder="PTR") == "ptr=PTR"

    def test_no_hex_unchanged(self):
        assert redact_hex_addresses("nothing here") == "nothing here"


class TestNormalizeLine:
    def test_default_strips_and_collapses(self):
        result = normalize_line("hello   world  \n")
        assert result == "hello world"

    def test_uuid_removed_when_enabled(self):
        line = "id=550e8400-e29b-41d4-a716-446655440000 ok"
        result = normalize_line(line, remove_uuids=True)
        assert "<UUID>" in result

    def test_hex_removed_when_enabled(self):
        line = "at 0xdeadbeef\n"
        result = normalize_line(line, remove_hex=True)
        assert "<ADDR>" in result
        assert "0xdeadbeef" not in result

    def test_no_strip_preserves_trailing(self):
        result = normalize_line("hi  \n", strip_whitespace=False, collapse_spaces=False)
        assert result.endswith("\n")


def test_normalize_lines_applies_to_all():
    lines = ["a  b\n", "c   d\n", "e f\n"]
    result = list(normalize_lines(lines))
    assert result == ["a b", "c d", "e f"]


def test_normalize_lines_empty_input():
    assert list(normalize_lines([])) == []
