"""Timestamp parsing utilities for logslice."""

import re
from datetime import datetime
from typing import Optional

# Common log timestamp patterns
TIMESTAMP_PATTERNS = [
    # ISO 8601: 2024-01-15T13:45:00 or 2024-01-15 13:45:00
    (r'(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})', "%Y-%m-%dT%H:%M:%S"),
    (r'(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})', "%Y-%m-%d %H:%M:%S"),
    # Syslog: Jan 15 13:45:00
    (r'([A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})', "%b %d %H:%M:%S"),
    # Apache/nginx: 15/Jan/2024:13:45:00
    (r'(\d{2}/[A-Z][a-z]{2}/\d{4}:\d{2}:\d{2}:\d{2})', "%d/%b/%Y:%H:%M:%S"),
]


def extract_timestamp(line: str) -> Optional[datetime]:
    """Extract the first recognizable timestamp from a log line.

    Args:
        line: A single log line string.

    Returns:
        A datetime object if a timestamp is found, otherwise None.
    """
    for pattern, fmt in TIMESTAMP_PATTERNS:
        match = re.search(pattern, line)
        if match:
            raw = match.group(1)
            # Normalize the ISO 8601 variant with space separator
            normalized = raw.replace(" ", "T") if "T" not in raw and fmt.startswith("%Y") else raw
            try:
                return datetime.strptime(normalized, fmt.replace(" ", "T") if "T" not in fmt else fmt)
            except ValueError:
                try:
                    return datetime.strptime(raw, fmt)
                except ValueError:
                    continue
    return None


def parse_datetime_arg(value: str) -> datetime:
    """Parse a user-supplied datetime string into a datetime object.

    Supports ISO 8601 formats with or without time component.

    Args:
        value: Datetime string from CLI or API.

    Returns:
        Parsed datetime object.

    Raises:
        ValueError: If the string cannot be parsed.
    """
    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(
        f"Cannot parse datetime '{value}'. "
        "Expected formats: YYYY-MM-DD, YYYY-MM-DDTHH:MM:SS, etc."
    )
