"""Orchestrates the full logslice processing pipeline."""

from __future__ import annotations

from typing import IO, List, Optional

from logslice.context import extract_context, find_match_indices
from logslice.deduplicator import deduplicate_lines
from logslice.filter import filter_lines
from logslice.formatter import format_lines, format_no_match, format_summary
from logslice.highlighter import highlight_lines
from logslice.sampler import sample_lines
from logslice.slicer import slice_log
from logslice.sorter import sort_by_timestamp
from logslice.stats import compute_stats, format_stats
from logslice.truncator import truncate_and_cap


def run_pipeline(
    source: IO[str],
    out: IO[str],
    *,
    start: Optional[str] = None,
    end: Optional[str] = None,
    level: Optional[str] = None,
    pattern: Optional[str] = None,
    keywords: Optional[List[str]] = None,
    deduplicate: bool = False,
    dedup_consecutive: bool = False,
    sample_rate: float = 1.0,
    sort: bool = False,
    reverse_sort: bool = False,
    before_context: int = 0,
    after_context: int = 0,
    line_numbers: bool = False,
    max_line_length: Optional[int] = None,
    max_lines: Optional[int] = None,
    show_stats: bool = False,
    bookmark_start: Optional[str] = None,
    bookmark_end: Optional[str] = None,
) -> int:
    """Run all pipeline stages and write results to *out*. Returns matched line count."""

    effective_start = bookmark_start or start
    effective_end = bookmark_end or end

    lines: List[str] = list(slice_log(source, start=effective_start, end=effective_end))

    lines = filter_lines(lines, level=level, pattern=pattern)

    if deduplicate or dedup_consecutive:
        lines = deduplicate_lines(lines, consecutive=dedup_consecutive)

    if sample_rate < 1.0:
        lines = list(sample_lines(lines, rate=sample_rate))

    if sort or reverse_sort:
        lines = sort_by_timestamp(lines, reverse=reverse_sort)

    if before_context or after_context:
        match_indices = find_match_indices(lines, pattern or "")
        lines = extract_context(lines, match_indices, before=before_context, after=after_context)

    if max_line_length or max_lines:
        lines = truncate_and_cap(
            lines,
            max_length=max_line_length or 0,
            max_lines=max_lines or 0,
        )

    if not lines:
        out.write(format_no_match() + "\n")
        return 0

    if keywords:
        lines = highlight_lines(lines, keywords)

    count = format_lines(lines, out, line_numbers=line_numbers)

    if show_stats:
        stats = compute_stats(lines)
        out.write("\n" + format_stats(stats) + "\n")

    out.write(format_summary(count) + "\n")
    return count
