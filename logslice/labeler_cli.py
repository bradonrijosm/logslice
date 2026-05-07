"""CLI entry-point for the labeler feature."""

from __future__ import annotations

import argparse
import sys
from typing import List

from logslice.labeler import LabelRule, label_lines


def build_labeler_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logslice-label",
        description="Attach labels to log lines that match regex patterns.",
    )
    parser.add_argument("logfile", help="Path to the log file to process.")
    parser.add_argument(
        "--rule",
        metavar="LABEL:PATTERN",
        action="append",
        dest="rules",
        default=[],
        help="Label rule in LABEL:PATTERN format. May be repeated.",
    )
    parser.add_argument(
        "--case-sensitive",
        action="store_true",
        default=False,
        help="Make pattern matching case-sensitive.",
    )
    parser.add_argument(
        "--labeled-only",
        action="store_true",
        default=False,
        help="Only output lines that received at least one label.",
    )
    parser.add_argument(
        "--separator",
        default=" ",
        help="Separator between label tags and the line text (default: space).",
    )
    return parser


def _parse_rules(raw: List[str], case_sensitive: bool) -> List[LabelRule]:
    rules: List[LabelRule] = []
    for item in raw:
        if ":" not in item:
            raise ValueError(f"Rule must be in LABEL:PATTERN format, got: {item!r}")
        label, _, pattern = item.partition(":")
        rules.append(LabelRule(label=label.strip(), pattern=pattern, case_sensitive=case_sensitive))
    return rules


def cmd_label(ns: argparse.Namespace, out=sys.stdout) -> int:
    try:
        rules = _parse_rules(ns.rules, ns.case_sensitive)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    try:
        with open(ns.logfile, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    for labeled in label_lines(lines, rules, labeled_only=ns.labeled_only):
        out.write(labeled.formatted(separator=ns.separator))
        if not labeled.line.endswith("\n"):
            out.write("\n")
    return 0


def main() -> None:  # pragma: no cover
    parser = build_labeler_parser()
    ns = parser.parse_args()
    sys.exit(cmd_label(ns))
