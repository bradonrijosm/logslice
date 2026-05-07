"""Assign short human-readable labels to log lines based on regex rules."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Optional


@dataclass
class LabelRule:
    label: str
    pattern: str
    case_sensitive: bool = False

    def __post_init__(self) -> None:
        flags = 0 if self.case_sensitive else re.IGNORECASE
        self._regex = re.compile(self.pattern, flags)

    def matches(self, line: str) -> bool:
        return bool(self._regex.search(line))


@dataclass
class LabeledLine:
    line: str
    labels: List[str] = field(default_factory=list)

    @property
    def is_labeled(self) -> bool:
        return len(self.labels) > 0

    def formatted(self, separator: str = " ") -> str:
        if not self.labels:
            return self.line
        tag_str = "|".join(f"[{lbl}]" for lbl in self.labels)
        return f"{tag_str}{separator}{self.line}"


def label_line(line: str, rules: List[LabelRule]) -> LabeledLine:
    """Apply all matching rules to *line* and return a LabeledLine."""
    matched = [rule.label for rule in rules if rule.matches(line)]
    return LabeledLine(line=line, labels=matched)


def label_lines(
    lines: Iterable[str],
    rules: List[LabelRule],
    labeled_only: bool = False,
) -> Iterator[LabeledLine]:
    """Yield LabeledLine objects for each line in *lines*.

    If *labeled_only* is True, lines that match no rule are skipped.
    """
    for line in lines:
        result = label_line(line, rules)
        if labeled_only and not result.is_labeled:
            continue
        yield result


def first_label(labeled: LabeledLine, default: Optional[str] = None) -> Optional[str]:
    """Return the first label assigned to *labeled*, or *default*."""
    return labeled.labels[0] if labeled.labels else default
