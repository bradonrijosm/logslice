"""Tests for logslice.watchdog."""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from logslice.watchdog import watch_and_collect, _read_new_lines


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _append_after(path: Path, lines: list[str], delay: float = 0.05) -> None:
    """Write *lines* to *path* after *delay* seconds (runs in a thread)."""
    def _write():
        time.sleep(delay)
        with path.open("a") as fh:
            for line in lines:
                fh.write(line + "\n")
    t = threading.Thread(target=_write, daemon=True)
    t.start()


@pytest.fixture()
def log_file(tmp_path):
    p = tmp_path / "watch.log"
    p.write_text("")  # create empty file
    return p


# ---------------------------------------------------------------------------
# _read_new_lines unit tests
# ---------------------------------------------------------------------------

class TestReadNewLines:
    def test_empty_file_returns_empty(self, log_file):
        with log_file.open("r") as fh:
            lines, pos = _read_new_lines(fh, 0)
        assert lines == []
        assert pos == 0

    def test_detects_appended_content(self, log_file):
        log_file.write_text("line1\nline2\n")
        with log_file.open("r") as fh:
            lines, pos = _read_new_lines(fh, 0)
        assert lines == ["line1", "line2"]
        assert pos > 0

    def test_does_not_re_read_old_content(self, log_file):
        log_file.write_text("old\n")
        with log_file.open("r") as fh:
            _, pos = _read_new_lines(fh, 0)
            log_file.open("a").write("new\n")
            lines, _ = _read_new_lines(fh, pos)
        assert lines == ["new"]


# ---------------------------------------------------------------------------
# watch_and_collect integration tests
# ---------------------------------------------------------------------------

class TestWatchAndCollect:
    def test_collects_appended_lines(self, log_file):
        _append_after(log_file, ["hello", "world"], delay=0.05)
        result = watch_and_collect(log_file, duration=0.4, poll_interval=0.05)
        assert "hello" in result
        assert "world" in result

    def test_predicate_filters_lines(self, log_file):
        _append_after(log_file, ["ERROR: boom", "INFO: ok"], delay=0.05)
        result = watch_and_collect(
            log_file,
            duration=0.4,
            poll_interval=0.05,
            predicate=lambda l: "ERROR" in l,
        )
        assert any("ERROR" in l for l in result)
        assert all("INFO" not in l for l in result)

    def test_empty_file_no_writes_returns_empty(self, log_file):
        result = watch_and_collect(log_file, duration=0.15, poll_interval=0.05)
        assert result == []

    def test_multiple_appends_all_collected(self, log_file):
        def _write():
            time.sleep(0.05)
            with log_file.open("a") as fh:
                fh.write("a\n")
            time.sleep(0.05)
            with log_file.open("a") as fh:
                fh.write("b\n")
        threading.Thread(target=_write, daemon=True).start()
        result = watch_and_collect(log_file, duration=0.5, poll_interval=0.04)
        assert "a" in result
        assert "b" in result
