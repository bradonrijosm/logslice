"""CLI sub-command: logslice profile — activity histogram for a log file."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from logslice.profiler import format_profile, profile_lines


def build_profile_parser(
    parent: Optional[argparse._SubParsersAction] = None,
) -> argparse.ArgumentParser:
    kwargs = dict(
        prog="logslice profile",
        description="Show a time-bucketed activity histogram for a log file.",
    )
    if parent is not None:
        parser = parent.add_parser("profile", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)

    parser.add_argument("file", help="Path to the log file to profile.")
    parser.add_argument(
        "--bucket",
        type=int,
        default=60,
        metavar="SECONDS",
        help="Bucket size in seconds (default: 60).",
    )
    parser.add_argument(
        "--bar-width",
        type=int,
        default=40,
        dest="bar_width",
        metavar="COLS",
        help="Width of histogram bars in characters (default: 40).",
    )
    return parser


def cmd_profile(args: argparse.Namespace, out=sys.stdout) -> int:
    """Execute the profile sub-command. Returns exit code."""
    try:
        with open(args.file, "r", errors="replace") as fh:
            result = profile_lines(fh, bucket_size_seconds=args.bucket)
    except FileNotFoundError:
        out.write(f"error: file not found: {args.file}\n")
        return 1
    except ValueError as exc:
        out.write(f"error: {exc}\n")
        return 1

    out.write(format_profile(result, bar_width=args.bar_width))
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_profile_parser()
    args = parser.parse_args(argv)
    return cmd_profile(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
