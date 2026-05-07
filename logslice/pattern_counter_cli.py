"""CLI entry-point for the pattern-counter feature."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from logslice.pattern_counter import count_patterns, format_pattern_counts


def build_pattern_counter_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-count",
        description="Count regex pattern occurrences in a log file.",
    )
    p.add_argument("file", help="Path to the log file")
    p.add_argument(
        "-p",
        "--pattern",
        dest="patterns",
        metavar="PATTERN",
        action="append",
        default=[],
        help="Regex pattern to count (may be repeated)",
    )
    p.add_argument(
        "--case-sensitive",
        action="store_true",
        default=False,
        help="Treat patterns as case-sensitive",
    )
    p.add_argument(
        "--max-samples",
        type=int,
        default=3,
        metavar="N",
        help="Max sample lines to show per pattern (default: 3)",
    )
    p.add_argument(
        "--no-samples",
        action="store_true",
        default=False,
        help="Suppress sample lines in output",
    )
    return p


def cmd_count(ns: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    if not ns.patterns:
        err.write("error: at least one --pattern/-p argument is required\n")
        return 2
    try:
        with open(ns.file, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
    except OSError as exc:
        err.write(f"error: {exc}\n")
        return 1

    results = count_patterns(
        lines,
        ns.patterns,
        case_sensitive=ns.case_sensitive,
        max_samples=ns.max_samples,
    )
    out.write(format_pattern_counts(results, show_samples=not ns.no_samples))
    out.write("\n")
    return 0


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_pattern_counter_parser()
    ns = parser.parse_args(argv)
    sys.exit(cmd_count(ns))


if __name__ == "__main__":  # pragma: no cover
    main()
