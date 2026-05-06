"""Redact sensitive patterns from log lines using named rules."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Optional


@dataclass
class RedactRule:
    name: str
    pattern: str
    replacement: str = "[REDACTED]"
    case_sensitive: bool = False

    def __post_init__(self) -> None:
        flags = 0 if self.case_sensitive else re.IGNORECASE
        self._regex = re.compile(self.pattern, flags)

    def apply(self, line: str) -> str:
        """Return *line* with all matches replaced by *replacement*."""
        return self._regex.sub(self.replacement, line)


# Built-in convenience rules
DEFAULT_RULES: List[RedactRule] = [
    RedactRule("credit_card", r"\b(?:\d[ -]?){13,16}\b", "[CARD]"),
    RedactRule("ssn", r"\b\d{3}-\d{2}-\d{4}\b", "[SSN]"),
    RedactRule("jwt", r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", "[JWT]"),
    RedactRule("api_key", r"(?i)(?:api[_-]?key|token)[=:\s]+[\w\-]{16,}", "[API_KEY]"),
]


def redact_line(
    line: str,
    rules: Optional[List[RedactRule]] = None,
) -> str:
    """Apply *rules* sequentially to *line* and return the redacted result."""
    if rules is None:
        rules = DEFAULT_RULES
    for rule in rules:
        line = rule.apply(line)
    return line


def redact_lines(
    lines: Iterable[str],
    rules: Optional[List[RedactRule]] = None,
) -> Iterator[str]:
    """Yield each line from *lines* after applying all *rules*."""
    if rules is None:
        rules = DEFAULT_RULES
    for line in lines:
        yield redact_line(line, rules)


def count_redactions(
    lines: Iterable[str],
    rules: Optional[List[RedactRule]] = None,
) -> dict:
    """Return a dict mapping rule name -> number of matches found across *lines*."""
    if rules is None:
        rules = DEFAULT_RULES
    counts: dict = {rule.name: 0 for rule in rules}
    for line in lines:
        for rule in rules:
            counts[rule.name] += len(rule._regex.findall(line))
    return counts
