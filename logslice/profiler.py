"""Profiler: analyse a log file and report activity patterns over time."""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable, Dict, List, Optional

from logslice.parser import extract_timestamp


@dataclass
class ProfileResult:
    bucket_size_seconds: int
    buckets: Dict[str, int] = field(default_factory=dict)  # bucket_label -> count
    total_lines: int = 0
    timestamped_lines: int = 0
    peak_bucket: Optional[str] = None
    peak_count: int = 0


def profile_lines(
    lines: Iterable[str],
    bucket_size_seconds: int = 60,
) -> ProfileResult:
    """Bucket lines by timestamp and count activity per bucket."""
    if bucket_size_seconds <= 0:
        raise ValueError("bucket_size_seconds must be a positive integer")

    counts: Dict[str, int] = defaultdict(int)
    total = 0
    timestamped = 0

    for line in lines:
        total += 1
        ts = extract_timestamp(line)
        if ts is None:
            continue
        timestamped += 1
        epoch = ts.timestamp()
        bucket_index = math.floor(epoch / bucket_size_seconds)
        bucket_label = _label(bucket_index, bucket_size_seconds)
        counts[bucket_label] += 1

    peak_bucket: Optional[str] = None
    peak_count = 0
    if counts:
        peak_bucket = max(counts, key=lambda k: counts[k])
        peak_count = counts[peak_bucket]

    return ProfileResult(
        bucket_size_seconds=bucket_size_seconds,
        buckets=dict(sorted(counts.items())),
        total_lines=total,
        timestamped_lines=timestamped,
        peak_bucket=peak_bucket,
        peak_count=peak_count,
    )


def _label(bucket_index: int, bucket_size_seconds: int) -> str:
    """Return a human-readable label for a bucket."""
    import datetime
    epoch = bucket_index * bucket_size_seconds
    dt = datetime.datetime.utcfromtimestamp(epoch)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_profile(result: ProfileResult, bar_width: int = 40) -> str:
    """Render a ProfileResult as a text histogram."""
    if not result.buckets:
        return "No timestamped lines found — nothing to profile.\n"

    lines: List[str] = [
        f"Profile  (bucket={result.bucket_size_seconds}s  "
        f"total={result.total_lines}  timestamped={result.timestamped_lines})",
        "-" * 72,
    ]
    max_count = result.peak_count or 1
    for label, count in result.buckets.items():
        bar_len = round(count / max_count * bar_width)
        bar = "#" * bar_len
        lines.append(f"{label}  {bar:<{bar_width}}  {count}")
    lines.append("-" * 72)
    lines.append(f"Peak: {result.peak_bucket}  ({result.peak_count} lines)")
    return "\n".join(lines) + "\n"
