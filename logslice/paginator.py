"""Pagination utilities for splitting log output into pages."""

from typing import List, Iterator, Tuple


def paginate_lines(lines: List[str], page_size: int) -> Iterator[List[str]]:
    """Yield successive pages of `page_size` lines from `lines`.

    Args:
        lines: The full list of log lines.
        page_size: Number of lines per page. Must be >= 1.

    Yields:
        Lists of lines, each of length <= page_size.

    Raises:
        ValueError: If page_size is less than 1.
    """
    if page_size < 1:
        raise ValueError(f"page_size must be >= 1, got {page_size}")
    for offset in range(0, max(len(lines), 1), page_size):
        chunk = lines[offset : offset + page_size]
        if chunk:
            yield chunk


def get_page(lines: List[str], page_size: int, page_number: int) -> List[str]:
    """Return a specific 1-indexed page of lines.

    Args:
        lines: The full list of log lines.
        page_size: Number of lines per page.
        page_number: 1-indexed page to retrieve.

    Returns:
        The lines for the requested page, or an empty list if out of range.

    Raises:
        ValueError: If page_size < 1 or page_number < 1.
    """
    if page_size < 1:
        raise ValueError(f"page_size must be >= 1, got {page_size}")
    if page_number < 1:
        raise ValueError(f"page_number must be >= 1, got {page_number}")
    start = (page_number - 1) * page_size
    return lines[start : start + page_size]


def count_pages(lines: List[str], page_size: int) -> int:
    """Return the total number of pages for the given lines and page size.

    Args:
        lines: The full list of log lines.
        page_size: Number of lines per page.

    Returns:
        Total page count (0 if lines is empty).

    Raises:
        ValueError: If page_size < 1.
    """
    if page_size < 1:
        raise ValueError(f"page_size must be >= 1, got {page_size}")
    if not lines:
        return 0
    return (len(lines) + page_size - 1) // page_size


def page_info(lines: List[str], page_size: int, page_number: int) -> Tuple[int, int, int]:
    """Return (current_page, total_pages, total_lines) for display purposes."""
    total_pages = count_pages(lines, page_size)
    clamped = max(1, min(page_number, total_pages)) if total_pages > 0 else 1
    return clamped, total_pages, len(lines)
