"""CLI entry-point for the log classifier."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from logslice.classifier import ClassifyRule, classify_lines, group_by_category


def build_classifier_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-classify",
        description="Classify log lines into categories using pattern rules.",
    )
    p.add_argument("logfile", help="Path to the log file (use '-' for stdin).")
    p.add_argument(
        "--rules",
        required=True,
        metavar="JSON",
        help=(
            'JSON array of rule objects, e.g. '
            '[{"category":"ERROR","pattern":"error"}]'
        ),
    )
    p.add_argument(
        "--default",
        default=None,
        metavar="LABEL",
        help="Category label for lines that match no rule (default: none).",
    )
    p.add_argument(
        "--unmatched-only",
        action="store_true",
        help="Print only lines that were not matched by any rule.",
    )
    p.add_argument(
        "--summary",
        action="store_true",
        help="Print a category count summary instead of individual lines.",
    )
    return p


def cmd_classify(args: argparse.Namespace, out=sys.stdout) -> int:
    raw_rules: List[dict] = json.loads(args.rules)
    rules = [
        ClassifyRule(
            category=r["category"],
            pattern=r["pattern"],
            case_sensitive=r.get("case_sensitive", False),
        )
        for r in raw_rules
    ]

    if args.logfile == "-":
        lines = [line.rstrip("\n") for line in sys.stdin]
    else:
        with open(args.logfile, encoding="utf-8") as fh:
            lines = [line.rstrip("\n") for line in fh]

    classified = list(classify_lines(lines, rules, default=args.default))

    if args.summary:
        groups = group_by_category(classified)
        for cat in sorted(str(k) for k in groups):
            out.write(f"{cat}: {len(groups.get(cat, []))!s}\n")  # type: ignore[arg-type]
        return 0

    for cl in classified:
        if args.unmatched_only and cl.is_classified:
            continue
        prefix = f"[{cl.category}] " if cl.category else "[?] "
        out.write(prefix + cl.line + "\n")

    return 0


def main() -> None:  # pragma: no cover
    parser = build_classifier_parser()
    args = parser.parse_args()
    sys.exit(cmd_classify(args))
