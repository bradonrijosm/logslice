"""Replay log lines at a controlled rate, simulating real-time log streaming."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Generator, Iterable, Optional

from logslice.parser import extract_timestamp


@dataclass
class ReplayEvent:
    """A single replayed log line with timing metadata."""

    line: str
    original_ts: Optional[str]
    elapsed_seconds: float


def replay_lines(
    lines: Iterable[str],
    speed: float = 1.0,
    max_gap: Optional[float] = None,
    on_emit: Optional[Callable[[ReplayEvent], None]] = None,
) -> Generator[ReplayEvent, None, None]:
    """Replay *lines* in timestamp order, sleeping between events.

    Args:
        lines:     Source log lines.
        speed:     Playback multiplier (2.0 = twice as fast, 0.5 = half speed).
        max_gap:   Cap the inter-line sleep to this many seconds (real time).
        on_emit:   Optional callback invoked for every emitted event.

    Yields:
        ReplayEvent for each line as it is "played back".
    """
    if speed <= 0:
        raise ValueError("speed must be a positive number")

    prev_log_ts: Optional[float] = None
    start_wall: float = time.monotonic()
    elapsed: float = 0.0

    for line in lines:
        ts_str = extract_timestamp(line)
        log_ts: Optional[float] = None
        if ts_str is not None:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                log_ts = dt.timestamp()
            except ValueError:
                log_ts = None

        if log_ts is not None and prev_log_ts is not None:
            gap = (log_ts - prev_log_ts) / speed
            if gap > 0:
                if max_gap is not None:
                    gap = min(gap, max_gap)
                time.sleep(gap)

        if log_ts is not None:
            prev_log_ts = log_ts

        elapsed = time.monotonic() - start_wall
        event = ReplayEvent(line=line, original_ts=ts_str, elapsed_seconds=elapsed)
        if on_emit is not None:
            on_emit(event)
        yield event


def collect_replay(
    lines: Iterable[str],
    speed: float = 1.0,
    max_gap: Optional[float] = None,
) -> list[ReplayEvent]:
    """Eagerly collect all replay events (useful for testing without real sleeps)."""
    return list(replay_lines(lines, speed=speed, max_gap=max_gap))
