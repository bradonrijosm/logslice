"""CLI entry-point for the log grouper."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from logslice.grouper import format_groups, group_lines


def build_grouper_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-group",
        description="Group log lines by a regex capture group.",
    )
    p.add_argument("file", help="Path to the log file (use '-' for stdin).")
    p.add_argument(
        "--pattern",
        required=True,
        help="Regex with at least one capture group used as the bucket key.",
    )
    p.add_argument(
        "--group",
        type=int,
        default=1,
        help="Which capture group number to use as the key (default: 1).",
    )
    p.add_argument(
        "--case-sensitive",
        action="store_true",
        default=False,
        help="Use case-sensitive matching (default: case-insensitive).",
    )
    p.add_argument(
        "--default-key",
        default="__ungrouped__",
        help="Key used for lines that do not match the pattern.",
    )
    p.add_argument(
        "--separator",
        default="---",
        help="Separator printed between groups (default: '---').",
    )
    return p


def cmd_group(ns: argparse.Namespace, out=sys.stdout) -> int:
    if ns.file == "-":
        lines: List[str] = [l.rstrip("\n") for l in sys.stdin]
    else:
        with open(ns.file) as fh:
            lines = [l.rstrip("\n") for l in fh]

    groups = group_lines(
        lines,
        pattern=ns.pattern,
        group=ns.group,
        case_sensitive=ns.case_sensitive,
        default_key=ns.default_key,
    )
    out.write(format_groups(groups, separator=ns.separator))
    out.write("\n")
    return 0


def main(argv: Optional[List[str]] = None) -> None:  # pragma: no cover
    parser = build_grouper_parser()
    ns = parser.parse_args(argv)
    sys.exit(cmd_group(ns))
