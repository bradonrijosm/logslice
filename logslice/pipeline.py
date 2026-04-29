"""High-level pipeline that wires slicer, filter, deduplicator, and formatter."""

from __future__ import annotations

import sys
from typing import IO, List, Optional

from logslice.slicer import slice_log
from logslice.filter import filter_lines
from logslice.highlighter import highlight_lines
from logslice.deduplicator import deduplicate_lines
from logslice.formatter import format_lines, format_summary, format_no_match


def run_pipeline(
    log_path: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    level: Optional[str] = None,
    pattern: Optional[str] = None,
    keywords: Optional[List[str]] = None,
    deduplicate: bool = False,
    consecutive_only: bool = False,
    line_numbers: bool = False,
    summary: bool = False,
    output: IO[str] = sys.stdout,
) -> int:
    """Execute the full logslice pipeline and write results to *output*.

    Returns the number of lines written.
    """
    # 1. Slice by time range
    sliced = slice_log(log_path, start=start, end=end)

    # 2. Filter by level / pattern
    filtered = filter_lines(
        sliced,
        level=level,
        pattern=pattern,
    )

    # 3. Optional deduplication
    if deduplicate:
        processed = deduplicate_lines(filtered, consecutive_only=consecutive_only)
    else:
        processed = filtered

    # 4. Highlight keywords
    if keywords:
        processed = highlight_lines(processed, keywords=keywords)

    # 5. Collect so we can report summary / no-match
    lines = list(processed)

    if not lines:
        format_no_match(output)
        return 0

    count = format_lines(
        lines,
        output=output,
        line_numbers=line_numbers,
    )

    if summary:
        format_summary(count, output=output)

    return count
