"""Tests for logslice.annotator."""
from __future__ import annotations

import pytest

from logslice.annotator import AnnotatedLine, annotate_lines, format_annotated


LINES_WITH_TS = [
    "2024-01-01 00:00:00 INFO  server started",
    "2024-01-01 00:00:05 DEBUG request received",
    "2024-01-01 00:00:10 ERROR something failed",
]

LINES_NO_TS = [
    "no timestamp here",
    "another plain line",
]


class TestAnnotateLines:
    def test_yields_annotated_line_objects(self):
        results = list(annotate_lines(LINES_WITH_TS))
        assert all(isinstance(r, AnnotatedLine) for r in results)

    def test_line_numbers_start_at_one_by_default(self):
        results = list(annotate_lines(LINES_WITH_TS))
        assert [r.line_number for r in results] == [1, 2, 3]

    def test_custom_start_lineno(self):
        results = list(annotate_lines(LINES_WITH_TS, start_lineno=10))
        assert results[0].line_number == 10
        assert results[-1].line_number == 12

    def test_source_tag_propagated(self):
        results = list(annotate_lines(LINES_WITH_TS, source_tag="app"))
        assert all(r.source_tag == "app" for r in results)

    def test_no_source_tag_is_none(self):
        results = list(annotate_lines(LINES_WITH_TS))
        assert all(r.source_tag is None for r in results)

    def test_first_timestamped_line_has_zero_offset(self):
        results = list(annotate_lines(LINES_WITH_TS))
        assert results[0].offset_seconds == pytest.approx(0.0)

    def test_offset_increases_for_later_lines(self):
        results = list(annotate_lines(LINES_WITH_TS))
        assert results[1].offset_seconds == pytest.approx(5.0)
        assert results[2].offset_seconds == pytest.approx(10.0)

    def test_lines_without_timestamp_have_none_offset(self):
        results = list(annotate_lines(LINES_NO_TS))
        assert all(r.offset_seconds is None for r in results)

    def test_empty_input_yields_nothing(self):
        assert list(annotate_lines([])) == []

    def test_original_text_preserved(self):
        results = list(annotate_lines(LINES_WITH_TS))
        assert results[0].original == LINES_WITH_TS[0]


class TestAnnotatedLineRender:
    def _al(self, **kwargs):
        defaults = dict(original="hello", line_number=1, source_tag="svc", offset_seconds=3.5)
        defaults.update(kwargs)
        return AnnotatedLine(**defaults)

    def test_render_contains_original(self):
        assert "hello" in self._al().render()

    def test_render_contains_line_number(self):
        assert "[1]" in self._al().render()

    def test_render_contains_tag(self):
        assert "<svc>" in self._al().render()

    def test_render_contains_offset(self):
        assert "+3.5s" in self._al().render()

    def test_render_no_lineno(self):
        rendered = self._al().render(show_lineno=False)
        assert "[1]" not in rendered

    def test_render_no_tag(self):
        rendered = self._al().render(show_tag=False)
        assert "<svc>" not in rendered

    def test_render_no_offset(self):
        rendered = self._al().render(show_offset=False)
        assert "+3.5s" not in rendered

    def test_render_none_offset_omitted(self):
        rendered = self._al(offset_seconds=None).render()
        assert "+" not in rendered

    def test_render_none_tag_omitted(self):
        rendered = self._al(source_tag=None).render()
        assert "<" not in rendered


class TestFormatAnnotated:
    def test_yields_strings(self):
        results = list(format_annotated(LINES_WITH_TS))
        assert all(isinstance(r, str) for r in results)

    def test_count_matches_input(self):
        results = list(format_annotated(LINES_WITH_TS))
        assert len(results) == len(LINES_WITH_TS)

    def test_empty_input_yields_nothing(self):
        assert list(format_annotated([])) == []
