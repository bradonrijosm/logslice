"""CLI entry-point for the scorer feature."""
from __future__ import annotations

import argparse
import sys
from typing import List

from logslice.scorer import format_scored, score_lines, top_scored


def build_scorer_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-score",
        description="Score log lines by keyword relevance.",
    )
    p.add_argument("file", help="Log file to score")
    p.add_argument(
        "--keyword",
        metavar="WORD:WEIGHT",
        action="append",
        dest="keywords",
        default=[],
        help="Keyword and numeric weight (e.g. ERROR:3.0). Repeatable.",
    )
    p.add_argument(
        "--threshold",
        type=float,
        default=0.0,
        help="Minimum score to include a line (default: 0.0)",
    )
    p.add_argument(
        "--top",
        type=int,
        default=0,
        help="Show only the top N results (0 = all matching lines)",
    )
    p.add_argument(
        "--show-keywords",
        action="store_true",
        default=False,
        help="Annotate output with matched keywords",
    )
    p.add_argument(
        "--case-sensitive",
        action="store_true",
        default=False,
    )
    return p


def _parse_weights(raw: List[str]) -> dict:
    weights: dict = {}
    for item in raw:
        if ":" in item:
            word, _, raw_weight = item.rpartition(":")
            try:
                weights[word] = float(raw_weight)
            except ValueError:
                weights[item] = 1.0
        else:
            weights[item] = 1.0
    return weights


def cmd_score(args: argparse.Namespace, out=sys.stdout) -> int:
    weights = _parse_weights(args.keywords)
    if not weights:
        out.write("No keywords specified. Use --keyword WORD:WEIGHT.\n")
        return 1
    with open(args.file, "r", errors="replace") as fh:
        lines = [l.rstrip("\n") for l in fh]
    if args.top > 0:
        results = top_scored(lines, weights, n=args.top, case_sensitive=args.case_sensitive)
    else:
        results = score_lines(
            lines, weights, case_sensitive=args.case_sensitive, threshold=args.threshold
        )
    formatted = format_scored(results, show_score=True, show_keywords=args.show_keywords)
    for line in formatted:
        out.write(line + "\n")
    return 0


def main(argv=None) -> None:
    parser = build_scorer_parser()
    args = parser.parse_args(argv)
    sys.exit(cmd_score(args))


if __name__ == "__main__":
    main()
