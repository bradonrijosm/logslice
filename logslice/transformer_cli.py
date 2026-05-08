"""CLI entry-point for the transformer module."""

from __future__ import annotations

import argparse
import sys
from typing import List

from logslice.transformer import TransformRule, apply_transforms


def build_transformer_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-transform",
        description="Apply regex find-and-replace rules to log lines.",
    )
    p.add_argument("file", help="Path to the log file (use '-' for stdin).")
    p.add_argument(
        "-r",
        "--rule",
        metavar="PATTERN=REPLACEMENT",
        action="append",
        dest="rules",
        default=[],
        help="Transformation rule in PATTERN=REPLACEMENT form. Repeatable.",
    )
    p.add_argument(
        "--case-sensitive",
        action="store_true",
        default=False,
        help="Make pattern matching case-sensitive.",
    )
    p.add_argument(
        "--changed-only",
        action="store_true",
        default=False,
        help="Only output lines that were actually changed.",
    )
    return p


def _parse_rules(raw: List[str], case_sensitive: bool) -> List[TransformRule]:
    rules: List[TransformRule] = []
    for item in raw:
        if "=" not in item:
            raise ValueError(f"Rule must be PATTERN=REPLACEMENT, got: {item!r}")
        pattern, _, replacement = item.partition("=")
        rules.append(
            TransformRule(
                pattern=pattern,
                replacement=replacement,
                case_sensitive=case_sensitive,
                label=pattern,
            )
        )
    return rules


def cmd_transform(ns: argparse.Namespace, out=sys.stdout) -> int:
    rules = _parse_rules(ns.rules, ns.case_sensitive)
    if ns.file == "-":
        lines = (line.rstrip("\n") for line in sys.stdin)
    else:
        with open(ns.file) as fh:
            lines = [line.rstrip("\n") for line in fh]
    for result in apply_transforms(lines, rules, changed_only=ns.changed_only):
        out.write(result + "\n")
    return 0


def main() -> None:  # pragma: no cover
    parser = build_transformer_parser()
    ns = parser.parse_args()
    sys.exit(cmd_transform(ns))
