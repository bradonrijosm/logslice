"""Normalize log lines by stripping noise, collapsing whitespace,
and standardizing timestamp formats for downstream processing."""

from __future__ import annotations

import re
from typing import Iterable, Iterator

# Matches common trailing noise: session IDs, hex addresses, UUIDs
_UUID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.IGNORECASE,
)
_HEX_ADDR_RE = re.compile(r"0x[0-9a-fA-F]+")
_MULTI_SPACE_RE = re.compile(r" {2,}")
_TRAILING_RE = re.compile(r"[\s\r\n]+$")


def strip_trailing_whitespace(line: str) -> str:
    """Remove trailing whitespace and newline characters."""
    return _TRAILING_RE.sub("", line)


def collapse_whitespace(line: str) -> str:
    """Replace runs of spaces with a single space."""
    return _MULTI_SPACE_RE.sub(" ", line)


def redact_uuids(line: str, placeholder: str = "<UUID>") -> str:
    """Replace UUID tokens with a placeholder."""
    return _UUID_RE.sub(placeholder, line)


def redact_hex_addresses(line: str, placeholder: str = "<ADDR>") -> str:
    """Replace hexadecimal address tokens with a placeholder."""
    return _HEX_ADDR_RE.sub(placeholder, line)


def normalize_line(
    line: str,
    *,
    strip_whitespace: bool = True,
    collapse_spaces: bool = True,
    remove_uuids: bool = False,
    remove_hex: bool = False,
    uuid_placeholder: str = "<UUID>",
    hex_placeholder: str = "<ADDR>",
) -> str:
    """Apply a configurable normalization pipeline to a single line."""
    if strip_whitespace:
        line = strip_trailing_whitespace(line)
    if remove_uuids:
        line = redact_uuids(line, uuid_placeholder)
    if remove_hex:
        line = redact_hex_addresses(line, hex_placeholder)
    if collapse_spaces:
        line = collapse_whitespace(line)
    return line


def normalize_lines(
    lines: Iterable[str],
    **kwargs,
) -> Iterator[str]:
    """Apply normalize_line to every line in *lines*, yielding results."""
    for line in lines:
        yield normalize_line(line, **kwargs)
