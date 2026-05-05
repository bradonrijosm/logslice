"""Tests for logslice.bookmark_cli."""

import argparse

import pytest

from logslice.bookmark_cli import (
    build_bookmark_parser,
    cmd_delete,
    cmd_list,
    cmd_load,
    cmd_save,
)
from logslice.bookmarks import save_bookmark, Bookmark


@pytest.fixture
def store(tmp_path):
    return str(tmp_path / "bm.json")


def _ns(store, **kwargs):
    ns = argparse.Namespace(store=store)
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


class TestCmdSave:
    def test_returns_zero_on_success(self, store, capsys):
        ns = _ns(store, name="mymark", file="app.log", start="2024-01-01", end=None)
        assert cmd_save(ns) == 0

    def test_prints_confirmation(self, store, capsys):
        ns = _ns(store, name="mymark", file="app.log", start=None, end=None)
        cmd_save(ns)
        out = capsys.readouterr().out
        assert "mymark" in out


class TestCmdLoad:
    def test_returns_zero_when_found(self, store, capsys):
        bm = Bookmark(name="found", file_path="x.log", start=None, end=None)
        save_bookmark(bm, store)
        ns = _ns(store, name="found")
        assert cmd_load(ns) == 0

    def test_returns_one_when_missing(self, store, capsys):
        ns = _ns(store, name="ghost")
        assert cmd_load(ns) == 1

    def test_prints_bookmark_details(self, store, capsys):
        bm = Bookmark(name="info", file_path="y.log", start="2024-01-01", end="2024-01-31")
        save_bookmark(bm, store)
        cmd_load(_ns(store, name="info"))
        out = capsys.readouterr().out
        assert "y.log" in out
        assert "2024-01-01" in out


class TestCmdDelete:
    def test_returns_zero_when_deleted(self, store, capsys):
        bm = Bookmark(name="bye", file_path="z.log", start=None, end=None)
        save_bookmark(bm, store)
        assert cmd_delete(_ns(store, name="bye")) == 0

    def test_returns_one_when_not_found(self, store, capsys):
        assert cmd_delete(_ns(store, name="nope")) == 1


class TestCmdList:
    def test_empty_store_returns_zero(self, store, capsys):
        assert cmd_list(_ns(store)) == 0

    def test_lists_saved_bookmarks(self, store, capsys):
        save_bookmark(Bookmark(name="alpha", file_path="a.log", start=None, end=None), store)
        save_bookmark(Bookmark(name="beta", file_path="b.log", start=None, end=None), store)
        cmd_list(_ns(store))
        out = capsys.readouterr().out
        assert "alpha" in out
        assert "beta" in out


class TestBuildBookmarkParser:
    def test_registers_bookmark_subcommand(self):
        parser = argparse.ArgumentParser()
        subs = parser.add_subparsers(dest="cmd")
        build_bookmark_parser(subs)
        args = parser.parse_args(["bookmark", "list"])
        assert args.cmd == "bookmark"
        assert args.bookmark_cmd == "list"
