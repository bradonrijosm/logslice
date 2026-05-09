"""Tests for logslice.indexer_cli."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from logslice.indexer_cli import build_indexer_parser, cmd_build, cmd_query

LINES = [
    "2024-06-01 10:00:01 INFO  boot",
    "2024-06-01 10:00:02 DEBUG tick",
    "2024-06-01 10:00:03 ERROR fail",
]


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    p = tmp_path / "srv.log"
    p.write_text("\n".join(LINES) + "\n")
    return p


def _ns(**kwargs) -> argparse.Namespace:
    defaults = dict(command="build", log=None, out=None, every=1)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestBuildIndexerParser:
    def test_returns_argument_parser(self) -> None:
        assert isinstance(build_indexer_parser(), argparse.ArgumentParser)

    def test_build_subcommand_exists(self) -> None:
        p = build_indexer_parser()
        ns = p.parse_args(["build", "/tmp/x.log"])
        assert ns.command == "build"

    def test_query_subcommand_exists(self) -> None:
        p = build_indexer_parser()
        ns = p.parse_args(["query", "/tmp/x.idx", "2024-01-01"])
        assert ns.command == "query"

    def test_default_every_is_one(self) -> None:
        p = build_indexer_parser()
        ns = p.parse_args(["build", "/tmp/x.log"])
        assert ns.every == 1

    def test_every_flag_parsed(self) -> None:
        p = build_indexer_parser()
        ns = p.parse_args(["build", "/tmp/x.log", "--every", "10"])
        assert ns.every == 10

    def test_out_flag_parsed(self, tmp_path: Path) -> None:
        p = build_indexer_parser()
        out = tmp_path / "out.idx"
        ns = p.parse_args(["build", "/tmp/x.log", "--out", str(out)])
        assert ns.out == out


class TestCmdBuild:
    def test_returns_zero_on_success(self, log_file: Path, tmp_path: Path) -> None:
        ns = _ns(log=log_file, out=tmp_path / "out.idx", every=1)
        assert cmd_build(ns) == 0

    def test_creates_index_file(self, log_file: Path, tmp_path: Path) -> None:
        out = tmp_path / "out.idx"
        ns = _ns(log=log_file, out=out, every=1)
        cmd_build(ns)
        assert out.exists()

    def test_default_out_uses_idx_extension(self, log_file: Path) -> None:
        ns = _ns(log=log_file, out=None, every=1)
        cmd_build(ns)
        assert log_file.with_suffix(".idx").exists()

    def test_prints_entry_count(self, log_file: Path, tmp_path: Path,
                                capsys: pytest.CaptureFixture) -> None:
        ns = _ns(log=log_file, out=tmp_path / "out.idx", every=1)
        cmd_build(ns)
        out = capsys.readouterr().out
        assert "Indexed" in out


class TestCmdQuery:
    def _build(self, log_file: Path, tmp_path: Path) -> Path:
        from logslice.indexer import build_index, save_index
        idx = build_index(log_file)
        dest = tmp_path / "out.idx"
        save_index(idx, dest)
        return dest

    def test_returns_zero_when_found(self, log_file: Path, tmp_path: Path) -> None:
        idx_path = self._build(log_file, tmp_path)
        ns = argparse.Namespace(command="query", index=idx_path,
                                timestamp="2024-06-01 10:00:02")
        assert cmd_query(ns) == 0

    def test_prints_offset_when_found(self, log_file: Path, tmp_path: Path,
                                      capsys: pytest.CaptureFixture) -> None:
        idx_path = self._build(log_file, tmp_path)
        ns = argparse.Namespace(command="query", index=idx_path,
                                timestamp="2024-06-01 10:00:01")
        cmd_query(ns)
        out = capsys.readouterr().out.strip()
        assert out == "0"

    def test_returns_one_when_not_found(self, log_file: Path, tmp_path: Path) -> None:
        idx_path = self._build(log_file, tmp_path)
        ns = argparse.Namespace(command="query", index=idx_path,
                                timestamp="9999-99-99")
        assert cmd_query(ns) == 1
