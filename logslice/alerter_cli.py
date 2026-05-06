"""CLI entry-point for the alerter feature."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from logslice.alerter import AlertRule, format_alert, run_alerts


def build_alerter_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-alert",
        description="Scan a log file and fire alerts when rules match.",
    )
    p.add_argument("file", type=Path, help="Log file to scan")
    p.add_argument(
        "--rule",
        dest="rules",
        metavar="NAME:PATTERN",
        action="append",
        default=[],
        help="Alert rule in NAME:PATTERN format (repeatable)",
    )
    p.add_argument(
        "--level",
        default=None,
        help="Restrict alerts to lines containing this log level",
    )
    p.add_argument(
        "--case-sensitive",
        action="store_true",
        default=False,
    )
    p.add_argument(
        "--count-only",
        action="store_true",
        default=False,
        help="Print only the total number of alert events",
    )
    return p


def cmd_alert(args: argparse.Namespace, out=sys.stdout) -> int:
    rules: list[AlertRule] = []
    for raw in args.rules:
        if ":" not in raw:
            out.write(f"Invalid rule (expected NAME:PATTERN): {raw}\n")
            return 1
        name, _, pattern = raw.partition(":")
        rules.append(
            AlertRule(
                name=name.strip(),
                pattern=pattern.strip(),
                level=args.level,
                case_sensitive=args.case_sensitive,
            )
        )

    if not rules:
        out.write("No rules specified. Use --rule NAME:PATTERN.\n")
        return 1

    lines = args.file.read_text(encoding="utf-8").splitlines()
    events = run_alerts(lines, rules)

    if args.count_only:
        out.write(f"{len(events)}\n")
    else:
        for event in events:
            out.write(format_alert(event) + "\n")

    return 0


def main() -> None:  # pragma: no cover
    parser = build_alerter_parser()
    args = parser.parse_args()
    sys.exit(cmd_alert(args))
