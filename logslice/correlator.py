"""Correlate log lines by a shared request/trace ID field."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List, Optional


# Common patterns for trace/request IDs
_DEFAULT_PATTERNS: List[str] = [
    r"request[_-]?id[=:\s]+([\w\-]+)",
    r"trace[_-]?id[=:\s]+([\w\-]+)",
    r"req[_-]?id[=:\s]+([\w\-]+)",
    r"rid[=:\s]+([\w\-]+)",
]


@dataclass
class CorrelatedGroup:
    correlation_id: str
    lines: List[str] = field(default_factory=list)

    def __len__(self) -> int:  # pragma: no cover
        return len(self.lines)


def extract_correlation_id(
    line: str,
    patterns: Optional[List[str]] = None,
    case_sensitive: bool = False,
) -> Optional[str]:
    """Return the first correlation ID found in *line*, or None."""
    flags = 0 if case_sensitive else re.IGNORECASE
    for pat in (patterns or _DEFAULT_PATTERNS):
        m = re.search(pat, line, flags)
        if m:
            return m.group(1)
    return None


def group_by_correlation(
    lines: Iterable[str],
    patterns: Optional[List[str]] = None,
    case_sensitive: bool = False,
) -> Dict[str, CorrelatedGroup]:
    """Group *lines* by their correlation ID.

    Lines that carry no recognisable ID are stored under the empty-string key.
    """
    groups: Dict[str, CorrelatedGroup] = {}
    for line in lines:
        cid = extract_correlation_id(line, patterns, case_sensitive) or ""
        if cid not in groups:
            groups[cid] = CorrelatedGroup(correlation_id=cid)
        groups[cid].lines.append(line)
    return groups


def iter_correlated(
    lines: Iterable[str],
    correlation_id: str,
    patterns: Optional[List[str]] = None,
    case_sensitive: bool = False,
) -> Iterator[str]:
    """Yield only lines that carry *correlation_id*."""
    flags = 0 if case_sensitive else re.IGNORECASE
    needle = re.escape(correlation_id)
    for line in lines:
        cid = extract_correlation_id(line, patterns, case_sensitive)
        if cid and re.fullmatch(needle, cid, flags):
            yield line
