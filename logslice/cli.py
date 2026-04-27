"""Command-line interface for logslice."""

import argparse
import sys
from typing import List, Optional

from logslice.parser import parse_datetime_arg
from logslice.slicer import slice_log, count_lines


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logslice",
        description="Extract time-range slices from large log files.",
    )
    parser.add_argument("file", help="Path to the log file.")
    parser.add_argument(
        "--start", "-s",
        metavar="DATETIME",
        help="Start of the time range (inclusive). E.g. 2024-01-15T08:00:00",
    )
    parser.add_argument(
        "--end", "-e",
        metavar="DATETIME",
        help="End of the time range (inclusive). E.g. 2024-01-15T17:00:00",
    )
    parser.add_argument(
        "--count", "-c",
        action="store_true",
        help="Print the number of matching lines instead of the lines themselves.",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="Log file encoding (default: utf-8).",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    start = None
    end = None

    try:
        if args.start:
            start = parse_datetime_arg(args.start)
        if args.end:
            end = parse_datetime_arg(args.end)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    try:
        if args.count:
            print(count_lines(args.file, start, end, args.encoding))
        else:
            for line in slice_log(args.file, start, end, args.encoding):
                print(line)
    except FileNotFoundError:
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Error reading file: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
