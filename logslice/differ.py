"""Utilities for diffing two sequences of log lines."""

from __future__ import annotations

import difflib
from dataclasses import dataclass
from typing import Iterator, List, Sequence, Tuple


@dataclass
class DiffLine:
    """A single line in a unified diff output."""

    tag: str          # '+', '-', ' ', or '@'
    content: str
    line_a: int | None = None  # 1-based line number in source A
    line_b: int | None = None  # 1-based line number in source B


def diff_lines(
    lines_a: Sequence[str],
    lines_b: Sequence[str],
    context: int = 3,
    label_a: str = "a",
    label_b: str = "b",
) -> List[DiffLine]:
    """Return a structured diff between two lists of log lines.

    Parameters
    ----------
    lines_a:  Original lines.
    lines_b:  Modified lines.
    context:  Number of unchanged lines to include around each change.
    label_a:  Display name for the original source.
    label_b:  Display name for the modified source.

    Returns
    -------
    A list of :class:`DiffLine` objects representing the diff.
    """
    result: List[DiffLine] = []
    matcher = difflib.SequenceMatcher(None, lines_a, lines_b, autojunk=False)

    for group in matcher.get_grouped_opcodes(context):
        # Hunk header
        first, last = group[0], group[-1]
        range_a = (first[1] + 1, last[2])
        range_b = (first[3] + 1, last[4])
        header = f"@@ -{range_a[0]},{range_a[1] - first[1]} +{range_b[0]},{range_b[1] - first[3]} @@"
        result.append(DiffLine(tag="@", content=header))

        for tag, i1, i2, j1, j2 in group:
            if tag == "equal":
                for k, line in enumerate(lines_a[i1:i2]):
                    result.append(DiffLine(" ", line, i1 + k + 1, j1 + k + 1))
            if tag in ("replace", "delete"):
                for k, line in enumerate(lines_a[i1:i2]):
                    result.append(DiffLine("-", line, i1 + k + 1, None))
            if tag in ("replace", "insert"):
                for k, line in enumerate(lines_b[j1:j2]):
                    result.append(DiffLine("+", line, None, j1 + k + 1))

    return result


def format_diff(diff: List[DiffLine], color: bool = False) -> Iterator[str]:
    """Yield human-readable lines from a structured diff.

    When *color* is True ANSI escape codes are added for terminals.
    """
    _RED = "\033[31m" if color else ""
    _GREEN = "\033[32m" if color else ""
    _CYAN = "\033[36m" if color else ""
    _RESET = "\033[0m" if color else ""

    for dl in diff:
        if dl.tag == "@":
            yield f"{_CYAN}{dl.content}{_RESET}"
        elif dl.tag == "-":
            yield f"{_RED}-{dl.content}{_RESET}"
        elif dl.tag == "+":
            yield f"{_GREEN}+{dl.content}{_RESET}"
        else:
            yield f" {dl.content}"


def count_changes(diff: List[DiffLine]) -> Tuple[int, int]:
    """Return (added, removed) line counts from a structured diff."""
    added = sum(1 for d in diff if d.tag == "+")
    removed = sum(1 for d in diff if d.tag == "-")
    return added, removed
