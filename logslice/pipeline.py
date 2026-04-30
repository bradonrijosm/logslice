"""End-to-end pipeline that wires all logslice stages together."""

from typing import List, Optional

from logslice.deduplicator import deduplicate_lines
from logslice.exporter import export_lines
from logslice.filter import filter_lines
from logslice.formatter import format_lines, format_no_match, format_summary
from logslice.highlighter import highlight_lines
from logslice.slicer import slice_log
from logslice.truncator import truncate_and_cap


def run_pipeline(
    log_path: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    level: Optional[str] = None,
    pattern: Optional[str] = None,
    keywords: Optional[List[str]] = None,
    deduplicate: bool = False,
    max_lines: Optional[int] = None,
    max_line_length: Optional[int] = None,
    line_numbers: bool = False,
    export_fmt: str = "text",
    export_metadata: Optional[dict] = None,
    output_file: Optional[str] = None,
) -> str:
    """Run the full logslice pipeline and return (or write) the result.

    Stages (in order):
      1. Slice by time range
      2. Filter by level / pattern
      3. Deduplicate
      4. Truncate lines and cap total count
      5. Highlight keywords
      6. Format (line numbers, summary)
      7. Export to the requested format

    Args:
        log_path: Path to the source log file.
        start: ISO-8601 start datetime string (inclusive).
        end: ISO-8601 end datetime string (inclusive).
        level: Log level to keep (e.g. 'ERROR').
        pattern: Regex pattern; only matching lines are kept.
        keywords: List of keywords to highlight in output.
        deduplicate: Remove duplicate lines when True.
        max_lines: Cap the number of output lines.
        max_line_length: Truncate lines longer than this many characters.
        line_numbers: Prefix each line with its line number.
        export_fmt: Output format — 'text', 'json', or 'csv'.
        export_metadata: Optional metadata dict for JSON exports.
        output_file: If given, write result to this path instead of returning.

    Returns:
        The formatted, exported string (empty string when written to file).
    """
    # Stage 1 – time-range slice
    lines: List[str] = slice_log(log_path, start=start, end=end)

    # Stage 2 – filtering
    lines = filter_lines(lines, level=level, pattern=pattern)

    # Stage 3 – deduplication
    if deduplicate:
        lines = deduplicate_lines(lines, consecutive=False)

    # Stage 4 – truncation / capping
    lines = truncate_and_cap(
        lines,
        max_length=max_line_length,
        max_lines=max_lines,
    )

    # Stage 5 – keyword highlighting (text/json only; skip for csv)
    if keywords and export_fmt.lower() != "csv":
        lines = highlight_lines(lines, keywords)

    # Stage 6 – formatting
    buf = []
    if not lines:
        buf.append(format_no_match())
    else:
        import io as _io
        sink = _io.StringIO()
        format_lines(lines, sink, line_numbers=line_numbers)
        buf.append(sink.getvalue().rstrip("\n"))
        buf.append(format_summary(len(lines)))

    combined = "\n".join(buf)
    final_lines = combined.splitlines()

    # Stage 7 – export
    result = export_lines(final_lines, fmt=export_fmt, metadata=export_metadata)

    if output_file:
        with open(output_file, "w", encoding="utf-8") as fh:
            fh.write(result)
        return ""

    return result
