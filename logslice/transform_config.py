"""Load and dump TransformRule lists from/to JSON configuration."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from logslice.transformer import TransformRule


def _parse_rule(obj: Dict[str, Any]) -> TransformRule:
    """Build a TransformRule from a plain dict (JSON object)."""
    pattern = obj["pattern"]
    replacement = obj["replacement"]
    case_sensitive = bool(obj.get("case_sensitive", False))
    label = obj.get("label") or None
    return TransformRule(
        pattern=pattern,
        replacement=replacement,
        case_sensitive=case_sensitive,
        label=label,
    )


def load_rules_from_json(path: str) -> List[TransformRule]:
    """Read a JSON file and return a list of TransformRule objects.

    The file must contain a JSON array of objects, each with at least
    ``pattern`` and ``replacement`` keys.
    """
    with open(path) as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError("Transform config must be a JSON array.")
    return [_parse_rule(item) for item in data]


def dump_rules_to_json(rules: List[TransformRule], path: str) -> None:
    """Serialise *rules* to a JSON file at *path*."""
    payload = [
        {
            "pattern": r.pattern,
            "replacement": r.replacement,
            "case_sensitive": r.case_sensitive,
            "label": r.label,
        }
        for r in rules
    ]
    with open(path, "w") as fh:
        json.dump(payload, fh, indent=2)


def rules_summary(rules: List[TransformRule]) -> str:
    """Return a human-readable summary of *rules*."""
    if not rules:
        return "No transform rules defined."
    lines = [f"{len(rules)} rule(s):"]
    for i, r in enumerate(rules, 1):
        label = r.label or r.pattern
        sensitivity = "case-sensitive" if r.case_sensitive else "case-insensitive"
        lines.append(f"  {i}. [{label}] {r.pattern!r} -> {r.replacement!r} ({sensitivity})")
    return "\n".join(lines)
