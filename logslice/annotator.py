"""Annotate log lines with metadata prefixes (timestamp offset, line number, source tag)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator, Optional

from logslice.parser import extract_timestamp


@dataclass
class AnnotatedLine:
    original: str
    line_number: int
    source_tag: Optional[str]
    offset_seconds: Optional[float]  # seconds since first timestamped line

    def render(self, *, show_lineno: bool = True, show_tag: bool = True, show_offset: bool = True) -> str:
        parts: list[str] = []
        if show_lineno:
            parts.append(f"[{self.line_number}]")
        if show_tag and self.source_tag:
            parts.append(f"<{self.source_tag}>")
        if show_offset and self.offset_seconds is not None:
            parts.append(f"+{self.offset_seconds:.1f}s")
        parts.append(self.original)
        return " ".join(parts)


def annotate_lines(
    lines: Iterable[str],
    *,
    source_tag: Optional[str] = None,
    start_lineno: int = 1,
) -> Iterator[AnnotatedLine]:
    """Yield AnnotatedLine objects for each input line."""
    first_dt = None
    for idx, line in enumerate(lines):
        stripped = line.rstrip("\n")
        dt = extract_timestamp(stripped)
        offset: Optional[float] = None
        if dt is not None:
            if first_dt is None:
                first_dt = dt
            offset = (dt - first_dt).total_seconds()
        yield AnnotatedLine(
            original=stripped,
            line_number=start_lineno + idx,
            source_tag=source_tag,
            offset_seconds=offset,
        )


def format_annotated(
    lines: Iterable[str],
    *,
    source_tag: Optional[str] = None,
    start_lineno: int = 1,
    show_lineno: bool = True,
    show_tag: bool = True,
    show_offset: bool = True,
) -> Iterator[str]:
    """Convenience wrapper — yields rendered strings directly."""
    for al in annotate_lines(lines, source_tag=source_tag, start_lineno=start_lineno):
        yield al.render(show_lineno=show_lineno, show_tag=show_tag, show_offset=show_offset)
