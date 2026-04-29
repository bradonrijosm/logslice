"""Statistics and summary reporting for log slices."""

from collections import Counter
from typing import List, Dict, Any


def compute_stats(lines: List[str]) -> Dict[str, Any]:
    """Compute basic statistics over a list of log lines."""
    if not lines:
        return {
            "total_lines": 0,
            "unique_lines": 0,
            "duplicate_lines": 0,
            "level_counts": {},
            "avg_line_length": 0.0,
            "max_line_length": 0,
            "min_line_length": 0,
        }

    counts = Counter(lines)
    unique = len(counts)
    duplicates = sum(c - 1 for c in counts.values())

    lengths = [len(line) for line in lines]
    avg_len = sum(lengths) / len(lengths)

    level_counts = _count_levels(lines)

    return {
        "total_lines": len(lines),
        "unique_lines": unique,
        "duplicate_lines": duplicates,
        "level_counts": level_counts,
        "avg_line_length": round(avg_len, 2),
        "max_line_length": max(lengths),
        "min_line_length": min(lengths),
    }


def _count_levels(lines: List[str]) -> Dict[str, int]:
    """Count occurrences of common log levels in lines."""
    levels = ["ERROR", "WARN", "WARNING", "INFO", "DEBUG", "CRITICAL", "FATAL"]
    counts: Dict[str, int] = {}
    for line in lines:
        upper = line.upper()
        for level in levels:
            if level in upper:
                canonical = "WARN" if level == "WARNING" else level
                counts[canonical] = counts.get(canonical, 0) + 1
                break
    return counts


def format_stats(stats: Dict[str, Any]) -> str:
    """Format statistics dict into a human-readable string."""
    lines = [
        "=== Log Statistics ===",
        f"Total lines    : {stats['total_lines']}",
        f"Unique lines   : {stats['unique_lines']}",
        f"Duplicate lines: {stats['duplicate_lines']}",
        f"Avg line length: {stats['avg_line_length']}",
        f"Max line length: {stats['max_line_length']}",
        f"Min line length: {stats['min_line_length']}",
    ]
    if stats.get("level_counts"):
        lines.append("Level counts:")
        for level, count in sorted(stats["level_counts"].items()):
            lines.append(f"  {level:<10}: {count}")
    return "\n".join(lines)
