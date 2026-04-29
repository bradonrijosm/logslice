"""Truncator module for limiting long log lines and capping output line counts."""

from typing import Iterator, List, Optional, Tuple

DEFAULT_MAX_LINE_LENGTH = 200
DEFAULT_TRUNCATION_MARKER = "...[truncated]"


def truncate_line(line: str, max_length: int = DEFAULT_MAX_LINE_LENGTH,
                 marker: str = DEFAULT_TRUNCATION_MARKER) -> Tuple[str, bool]:
    """Truncate a single line if it exceeds max_length.

    Returns a tuple of (possibly truncated line, was_truncated).
    """
    if max_length <= 0:
        raise ValueError("max_length must be a positive integer")
    if len(line) <= max_length:
        return line, False
    truncated = line[:max_length] + marker
    return truncated, True


def truncate_lines(
    lines: List[str],
    max_length: int = DEFAULT_MAX_LINE_LENGTH,
    marker: str = DEFAULT_TRUNCATION_MARKER,
) -> Tuple[List[str], int]:
    """Truncate all lines that exceed max_length.

    Returns a tuple of (list of processed lines, count of lines that were truncated).
    """
    result: List[str] = []
    truncated_count = 0
    for line in lines:
        processed, was_truncated = truncate_line(line, max_length, marker)
        result.append(processed)
        if was_truncated:
            truncated_count += 1
    return result, truncated_count


def cap_lines(
    lines: List[str],
    max_lines: Optional[int],
) -> Tuple[List[str], bool]:
    """Cap the number of output lines to max_lines.

    Returns a tuple of (capped list, was_capped).
    """
    if max_lines is None or max_lines <= 0 or len(lines) <= max_lines:
        return lines, False
    return lines[:max_lines], True


def truncate_and_cap(
    lines: List[str],
    max_length: int = DEFAULT_MAX_LINE_LENGTH,
    max_lines: Optional[int] = None,
    marker: str = DEFAULT_TRUNCATION_MARKER,
) -> Tuple[List[str], int, bool]:
    """Apply both line-length truncation and line-count capping.

    Returns a tuple of (processed lines, truncated_line_count, was_capped).
    """
    capped, was_capped = cap_lines(lines, max_lines)
    processed, truncated_count = truncate_lines(capped, max_length, marker)
    return processed, truncated_count, was_capped
