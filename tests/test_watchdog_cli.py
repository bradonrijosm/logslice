"""Tests for logslice.watchdog_cli."""

from __future__ import annotations

import threading
import time
from io import StringIO
from pathlib import Path

import pytest

from logslice.watchdog_cli import build_watchdog_parser, cmd_watch


@pytest.fixture()
def log_file(tmp_path):
    p = tmp_path / "app.log"
    p.write_text("")
    return p


def _ns(file, pattern=None, level=None, max_lines=None, poll=0.05):
    """Build a minimal Namespace for cmd_watch."""
    import argparse
    return argparse.Namespace(
        file=str(file),
        pattern=pattern,
        level=level,
        max_lines=max_lines,
        poll=poll,
    )


# ---------------------------------------------------------------------------
# build_watchdog_parser
# ---------------------------------------------------------------------------

class TestBuildWatchdogParser:
    def test_returns_argument_parser(self):
        import argparse
        assert isinstance(build_watchdog_parser(), argparse.ArgumentParser)

    def test_default_poll_is_half_second(self):
        p = build_watchdog_parser()
        args = p.parse_args(["some.log"])
        assert args.poll == 0.5

    def test_default_max_lines_is_none(self):
        p = build_watchdog_parser()
        args = p.parse_args(["some.log"])
        assert args.max_lines is None

    def test_pattern_flag_stored(self):
        p = build_watchdog_parser()
        args = p.parse_args(["some.log", "--pattern", "ERROR"])
        assert args.pattern == "ERROR"


# ---------------------------------------------------------------------------
# cmd_watch
# ---------------------------------------------------------------------------

class TestCmdWatch:
    def test_returns_one_for_missing_file(self, tmp_path):
        ns = _ns(tmp_path / "nope.log")
        assert cmd_watch(ns) == 1

    def test_collects_max_lines_then_returns(self, log_file):
        def _write():
            time.sleep(0.05)
            with log_file.open("a") as fh:
                for i in range(5):
                    fh.write(f"line{i}\n")
        threading.Thread(target=_write, daemon=True).start()

        out = StringIO()
        ns = _ns(log_file, max_lines=3, poll=0.04)
        rc = cmd_watch(ns, out=out)
        assert rc == 0
        assert out.getvalue().count("\n") == 3

    def test_level_filter_applied(self, log_file):
        def _write():
            time.sleep(0.05)
            with log_file.open("a") as fh:
                fh.write("ERROR: bad\n")
                fh.write("INFO: good\n")
                fh.write("ERROR: worse\n")
        threading.Thread(target=_write, daemon=True).start()

        out = StringIO()
        ns = _ns(log_file, level="ERROR", max_lines=2, poll=0.04)
        cmd_watch(ns, out=out)
        output = out.getvalue()
        assert "INFO" not in output
        assert output.count("ERROR") == 2

    def test_pattern_filter_applied(self, log_file):
        def _write():
            time.sleep(0.05)
            with log_file.open("a") as fh:
                fh.write("timeout reached\n")
                fh.write("connection ok\n")
                fh.write("timeout again\n")
        threading.Thread(target=_write, daemon=True).start()

        out = StringIO()
        ns = _ns(log_file, pattern="timeout", max_lines=2, poll=0.04)
        cmd_watch(ns, out=out)
        lines = [l for l in out.getvalue().splitlines() if l]
        assert all("timeout" in l for l in lines)
