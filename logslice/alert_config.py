"""Load and validate alert rules from a simple TOML/JSON config file."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from logslice.alerter import AlertRule


def _parse_rule(raw: dict[str, Any], index: int) -> AlertRule:
    """Convert a raw mapping to an AlertRule, raising ValueError on bad input."""
    if "name" not in raw:
        raise ValueError(f"Rule #{index} is missing required field 'name'")
    if "pattern" not in raw:
        raise ValueError(f"Rule #{index} ('{raw['name']}') is missing 'pattern'")
    return AlertRule(
        name=raw["name"],
        pattern=raw["pattern"],
        level=raw.get("level"),
        case_sensitive=bool(raw.get("case_sensitive", False)),
    )


def load_rules_from_json(path: Path) -> list[AlertRule]:
    """Load alert rules from a JSON file.

    Expected format::

        {"rules": [{"name": "...", "pattern": "...", "level": null, "case_sensitive": false}]}
    """
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    raw_rules = data.get("rules", [])
    if not isinstance(raw_rules, list):
        raise ValueError("'rules' must be a JSON array")
    return [_parse_rule(r, i) for i, r in enumerate(raw_rules)]


def dump_rules_to_json(rules: list[AlertRule], path: Path) -> None:
    """Serialise *rules* to *path* as JSON."""
    payload = {
        "rules": [
            {
                "name": r.name,
                "pattern": r.pattern,
                "level": r.level,
                "case_sensitive": r.case_sensitive,
            }
            for r in rules
        ]
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def rules_summary(rules: list[AlertRule]) -> str:
    """Return a human-readable summary of loaded rules."""
    if not rules:
        return "No alert rules loaded."
    lines = [f"{len(rules)} alert rule(s) loaded:"]
    for r in rules:
        level_hint = f" [level={r.level}]" if r.level else ""
        cs_hint = " [case-sensitive]" if r.case_sensitive else ""
        lines.append(f"  • {r.name}: /{r.pattern}/{level_hint}{cs_hint}")
    return "\n".join(lines)
