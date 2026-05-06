"""watchdog_cli.py — CLI entry-point for the live log-watching feature."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from logslice.watchdog import tail_file


def build_watchdog_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-watch",
        description="Tail a log file and print new lines as they arrive.",
    )
    p.add_argument("file", help="Log file to watch.")
    p.add_argument(
        "--pattern",
        default=None,
        metavar="REGEX",
        help="Only show lines matching this regular expression.",
    )
    p.add_argument(
        "--level",
        default=None,
        metavar="LEVEL",
        help="Only show lines containing this log level (case-insensitive).",
    )
    p.add_argument(
        "--max-lines",
        type=int,
        default=None,
        metavar="N",
        help="Stop after printing N matching lines.",
    )
    p.add_argument(
        "--poll",
        type=float,
        default=0.5,
        metavar="SECONDS",
        help="Polling interval in seconds (default: 0.5).",
    )
    return p


def cmd_watch(args: argparse.Namespace, out=sys.stdout) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1

    predicates = []
    if args.pattern:
        rx = re.compile(args.pattern)
        predicates.append(lambda line, _rx=rx: bool(_rx.search(line)))
    if args.level:
        lvl = args.level.upper()
        predicates.append(lambda line, _lvl=lvl: _lvl in line.upper())

    def combined(line: str) -> bool:
        return all(p(line) for p in predicates)

    predicate = combined if predicates else None

    try:
        for line in tail_file(
            path,
            poll_interval=args.poll,
            predicate=predicate,
            max_lines=args.max_lines,
        ):
            out.write(line + "\n")
            out.flush()
    except KeyboardInterrupt:
        pass

    return 0


def main(argv=None) -> None:
    parser = build_watchdog_parser()
    args = parser.parse_args(argv)
    sys.exit(cmd_watch(args))


if __name__ == "__main__":  # pragma: no cover
    main()
