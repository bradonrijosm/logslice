"""Group log lines by a regex-extracted key (e.g. hostname, user, request path)."""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional


@dataclass
class GroupedLines:
    key: str
    lines: List[str] = field(default_factory=list)

    def __len__(self) -> int:  # pragma: no cover
        return len(self.lines)


def extract_group_key(
    line: str,
    pattern: str,
    group: int = 1,
    case_sensitive: bool = False,
) -> Optional[str]:
    """Return the captured group from *line* or ``None`` if no match."""
    flags = 0 if case_sensitive else re.IGNORECASE
    m = re.search(pattern, line, flags)
    if m is None:
        return None
    try:
        return m.group(group)
    except IndexError:
        return None


def group_lines(
    lines: Iterable[str],
    pattern: str,
    group: int = 1,
    case_sensitive: bool = False,
    default_key: str = "__ungrouped__",
) -> Dict[str, GroupedLines]:
    """Partition *lines* into buckets keyed by the first capture group of *pattern*.

    Lines that do not match are placed under *default_key*.
    """
    buckets: Dict[str, GroupedLines] = defaultdict(lambda: GroupedLines(key=""))
    for line in lines:
        key = extract_group_key(line, pattern, group, case_sensitive) or default_key
        if key not in buckets:
            buckets[key] = GroupedLines(key=key)
        buckets[key].lines.append(line)
    return dict(buckets)


def format_groups(groups: Dict[str, GroupedLines], separator: str = "---") -> str:
    """Return a human-readable string of all groups and their lines."""
    parts: List[str] = []
    for key, grp in sorted(groups.items()):
        parts.append(f"[{key}] ({len(grp.lines)} lines)")
        parts.extend(grp.lines)
        parts.append(separator)
    return "\n".join(parts)
