"""Context lines module: extract surrounding lines around matches."""

from typing import List, Tuple, Iterator


def extract_context(
    lines: List[Tuple[int, str]],
    match_indices: List[int],
    before: int = 0,
    after: int = 0,
) -> List[Tuple[int, str, bool]]:
    """
    Given a list of (line_number, line_text) tuples and a list of matched
    indices into that list, return a deduplicated, ordered list of
    (line_number, line_text, is_match) tuples that includes `before` lines
    before each match and `after` lines after each match.

    Args:
        lines: All lines as (line_number, text) pairs.
        match_indices: Indices (into `lines`) of matched lines.
        before: Number of context lines to include before each match.
        after: Number of context lines to include after each match.

    Returns:
        List of (line_number, text, is_match) tuples, sorted by line_number,
        with no duplicates.

    Raises:
        ValueError: If any index in `match_indices` is out of range for `lines`.
    """
    if not lines or not match_indices:
        return []

    before = max(0, before)
    after = max(0, after)
    total = len(lines)

    for idx in match_indices:
        if idx < 0 or idx >= total:
            raise ValueError(
                f"match index {idx} is out of range for lines of length {total}"
            )

    selected: dict[int, bool] = {}

    for idx in match_indices:
        start = max(0, idx - before)
        end = min(total - 1, idx + after)
        for i in range(start, end + 1):
            is_match = i == idx
            # A line already marked as a match stays a match
            if i not in selected or is_match:
                selected[i] = is_match

    result: List[Tuple[int, str, bool]] = [
        (lines[i][0], lines[i][1], selected[i])
        for i in sorted(selected)
    ]
    return result


def find_match_indices(
    lines: List[Tuple[int, str]],
    predicate,
) -> List[int]:
    """
    Return the list indices (not line numbers) of lines that satisfy
    `predicate(line_text)`.

    Args:
        lines: List of (line_number, text) tuples.
        predicate: Callable[[str], bool] used to test each line.

    Returns:
        List of integer indices into `lines`.
    """
    return [i for i, (_, text) in enumerate(lines) if predicate(text)]
