"""CLI entry-point for the dispatcher feature."""
from __future__ import annotations

import argparse
import sys
from typing import List

from logslice.dispatcher import DispatchRule, dispatch_lines, group_by_channel, channel_summary


def build_dispatcher_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-dispatch",
        description="Route log lines to named channels via pattern rules.",
    )
    p.add_argument("logfile", help="Path to the log file (use '-' for stdin).")
    p.add_argument(
        "--rule",
        dest="rules",
        metavar="CHANNEL:PATTERN",
        action="append",
        default=[],
        help="Dispatch rule in CHANNEL:PATTERN format. May be repeated.",
    )
    p.add_argument(
        "--default-channel",
        default="default",
        help="Channel name for unmatched lines (default: 'default').",
    )
    p.add_argument(
        "--case-sensitive",
        action="store_true",
        default=False,
        help="Apply patterns case-sensitively.",
    )
    p.add_argument(
        "--summary",
        action="store_true",
        default=False,
        help="Print a per-channel line count instead of the lines themselves.",
    )
    return p


def _parse_rules(raw: List[str], case_sensitive: bool) -> List[DispatchRule]:
    rules: List[DispatchRule] = []
    for token in raw:
        channel, _, pattern = token.partition(":")
        if not pattern:
            raise ValueError(f"Invalid rule (expected CHANNEL:PATTERN): {token!r}")
        rules.append(DispatchRule(channel=channel.strip(), pattern=pattern.strip(), case_sensitive=case_sensitive))
    return rules


def cmd_dispatch(ns: argparse.Namespace) -> int:
    try:
        rules = _parse_rules(ns.rules, ns.case_sensitive)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if ns.logfile == "-":
        raw_lines = (line.rstrip("\n") for line in sys.stdin)
    else:
        try:
            fh = open(ns.logfile)
        except OSError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        raw_lines = (line.rstrip("\n") for line in fh)

    groups = group_by_channel(dispatch_lines(raw_lines, rules, ns.default_channel))

    if ns.summary:
        for channel, count in channel_summary(groups):
            print(f"{channel}: {count}")
    else:
        for channel, lines in sorted(groups.items()):
            for line in lines:
                print(f"[{channel}] {line}")

    return 0


def main() -> None:  # pragma: no cover
    sys.exit(cmd_dispatch(build_dispatcher_parser().parse_args()))
