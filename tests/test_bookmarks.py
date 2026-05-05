"""Tests for logslice.bookmarks."""

import json
import os
import tempfile

import pytest

from logslice.bookmarks import (
    Bookmark,
    delete_bookmark,
    list_bookmarks,
    load_bookmark,
    save_bookmark,
)


@pytest.fixture
def store(tmp_path):
    return str(tmp_path / "bookmarks.json")


def _make_bm(name="test", file_path="app.log", start=None, end=None):
    return Bookmark(name=name, file_path=file_path, start=start, end=end)


class TestSaveAndLoadBookmark:
    def test_save_creates_file(self, store):
        save_bookmark(_make_bm(), store)
        assert os.path.exists(store)

    def test_round_trip(self, store):
        bm = _make_bm(name="deploy", start="2024-01-01T00:00:00", end="2024-01-02T00:00:00")
        save_bookmark(bm, store)
        loaded = load_bookmark("deploy", store)
        assert loaded is not None
        assert loaded.name == "deploy"
        assert loaded.start == "2024-01-01T00:00:00"
        assert loaded.end == "2024-01-02T00:00:00"

    def test_load_missing_returns_none(self, store):
        assert load_bookmark("ghost", store) is None

    def test_load_from_missing_store_returns_none(self, tmp_path):
        result = load_bookmark("x", str(tmp_path / "nonexistent.json"))
        assert result is None

    def test_overwrite_existing_bookmark(self, store):
        save_bookmark(_make_bm(name="a", start="2024-01-01T00:00:00"), store)
        save_bookmark(_make_bm(name="a", start="2024-06-01T00:00:00"), store)
        loaded = load_bookmark("a", store)
        assert loaded.start == "2024-06-01T00:00:00"

    def test_created_at_is_set_automatically(self, store):
        bm = _make_bm()
        assert bm.created_at != ""


class TestDeleteBookmark:
    def test_delete_existing(self, store):
        save_bookmark(_make_bm(name="rm_me"), store)
        result = delete_bookmark("rm_me", store)
        assert result is True
        assert load_bookmark("rm_me", store) is None

    def test_delete_nonexistent_returns_false(self, store):
        assert delete_bookmark("nope", store) is False

    def test_delete_from_missing_store_returns_false(self, tmp_path):
        assert delete_bookmark("x", str(tmp_path / "missing.json")) is False


class TestListBookmarks:
    def test_empty_store_returns_empty(self, store):
        assert list_bookmarks(store) == []

    def test_returns_all_bookmarks(self, store):
        save_bookmark(_make_bm(name="a"), store)
        save_bookmark(_make_bm(name="b"), store)
        result = list_bookmarks(store)
        names = [b.name for b in result]
        assert "a" in names and "b" in names

    def test_sorted_by_created_at(self, store):
        bm1 = Bookmark(name="first", file_path="a.log", start=None, end=None, created_at="2024-01-01T00:00:00")
        bm2 = Bookmark(name="second", file_path="b.log", start=None, end=None, created_at="2024-06-01T00:00:00")
        save_bookmark(bm2, store)
        save_bookmark(bm1, store)
        result = list_bookmarks(store)
        assert result[0].name == "first"
        assert result[1].name == "second"
