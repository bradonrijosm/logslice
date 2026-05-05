"""CLI sub-commands for bookmark management."""

from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional

from logslice.bookmarks import (
    Bookmark,
    delete_bookmark,
    list_bookmarks,
    load_bookmark,
    save_bookmark,
)

DEFAULT_STORE = os.path.join(os.path.expanduser("~"), ".logslice_bookmarks.json")


def _store_path(args: argparse.Namespace) -> str:
    return getattr(args, "store", None) or DEFAULT_STORE


def cmd_save(args: argparse.Namespace) -> int:
    bm = Bookmark(
        name=args.name,
        file_path=args.file,
        start=args.start,
        end=args.end,
    )
    save_bookmark(bm, _store_path(args))
    print(f"Bookmark '{args.name}' saved.")
    return 0


def cmd_load(args: argparse.Namespace) -> int:
    bm = load_bookmark(args.name, _store_path(args))
    if bm is None:
        print(f"No bookmark named '{args.name}'.", file=sys.stderr)
        return 1
    print(f"file={bm.file_path}  start={bm.start}  end={bm.end}")
    return 0


def cmd_delete(args: argparse.Namespace) -> int:
    removed = delete_bookmark(args.name, _store_path(args))
    if not removed:
        print(f"Bookmark '{args.name}' not found.", file=sys.stderr)
        return 1
    print(f"Bookmark '{args.name}' deleted.")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    bookmarks = list_bookmarks(_store_path(args))
    if not bookmarks:
        print("No bookmarks saved.")
        return 0
    for bm in bookmarks:
        print(f"{bm.name:20s}  {bm.file_path}  [{bm.start} -> {bm.end}]")
    return 0


def build_bookmark_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    bp = subparsers.add_parser("bookmark", help="Manage named log bookmarks")
    bp.add_argument("--store", default=None, help="Path to bookmark store JSON")
    bsub = bp.add_subparsers(dest="bookmark_cmd", required=True)

    ps = bsub.add_parser("save", help="Save a bookmark")
    ps.add_argument("name")
    ps.add_argument("file")
    ps.add_argument("--start", default=None)
    ps.add_argument("--end", default=None)
    ps.set_defaults(func=cmd_save)

    pl = bsub.add_parser("load", help="Show a bookmark")
    pl.add_argument("name")
    pl.set_defaults(func=cmd_load)

    pd = bsub.add_parser("delete", help="Delete a bookmark")
    pd.add_argument("name")
    pd.set_defaults(func=cmd_delete)

    pli = bsub.add_parser("list", help="List all bookmarks")
    pli.set_defaults(func=cmd_list)
