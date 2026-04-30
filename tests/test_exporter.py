"""Tests for logslice.exporter."""

import csv
import io
import json

import pytest

from logslice.exporter import (
    export_as_csv,
    export_as_json,
    export_as_text,
    export_lines,
)

SAMPLE = [
    "2024-01-01 00:00:01 INFO  server started",
    "2024-01-01 00:00:02 ERROR disk full",
    "2024-01-01 00:00:03 WARN  high memory",
]


class TestExportAsText:
    def test_joins_lines_with_newline(self):
        result = export_as_text(SAMPLE)
        assert result == "\n".join(SAMPLE)

    def test_empty_input_returns_empty_string(self):
        assert export_as_text([]) == ""

    def test_custom_separator(self):
        result = export_as_text(["a", "b"], separator="|")
        assert result == "a|b"


class TestExportAsJson:
    def test_contains_lines_key(self):
        data = json.loads(export_as_json(SAMPLE))
        assert data["lines"] == SAMPLE

    def test_count_matches_input(self):
        data = json.loads(export_as_json(SAMPLE))
        assert data["count"] == len(SAMPLE)

    def test_empty_input(self):
        data = json.loads(export_as_json([]))
        assert data["lines"] == []
        assert data["count"] == 0

    def test_metadata_embedded_when_provided(self):
        meta = {"source": "app.log", "host": "web01"}
        data = json.loads(export_as_json(SAMPLE, metadata=meta))
        assert data["metadata"] == meta

    def test_no_metadata_key_when_omitted(self):
        data = json.loads(export_as_json(SAMPLE))
        assert "metadata" not in data


class TestExportAsCsv:
    def _parse(self, text: str) -> list:
        return list(csv.DictReader(io.StringIO(text)))

    def test_row_count_matches_input(self):
        rows = self._parse(export_as_csv(SAMPLE))
        assert len(rows) == len(SAMPLE)

    def test_index_column_present_by_default(self):
        rows = self._parse(export_as_csv(SAMPLE))
        assert "index" in rows[0]

    def test_index_starts_at_one(self):
        rows = self._parse(export_as_csv(SAMPLE))
        assert rows[0]["index"] == "1"

    def test_no_index_column_when_disabled(self):
        rows = self._parse(export_as_csv(SAMPLE, index_column=False))
        assert "index" not in rows[0]

    def test_line_content_preserved(self):
        rows = self._parse(export_as_csv(SAMPLE))
        assert rows[1]["line"] == SAMPLE[1]

    def test_empty_input_yields_header_only(self):
        rows = self._parse(export_as_csv([]))
        assert rows == []


class TestExportLines:
    def test_text_format_dispatches_correctly(self):
        assert export_lines(SAMPLE, fmt="text") == export_as_text(SAMPLE)

    def test_json_format_dispatches_correctly(self):
        assert export_lines(SAMPLE, fmt="json") == export_as_json(SAMPLE)

    def test_csv_format_dispatches_correctly(self):
        assert export_lines(SAMPLE, fmt="csv") == export_as_csv(SAMPLE)

    def test_case_insensitive_format_arg(self):
        result = export_lines(SAMPLE, fmt="JSON")
        data = json.loads(result)
        assert data["count"] == len(SAMPLE)

    def test_unsupported_format_raises_value_error(self):
        with pytest.raises(ValueError, match="Unsupported export format"):
            export_lines(SAMPLE, fmt="xml")

    def test_metadata_forwarded_to_json(self):
        meta = {"env": "prod"}
        data = json.loads(export_lines(SAMPLE, fmt="json", metadata=meta))
        assert data["metadata"] == meta
