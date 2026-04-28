"""Command-line interface for logslice."""

import argparse
import sys
from typing import Optional

from logslice.parser import parse_datetime_arg
from logslice.slicer import slice_log, count_lines
from logslice.formatter import format_lines, format_summary, format_no_match
from logslice.highlighter import highlight_lines


def build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="logslice",
        description="Extract time-range slices from large log files.",
    )
    parser.add_argument("logfile", help="Path to the log file to slice.")
    parser.add_argument(
        "--start",
        default=None,
        metavar="DATETIME",
        help="Start of the time range (inclusive).",
    )
    parser.add_argument(
        "--end",
        default=None,
        metavar="DATETIME",
        help="End of the time range (inclusive).",
    )
    parser.add_argument(
        "-n",
        "--line-numbers",
        action="store_true",
        default=False,
        help="Prefix each output line with its line number.",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        default=False,
        help="Print a summary of matched vs total lines after output.",
    )
    parser.add_argument(
        "--highlight",
        nargs="+",
        metavar="KEYWORD",
        default=[],
        help="Highlight one or more keywords in the output.",
    )
    parser.add_argument(
        "--highlight-color",
        choices=["yellow", "red"],
        default="yellow",
        help="Color to use for keyword highlighting (default: yellow).",
    )
    return parser


def main(argv: Optional[list] = None) -> int:
    """Entry point for the logslice CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    start = parse_datetime_arg(args.start) if args.start else None
    end = parse_datetime_arg(args.end) if args.end else None

    try:
        lines, total = slice_log(args.logfile, start=start, end=end)
    except FileNotFoundError:
        print(f"logslice: error: file not found: {args.logfile}", file=sys.stderr)
        return 1

    if not lines:
        print(format_no_match())
        return 0

    if args.highlight:
        lines = highlight_lines(
            lines, args.highlight, color=args.highlight_color
        )

    matched = format_lines(lines, line_numbers=args.line_numbers)

    if args.summary:
        print(format_summary(matched, total))

    return 0
