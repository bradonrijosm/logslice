"""CLI entry-point for the correlator feature."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from logslice.correlator import group_by_correlation, iter_correlated


def build_correlator_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-correlate",
        description="Group or filter log lines by a shared correlation/trace ID.",
    )
    p.add_argument("logfile", help="Path to the log file (use '-' for stdin).")
    p.add_argument(
        "--id",
        dest="correlation_id",
        default=None,
        help="Filter to lines matching this specific correlation ID.",
    )
    p.add_argument(
        "--list",
        dest="list_ids",
        action="store_true",
        help="Print all discovered correlation IDs and their line counts.",
    )
    p.add_argument(
        "--pattern",
        dest="patterns",
        action="append",
        default=None,
        metavar="REGEX",
        help="Custom extraction pattern (may be given multiple times).",
    )
    p.add_argument(
        "--case-sensitive",
        action="store_true",
        default=False,
        help="Use case-sensitive pattern matching.",
    )
    return p


def cmd_correlate(args: argparse.Namespace, out=sys.stdout) -> int:
    if args.logfile == "-":
        raw_lines: List[str] = sys.stdin.readlines()
    else:
        with open(args.logfile) as fh:
            raw_lines = fh.readlines()

    lines = [ln.rstrip("\n") for ln in raw_lines]

    if args.list_ids:
        groups = group_by_correlation(
            lines, patterns=args.patterns, case_sensitive=args.case_sensitive
        )
        for cid, grp in sorted(groups.items(), key=lambda kv: -len(kv[1].lines)):
            label = cid if cid else "<no-id>"
            out.write(f"{label}\t{len(grp.lines)}\n")
        return 0

    if args.correlation_id:
        matched = list(
            iter_correlated(
                lines,
                args.correlation_id,
                patterns=args.patterns,
                case_sensitive=args.case_sensitive,
            )
        )
        for ln in matched:
            out.write(ln + "\n")
        return 0

    out.write("Specify --id <ID> or --list.\n")
    return 1


def main(argv: Optional[List[str]] = None) -> None:  # pragma: no cover
    parser = build_correlator_parser()
    args = parser.parse_args(argv)
    sys.exit(cmd_correlate(args))
