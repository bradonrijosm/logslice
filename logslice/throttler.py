"""throttler.py – rate-limit log lines by capping output per time bucket.

Public API
----------
bucket_lines(lines, bucket_seconds, max_per_bucket)
    Yield at most *max_per_bucket* lines whose timestamp falls inside each
    fixed-width time bucket of *bucket_seconds* seconds.  Lines without a
    parseable timestamp are always passed through unchanged.

count_throttled(lines, bucket_seconds, max_per_bucket)
    Return (kept, dropped) counts without writing any output.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Iterable, Iterator, Tuple

from logslice.parser import extract_timestamp


def _bucket_key(ts_seconds: float, bucket_seconds: int) -> int:
    """Map a POSIX timestamp to an integer bucket index."""
    return math.floor(ts_seconds / bucket_seconds)


def bucket_lines(
    lines: Iterable[str],
    bucket_seconds: int = 60,
    max_per_bucket: int = 100,
) -> Iterator[str]:
    """Yield lines, dropping those that exceed *max_per_bucket* per bucket.

    Lines whose timestamp cannot be parsed are always yielded (they are
    treated as bucket-agnostic).
    """
    if bucket_seconds <= 0:
        raise ValueError("bucket_seconds must be a positive integer")
    if max_per_bucket <= 0:
        raise ValueError("max_per_bucket must be a positive integer")

    counts: dict[int, int] = defaultdict(int)

    for line in lines:
        ts = extract_timestamp(line)
        if ts is None:
            yield line
            continue
        key = _bucket_key(ts.timestamp(), bucket_seconds)
        if counts[key] < max_per_bucket:
            counts[key] += 1
            yield line
        # else: silently drop the line


def count_throttled(
    lines: Iterable[str],
    bucket_seconds: int = 60,
    max_per_bucket: int = 100,
) -> Tuple[int, int]:
    """Return ``(kept, dropped)`` line counts without producing output."""
    kept = 0
    dropped = 0
    for line in bucket_lines(lines, bucket_seconds, max_per_bucket):
        kept += 1
    # We need a second pass to get dropped; use a counting wrapper instead.
    # Re-implement inline to avoid consuming the iterator twice.
    kept = 0
    dropped = 0
    if bucket_seconds <= 0 or max_per_bucket <= 0:
        raise ValueError("bucket_seconds and max_per_bucket must be positive")
    counts: dict[int, int] = defaultdict(int)
    for line in lines:
        ts = extract_timestamp(line)
        if ts is None:
            kept += 1
            continue
        key = _bucket_key(ts.timestamp(), bucket_seconds)
        if counts[key] < max_per_bucket:
            counts[key] += 1
            kept += 1
        else:
            dropped += 1
    return kept, dropped
