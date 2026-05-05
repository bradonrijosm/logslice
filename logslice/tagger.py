"""Tag log lines with custom labels based on pattern matching."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Iterator


@dataclass
class TagRule:
    """A rule that maps a regex pattern to a tag label."""

    tag: str
    pattern: str
    case_sensitive: bool = False

    def __post_init__(self) -> None:
        flags = 0 if self.case_sensitive else re.IGNORECASE
        self._regex = re.compile(self.pattern, flags)

    def matches(self, line: str) -> bool:
        return bool(self._regex.search(line))


@dataclass
class TaggedLine:
    """A log line paired with the set of tags applied to it."""

    line: str
    tags: list[str] = field(default_factory=list)

    @property
    def tagged(self) -> bool:
        return len(self.tags) > 0

    def __str__(self) -> str:
        if not self.tags:
            return self.line
        label = ",".join(self.tags)
        return f"[{label}] {self.line}"


def tag_lines(
    lines: Iterable[str],
    rules: list[TagRule],
    *,
    multi_tag: bool = True,
) -> Iterator[TaggedLine]:
    """Yield TaggedLine objects for each line, applying all matching rules.

    Args:
        lines: Iterable of raw log lines.
        rules: Ordered list of TagRule objects to evaluate.
        multi_tag: When False, stop after the first matching rule per line.
    """
    for line in lines:
        tags: list[str] = []
        for rule in rules:
            if rule.matches(line):
                tags.append(rule.tag)
                if not multi_tag:
                    break
        yield TaggedLine(line=line, tags=tags)


def filter_by_tag(
    tagged: Iterable[TaggedLine],
    tag: str,
) -> Iterator[TaggedLine]:
    """Yield only TaggedLine objects that carry the given tag."""
    for tl in tagged:
        if tag in tl.tags:
            yield tl


def collect_tags(tagged: Iterable[TaggedLine]) -> dict[str, int]:
    """Return a frequency map of tag -> occurrence count."""
    counts: dict[str, int] = {}
    for tl in tagged:
        for tag in tl.tags:
            counts[tag] = counts.get(tag, 0) + 1
    return counts
