"""CLI entry-point for the timeline feature."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from logslice.timeline import build_timeline, format_timeline


def build_timeline_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-timeline",
        description="Display a bucketed timeline of log activity.",
    )
    p.add_argument("file", help="Path to the log file.")
    p.add_argument(
        "--bucket",
        type=int,
        default=60,
        metavar="SECONDS",
        help="Bucket width in seconds (default: 60).",
    )
    p.add_argument(
        "--bar-width",
        type=int,
        default=40,
        dest="bar_width",
        help="Width of the ASCII bar (default: 40).",
    )
    p.add_argument(
        "--keep-lines",
        action="store_true",
        dest="keep_lines",
        help="Store matched lines inside each bucket (for debugging).",
    )
    return p


def cmd_timeline(ns: argparse.Namespace, out=sys.stdout) -> int:
    try:
        with open(ns.file, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    tl = build_timeline(lines, bucket_seconds=ns.bucket, keep_lines=ns.keep_lines)
    rendered = format_timeline(tl, bar_width=ns.bar_width)
    print(rendered, file=out)
    return 0


def main(argv: Optional[List[str]] = None) -> None:  # pragma: no cover
    parser = build_timeline_parser()
    ns = parser.parse_args(argv)
    sys.exit(cmd_timeline(ns))


if __name__ == "__main__":  # pragma: no cover
    main()
