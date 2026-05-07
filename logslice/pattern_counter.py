"""Count occurrences of regex patterns across log lines."""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional


@dataclass
class PatternCount:
    pattern: str
    count: int
    sample_lines: List[str] = field(default_factory=list)


def count_pattern(
    lines: Iterable[str],
    pattern: str,
    case_sensitive: bool = False,
    max_samples: int = 3,
) -> PatternCount:
    """Count how many lines match *pattern* and collect sample matches."""
    flags = 0 if case_sensitive else re.IGNORECASE
    compiled = re.compile(pattern, flags)
    count = 0
    samples: List[str] = []
    for line in lines:
        if compiled.search(line):
            count += 1
            if len(samples) < max_samples:
                samples.append(line.rstrip("\n"))
    return PatternCount(pattern=pattern, count=count, sample_lines=samples)


def count_patterns(
    lines: Iterable[str],
    patterns: List[str],
    case_sensitive: bool = False,
    max_samples: int = 3,
) -> Dict[str, PatternCount]:
    """Count occurrences of each pattern in *patterns* across *lines*.

    Lines are iterated once; all patterns are tested per line.
    """
    flags = 0 if case_sensitive else re.IGNORECASE
    compiled = [(p, re.compile(p, flags)) for p in patterns]
    counts: Counter = Counter()
    samples: Dict[str, List[str]] = {p: [] for p in patterns}

    for line in lines:
        stripped = line.rstrip("\n")
        for pat, regex in compiled:
            if regex.search(stripped):
                counts[pat] += 1
                if len(samples[pat]) < max_samples:
                    samples[pat].append(stripped)

    return {
        pat: PatternCount(pattern=pat, count=counts[pat], sample_lines=samples[pat])
        for pat in patterns
    }


def format_pattern_counts(
    results: Dict[str, PatternCount],
    show_samples: bool = True,
) -> str:
    """Return a human-readable summary of pattern counts."""
    if not results:
        return "No patterns specified."
    lines: List[str] = []
    for pat, pc in results.items():
        lines.append(f"  {pat!r:40s}  {pc.count:>6} match(es)")
        if show_samples and pc.sample_lines:
            for s in pc.sample_lines:
                lines.append(f"      sample: {s}")
    return "Pattern counts:\n" + "\n".join(lines)
