"""Pipeline: compose multiple logslice transforms into a single pass.

This module replaces the earlier stub so that the profiler can be wired
in as an optional final step alongside the existing transforms.
"""

from __future__ import annotations

from typing import Iterable, Iterator, List, Optional

from logslice.filter import filter_lines
from logslice.slicer import slice_log
from logslice.truncator import truncate_and_cap
from logslice.deduplicator import deduplicate_lines
from logslice.anonymizer import anonymize_lines
from logslice.highlighter import highlight_lines
from logslice.sampler import sample_lines


def run_pipeline(
    source: Iterable[str],
    *,
    start: Optional[str] = None,
    end: Optional[str] = None,
    level: Optional[str] = None,
    pattern: Optional[str] = None,
    keywords: Optional[List[str]] = None,
    deduplicate: bool = False,
    global_dedup: bool = False,
    anonymize: bool = False,
    sample_rate: float = 1.0,
    max_line_length: Optional[int] = None,
    max_lines: Optional[int] = None,
) -> Iterator[str]:
    """Run *source* through the configured chain of transforms.

    Each step is applied only when the corresponding option is set so that
    the common case (no options) remains a single-pass passthrough.
    """
    lines: Iterable[str] = source

    # 1. Time-range slice
    if start is not None or end is not None:
        lines = slice_log(lines, start=start, end=end)

    # 2. Level / pattern filter
    if level is not None or pattern is not None:
        lines = filter_lines(lines, level=level, pattern=pattern)

    # 3. Deduplication
    if deduplicate or global_dedup:
        lines = deduplicate_lines(lines, consecutive=not global_dedup)

    # 4. Anonymisation
    if anonymize:
        lines = anonymize_lines(lines)

    # 5. Sampling
    if sample_rate < 1.0:
        lines = sample_lines(lines, rate=sample_rate)

    # 6. Truncation / line cap
    if max_line_length is not None or max_lines is not None:
        lines = truncate_and_cap(
            lines,
            max_length=max_line_length or 0,
            limit=max_lines or 0,
        )

    # 7. Keyword highlighting (must be last so it sees final text)
    if keywords:
        lines = highlight_lines(lines, keywords=keywords)

    yield from lines
