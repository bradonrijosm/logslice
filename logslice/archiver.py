"""Compress and archive log slices to gzip or bzip2 files."""

import bz2
import gzip
import io
import os
from typing import Iterable, Literal

CompressionFormat = Literal["gz", "bz2"]


def compress_lines(
    lines: Iterable[str],
    dest_path: str,
    fmt: CompressionFormat = "gz",
    encoding: str = "utf-8",
) -> int:
    """Write *lines* to *dest_path* using the given compression format.

    Returns the number of lines written.
    """
    openers = {
        "gz": lambda p: gzip.open(p, "wb"),
        "bz2": lambda p: bz2.open(p, "wb"),
    }
    if fmt not in openers:
        raise ValueError(f"Unsupported compression format: {fmt!r}. Use 'gz' or 'bz2'.")

    count = 0
    with openers[fmt](dest_path) as fh:
        for line in lines:
            fh.write((line.rstrip("\n") + "\n").encode(encoding))
            count += 1
    return count


def decompress_lines(
    src_path: str,
    encoding: str = "utf-8",
) -> list[str]:
    """Read and decompress *src_path*, returning lines (without trailing newline).

    The format is inferred from the file extension (.gz or .bz2).
    """
    ext = os.path.splitext(src_path)[1].lstrip(".")
    openers = {
        "gz": lambda p: gzip.open(p, "rb"),
        "bz2": lambda p: bz2.open(p, "rb"),
    }
    if ext not in openers:
        raise ValueError(f"Cannot infer compression format from extension: {ext!r}")

    with openers[ext](src_path) as fh:
        raw = fh.read().decode(encoding)
    return [line for line in raw.splitlines()]


def archive_to_bytes(
    lines: Iterable[str],
    fmt: CompressionFormat = "gz",
    encoding: str = "utf-8",
) -> bytes:
    """Compress *lines* in-memory and return the raw compressed bytes."""
    buf = io.BytesIO()
    if fmt == "gz":
        with gzip.GzipFile(fileobj=buf, mode="wb") as gz:
            for line in lines:
                gz.write((line.rstrip("\n") + "\n").encode(encoding))
    elif fmt == "bz2":
        data = "".join(line.rstrip("\n") + "\n" for line in lines)
        buf.write(bz2.compress(data.encode(encoding)))
    else:
        raise ValueError(f"Unsupported compression format: {fmt!r}")
    return buf.getvalue()
