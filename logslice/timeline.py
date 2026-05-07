"""Build a timeline view of log activity bucketed by time interval."""

from __future__ import annotations

from dataclasses import dataclass, field
from collections import defaultdict
from typing import Dict, Iterable, List, Optional

from logslice.parser import extract_timestamp


@dataclass
class TimelineBucket:
    label: str
    count: int = 0
    lines: List[str] = field(default_factory=list)


@dataclass
class Timeline:
    bucket_seconds: int
    buckets: Dict[str, TimelineBucket] = field(default_factory=dict)
    untimed: List[str] = field(default_factory=list)

    def ordered_buckets(self) -> List[TimelineBucket]:
        return [self.buckets[k] for k in sorted(self.buckets)]


def _bucket_label(ts: float, bucket_seconds: int) -> str:
    """Return an ISO-like label for the bucket containing *ts*."""
    import datetime

    origin = int(ts) - (int(ts) % bucket_seconds)
    dt = datetime.datetime.utcfromtimestamp(origin)
    if bucket_seconds < 3600:
        return dt.strftime("%Y-%m-%d %H:%M")
    if bucket_seconds < 86400:
        return dt.strftime("%Y-%m-%d %H:00")
    return dt.strftime("%Y-%m-%d")


def build_timeline(
    lines: Iterable[str],
    bucket_seconds: int = 60,
    keep_lines: bool = False,
) -> Timeline:
    """Iterate *lines* and group them into time buckets.

    Args:
        lines: Iterable of raw log lines.
        bucket_seconds: Width of each bucket in seconds (default 60).
        keep_lines: If True, store the original lines in each bucket.

    Returns:
        A :class:`Timeline` instance.
    """
    if bucket_seconds < 1:
        raise ValueError("bucket_seconds must be >= 1")

    tl = Timeline(bucket_seconds=bucket_seconds)
    for line in lines:
        ts = extract_timestamp(line)
        if ts is None:
            tl.untimed.append(line)
            continue
        label = _bucket_label(ts.timestamp(), bucket_seconds)
        if label not in tl.buckets:
            tl.buckets[label] = TimelineBucket(label=label)
        bucket = tl.buckets[label]
        bucket.count += 1
        if keep_lines:
            bucket.lines.append(line)
    return tl


def format_timeline(tl: Timeline, bar_width: int = 40) -> str:
    """Render a simple ASCII bar chart of the timeline."""
    buckets = tl.ordered_buckets()
    if not buckets:
        return "(no timestamped lines)"
    max_count = max(b.count for b in buckets) or 1
    rows: List[str] = []
    for b in buckets:
        filled = round(b.count / max_count * bar_width)
        bar = "#" * filled + "-" * (bar_width - filled)
        rows.append(f"{b.label}  [{bar}] {b.count}")
    if tl.untimed:
        rows.append(f"(untimed)  {len(tl.untimed)} line(s)")
    return "\n".join(rows)
