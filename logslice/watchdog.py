"""watchdog.py — Tail and watch a log file for new lines matching optional criteria."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, Generator, Optional


def _read_new_lines(fh, last_pos: int) -> tuple[list[str], int]:
    """Seek to last_pos, read any new lines, return them and the new position."""
    fh.seek(0, 2)  # end of file
    end_pos = fh.tell()
    if end_pos <= last_pos:
        return [], last_pos
    fh.seek(last_pos)
    new_lines = fh.readlines()
    return [line.rstrip("\n") for line in new_lines], fh.tell()


def tail_file(
    path: str | Path,
    poll_interval: float = 0.5,
    predicate: Optional[Callable[[str], bool]] = None,
    max_lines: Optional[int] = None,
) -> Generator[str, None, None]:
    """Yield new lines appended to *path* in real time.

    Args:
        path: Path to the log file to watch.
        poll_interval: Seconds between filesystem polls.
        predicate: Optional filter; only lines for which predicate(line) is True
            are yielded.
        max_lines: Stop after yielding this many lines (None = run forever).
    """
    path = Path(path)
    yielded = 0

    with path.open("r", errors="replace") as fh:
        # Start at end so we only see new content.
        fh.seek(0, 2)
        last_pos = fh.tell()

        while True:
            new_lines, last_pos = _read_new_lines(fh, last_pos)
            for line in new_lines:
                if predicate is None or predicate(line):
                    yield line
                    yielded += 1
                    if max_lines is not None and yielded >= max_lines:
                        return
            time.sleep(poll_interval)


def watch_and_collect(
    path: str | Path,
    duration: float,
    poll_interval: float = 0.1,
    predicate: Optional[Callable[[str], bool]] = None,
) -> list[str]:
    """Collect lines appended to *path* for *duration* seconds.

    Useful for testing or short-lived monitoring tasks.
    """
    path = Path(path)
    collected: list[str] = []
    deadline = time.monotonic() + duration

    with path.open("r", errors="replace") as fh:
        fh.seek(0, 2)
        last_pos = fh.tell()

        while time.monotonic() < deadline:
            new_lines, last_pos = _read_new_lines(fh, last_pos)
            for line in new_lines:
                if predicate is None or predicate(line):
                    collected.append(line)
            time.sleep(poll_interval)

    return collected
