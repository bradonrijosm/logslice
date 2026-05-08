"""Tests for logslice.comparator."""
import pytest

from logslice.comparator import compare_logs, format_comparison


LINES_A = [
    "2024-01-01 10:00:00 INFO  service started",
    "2024-01-01 10:01:00 ERROR disk full",
    "2024-01-01 10:02:00 INFO  heartbeat ok",
    "2024-01-01 10:02:00 INFO  heartbeat ok",  # duplicate
]

LINES_B = [
    "2024-01-01 10:00:00 INFO  service started",
    "2024-01-01 10:01:00 WARN  memory high",
    "2024-01-01 10:03:00 DEBUG connection pool resized",
]


def test_total_lines_counted():
    report = compare_logs(LINES_A, LINES_B)
    assert report.total_a == 4
    assert report.total_b == 3


def test_unique_lines_counted():
    report = compare_logs(LINES_A, LINES_B)
    assert report.unique_a == 3  # one duplicate removed
    assert report.unique_b == 3


def test_only_in_a_excludes_shared_lines():
    report = compare_logs(LINES_A, LINES_B)
    assert all(line not in LINES_B for line in report.only_in_a)


def test_only_in_b_excludes_shared_lines():
    report = compare_logs(LINES_A, LINES_B)
    assert all(line not in LINES_A for line in report.only_in_b)


def test_common_lines_present_in_both():
    report = compare_logs(LINES_A, LINES_B)
    assert len(report.common) >= 1
    for line in report.common:
        assert line in LINES_A
        assert line in LINES_B


def test_empty_inputs_return_zeros():
    report = compare_logs([], [])
    assert report.total_a == 0
    assert report.total_b == 0
    assert report.only_in_a == []
    assert report.only_in_b == []
    assert report.common == []


def test_identical_inputs_have_no_exclusive_lines():
    report = compare_logs(LINES_A, LINES_A)
    assert report.only_in_a == []
    assert report.only_in_b == []


def test_levels_a_counts_error():
    report = compare_logs(LINES_A, LINES_B)
    assert report.levels_a.get("ERROR", 0) >= 1


def test_levels_b_counts_warn():
    report = compare_logs(LINES_A, LINES_B)
    assert report.levels_b.get("WARN", 0) >= 1


def test_format_comparison_returns_string():
    report = compare_logs(LINES_A, LINES_B)
    output = format_comparison(report)
    assert isinstance(output, str)
    assert "Source A" in output
    assert "Source B" in output


def test_format_comparison_includes_level_section():
    report = compare_logs(LINES_A, LINES_B)
    output = format_comparison(report)
    assert "Level distribution" in output


def test_format_comparison_shows_only_in_counts():
    report = compare_logs(LINES_A, LINES_B)
    output = format_comparison(report)
    assert "Only in A" in output
    assert "Only in B" in output
