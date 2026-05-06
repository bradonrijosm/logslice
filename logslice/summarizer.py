"""Summarize log content into a condensed human-readable report."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence

from logslice.stats import compute_stats, _count_levels
from logslice.parser import extract_timestamp


@dataclass
class SummaryReport:
    total_lines: int
    unique_lines: int
    duplicate_lines: int
    level_counts: Dict[str, int]
    first_timestamp: str | None
    last_timestamp: str | None
    top_lines: List[str] = field(default_factory=list)


def summarize_lines(
    lines: Sequence[str],
    top_n: int = 5,
) -> SummaryReport:
    """Produce a SummaryReport from a sequence of log lines."""
    stats = compute_stats(lines)
    level_counts = _count_levels(lines)

    first_ts: str | None = None
    last_ts: str | None = None
    for line in lines:
        ts = extract_timestamp(line)
        if ts is not None:
            if first_ts is None:
                first_ts = ts
            last_ts = ts

    from collections import Counter
    counts = Counter(lines)
    top_lines = [line for line, _ in counts.most_common(top_n)]

    return SummaryReport(
        total_lines=stats["total"],
        unique_lines=stats["unique"],
        duplicate_lines=stats["duplicates"],
        level_counts=level_counts,
        first_timestamp=first_ts,
        last_timestamp=last_ts,
        top_lines=top_lines,
    )


def format_summary_report(report: SummaryReport) -> str:
    """Render a SummaryReport as a human-readable string."""
    lines: List[str] = [
        "=== Log Summary ===",
        f"Total lines    : {report.total_lines}",
        f"Unique lines   : {report.unique_lines}",
        f"Duplicate lines: {report.duplicate_lines}",
    ]
    if report.level_counts:
        lines.append("Levels:")
        for lvl, cnt in sorted(report.level_counts.items()):
            lines.append(f"  {lvl:<8}: {cnt}")
    lines.append(f"First timestamp: {report.first_timestamp or 'n/a'}")
    lines.append(f"Last timestamp : {report.last_timestamp or 'n/a'}")
    if report.top_lines:
        lines.append("Top repeated lines:")
        for i, ln in enumerate(report.top_lines, 1):
            lines.append(f"  {i}. {ln.rstrip()}")
    return "\n".join(lines)
