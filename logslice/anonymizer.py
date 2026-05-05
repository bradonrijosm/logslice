"""Anonymize sensitive data in log lines (IPs, emails, tokens)."""

import re
from typing import List, Optional

_IP_RE = re.compile(
    r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
)
_EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
)
_TOKEN_RE = re.compile(
    r"(?:bearer|token|api[_-]?key|secret)[=:\s]+[\w\-\.]+",
    re.IGNORECASE,
)

_PLACEHOLDER_IP = "<IP>"
_PLACEHOLDER_EMAIL = "<EMAIL>"
_PLACEHOLDER_TOKEN = "<TOKEN>"


def anonymize_ips(line: str, placeholder: str = _PLACEHOLDER_IP) -> str:
    """Replace all IPv4 addresses in *line* with *placeholder*."""
    return _IP_RE.sub(placeholder, line)


def anonymize_emails(line: str, placeholder: str = _PLACEHOLDER_EMAIL) -> str:
    """Replace all e-mail addresses in *line* with *placeholder*."""
    return _EMAIL_RE.sub(placeholder, line)


def anonymize_tokens(line: str, placeholder: str = _PLACEHOLDER_TOKEN) -> str:
    """Replace bearer/token/api-key assignments in *line* with *placeholder*."""
    return _TOKEN_RE.sub(placeholder, line)


def anonymize_line(
    line: str,
    *,
    ips: bool = True,
    emails: bool = True,
    tokens: bool = True,
) -> str:
    """Apply selected anonymization passes to a single *line*."""
    if ips:
        line = anonymize_ips(line)
    if emails:
        line = anonymize_emails(line)
    if tokens:
        line = anonymize_tokens(line)
    return line


def anonymize_lines(
    lines: List[str],
    *,
    ips: bool = True,
    emails: bool = True,
    tokens: bool = True,
) -> List[str]:
    """Return a new list with every line anonymized.

    Args:
        lines:  Input log lines.
        ips:    Anonymize IPv4 addresses when *True* (default).
        emails: Anonymize e-mail addresses when *True* (default).
        tokens: Anonymize token/key values when *True* (default).

    Returns:
        List of anonymized lines in the same order as *lines*.
    """
    return [
        anonymize_line(line, ips=ips, emails=emails, tokens=tokens)
        for line in lines
    ]
