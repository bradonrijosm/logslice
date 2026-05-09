"""Tests for logslice.replayer and logslice.replayer_cli."""

from __future__ import annotations

import argparse
import io
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from logslice.replayer import ReplayEvent, collect_replay, replay_lines
from logslice.replayer_cli import build_replayer_parser, cmd_replay


LINES_WITH_TS = [
    "2024-01-01T00:00:00 INFO  server started",
    "2024-01-01T00:00:02 INFO  request received",
    "2024-01-01T00:00:05 ERROR timeout",
]

LINES_NO_TS = [
    "no timestamp here",
    "another plain line",
]


# ---------------------------------------------------------------------------
# collect_replay (no real sleeping — max_gap=0)
# ---------------------------------------------------------------------------

class TestCollectReplay:
    def test_returns_replay_events(self):
        events = collect_replay(LINES_WITH_TS, speed=1.0, max_gap=0)
        assert all(isinstance(e, ReplayEvent) for e in events)

    def test_event_count_matches_line_count(self):
        events = collect_replay(LINES_WITH_TS, speed=1.0, max_gap=0)
        assert len(events) == len(LINES_WITH_TS)

    def test_event_lines_match_input(self):
        events = collect_replay(LINES_WITH_TS, speed=1.0, max_gap=0)
        assert [e.line for e in events] == LINES_WITH_TS

    def test_timestamps_extracted(self):
        events = collect_replay(LINES_WITH_TS, speed=1.0, max_gap=0)
        assert events[0].original_ts is not None
        assert "2024-01-01" in events[0].original_ts

    def test_no_timestamp_lines_have_none(self):
        events = collect_replay(LINES_NO_TS, speed=1.0, max_gap=0)
        assert all(e.original_ts is None for e in events)

    def test_empty_input_returns_empty(self):
        events = collect_replay([], speed=1.0, max_gap=0)
        assert events == []

    def test_invalid_speed_raises(self):
        with pytest.raises(ValueError):
            collect_replay(LINES_WITH_TS, speed=0)

    def test_negative_speed_raises(self):
        with pytest.raises(ValueError):
            collect_replay(LINES_WITH_TS, speed=-1.0)

    def test_on_emit_callback_called_for_each_line(self):
        seen: list[ReplayEvent] = []
        collect_replay(LINES_WITH_TS, speed=1.0, max_gap=0, on_emit=seen.append)
        assert len(seen) == len(LINES_WITH_TS)

    def test_elapsed_seconds_non_negative(self):
        events = collect_replay(LINES_WITH_TS, speed=1.0, max_gap=0)
        assert all(e.elapsed_seconds >= 0 for e in events)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

class TestBuildReplayerParser:
    def test_returns_argument_parser(self):
        assert isinstance(build_replayer_parser(), argparse.ArgumentParser)

    def test_default_speed_is_one(self):
        ns = build_replayer_parser().parse_args(["somefile.log"])
        assert ns.speed == pytest.approx(1.0)

    def test_default_max_gap_is_none(self):
        ns = build_replayer_parser().parse_args(["somefile.log"])
        assert ns.max_gap is None

    def test_default_no_timestamps_is_false(self):
        ns = build_replayer_parser().parse_args(["somefile.log"])
        assert ns.no_timestamps is False


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    p = tmp_path / "sample.log"
    p.write_text("\n".join(LINES_WITH_TS) + "\n", encoding="utf-8")
    return p


def _ns(**kwargs) -> argparse.Namespace:
    defaults = dict(file="", speed=1.0, max_gap=0.0, no_timestamps=False)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestCmdReplay:
    def test_returns_zero_on_success(self, log_file: Path):
        out = io.StringIO()
        rc = cmd_replay(_ns(file=str(log_file), max_gap=0.0), out=out)
        assert rc == 0

    def test_writes_all_lines(self, log_file: Path):
        out = io.StringIO()
        cmd_replay(_ns(file=str(log_file), max_gap=0.0), out=out)
        written = out.getvalue().splitlines()
        assert written == LINES_WITH_TS

    def test_returns_one_for_missing_file(self):
        out = io.StringIO()
        rc = cmd_replay(_ns(file="/no/such/file.log", max_gap=0.0), out=out)
        assert rc == 1

    def test_no_timestamps_flag_emits_all_lines(self, log_file: Path):
        out = io.StringIO()
        rc = cmd_replay(_ns(file=str(log_file), no_timestamps=True, max_gap=0.0), out=out)
        assert rc == 0
        assert len(out.getvalue().splitlines()) == len(LINES_WITH_TS)
