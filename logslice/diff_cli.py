"""CLI helpers for the `logslice diff` sub-command."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from logslice.differ import count_changes, diff_lines, format_diff


def _read_lines(path: str) -> List[str]:
    """Read a file and return lines stripped of trailing newlines."""
    return Path(path).read_text(encoding="utf-8").splitlines()


def build_diff_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:
    """Build (or register) the argument parser for the diff sub-command."""
    kwargs = dict(
        description="Show a structured diff between two log files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    if parent is not None:
        parser = parent.add_parser("diff", **kwargs)
    else:
        parser = argparse.ArgumentParser(prog="logslice diff", **kwargs)

    parser.add_argument("file_a", metavar="FILE_A", help="Original log file.")
    parser.add_argument("file_b", metavar="FILE_B", help="Modified log file.")
    parser.add_argument(
        "-c", "--context",
        type=int,
        default=3,
        metavar="N",
        help="Lines of context around each change (default: 3).",
    )
    parser.add_argument(
        "--color",
        action="store_true",
        default=False,
        help="Enable ANSI colour output.",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        default=False,
        help="Print only the change summary, not the full diff.",
    )
    return parser


def cmd_diff(args: argparse.Namespace) -> int:
    """Execute the diff command.  Returns an exit code."""
    try:
        lines_a = _read_lines(args.file_a)
        lines_b = _read_lines(args.file_b)
    except OSError as exc:
        print(f"logslice diff: error reading file: {exc}", file=sys.stderr)
        return 1

    diff = diff_lines(
        lines_a,
        lines_b,
        context=args.context,
        label_a=args.file_a,
        label_b=args.file_b,
    )

    added, removed = count_changes(diff)

    if not args.summary:
        for line in format_diff(diff, color=args.color):
            print(line)

    print(f"--- {args.file_a}")
    print(f"+++ {args.file_b}")
    print(f"+{added} lines added, -{removed} lines removed.")

    return 0 if (added + removed) == 0 else 1


def main(argv: List[str] | None = None) -> int:  # pragma: no cover
    parser = build_diff_parser()
    args = parser.parse_args(argv)
    return cmd_diff(args)
