"""Deduplication utilities for removing repeated log lines."""

from collections import OrderedDict
from typing import Iterable, Iterator, Tuple


def deduplicate_lines(
    lines: Iterable[Tuple[int, str]],
    consecutive_only: bool = False,
) -> Iterator[Tuple[int, str]]:
    """Yield unique (lineno, line) tuples, removing duplicates.

    Args:
        lines: Iterable of (line_number, line_text) tuples.
        consecutive_only: If True, only collapse immediately repeated lines.
            If False (default), remove all duplicate lines globally.

    Yields:
        Unique (line_number, line_text) tuples.
    """
    if consecutive_only:
        yield from _deduplicate_consecutive(lines)
    else:
        yield from _deduplicate_global(lines)


def _deduplicate_consecutive(
    lines: Iterable[Tuple[int, str]],
) -> Iterator[Tuple[int, str]]:
    """Remove only consecutively repeated lines."""
    last_text: str | None = None
    for lineno, text in lines:
        if text != last_text:
            yield lineno, text
            last_text = text


def _deduplicate_global(
    lines: Iterable[Tuple[int, str]],
) -> Iterator[Tuple[int, str]]:
    """Remove all duplicate lines, keeping first occurrence."""
    seen: OrderedDict[str, None] = OrderedDict()
    result = []
    for lineno, text in lines:
        if text not in seen:
            seen[text] = None
            result.append((lineno, text))
    yield from result


def count_duplicates(
    lines: Iterable[Tuple[int, str]],
    consecutive_only: bool = False,
) -> int:
    """Return the number of duplicate lines that would be removed.

    Args:
        lines: Iterable of (line_number, line_text) tuples.
        consecutive_only: Match behaviour of deduplicate_lines.

    Returns:
        Count of lines that are duplicates.
    """
    all_lines = list(lines)
    total = len(all_lines)
    unique = sum(1 for _ in deduplicate_lines(iter(all_lines), consecutive_only))
    return total - unique
