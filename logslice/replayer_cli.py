"""CLI entry point for the log replayer."""

from __future__ import annotations

import argparse
import sys
from typing import List

from logslice.replayer import replay_lines


def build_replayer_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-replay",
        description="Replay a log file at a controlled speed, simulating live streaming.",
    )
    p.add_argument("file", help="Path to the log file to replay.")
    p.add_argument(
        "--speed",
        type=float,
        default=1.0,
        metavar="FACTOR",
        help="Playback speed multiplier (default: 1.0).",
    )
    p.add_argument(
        "--max-gap",
        type=float,
        default=None,
        metavar="SECONDS",
        dest="max_gap",
        help="Maximum real-time pause between lines in seconds.",
    )
    p.add_argument(
        "--no-timestamps",
        action="store_true",
        default=False,
        help="Ignore timestamps and emit lines immediately.",
    )
    return p


def cmd_replay(ns: argparse.Namespace, out=None) -> int:
    if out is None:
        out = sys.stdout

    speed = ns.speed if not ns.no_timestamps else float("inf")
    max_gap: float | None = ns.max_gap

    # When no_timestamps, force speed so high gaps become 0; simpler: set max_gap=0
    if ns.no_timestamps:
        max_gap = 0.0
        speed = 1.0

    try:
        with open(ns.file, "r", encoding="utf-8", errors="replace") as fh:
            lines = (line.rstrip("\n") for line in fh)
            for event in replay_lines(lines, speed=speed, max_gap=max_gap):
                out.write(event.line + "\n")
    except FileNotFoundError:
        sys.stderr.write(f"logslice-replay: file not found: {ns.file}\n")
        return 1
    except ValueError as exc:
        sys.stderr.write(f"logslice-replay: {exc}\n")
        return 1

    return 0


def main(argv: List[str] | None = None) -> None:
    parser = build_replayer_parser()
    ns = parser.parse_args(argv)
    sys.exit(cmd_replay(ns))


if __name__ == "__main__":  # pragma: no cover
    main()
