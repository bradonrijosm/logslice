"""Output formatting utilities for logslice results."""

import sys
from typing import Iterable, Optional, TextIO


def format_lines(
    lines: Iterable[str],
    output: TextIO = sys.stdout,
    prefix_line_numbers: bool = False,
    start_line: int = 1,
) -> int:
    """Write lines to the given output stream.

    Args:
        lines: Iterable of log line strings.
        output: File-like object to write to (defaults to stdout).
        prefix_line_numbers: If True, prepend each line with its line number.
        start_line: The starting line number when prefixing (default 1).

    Returns:
        The total number of lines written.
    """
    count = 0
    for i, line in enumerate(lines, start=start_line):
        if prefix_line_numbers:
            output.write(f"{i:>6}  {line}")
        else:
            output.write(line)
        if not line.endswith("\n"):
            output.write("\n")
        count += 1
    return count


def format_summary(
    matched: int,
    total: Optional[int] = None,
    output: TextIO = sys.stderr,
) -> None:
    """Print a summary of matched vs total lines to stderr.

    Args:
        matched: Number of lines that matched the time range.
        total: Total lines scanned (optional).
        output: File-like object for summary output.
    """
    if total is not None:
        pct = (matched / total * 100) if total > 0 else 0.0
        output.write(
            f"[logslice] {matched} of {total} lines matched ({pct:.1f}%)\n"
        )
    else:
        output.write(f"[logslice] {matched} lines matched\n")


def format_no_match(output: TextIO = sys.stderr) -> None:
    """Emit a warning when no lines matched the given time range."""
    output.write(
        "[logslice] Warning: no lines matched the specified time range.\n"
    )
