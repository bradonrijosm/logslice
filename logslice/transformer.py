"""Line transformation pipeline: apply ordered transforms to log lines."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Iterable, Iterator, List, Optional


@dataclass
class TransformRule:
    """A single find-and-replace transformation rule."""

    pattern: str
    replacement: str
    case_sensitive: bool = False
    label: Optional[str] = None

    def __post_init__(self) -> None:
        flags = 0 if self.case_sensitive else re.IGNORECASE
        self._regex = re.compile(self.pattern, flags)

    def apply(self, line: str) -> str:
        """Return *line* with all matches replaced."""
        return self._regex.sub(self.replacement, line)

    def matches(self, line: str) -> bool:
        """Return True if the pattern matches anywhere in *line*."""
        return bool(self._regex.search(line))


@dataclass
class TransformedLine:
    original: str
    result: str
    applied: List[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return self.original != self.result


def transform_line(
    line: str,
    rules: List[TransformRule],
) -> TransformedLine:
    """Apply every rule in order and return a TransformedLine."""
    current = line
    applied: List[str] = []
    for rule in rules:
        if rule.matches(current):
            current = rule.apply(current)
            applied.append(rule.label or rule.pattern)
    return TransformedLine(original=line, result=current, applied=applied)


def transform_lines(
    lines: Iterable[str],
    rules: List[TransformRule],
) -> Iterator[TransformedLine]:
    """Yield a TransformedLine for every input line."""
    for line in lines:
        yield transform_line(line, rules)


def apply_transforms(
    lines: Iterable[str],
    rules: List[TransformRule],
    changed_only: bool = False,
) -> Iterator[str]:
    """Yield the result strings; optionally skip unchanged lines."""
    for tl in transform_lines(lines, rules):
        if changed_only and not tl.changed:
            continue
        yield tl.result
