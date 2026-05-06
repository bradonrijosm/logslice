"""Tests for logslice.rotator."""

from __future__ import annotations

import gzip
import os
import pytest

from logslice.rotator import (
    RotationState,
    find_rotated_files,
    get_rotation_state,
    has_rotated,
    iter_with_rotation,
)


# ---------------------------------------------------------------------------
# get_rotation_state
# ---------------------------------------------------------------------------

def test_get_rotation_state_returns_none_for_missing_file(tmp_path):
    state = get_rotation_state(str(tmp_path / "no_such.log"))
    assert state is None


def test_get_rotation_state_captures_inode_and_size(tmp_path):
    p = tmp_path / "app.log"
    p.write_text("hello\n")
    state = get_rotation_state(str(p))
    assert isinstance(state, RotationState)
    assert state.inode == p.stat().st_ino
    assert state.size == p.stat().st_size


# ---------------------------------------------------------------------------
# has_rotated
# ---------------------------------------------------------------------------

def test_has_rotated_false_when_unchanged(tmp_path):
    p = tmp_path / "app.log"
    p.write_text("line\n")
    state = get_rotation_state(str(p))
    assert not has_rotated(state, str(p))


def test_has_rotated_true_when_file_shrinks(tmp_path):
    p = tmp_path / "app.log"
    p.write_text("some long content here\n")
    state = get_rotation_state(str(p))
    p.write_text("x\n")  # smaller
    assert has_rotated(state, str(p))


def test_has_rotated_true_when_file_missing(tmp_path):
    p = tmp_path / "app.log"
    p.write_text("data\n")
    state = get_rotation_state(str(p))
    p.unlink()
    assert has_rotated(state, str(p))


# ---------------------------------------------------------------------------
# find_rotated_files
# ---------------------------------------------------------------------------

def test_find_rotated_files_empty_when_none_exist(tmp_path):
    base = str(tmp_path / "app.log")
    assert find_rotated_files(base) == []


def test_find_rotated_files_returns_existing_indices(tmp_path):
    base = tmp_path / "app.log"
    (tmp_path / "app.log.1").write_text("old\n")
    (tmp_path / "app.log.2").write_text("older\n")
    result = find_rotated_files(str(base))
    assert len(result) == 2
    # oldest first (highest index first)
    assert result[0].endswith(".2")
    assert result[1].endswith(".1")


def test_find_rotated_files_respects_max_count(tmp_path):
    base = tmp_path / "app.log"
    for i in range(1, 6):
        (tmp_path / f"app.log.{i}").write_text(f"entry {i}\n")
    result = find_rotated_files(str(base), max_count=3)
    assert len(result) == 3


# ---------------------------------------------------------------------------
# iter_with_rotation
# ---------------------------------------------------------------------------

def test_iter_with_rotation_yields_live_lines(tmp_path):
    p = tmp_path / "app.log"
    p.write_text("line1\nline2\n")
    lines = list(iter_with_rotation(str(p), include_rotated=False))
    assert lines == ["line1", "line2"]


def test_iter_with_rotation_includes_rotated_plain(tmp_path):
    base = tmp_path / "app.log"
    (tmp_path / "app.log.1").write_text("archived\n")
    base.write_text("live\n")
    lines = list(iter_with_rotation(str(base)))
    assert lines[0] == "archived"
    assert lines[-1] == "live"


def test_iter_with_rotation_includes_gz_rotated(tmp_path):
    base = tmp_path / "app.log"
    gz_path = tmp_path / "app.log.1.gz"
    with gzip.open(str(gz_path), "wt") as fh:
        fh.write("compressed\n")
    base.write_text("current\n")
    lines = list(iter_with_rotation(str(base)))
    assert "compressed" in lines
    assert "current" in lines


def test_iter_with_rotation_skips_missing_live_file(tmp_path):
    path = str(tmp_path / "ghost.log")
    lines = list(iter_with_rotation(path, include_rotated=False))
    assert lines == []
