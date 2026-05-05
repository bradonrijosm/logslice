"""Tests for logslice.splitter."""

import os
import pytest

from logslice.splitter import (
    _chunk_path,
    split_by_lines,
    split_by_time,
    write_chunks,
)

LINES_TS = [
    "2024-01-01 00:00:00 INFO  alpha\n",
    "2024-01-01 00:00:30 INFO  beta\n",
    "2024-01-01 00:01:10 INFO  gamma\n",
    "2024-01-01 00:01:45 INFO  delta\n",
    "2024-01-01 00:03:05 INFO  epsilon\n",
]


# ---------------------------------------------------------------------------
# _chunk_path
# ---------------------------------------------------------------------------

def test_chunk_path_uses_index():
    assert _chunk_path("/tmp/out.log", 0) == "/tmp/out_000.log"
    assert _chunk_path("/tmp/out.log", 7) == "/tmp/out_007.log"


def test_chunk_path_no_extension_adds_log():
    assert _chunk_path("/tmp/out", 1) == "/tmp/out_001.log"


# ---------------------------------------------------------------------------
# split_by_lines
# ---------------------------------------------------------------------------

def test_split_by_lines_exact_multiple():
    lines = ["a\n", "b\n", "c\n", "d\n"]
    chunks = list(split_by_lines(lines, 2))
    assert chunks == [["a\n", "b\n"], ["c\n", "d\n"]]


def test_split_by_lines_remainder():
    lines = ["a\n", "b\n", "c\n"]
    chunks = list(split_by_lines(lines, 2))
    assert len(chunks) == 2
    assert chunks[-1] == ["c\n"]


def test_split_by_lines_empty_input():
    assert list(split_by_lines([], 10)) == []


def test_split_by_lines_invalid_chunk_size():
    with pytest.raises(ValueError):
        list(split_by_lines(["x\n"], 0))


# ---------------------------------------------------------------------------
# split_by_time
# ---------------------------------------------------------------------------

def test_split_by_time_groups_within_window():
    # window of 90 s: lines 0+1 share window; line 2 starts new; etc.
    chunks = list(split_by_time(LINES_TS, window_seconds=90))
    assert len(chunks) == 3
    assert LINES_TS[0] in chunks[0]
    assert LINES_TS[1] in chunks[0]


def test_split_by_time_single_chunk_wide_window():
    chunks = list(split_by_time(LINES_TS, window_seconds=3600))
    assert len(chunks) == 1
    assert len(chunks[0]) == len(LINES_TS)


def test_split_by_time_no_timestamp_lines_appended_to_current_chunk():
    lines = [
        "2024-01-01 00:00:00 INFO start\n",
        "no timestamp here\n",
        "2024-01-01 01:00:00 INFO end\n",
    ]
    chunks = list(split_by_time(lines, window_seconds=60))
    assert lines[1] in chunks[0]


def test_split_by_time_invalid_window():
    with pytest.raises(ValueError):
        list(split_by_time(LINES_TS, window_seconds=0))


# ---------------------------------------------------------------------------
# write_chunks
# ---------------------------------------------------------------------------

def test_write_chunks_creates_files(tmp_path):
    base = str(tmp_path / "chunk.log")
    chunks_iter = split_by_lines(["a\n", "b\n", "c\n"], 2)
    paths = write_chunks(chunks_iter, base)
    assert len(paths) == 2
    for p in paths:
        assert os.path.exists(p)


def test_write_chunks_content_correct(tmp_path):
    base = str(tmp_path / "out.log")
    paths = write_chunks(iter([["hello\n", "world\n"]]), base)
    with open(paths[0]) as fh:
        assert fh.read() == "hello\nworld\n"
