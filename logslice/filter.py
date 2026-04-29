"""Filter log lines by keyword, log level, or regex pattern."""

import re
from typing import Iterable, Iterator, List, Optional


LEVEL_PATTERNS = {
    "debug": re.compile(r"\b(DEBUG)\b", re.IGNORECASE),
    "info": re.compile(r"\b(INFO)\b", re.IGNORECASE),
    "warning": re.compile(r"\b(WARN(?:ING)?)\b", re.IGNORECASE),
    "error": re.compile(r"\b(ERROR)\b", re.IGNORECASE),
    "critical": re.compile(r"\b(CRITICAL|FATAL)\b", re.IGNORECASE),
}


def filter_by_level(lines: Iterable[str], level: str) -> Iterator[str]:
    """Yield only lines matching the given log level.

    Args:
        lines: Iterable of log line strings.
        level: One of 'debug', 'info', 'warning', 'error', 'critical'.

    Yields:
        Lines that contain the specified log level token.

    Raises:
        ValueError: If the level is not recognised.
    """
    level_key = level.lower()
    if level_key not in LEVEL_PATTERNS:
        raise ValueError(
            f"Unknown log level '{level}'. "
            f"Choose from: {', '.join(LEVEL_PATTERNS)}"
        )
    pattern = LEVEL_PATTERNS[level_key]
    for line in lines:
        if pattern.search(line):
            yield line


def filter_by_pattern(
    lines: Iterable[str],
    pattern: str,
    case_sensitive: bool = False,
) -> Iterator[str]:
    """Yield only lines matching a regex pattern.

    Args:
        lines: Iterable of log line strings.
        pattern: Regular expression pattern string.
        case_sensitive: When False (default) matching is case-insensitive.

    Yields:
        Lines that match the compiled pattern.

    Raises:
        re.error: If *pattern* is not a valid regular expression.
    """
    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        compiled = re.compile(pattern, flags)
    except re.error as exc:
        raise ValueError(f"Invalid regex pattern '{pattern}': {exc}") from exc
    for line in lines:
        if compiled.search(line):
            yield line


def filter_lines(
    lines: Iterable[str],
    level: Optional[str] = None,
    pattern: Optional[str] = None,
    case_sensitive: bool = False,
) -> Iterator[str]:
    """Apply optional level and/or pattern filters to log lines.

    Filters are applied in order: level first, then pattern.  Either
    filter may be omitted by passing ``None``.

    Args:
        lines: Iterable of log line strings.
        level: Optional log level string (see :func:`filter_by_level`).
        pattern: Optional regex pattern string.
        case_sensitive: Passed through to :func:`filter_by_pattern`.

    Yields:
        Lines that pass all active filters.
    """
    stream: Iterable[str] = lines
    if level is not None:
        stream = filter_by_level(stream, level)
    if pattern is not None:
        stream = filter_by_pattern(stream, pattern, case_sensitive=case_sensitive)
    yield from stream
