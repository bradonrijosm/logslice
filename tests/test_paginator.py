"""Tests for logslice.paginator."""

import pytest
from logslice.paginator import paginate_lines, get_page, count_pages, page_info


LINES = [f"line {i}" for i in range(1, 11)]  # 10 lines


class TestPaginateLines:
    def test_empty_input_yields_nothing(self):
        pages = list(paginate_lines([], page_size=5))
        assert pages == []

    def test_exact_multiple_of_page_size(self):
        pages = list(paginate_lines(LINES, page_size=5))
        assert len(pages) == 2
        assert pages[0] == LINES[:5]
        assert pages[1] == LINES[5:]

    def test_non_multiple_last_page_shorter(self):
        pages = list(paginate_lines(LINES, page_size=3))
        assert len(pages) == 4
        assert pages[-1] == ["line 10"]

    def test_page_size_larger_than_input(self):
        pages = list(paginate_lines(LINES, page_size=50))
        assert len(pages) == 1
        assert pages[0] == LINES

    def test_page_size_one(self):
        pages = list(paginate_lines(LINES[:3], page_size=1))
        assert pages == [["line 1"], ["line 2"], ["line 3"]]

    def test_invalid_page_size_raises(self):
        with pytest.raises(ValueError, match="page_size must be >= 1"):
            list(paginate_lines(LINES, page_size=0))


class TestGetPage:
    def test_first_page(self):
        assert get_page(LINES, page_size=5, page_number=1) == LINES[:5]

    def test_second_page(self):
        assert get_page(LINES, page_size=5, page_number=2) == LINES[5:]

    def test_out_of_range_returns_empty(self):
        assert get_page(LINES, page_size=5, page_number=99) == []

    def test_invalid_page_number_raises(self):
        with pytest.raises(ValueError, match="page_number must be >= 1"):
            get_page(LINES, page_size=5, page_number=0)

    def test_invalid_page_size_raises(self):
        with pytest.raises(ValueError, match="page_size must be >= 1"):
            get_page(LINES, page_size=-1, page_number=1)

    def test_partial_last_page(self):
        result = get_page(LINES, page_size=3, page_number=4)
        assert result == ["line 10"]


class TestCountPages:
    def test_empty_returns_zero(self):
        assert count_pages([], page_size=5) == 0

    def test_exact_multiple(self):
        assert count_pages(LINES, page_size=5) == 2

    def test_non_multiple(self):
        assert count_pages(LINES, page_size=3) == 4

    def test_single_line(self):
        assert count_pages(["only"], page_size=10) == 1

    def test_invalid_page_size_raises(self):
        with pytest.raises(ValueError):
            count_pages(LINES, page_size=0)


class TestPageInfo:
    def test_returns_correct_tuple(self):
        current, total, total_lines = page_info(LINES, page_size=5, page_number=1)
        assert current == 1
        assert total == 2
        assert total_lines == 10

    def test_clamps_page_number_above_max(self):
        current, total, _ = page_info(LINES, page_size=5, page_number=100)
        assert current == total

    def test_clamps_page_number_below_min(self):
        current, _, _ = page_info(LINES, page_size=5, page_number=-5)
        assert current == 1

    def test_empty_lines(self):
        current, total, total_lines = page_info([], page_size=5, page_number=1)
        assert total == 0
        assert total_lines == 0
