"""Classify log lines into named categories based on pattern rules."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Optional


@dataclass
class ClassifyRule:
    """A named rule that maps a regex pattern to a category label."""

    category: str
    pattern: str
    case_sensitive: bool = False

    def __post_init__(self) -> None:
        flags = 0 if self.case_sensitive else re.IGNORECASE
        self._regex = re.compile(self.pattern, flags)

    def matches(self, line: str) -> bool:
        return bool(self._regex.search(line))


@dataclass
class ClassifiedLine:
    """A log line paired with its assigned category (or None if unmatched)."""

    line: str
    category: Optional[str] = None

    @property
    def is_classified(self) -> bool:
        return self.category is not None


def classify_line(
    line: str,
    rules: List[ClassifyRule],
    default: Optional[str] = None,
) -> ClassifiedLine:
    """Return a ClassifiedLine by applying the first matching rule.

    If no rule matches, *default* is used as the category.
    """
    for rule in rules:
        if rule.matches(line):
            return ClassifiedLine(line=line, category=rule.category)
    return ClassifiedLine(line=line, category=default)


def classify_lines(
    lines: Iterable[str],
    rules: List[ClassifyRule],
    default: Optional[str] = None,
) -> Iterator[ClassifiedLine]:
    """Yield ClassifiedLine objects for every input line."""
    for line in lines:
        yield classify_line(line, rules, default=default)


def group_by_category(
    classified: Iterable[ClassifiedLine],
) -> dict[Optional[str], List[str]]:
    """Aggregate classified lines into a dict keyed by category."""
    groups: dict[Optional[str], List[str]] = {}
    for cl in classified:
        groups.setdefault(cl.category, []).append(cl.line)
    return groups
