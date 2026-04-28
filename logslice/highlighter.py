"""Keyword highlighting utilities for matched log lines."""

import re
from typing import List, Optional


ANSI_YELLOW = "\033[33m"
ANSI_RED = "\033[31m"
ANSI_RESET = "\033[0m"

COLOR_MAP = {
    "yellow": ANSI_YELLOW,
    "red": ANSI_RED,
}


def highlight_keywords(
    line: str,
    keywords: List[str],
    color: str = "yellow",
    case_sensitive: bool = False,
) -> str:
    """Return *line* with every occurrence of each keyword wrapped in ANSI color codes.

    Parameters
    ----------
    line:
        The raw log line to process.
    keywords:
        List of keyword strings to highlight.
    color:
        One of ``'yellow'`` (default) or ``'red'``.
    case_sensitive:
        When ``False`` (default) matching is case-insensitive.

    Returns
    -------
    str
        The line with matching substrings wrapped in ANSI escape sequences.
        If *keywords* is empty the original line is returned unchanged.
    """
    if not keywords:
        return line

    ansi_color = COLOR_MAP.get(color, ANSI_YELLOW)
    flags = 0 if case_sensitive else re.IGNORECASE

    for keyword in keywords:
        escaped = re.escape(keyword)
        line = re.sub(
            f"({escaped})",
            f"{ansi_color}\\1{ANSI_RESET}",
            line,
            flags=flags,
        )
    return line


def highlight_lines(
    lines: List[str],
    keywords: List[str],
    color: str = "yellow",
    case_sensitive: bool = False,
) -> List[str]:
    """Apply :func:`highlight_keywords` to every line in *lines*."""
    return [
        highlight_keywords(line, keywords, color=color, case_sensitive=case_sensitive)
        for line in lines
    ]
