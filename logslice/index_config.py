"""Load and dump indexer configuration from JSON."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class IndexConfig:
    every_nth: int = 1
    output_suffix: str = ".idx"
    encoding: str = "utf-8"
    log_path: Optional[str] = None


def _validate(cfg: IndexConfig) -> None:
    if cfg.every_nth < 1:
        raise ValueError(f"every_nth must be >= 1, got {cfg.every_nth}")
    if not cfg.output_suffix:
        raise ValueError("output_suffix must not be empty")


def load_config(src: Path) -> IndexConfig:
    """Load an IndexConfig from a JSON file at *src*."""
    raw = json.loads(src.read_text())
    cfg = IndexConfig(
        every_nth=raw.get("every_nth", 1),
        output_suffix=raw.get("output_suffix", ".idx"),
        encoding=raw.get("encoding", "utf-8"),
        log_path=raw.get("log_path"),
    )
    _validate(cfg)
    return cfg


def dump_config(cfg: IndexConfig, dest: Path) -> None:
    """Persist *cfg* as a JSON file at *dest*."""
    _validate(cfg)
    payload = {
        "every_nth": cfg.every_nth,
        "output_suffix": cfg.output_suffix,
        "encoding": cfg.encoding,
        "log_path": cfg.log_path,
    }
    dest.write_text(json.dumps(payload, indent=2))


def config_summary(cfg: IndexConfig) -> str:
    """Return a human-readable one-liner describing *cfg*."""
    parts = [f"every_nth={cfg.every_nth}", f"suffix={cfg.output_suffix!r}"]
    if cfg.log_path:
        parts.append(f"log={cfg.log_path}")
    return "IndexConfig(" + ", ".join(parts) + ")"
