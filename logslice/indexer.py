"""Build and query a byte-offset index over a log file for fast seeking."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, List, Optional

from logslice.parser import extract_timestamp


@dataclass
class IndexEntry:
    lineno: int          # 1-based
    offset: int          # byte offset from start of file
    timestamp: Optional[str]


@dataclass
class LogIndex:
    entries: List[IndexEntry] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.entries)

    def find_offset(self, timestamp: str) -> int:
        """Return the byte offset of the first entry >= *timestamp*."""
        for entry in self.entries:
            if entry.timestamp and entry.timestamp >= timestamp:
                return entry.offset
        return -1


def build_index(path: Path, every_nth: int = 1) -> LogIndex:
    """Scan *path* and record byte offsets every *every_nth* lines."""
    index = LogIndex()
    with path.open("rb") as fh:
        lineno = 0
        offset = 0
        for raw in fh:
            lineno += 1
            if lineno % every_nth == 0:
                line = raw.decode(errors="replace").rstrip("\n")
                ts = extract_timestamp(line)
                index.entries.append(IndexEntry(lineno, offset, ts))
            offset += len(raw)
    return index


def save_index(index: LogIndex, dest: Path) -> None:
    """Persist *index* as a JSON file."""
    payload = [
        {"lineno": e.lineno, "offset": e.offset, "timestamp": e.timestamp}
        for e in index.entries
    ]
    dest.write_text(json.dumps(payload, indent=2))


def load_index(src: Path) -> LogIndex:
    """Load a previously saved index from *src*."""
    payload = json.loads(src.read_text())
    entries = [
        IndexEntry(e["lineno"], e["offset"], e["timestamp"])
        for e in payload
    ]
    return LogIndex(entries=entries)


def iter_from_offset(path: Path, offset: int) -> Iterator[str]:
    """Yield decoded lines from *path* starting at byte *offset*."""
    with path.open("rb") as fh:
        fh.seek(offset)
        for raw in fh:
            yield raw.decode(errors="replace").rstrip("\n")
