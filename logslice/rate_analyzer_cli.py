"""CLI entry-point for the rate-analyzer feature."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from logslice.rate_analyzer import analyze_rate, format_rate_report


def build_rate_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-rate",
        description="Analyse event rates in a log file over fixed time windows.",
    )
    p.add_argument("file", help="Path to the log file (use '-' for stdin).")
    p.add_argument(
        "--window",
        type=int,
        default=60,
        metavar="SECONDS",
        help="Bucket window size in seconds (default: 60).",
    )
    p.add_argument(
        "--include-lines",
        action="store_true",
        default=False,
        help="Include matched lines in each bucket (verbose).",
    )
    p.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output report as JSON.",
    )
    return p


def cmd_rate(ns: argparse.Namespace, out=sys.stdout) -> int:
    import json

    if ns.file == "-":
        lines: List[str] = sys.stdin.read().splitlines()
    else:
        with open(ns.file, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()

    report = analyze_rate(
        lines,
        window_seconds=ns.window,
        include_lines=ns.include_lines,
    )

    if ns.json:
        payload = {
            "window_seconds": report.window_seconds,
            "total_lines": report.total_lines,
            "average_rate": report.average_rate,
            "peak_bucket": (
                {"key": report.peak_bucket.key, "count": report.peak_bucket.count}
                if report.peak_bucket
                else None
            ),
            "buckets": [
                {"key": b.key, "count": b.count}
                for b in report.buckets
            ],
        }
        out.write(json.dumps(payload, indent=2))
        out.write("\n")
    else:
        out.write(format_rate_report(report))
        out.write("\n")

    return 0


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_rate_parser()
    ns = parser.parse_args(argv)
    sys.exit(cmd_rate(ns))


if __name__ == "__main__":  # pragma: no cover
    main()
