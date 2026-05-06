"""Utilities for detecting and handling rotated log files."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, List, Optional


@dataclass
class RotationState:
    """Tracks inode and size to detect log rotation."""

    path: str
    inode: int
    size: int


def get_rotation_state(path: str) -> Optional[RotationState]:
    """Return a RotationState snapshot for *path*, or None if the file is missing."""
    try:
        st = os.stat(path)
        return RotationState(path=path, inode=st.st_ino, size=st.st_size)
    except FileNotFoundError:
        return None


def has_rotated(previous: RotationState, path: str) -> bool:
    """Return True if the file at *path* has been rotated since *previous* was taken.

    Rotation is detected when the inode changes or the file is smaller than before.
    """
    current = get_rotation_state(path)
    if current is None:
        return True
    return current.inode != previous.inode or current.size < previous.size


def find_rotated_files(base_path: str, max_count: int = 10) -> List[str]:
    """Return a list of rotated log files derived from *base_path*.

    Looks for files named ``<base_path>.1``, ``<base_path>.2``, … up to
    *max_count*, as well as ``<base_path>.1.gz`` variants.
    Returned paths are ordered oldest-first (highest index first).
    """
    found: List[str] = []
    for i in range(max_count, 0, -1):
        for suffix in (f".{i}", f".{i}.gz"):
            candidate = base_path + suffix
            if os.path.isfile(candidate):
                found.append(candidate)
                break
    return found


def iter_with_rotation(
    path: str,
    include_rotated: bool = True,
    max_rotated: int = 10,
) -> Iterator[str]:
    """Yield lines from rotated archives (oldest first) then the live file.

    If *include_rotated* is False only the live file is read.
    """
    sources: List[str] = []
    if include_rotated:
        sources.extend(find_rotated_files(path, max_count=max_rotated))
    sources.append(path)

    for source in sources:
        try:
            opener = _open_maybe_gz(source)
            with opener as fh:
                for line in fh:
                    yield line.rstrip("\n")
        except FileNotFoundError:
            continue


def _open_maybe_gz(path: str):
    """Return an open file handle, using gzip for .gz paths."""
    if path.endswith(".gz"):
        import gzip
        return gzip.open(path, "rt", errors="replace")
    return open(path, "r", errors="replace")
