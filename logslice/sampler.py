"""Sampling utilities for reducing large log outputs to a representative subset."""

from typing import List, Optional
import math


def sample_lines(
    lines: List[str],
    rate: float,
    offset: int = 0,
) -> List[str]:
    """Return every Nth line based on a sampling rate between 0.0 and 1.0.

    Args:
        lines: Input log lines.
        rate: Fraction of lines to keep (e.g. 0.1 keeps ~10%).
        offset: Starting index offset for deterministic selection.

    Returns:
        A list of sampled lines.

    Raises:
        ValueError: If rate is not in the range (0.0, 1.0].
    """
    if not (0.0 < rate <= 1.0):
        raise ValueError(f"rate must be between 0 (exclusive) and 1 (inclusive), got {rate}")

    if not lines:
        return []

    if rate == 1.0:
        return list(lines)

    step = 1.0 / rate
    result: List[str] = []
    idx = offset % step if step > 1 else 0.0

    for i, line in enumerate(lines):
        if i >= math.floor(idx):
            result.append(line)
            idx += step

    return result


def sample_head(lines: List[str], n: int) -> List[str]:
    """Return the first N lines.

    Args:
        lines: Input log lines.
        n: Maximum number of lines to return.

    Returns:
        Up to N lines from the start.
    """
    if n < 0:
        raise ValueError(f"n must be non-negative, got {n}")
    return lines[:n]


def sample_tail(lines: List[str], n: int) -> List[str]:
    """Return the last N lines.

    Args:
        lines: Input log lines.
        n: Maximum number of lines to return from the end.

    Returns:
        Up to N lines from the end.
    """
    if n < 0:
        raise ValueError(f"n must be non-negative, got {n}")
    if n == 0:
        return []
    return lines[-n:]


def sample_every_nth(lines: List[str], n: int) -> List[str]:
    """Return every Nth line (1-indexed).

    Args:
        lines: Input log lines.
        n: Step size; must be >= 1.

    Returns:
        Every Nth line.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")
    return lines[::n]
