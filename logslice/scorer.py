"""Score log lines by relevance based on keyword weights."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Tuple


@dataclass
class ScoredLine:
    line: str
    score: float
    matched_keywords: List[str] = field(default_factory=list)


def _compile(keyword: str, case_sensitive: bool) -> re.Pattern:
    flags = 0 if case_sensitive else re.IGNORECASE
    return re.compile(re.escape(keyword), flags)


def score_line(
    line: str,
    weights: Dict[str, float],
    *,
    case_sensitive: bool = False,
) -> ScoredLine:
    """Return a ScoredLine with cumulative weight of all matching keywords."""
    total = 0.0
    matched: List[str] = []
    for keyword, weight in weights.items():
        pattern = _compile(keyword, case_sensitive)
        if pattern.search(line):
            total += weight
            matched.append(keyword)
    return ScoredLine(line=line, score=total, matched_keywords=matched)


def score_lines(
    lines: Iterable[str],
    weights: Dict[str, float],
    *,
    case_sensitive: bool = False,
    threshold: float = 0.0,
) -> List[ScoredLine]:
    """Score every line and return those at or above *threshold*, sorted descending."""
    results: List[ScoredLine] = []
    for line in lines:
        scored = score_line(line, weights, case_sensitive=case_sensitive)
        if scored.score >= threshold:
            results.append(scored)
    results.sort(key=lambda s: s.score, reverse=True)
    return results


def top_scored(
    lines: Iterable[str],
    weights: Dict[str, float],
    n: int = 10,
    *,
    case_sensitive: bool = False,
) -> List[ScoredLine]:
    """Return the top *n* highest-scoring lines."""
    scored = score_lines(lines, weights, case_sensitive=case_sensitive)
    return scored[:n]


def format_scored(
    scored_lines: List[ScoredLine],
    *,
    show_score: bool = True,
    show_keywords: bool = False,
) -> List[str]:
    """Format ScoredLine objects into human-readable strings."""
    out: List[str] = []
    for sl in scored_lines:
        prefix_parts: List[str] = []
        if show_score:
            prefix_parts.append(f"[{sl.score:.2f}]")
        if show_keywords and sl.matched_keywords:
            prefix_parts.append(f"({', '.join(sl.matched_keywords)})")
        prefix = " ".join(prefix_parts)
        out.append(f"{prefix} {sl.line}".strip() if prefix else sl.line)
    return out
