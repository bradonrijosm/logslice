"""Bookmark management for saving and restoring named log positions."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class Bookmark:
    name: str
    file_path: str
    start: Optional[str]
    end: Optional[str]
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


def _load_store(store_path: str) -> Dict[str, dict]:
    if not os.path.exists(store_path):
        return {}
    with open(store_path, "r", encoding="utf-8") as fh:
        try:
            return json.load(fh)
        except json.JSONDecodeError:
            return {}


def _save_store(store_path: str, data: Dict[str, dict]) -> None:
    with open(store_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def save_bookmark(bookmark: Bookmark, store_path: str) -> None:
    """Persist a bookmark to the JSON store."""
    data = _load_store(store_path)
    data[bookmark.name] = asdict(bookmark)
    _save_store(store_path, data)


def load_bookmark(name: str, store_path: str) -> Optional[Bookmark]:
    """Retrieve a named bookmark; returns None if not found."""
    data = _load_store(store_path)
    entry = data.get(name)
    if entry is None:
        return None
    return Bookmark(**entry)


def delete_bookmark(name: str, store_path: str) -> bool:
    """Remove a bookmark by name. Returns True if it existed."""
    data = _load_store(store_path)
    if name not in data:
        return False
    del data[name]
    _save_store(store_path, data)
    return True


def list_bookmarks(store_path: str) -> List[Bookmark]:
    """Return all bookmarks sorted by creation time."""
    data = _load_store(store_path)
    bookmarks = [Bookmark(**v) for v in data.values()]
    return sorted(bookmarks, key=lambda b: b.created_at)
