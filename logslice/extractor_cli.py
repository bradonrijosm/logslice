"""CLI interface for the field extractor."""
from __future__ import annotations

import argparse
import sys
from typing import List

from logslice.extractor import ExtractRule, extract_fields, format_extracted


def build_extractor_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-extract",
        description="Extract named fields from log lines using regex patterns.",
    )
    p.add_argument("logfile", help="Path to the log file (use - for stdin).")
    p.add_argument(
        "--field",
        dest="fields",
        metavar="NAME:PATTERN",
        action="append",
        default=[],
        help="Field definition as NAME:PATTERN (repeatable).",
    )
    p.add_argument(
        "--separator",
        default="\t",
        help="Output column separator (default: tab).",
    )
    p.add_argument(
        "--missing",
        default="-",
        help="Placeholder for unmatched fields (default: -).",
    )
    p.add_argument(
        "--case-sensitive",
        action="store_true",
        default=False,
        help="Make pattern matching case-sensitive.",
    )
    return p


def _parse_rules(raw: List[str], case_sensitive: bool) -> List[ExtractRule]:
    rules: List[ExtractRule] = []
    for item in raw:
        name, _, pattern = item.partition(":")
        if not name or not pattern:
            raise ValueError(f"Invalid field spec {item!r}; expected NAME:PATTERN")
        rules.append(ExtractRule(name=name.strip(), pattern=pattern.strip(),
                                 case_sensitive=case_sensitive))
    return rules


def cmd_extract(ns: argparse.Namespace) -> int:
    rules = _parse_rules(ns.fields, ns.case_sensitive)
    if not rules:
        print("error: at least one --field is required", file=sys.stderr)
        return 1

    fh = sys.stdin if ns.logfile == "-" else open(ns.logfile)
    try:
        extracted = extract_fields(fh, rules)
        for row in format_extracted(extracted, separator=ns.separator,
                                    missing=ns.missing):
            print(row)
    finally:
        if fh is not sys.stdin:
            fh.close()
    return 0


def main() -> None:  # pragma: no cover
    parser = build_extractor_parser()
    ns = parser.parse_args()
    sys.exit(cmd_extract(ns))
