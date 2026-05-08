"""Load and dump annotator display configuration from JSON."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Union


_DEFAULTS: Dict[str, Any] = {
    "show_lineno": True,
    "show_tag": True,
    "show_offset": True,
    "start_lineno": 1,
    "source_tag": None,
}


def _validate(cfg: Dict[str, Any]) -> None:
    bool_keys = ("show_lineno", "show_tag", "show_offset")
    for key in bool_keys:
        if key in cfg and not isinstance(cfg[key], bool):
            raise ValueError(f"'{key}' must be a boolean, got {cfg[key]!r}")
    if "start_lineno" in cfg:
        val = cfg["start_lineno"]
        if not isinstance(val, int) or val < 1:
            raise ValueError(f"'start_lineno' must be a positive integer, got {val!r}")


def load_config(path: Union[str, Path]) -> Dict[str, Any]:
    """Load annotator config from a JSON file, filling missing keys with defaults."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Annotator config must be a JSON object")
    _validate(raw)
    merged = {**_DEFAULTS, **raw}
    return merged


def dump_config(cfg: Dict[str, Any], path: Union[str, Path]) -> None:
    """Persist an annotator config dict to a JSON file."""
    _validate(cfg)
    Path(path).write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def config_summary(cfg: Dict[str, Any]) -> str:
    """Return a human-readable one-liner describing the config."""
    flags = []
    if cfg.get("show_lineno", True):
        flags.append("lineno")
    if cfg.get("show_tag", True):
        flags.append("tag")
    if cfg.get("show_offset", True):
        flags.append("offset")
    tag = cfg.get("source_tag") or "(none)"
    start = cfg.get("start_lineno", 1)
    shown = ", ".join(flags) if flags else "nothing"
    return f"annotator: showing [{shown}], tag={tag}, start={start}"
