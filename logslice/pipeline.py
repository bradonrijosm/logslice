"""Pipeline orchestration for logslice processing steps."""

from typing import List, Optional, Dict, Any

from logslice.filter import filter_lines
from logslice.deduplicator import deduplicate_lines
from logslice.truncator import truncate_and_cap
from logslice.highlighter import highlight_lines
from logslice.context import extract_context, find_match_indices
from logslice.stats import compute_stats


def run_pipeline(
    lines: List[str],
    *,
    level: Optional[str] = None,
    pattern: Optional[str] = None,
    deduplicate: bool = False,
    dedup_consecutive: bool = False,
    max_length: Optional[int] = None,
    cap: Optional[int] = None,
    keywords: Optional[List[str]] = None,
    case_sensitive: bool = False,
    before_context: int = 0,
    after_context: int = 0,
    include_stats: bool = False,
) -> Dict[str, Any]:
    """Run the full processing pipeline on a list of log lines.

    Returns a dict with:
      - 'lines': the processed lines
      - 'stats': optional statistics dict (empty if include_stats=False)
    """
    result = list(lines)

    # Filter by level and/or pattern
    if level or pattern:
        result = filter_lines(result, level=level, pattern=pattern)

    # Context extraction (operates on filtered set)
    if before_context > 0 or after_context > 0:
        match_indices = find_match_indices(result, pattern or "")
        result = extract_context(
            result,
            match_indices,
            before=before_context,
            after=after_context,
        )

    # Deduplication
    if deduplicate or dedup_consecutive:
        mode = "consecutive" if dedup_consecutive else "global"
        result = deduplicate_lines(result, mode=mode)

    # Truncation / capping
    if max_length is not None or cap is not None:
        result = truncate_and_cap(
            result,
            max_length=max_length or 0,
            limit=cap or 0,
        )

    # Keyword highlighting
    if keywords:
        result = highlight_lines(result, keywords, case_sensitive=case_sensitive)

    stats: Dict[str, Any] = {}
    if include_stats:
        # Compute stats on un-highlighted lines to avoid ANSI noise
        stats = compute_stats(lines if not keywords else result)

    return {"lines": result, "stats": stats}
