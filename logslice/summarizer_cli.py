"""CLI entry-point for the summarizer feature."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from logslice.summarizer import summarize_lines, format_summary_report


def build_summarizer_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-summarize",
        description="Print a condensed summary of a log file.",
    )
    p.add_argument("file", help="Path to the log file.")
    p.add_argument(
        "--top",
        type=int,
        default=5,
        metavar="N",
        help="Number of top repeated lines to show (default: 5).",
    )
    p.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output summary as JSON.",
    )
    return p


def cmd_summarize(ns: argparse.Namespace, out=sys.stdout) -> int:
    path = Path(ns.file)
    if not path.is_file():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1

    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    report = summarize_lines(lines, top_n=ns.top)

    if ns.json:
        import json
        data = {
            "total_lines": report.total_lines,
            "unique_lines": report.unique_lines,
            "duplicate_lines": report.duplicate_lines,
            "level_counts": report.level_counts,
            "first_timestamp": report.first_timestamp,
            "last_timestamp": report.last_timestamp,
            "top_lines": report.top_lines,
        }
        out.write(json.dumps(data, indent=2) + "\n")
    else:
        out.write(format_summary_report(report) + "\n")
    return 0


def main(argv=None) -> None:
    parser = build_summarizer_parser()
    ns = parser.parse_args(argv)
    sys.exit(cmd_summarize(ns))


if __name__ == "__main__":
    main()
