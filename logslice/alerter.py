"""Alert rules that fire when log lines match specified conditions."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Iterable, Iterator


@dataclass
class AlertRule:
    name: str
    pattern: str
    level: str | None = None          # optional level filter (e.g. "ERROR")
    case_sensitive: bool = False
    _regex: re.Pattern = field(init=False, repr=False)

    def __post_init__(self) -> None:
        flags = 0 if self.case_sensitive else re.IGNORECASE
        self._regex = re.compile(self.pattern, flags)

    def matches(self, line: str) -> bool:
        if self.level and self.level.upper() not in line.upper():
            return False
        return bool(self._regex.search(line))


@dataclass
class AlertEvent:
    rule_name: str
    line: str
    line_number: int


def evaluate_rules(
    lines: Iterable[str],
    rules: list[AlertRule],
    *,
    start: int = 1,
) -> Iterator[AlertEvent]:
    """Yield an AlertEvent for every line that matches at least one rule."""
    for idx, line in enumerate(lines, start=start):
        stripped = line.rstrip("\n")
        for rule in rules:
            if rule.matches(stripped):
                yield AlertEvent(
                    rule_name=rule.name,
                    line=stripped,
                    line_number=idx,
                )


def format_alert(event: AlertEvent) -> str:
    return f"[ALERT:{event.rule_name}] line {event.line_number}: {event.line}"


def run_alerts(
    lines: Iterable[str],
    rules: list[AlertRule],
    callback: Callable[[AlertEvent], None] | None = None,
) -> list[AlertEvent]:
    """Collect all alert events; optionally call *callback* for each."""
    events: list[AlertEvent] = []
    for event in evaluate_rules(lines, rules):
        events.append(event)
        if callback is not None:
            callback(event)
    return events
