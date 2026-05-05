"""CLI entry point for the tagger module."""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from logslice.tagger import TagRule, collect_tags, filter_by_tag, tag_lines


def build_tagger_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-tag",
        description="Tag log lines with labels based on regex patterns.",
    )
    p.add_argument("file", help="Path to the log file.")
    p.add_argument(
        "--rule",
        metavar="TAG:PATTERN",
        action="append",
        dest="rules",
        default=[],
        help="Tag rule in TAG:PATTERN format. May be repeated.",
    )
    p.add_argument(
        "--filter-tag",
        metavar="TAG",
        default=None,
        help="Only output lines that carry this tag.",
    )
    p.add_argument(
        "--summary",
        action="store_true",
        default=False,
        help="Print a tag frequency summary instead of tagged lines.",
    )
    p.add_argument(
        "--case-sensitive",
        action="store_true",
        default=False,
        help="Make pattern matching case-sensitive.",
    )
    return p


def cmd_tag(args: argparse.Namespace, out=sys.stdout) -> int:
    rules: list[TagRule] = []
    for raw in args.rules:
        if ":" not in raw:
            out.write(f"Invalid rule (expected TAG:PATTERN): {raw!r}\n")
            return 1
        tag, _, pattern = raw.partition(":")
        rules.append(
            TagRule(tag=tag.strip(), pattern=pattern.strip(),
                    case_sensitive=args.case_sensitive)
        )

    try:
        with open(args.file, "r", encoding="utf-8", errors="replace") as fh:
            raw_lines = [line.rstrip("\n") for line in fh]
    except OSError as exc:
        out.write(f"Cannot open file: {exc}\n")
        return 1

    tagged = list(tag_lines(raw_lines, rules))

    if args.summary:
        counts = collect_tags(tagged)
        if not counts:
            out.write("No tags matched.\n")
        else:
            for tag, n in sorted(counts.items(), key=lambda kv: -kv[1]):
                out.write(f"{tag}: {n}\n")
        return 0

    results = (
        filter_by_tag(tagged, args.filter_tag)
        if args.filter_tag
        else tagged
    )
    for tl in results:
        out.write(str(tl) + "\n")
    return 0


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_tagger_parser()
    args = parser.parse_args(argv)
    sys.exit(cmd_tag(args))
