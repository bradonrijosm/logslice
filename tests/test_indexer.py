"""Tests for logslice.indexer."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from logslice.indexer import (
    IndexEntry,
    LogIndex,
    build_index,
    iter_from_offset,
    load_index,
    save_index,
)

LINES = [
    "2024-01-01 00:00:01 INFO  starting",
    "2024-01-01 00:00:02 DEBUG loop",
    "2024-01-01 00:00:03 ERROR boom",
    "no-timestamp line",
    "2024-01-01 00:00:05 INFO  done",
]


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    p = tmp_path / "app.log"
    p.write_text("\n".join(LINES) + "\n")
    return p


class TestBuildIndex:
    def test_returns_log_index(self, log_file: Path) -> None:
        idx = build_index(log_file)
        assert isinstance(idx, LogIndex)

    def test_entry_count_equals_line_count(self, log_file: Path) -> None:
        idx = build_index(log_file)
        assert len(idx) == len(LINES)

    def test_every_nth_reduces_entries(self, log_file: Path) -> None:
        idx = build_index(log_file, every_nth=2)
        assert len(idx) == len(LINES) // 2

    def test_first_entry_offset_is_zero(self, log_file: Path) -> None:
        idx = build_index(log_file)
        assert idx.entries[0].offset == 0

    def test_offsets_are_strictly_increasing(self, log_file: Path) -> None:
        idx = build_index(log_file)
        offsets = [e.offset for e in idx.entries]
        assert offsets == sorted(offsets)
        assert len(set(offsets)) == len(offsets)

    def test_timestamps_extracted(self, log_file: Path) -> None:
        idx = build_index(log_file)
        ts_values = [e.timestamp for e in idx.entries if e.timestamp]
        assert len(ts_values) >= 4

    def test_no_timestamp_line_has_none(self, log_file: Path) -> None:
        idx = build_index(log_file)
        no_ts = [e for e in idx.entries if e.timestamp is None]
        assert len(no_ts) == 1


class TestLogIndexFindOffset:
    def test_finds_exact_timestamp(self, log_file: Path) -> None:
        idx = build_index(log_file)
        offset = idx.find_offset("2024-01-01 00:00:03")
        assert offset >= 0

    def test_returns_minus_one_when_not_found(self, log_file: Path) -> None:
        idx = build_index(log_file)
        assert idx.find_offset("9999-99-99") == -1

    def test_empty_index_returns_minus_one(self) -> None:
        idx = LogIndex()
        assert idx.find_offset("2024-01-01") == -1


class TestSaveAndLoadIndex:
    def test_round_trip(self, log_file: Path, tmp_path: Path) -> None:
        idx = build_index(log_file)
        dest = tmp_path / "app.idx"
        save_index(idx, dest)
        loaded = load_index(dest)
        assert len(loaded) == len(idx)
        assert loaded.entries[0].offset == idx.entries[0].offset

    def test_saved_file_is_valid_json(self, log_file: Path, tmp_path: Path) -> None:
        idx = build_index(log_file)
        dest = tmp_path / "app.idx"
        save_index(idx, dest)
        data = json.loads(dest.read_text())
        assert isinstance(data, list)
        assert "offset" in data[0]


class TestIterFromOffset:
    def test_yields_all_lines_from_zero(self, log_file: Path) -> None:
        lines = list(iter_from_offset(log_file, 0))
        assert lines == LINES

    def test_yields_subset_from_mid_offset(self, log_file: Path) -> None:
        idx = build_index(log_file)
        third_offset = idx.entries[2].offset
        lines = list(iter_from_offset(log_file, third_offset))
        assert lines[0] == LINES[2]
