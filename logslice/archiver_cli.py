"""CLI commands for compressing and decompressing log slices."""

import argparse
import sys
from typing import Optional, Sequence

from logslice.archiver import CompressionFormat, compress_lines, decompress_lines


def build_archiver_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logslice-archive",
        description="Compress or decompress log files.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # compress sub-command
    comp = sub.add_parser("compress", help="Compress a log file")
    comp.add_argument("input", help="Source log file")
    comp.add_argument("output", help="Destination compressed file")
    comp.add_argument(
        "--format",
        choices=["gz", "bz2"],
        default="gz",
        dest="fmt",
        help="Compression format (default: gz)",
    )

    # decompress sub-command
    decomp = sub.add_parser("decompress", help="Decompress a log file")
    decomp.add_argument("input", help="Compressed source file")
    decomp.add_argument(
        "output",
        nargs="?",
        default=None,
        help="Destination file (omit to print to stdout)",
    )

    return parser


def cmd_compress(ns: argparse.Namespace) -> int:
    try:
        with open(ns.input, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
        count = compress_lines(lines, ns.output, fmt=ns.fmt)
        print(f"Compressed {count} lines -> {ns.output} [{ns.fmt}]")
        return 0
    except Exception as exc:  # pragma: no cover
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_decompress(ns: argparse.Namespace) -> int:
    try:
        lines = decompress_lines(ns.input)
        if ns.output:
            with open(ns.output, "w", encoding="utf-8") as fh:
                fh.write("\n".join(lines))
                if lines:
                    fh.write("\n")
            print(f"Decompressed {len(lines)} lines -> {ns.output}")
        else:
            for line in lines:
                print(line)
        return 0
    except Exception as exc:  # pragma: no cover
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_archiver_parser()
    ns = parser.parse_args(argv)
    if ns.command == "compress":
        return cmd_compress(ns)
    return cmd_decompress(ns)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
