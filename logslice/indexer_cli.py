"""CLI commands for building and querying log file indexes."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from logslice.indexer import build_index, load_index, save_index


def build_indexer_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logslice-index",
        description="Build or query a byte-offset index for a log file.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # build sub-command
    build_p = sub.add_parser("build", help="Build an index file.")
    build_p.add_argument("log", type=Path, help="Log file to index.")
    build_p.add_argument("--out", type=Path, default=None,
                         help="Output path (default: <log>.idx).")
    build_p.add_argument("--every", type=int, default=1, metavar="N",
                         help="Record every Nth line (default: 1).")

    # query sub-command
    query_p = sub.add_parser("query", help="Find byte offset for a timestamp.")
    query_p.add_argument("index", type=Path, help="Index file.")
    query_p.add_argument("timestamp", help="Timestamp prefix to search for.")

    return parser


def cmd_build(ns: argparse.Namespace) -> int:
    out = ns.out or ns.log.with_suffix(".idx")
    index = build_index(ns.log, every_nth=ns.every)
    save_index(index, out)
    print(f"Indexed {len(index)} entries → {out}")
    return 0


def cmd_query(ns: argparse.Namespace) -> int:
    index = load_index(ns.index)
    offset = index.find_offset(ns.timestamp)
    if offset == -1:
        print(f"No entry found for timestamp >= {ns.timestamp!r}",
              file=sys.stderr)
        return 1
    print(offset)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_indexer_parser()
    ns = parser.parse_args(argv)
    if ns.command == "build":
        return cmd_build(ns)
    return cmd_query(ns)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
