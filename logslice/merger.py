"""Merge and interleave multiple sorted log line sequences by timestamp."""

from typing import Iterable, Iterator, List, Optional, Tuple
import heapq

from logslice.parser import extract_timestamp


def _timestamped(lines: Iterable[str], source: str) -> Iterator[Tuple]:
    """Yield (timestamp_or_none, index, source, line) tuples for heap ordering."""
    for idx, line in enumerate(lines):
        ts = extract_timestamp(line)
        # Lines without timestamps sort after those with timestamps
        sort_key = (0, ts.isoformat()) if ts is not None else (1, "")
        yield (sort_key, idx, source, line)


def merge_logs(
    sources: List[Tuple[str, Iterable[str]]],
    stable: bool = True,
) -> Iterator[str]:
    """Merge multiple log line iterables, interleaving by timestamp.

    Args:
        sources: List of (name, iterable_of_lines) pairs.
        stable: If True, preserve original order for lines with equal timestamps.

    Yields:
        Lines interleaved in timestamp order.
    """
    iterators = [
        _timestamped(lines, name)
        for name, lines in sources
    ]

    heap: List[Tuple] = []
    # Bootstrap the heap with the first item from each iterator
    iters = [iter(it) for it in iterators]
    for source_idx, it in enumerate(iters):
        try:
            sort_key, idx, source, line = next(it)
            heapq.heappush(heap, (sort_key, source_idx, idx, source, line, it))
        except StopIteration:
            pass

    while heap:
        sort_key, source_idx, idx, source, line, it = heapq.heappop(heap)
        yield line
        try:
            sort_key2, idx2, source2, line2 = next(it)
            heapq.heappush(heap, (sort_key2, source_idx, idx2, source2, line2, it))
        except StopIteration:
            pass


def merge_log_files(
    file_paths: List[str],
    encoding: str = "utf-8",
    errors: str = "replace",
) -> Iterator[str]:
    """Open multiple log files and merge their lines by timestamp.

    Args:
        file_paths: Paths to log files to merge.
        encoding: File encoding.
        errors: Error handling mode for open().

    Yields:
        Merged lines in timestamp order.
    """
    handles = [open(p, "r", encoding=encoding, errors=errors) for p in file_paths]
    try:
        sources = [(p, h) for p, h in zip(file_paths, handles)]
        yield from merge_logs(sources)
    finally:
        for h in handles:
            h.close()
