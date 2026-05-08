"""Route log lines to named output channels based on matching rules."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List, Optional, Tuple


@dataclass
class DispatchRule:
    channel: str
    pattern: str
    case_sensitive: bool = False

    def __post_init__(self) -> None:
        flags = 0 if self.case_sensitive else re.IGNORECASE
        self._regex = re.compile(self.pattern, flags)

    def matches(self, line: str) -> bool:
        return bool(self._regex.search(line))


@dataclass
class DispatchedLine:
    line: str
    channel: str
    rule_index: Optional[int] = None


_DEFAULT_CHANNEL = "default"


def dispatch_line(
    line: str,
    rules: List[DispatchRule],
    default_channel: str = _DEFAULT_CHANNEL,
) -> DispatchedLine:
    """Return a DispatchedLine assigning *line* to the first matching channel."""
    for idx, rule in enumerate(rules):
        if rule.matches(line):
            return DispatchedLine(line=line, channel=rule.channel, rule_index=idx)
    return DispatchedLine(line=line, channel=default_channel, rule_index=None)


def dispatch_lines(
    lines: Iterable[str],
    rules: List[DispatchRule],
    default_channel: str = _DEFAULT_CHANNEL,
) -> Iterator[DispatchedLine]:
    """Yield DispatchedLine objects for every line in *lines*."""
    for line in lines:
        yield dispatch_line(line, rules, default_channel)


def group_by_channel(
    dispatched: Iterable[DispatchedLine],
) -> Dict[str, List[str]]:
    """Collect dispatched lines into a dict keyed by channel name."""
    groups: Dict[str, List[str]] = {}
    for dl in dispatched:
        groups.setdefault(dl.channel, []).append(dl.line)
    return groups


def channel_summary(groups: Dict[str, List[str]]) -> List[Tuple[str, int]]:
    """Return (channel, count) pairs sorted by count descending."""
    return sorted(((ch, len(lines)) for ch, lines in groups.items()), key=lambda t: t[1], reverse=True)
