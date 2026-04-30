"""Export log slices to different output formats (plain text, JSON, CSV)."""

import csv
import io
import json
from typing import List, Optional


SUPPORTED_FORMATS = ("text", "json", "csv")


def export_as_text(lines: List[str], separator: str = "\n") -> str:
    """Join lines into a plain-text string."""
    return separator.join(lines)


def export_as_json(
    lines: List[str],
    metadata: Optional[dict] = None,
) -> str:
    """Serialise lines to a JSON string, optionally embedding metadata."""
    payload: dict = {"lines": lines, "count": len(lines)}
    if metadata:
        payload["metadata"] = metadata
    return json.dumps(payload, indent=2)


def export_as_csv(lines: List[str], index_column: bool = True) -> str:
    """Serialise lines to CSV.  Each row contains an optional index and the line."""
    buf = io.StringIO()
    fieldnames = ["index", "line"] if index_column else ["line"]
    writer = csv.DictWriter(buf, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for i, line in enumerate(lines, start=1):
        row = {"line": line}
        if index_column:
            row["index"] = i
        writer.writerow(row)
    return buf.getvalue()


def export_lines(
    lines: List[str],
    fmt: str = "text",
    metadata: Optional[dict] = None,
    index_column: bool = True,
) -> str:
    """Dispatch export to the requested format.

    Args:
        lines: The log lines to export.
        fmt: One of 'text', 'json', or 'csv'.
        metadata: Optional dict embedded in JSON exports.
        index_column: Whether to include an index column in CSV exports.

    Returns:
        Formatted string ready for writing to a file or stdout.

    Raises:
        ValueError: If *fmt* is not a supported format.
    """
    fmt = fmt.lower()
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported export format '{fmt}'. "
            f"Choose one of: {', '.join(SUPPORTED_FORMATS)}"
        )
    if fmt == "json":
        return export_as_json(lines, metadata=metadata)
    if fmt == "csv":
        return export_as_csv(lines, index_column=index_column)
    return export_as_text(lines)
