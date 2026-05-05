"""Sorting utilities for log lines by timestamp or lexicographic order."""

from typing import List, Optional, Callable
from logslice.parser import extract_timestamp


def sort_by_timestamp(
    lines: List[str],
    reverse: bool = False,
    fallback_to_original: bool = True,
) -> List[str]:
    """Sort log lines by their extracted timestamp.

    Lines without a detectable timestamp are placed at the end (or beginning
    when reverse=True) unless fallback_to_original is False, in which case
    they are dropped.

    Args:
        lines: The log lines to sort.
        reverse: If True, sort in descending order.
        fallback_to_original: If True, keep lines with no timestamp; otherwise drop them.

    Returns:
        A new list of lines sorted by timestamp.
    """
    timestamped: List[tuple] = []
    untimed: List[str] = []

    for line in lines:
        ts = extract_timestamp(line)
        if ts is not None:
            timestamped.append((ts, line))
        else:
            if fallback_to_original:
                untimed.append(line)

    timestamped.sort(key=lambda pair: pair[0], reverse=reverse)
    sorted_lines = [line for _, line in timestamped]

    if fallback_to_original:
        if reverse:
            return untimed + sorted_lines
        return sorted_lines + untimed

    return sorted_lines


def sort_lexicographic(
    lines: List[str],
    reverse: bool = False,
    key: Optional[Callable[[str], str]] = None,
) -> List[str]:
    """Sort log lines lexicographically.

    Args:
        lines: The log lines to sort.
        reverse: If True, sort in descending order.
        key: Optional key function applied to each line before comparison.

    Returns:
        A new sorted list of lines.
    """
    return sorted(lines, key=key, reverse=reverse)


def stable_sort(
    lines: List[str],
    by: str = "timestamp",
    reverse: bool = False,
) -> List[str]:
    """Convenience wrapper that dispatches to the appropriate sort function.

    Args:
        lines: The log lines to sort.
        by: Either 'timestamp' or 'lexicographic'.
        reverse: If True, sort in descending order.

    Returns:
        Sorted list of lines.

    Raises:
        ValueError: If *by* is not a recognised sort mode.
    """
    if by == "timestamp":
        return sort_by_timestamp(lines, reverse=reverse)
    if by == "lexicographic":
        return sort_lexicographic(lines, reverse=reverse)
    raise ValueError(f"Unknown sort mode: {by!r}. Choose 'timestamp' or 'lexicographic'.")
