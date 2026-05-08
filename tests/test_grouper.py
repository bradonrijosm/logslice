"""Tests for logslice.grouper."""
from __future__ import annotations

import pytest

from logslice.grouper import (
    GroupedLines,
    extract_group_key,
    format_groups,
    group_lines,
)

LINES = [
    "2024-01-01 host-a INFO  starting up",
    "2024-01-01 host-b ERROR disk full",
    "2024-01-01 host-a WARN  high memory",
    "2024-01-01 host-c INFO  connected",
    "2024-01-01 host-b INFO  recovered",
    "no-host-here just some text",
]

HOST_PATTERN = r"(host-\w+)"


class TestExtractGroupKey:
    def test_returns_matched_group(self):
        assert extract_group_key(LINES[0], HOST_PATTERN) == "host-a"

    def test_returns_none_on_no_match(self):
        assert extract_group_key("no host here", HOST_PATTERN) is None

    def test_case_insensitive_by_default(self):
        assert extract_group_key("HOST-A info", HOST_PATTERN) == "HOST-A"

    def test_case_sensitive_no_match(self):
        assert extract_group_key("HOST-A info", r"(host-\w+)", case_sensitive=True) is None

    def test_invalid_group_index_returns_none(self):
        assert extract_group_key(LINES[0], HOST_PATTERN, group=99) is None

    def test_second_group(self):
        line = "2024-01-01 host-a ERROR disk full"
        result = extract_group_key(line, r"(host-\w+)\s+(\w+)", group=2)
        assert result == "ERROR"


class TestGroupLines:
    def test_keys_present(self):
        groups = group_lines(LINES, HOST_PATTERN)
        assert "host-a" in groups
        assert "host-b" in groups
        assert "host-c" in groups

    def test_correct_line_counts(self):
        groups = group_lines(LINES, HOST_PATTERN)
        assert len(groups["host-a"].lines) == 2
        assert len(groups["host-b"].lines) == 2
        assert len(groups["host-c"].lines) == 1

    def test_unmatched_lines_go_to_default_key(self):
        groups = group_lines(LINES, HOST_PATTERN)
        assert "__ungrouped__" in groups
        assert len(groups["__ungrouped__"].lines) == 1

    def test_custom_default_key(self):
        groups = group_lines(LINES, HOST_PATTERN, default_key="other")
        assert "other" in groups
        assert "__ungrouped__" not in groups

    def test_empty_input_returns_empty_dict(self):
        assert group_lines([], HOST_PATTERN) == {}

    def test_all_unmatched_single_bucket(self):
        lines = ["foo", "bar", "baz"]
        groups = group_lines(lines, HOST_PATTERN)
        assert list(groups.keys()) == ["__ungrouped__"]
        assert len(groups["__ungrouped__"].lines) == 3

    def test_group_key_stored_on_grouped_lines(self):
        groups = group_lines(LINES, HOST_PATTERN)
        assert groups["host-a"].key == "host-a"


class TestFormatGroups:
    def test_contains_key_header(self):
        groups = group_lines(LINES[:3], HOST_PATTERN)
        output = format_groups(groups)
        assert "[host-a]" in output
        assert "[host-b]" in output

    def test_contains_separator(self):
        groups = group_lines(LINES[:2], HOST_PATTERN)
        output = format_groups(groups, separator="===")
        assert "===" in output

    def test_empty_groups_returns_empty_string(self):
        assert format_groups({}) == ""
