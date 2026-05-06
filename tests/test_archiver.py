"""Tests for logslice.archiver and logslice.archiver_cli."""

import os
import pytest

from logslice.archiver import archive_to_bytes, compress_lines, decompress_lines
from logslice.archiver_cli import build_archiver_parser, cmd_compress, cmd_decompress


SAMPLE_LINES = [
    "2024-01-01 00:00:01 INFO  server started",
    "2024-01-01 00:00:02 DEBUG request received",
    "2024-01-01 00:00:03 ERROR something went wrong",
]


# ---------------------------------------------------------------------------
# compress_lines / decompress_lines
# ---------------------------------------------------------------------------

class TestCompressDecompress:
    def test_gz_round_trip(self, tmp_path):
        dest = str(tmp_path / "out.gz")
        count = compress_lines(SAMPLE_LINES, dest, fmt="gz")
        assert count == len(SAMPLE_LINES)
        result = decompress_lines(dest)
        assert result == [l.rstrip("\n") for l in SAMPLE_LINES]

    def test_bz2_round_trip(self, tmp_path):
        dest = str(tmp_path / "out.bz2")
        compress_lines(SAMPLE_LINES, dest, fmt="bz2")
        result = decompress_lines(dest)
        assert result == [l.rstrip("\n") for l in SAMPLE_LINES]

    def test_empty_input_creates_file(self, tmp_path):
        dest = str(tmp_path / "empty.gz")
        count = compress_lines([], dest)
        assert count == 0
        assert os.path.exists(dest)
        assert decompress_lines(dest) == []

    def test_invalid_format_raises(self, tmp_path):
        with pytest.raises(ValueError, match="Unsupported"):
            compress_lines(SAMPLE_LINES, str(tmp_path / "out.xz"), fmt="xz")  # type: ignore

    def test_decompress_unknown_extension_raises(self, tmp_path):
        p = tmp_path / "file.txt"
        p.write_text("data")
        with pytest.raises(ValueError, match="Cannot infer"):
            decompress_lines(str(p))


# ---------------------------------------------------------------------------
# archive_to_bytes
# ---------------------------------------------------------------------------

class TestArchiveToBytes:
    def test_returns_bytes(self):
        data = archive_to_bytes(SAMPLE_LINES, fmt="gz")
        assert isinstance(data, bytes)
        assert len(data) > 0

    def test_bz2_returns_bytes(self):
        data = archive_to_bytes(SAMPLE_LINES, fmt="bz2")
        assert isinstance(data, bytes)

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError):
            archive_to_bytes(SAMPLE_LINES, fmt="xz")  # type: ignore


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@pytest.fixture
def log_file(tmp_path):
    p = tmp_path / "sample.log"
    p.write_text("\n".join(SAMPLE_LINES) + "\n", encoding="utf-8")
    return str(p)


def _ns(**kwargs):
    import argparse
    defaults = {"input": "in.log", "output": "out.gz", "fmt": "gz", "command": "compress"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestBuildArchiverParser:
    def test_returns_argument_parser(self):
        import argparse
        assert isinstance(build_archiver_parser(), argparse.ArgumentParser)

    def test_compress_subcommand_exists(self):
        p = build_archiver_parser()
        ns = p.parse_args(["compress", "a.log", "a.gz"])
        assert ns.command == "compress"

    def test_default_format_is_gz(self):
        p = build_archiver_parser()
        ns = p.parse_args(["compress", "a.log", "a.gz"])
        assert ns.fmt == "gz"

    def test_decompress_subcommand_exists(self):
        p = build_archiver_parser()
        ns = p.parse_args(["decompress", "a.gz"])
        assert ns.command == "decompress"

    def test_decompress_output_optional(self):
        p = build_archiver_parser()
        ns = p.parse_args(["decompress", "a.gz"])
        assert ns.output is None


class TestCmdCompress:
    def test_returns_zero_on_success(self, log_file, tmp_path):
        out = str(tmp_path / "out.gz")
        assert cmd_compress(_ns(input=log_file, output=out, fmt="gz")) == 0

    def test_creates_output_file(self, log_file, tmp_path):
        out = str(tmp_path / "out.bz2")
        cmd_compress(_ns(input=log_file, output=out, fmt="bz2"))
        assert os.path.exists(out)


class TestCmdDecompress:
    def test_returns_zero_on_success(self, log_file, tmp_path, capsys):
        compressed = str(tmp_path / "out.gz")
        cmd_compress(_ns(input=log_file, output=compressed, fmt="gz"))
        ns = _ns(command="decompress", input=compressed, output=None)
        rc = cmd_decompress(ns)
        assert rc == 0
        captured = capsys.readouterr()
        assert "INFO" in captured.out

    def test_writes_to_file_when_output_given(self, log_file, tmp_path):
        compressed = str(tmp_path / "out.gz")
        cmd_compress(_ns(input=log_file, output=compressed, fmt="gz"))
        out_txt = str(tmp_path / "restored.log")
        ns = _ns(command="decompress", input=compressed, output=out_txt)
        cmd_decompress(ns)
        assert os.path.exists(out_txt)
        content = open(out_txt).read()
        assert "ERROR" in content
