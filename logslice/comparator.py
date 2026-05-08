"""Compare two sets of log lines and report structural differences in frequency and level distribution."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence

from logslice.stats import _count_levels


@dataclass
class ComparisonReport:
    total_a: int
    total_b: int
    unique_a: int
    unique_b: int
    levels_a: Dict[str, int]
    levels_b: Dict[str, int]
    only_in_a: List[str] = field(default_factory=list)
    only_in_b: List[str] = field(default_factory=list)
    common: List[str] = field(default_factory=list)


def compare_logs(
    lines_a: Sequence[str],
    lines_b: Sequence[str],
) -> ComparisonReport:
    """Return a :class:`ComparisonReport` summarising differences between two log sets."""
    set_a = set(lines_a)
    set_b = set(lines_b)

    return ComparisonReport(
        total_a=len(lines_a),
        total_b=len(lines_b),
        unique_a=len(set_a),
        unique_b=len(set_b),
        levels_a=_count_levels(list(lines_a)),
        levels_b=_count_levels(list(lines_b)),
        only_in_a=sorted(set_a - set_b),
        only_in_b=sorted(set_b - set_a),
        common=sorted(set_a & set_b),
    )


def format_comparison(report: ComparisonReport) -> str:
    """Return a human-readable summary of a :class:`ComparisonReport`."""
    lines: List[str] = [
        "=== Log Comparison ===",
        f"  Source A : {report.total_a} lines ({report.unique_a} unique)",
        f"  Source B : {report.total_b} lines ({report.unique_b} unique)",
        "",
        "Level distribution:",
    ]

    all_levels = sorted(set(report.levels_a) | set(report.levels_b))
    for lvl in all_levels:
        a_cnt = report.levels_a.get(lvl, 0)
        b_cnt = report.levels_b.get(lvl, 0)
        lines.append(f"  {lvl:<8}  A={a_cnt}  B={b_cnt}")

    lines += [
        "",
        f"Only in A : {len(report.only_in_a)} line(s)",
        f"Only in B : {len(report.only_in_b)} line(s)",
        f"Common    : {len(report.common)} line(s)",
    ]
    return "\n".join(lines)
