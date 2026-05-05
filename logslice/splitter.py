"""Split a large log file into smaller chunk files by line count or time window."""

from __future__ import annotations

import os
from typing import Iterator, List, Optional

from logslice.parser import extract_timestamp


def _chunk_path(base: str, index: int, suffix: str = ".log") -> str:
    """Build an output path like base_000.log, base_001.log, …"""
    root, ext = os.path.splitext(base)
    if not ext:
        ext = suffix
    return f"{root}_{index:03d}{ext}"


def split_by_lines(
    lines: List[str],
    chunk_size: int,
) -> Iterator[List[str]]:
    """Yield successive chunks of *chunk_size* lines."""
    if chunk_size < 1:
        raise ValueError("chunk_size must be >= 1")
    for start in range(0, len(lines), chunk_size):
        yield lines[start : start + chunk_size]


def split_by_time(
    lines: List[str],
    window_seconds: float,
) -> Iterator[List[str]]:
    """Yield chunks where all lines fall within *window_seconds* of the first
    timestamped line in that chunk."""
    if window_seconds <= 0:
        raise ValueError("window_seconds must be > 0")

    chunk: List[str] = []
    window_start: Optional[float] = None

    for line in lines:
        ts = extract_timestamp(line)
        if ts is None:
            chunk.append(line)
            continue

        epoch = ts.timestamp()
        if window_start is None:
            window_start = epoch

        if epoch - window_start > window_seconds:
            if chunk:
                yield chunk
            chunk = [line]
            window_start = epoch
        else:
            chunk.append(line)

    if chunk:
        yield chunk


def write_chunks(
    chunks: Iterator[List[str]],
    output_base: str,
) -> List[str]:
    """Write each chunk to a numbered file; return the list of paths written."""
    paths: List[str] = []
    for index, chunk in enumerate(chunks):
        path = _chunk_path(output_base, index)
        with open(path, "w", encoding="utf-8") as fh:
            fh.writelines(chunk)
        paths.append(path)
    return paths
