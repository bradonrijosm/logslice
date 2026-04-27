"""Core log slicing logic for extracting time-range filtered lines."""

from datetime import datetime
from typing import Generator, Optional

from logslice.parser import extract_timestamp


def slice_log(
    filepath: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    encoding: str = "utf-8",
) -> Generator[str, None, None]:
    """Yield log lines whose timestamps fall within [start, end].

    Lines without a detectable timestamp are skipped unless no boundaries
    are specified, in which case all lines are yielded.

    Args:
        filepath: Path to the log file.
        start: Inclusive start datetime. None means no lower bound.
        end: Inclusive end datetime. None means no upper bound.
        encoding: File encoding (default utf-8).

    Yields:
        Log lines (with newline stripped) within the specified range.
    """
    if start is None and end is None:
        with open(filepath, "r", encoding=encoding, errors="replace") as fh:
            for line in fh:
                yield line.rstrip("\n")
        return

    with open(filepath, "r", encoding=encoding, errors="replace") as fh:
        for line in fh:
            stripped = line.rstrip("\n")
            ts = extract_timestamp(stripped)
            if ts is None:
                continue
            if start is not None and ts < start:
                continue
            if end is not None and ts > end:
                continue
            yield stripped


def count_lines(
    filepath: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    encoding: str = "utf-8",
) -> int:
    """Count lines in the given time range without storing them.

    Args:
        filepath: Path to the log file.
        start: Inclusive start datetime.
        end: Inclusive end datetime.
        encoding: File encoding.

    Returns:
        Number of matching lines.
    """
    return sum(1 for _ in slice_log(filepath, start, end, encoding))
