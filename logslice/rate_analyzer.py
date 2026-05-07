"""Analyze log event rates over time windows."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

from logslice.parser import extract_timestamp


@dataclass
class RateBucket:
    key: str
    count: int
    lines: List[str] = field(default_factory=list)


@dataclass
class RateReport:
    window_seconds: int
    buckets: List[RateBucket]
    peak_bucket: Optional[RateBucket]
    total_lines: int

    @property
    def average_rate(self) -> float:
        if not self.buckets:
            return 0.0
        return self.total_lines / len(self.buckets)


def _bucket_key(ts: float, window: int) -> str:
    """Return a bucket key string for a timestamp and window size."""
    slot = int(ts // window) * window
    from datetime import datetime, timezone
    dt = datetime.fromtimestamp(slot, tz=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def analyze_rate(
    lines: Iterable[str],
    window_seconds: int = 60,
    include_lines: bool = False,
) -> RateReport:
    """Group lines into time buckets and compute event rates."""
    import datetime

    counts: Dict[str, int] = defaultdict(int)
    bucket_lines: Dict[str, List[str]] = defaultdict(list)
    total = 0
    no_ts_key = "(no-timestamp)"

    for line in lines:
        total += 1
        ts = extract_timestamp(line)
        if ts is None:
            key = no_ts_key
        else:
            try:
                dt = datetime.datetime.fromisoformat(ts)
                epoch = dt.timestamp()
                key = _bucket_key(epoch, window_seconds)
            except ValueError:
                key = no_ts_key
        counts[key] += 1
        if include_lines:
            bucket_lines[key].append(line)

    buckets = [
        RateBucket(
            key=k,
            count=v,
            lines=bucket_lines.get(k, []) if include_lines else [],
        )
        for k, v in sorted(counts.items())
    ]
    peak = max(buckets, key=lambda b: b.count) if buckets else None
    return RateReport(
        window_seconds=window_seconds,
        buckets=buckets,
        peak_bucket=peak,
        total_lines=total,
    )


def format_rate_report(report: RateReport) -> str:
    """Return a human-readable rate report string."""
    lines = [
        f"Rate analysis  window={report.window_seconds}s",
        f"Total lines : {report.total_lines}",
        f"Buckets     : {len(report.buckets)}",
        f"Avg rate    : {report.average_rate:.2f} lines/bucket",
    ]
    if report.peak_bucket:
        lines.append(
            f"Peak bucket : {report.peak_bucket.key}  ({report.peak_bucket.count} lines)"
        )
    lines.append("")
    lines.append(f"{'Bucket':<25} {'Count':>8}")
    lines.append("-" * 35)
    for b in report.buckets:
        lines.append(f"{b.key:<25} {b.count:>8}")
    return "\n".join(lines)
