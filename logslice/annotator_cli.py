"""CLI entry-point for the annotator feature."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from logslice.annotator import format_annotated


def build_annotator_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-annotate",
        description="Annotate log lines with line numbers, source tags, and time offsets.",
    )
    p.add_argument("file", help="Log file to annotate (use '-' for stdin)")
    p.add_argument("--tag", default=None, metavar="TAG", help="Source tag to prefix each line")
    p.add_argument("--start", type=int, default=1, metavar="N", help="Starting line number (default: 1)")
    p.add_argument("--no-lineno", dest="show_lineno", action="store_false", help="Omit line numbers")
    p.add_argument("--no-offset", dest="show_offset", action="store_false", help="Omit time offsets")
    p.add_argument("--no-tag", dest="show_tag", action="store_false", help="Omit source tag")
    return p


def cmd_annotate(ns: argparse.Namespace, out=sys.stdout) -> int:
    fh = sys.stdin if ns.file == "-" else open(ns.file, "r", encoding="utf-8", errors="replace")
    try:
        for rendered in format_annotated(
            fh,
            source_tag=ns.tag,
            start_lineno=ns.start,
            show_lineno=ns.show_lineno,
            show_tag=ns.show_tag,
            show_offset=ns.show_offset,
        ):
            out.write(rendered + "\n")
    finally:
        if fh is not sys.stdin:
            fh.close()
    return 0


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_annotator_parser()
    ns = parser.parse_args(argv)
    sys.exit(cmd_annotate(ns))


if __name__ == "__main__":  # pragma: no cover
    main()
