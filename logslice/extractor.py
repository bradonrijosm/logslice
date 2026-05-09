"""Field extractor: pull named fields from structured log lines."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List, Optional


@dataclass
class ExtractRule:
    """A named capture-group pattern used to extract a field."""

    name: str
    pattern: str
    case_sensitive: bool = True

    def __post_init__(self) -> None:
        flags = 0 if self.case_sensitive else re.IGNORECASE
        self._re = re.compile(self.pattern, flags)

    def extract(self, line: str) -> Optional[str]:
        """Return the first captured group, or None if no match."""
        m = self._re.search(line)
        if m is None:
            return None
        groups = m.groups()
        return groups[0] if groups else m.group(0)


@dataclass
class ExtractedLine:
    """A log line paired with its extracted field values."""

    line: str
    fields: Dict[str, Optional[str]] = field(default_factory=dict)

    def has_field(self, name: str) -> bool:
        return self.fields.get(name) is not None


def extract_fields(
    lines: Iterable[str],
    rules: List[ExtractRule],
) -> Iterator[ExtractedLine]:
    """Yield an ExtractedLine for every input line."""
    for line in lines:
        stripped = line.rstrip("\n")
        fields: Dict[str, Optional[str]] = {
            rule.name: rule.extract(stripped) for rule in rules
        }
        yield ExtractedLine(line=stripped, fields=fields)


def format_extracted(
    extracted: Iterable[ExtractedLine],
    separator: str = "\t",
    missing: str = "-",
) -> Iterator[str]:
    """Yield tab-separated (or custom) field values per line."""
    for el in extracted:
        values = [
            v if v is not None else missing for v in el.fields.values()
        ]
        yield separator.join(values)
