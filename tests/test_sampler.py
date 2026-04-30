"""Tests for logslice.sampler."""

import pytest
from logslice.sampler import sample_lines, sample_head, sample_tail, sample_every_nth


LINES = [f"line {i}" for i in range(1, 21)]  # 20 lines


class TestSampleLines:
    def test_empty_input_returns_empty(self):
        assert sample_lines([], rate=0.5) == []

    def test_rate_one_returns_all_lines(self):
        assert sample_lines(LINES, rate=1.0) == LINES

    def test_rate_half_returns_roughly_half(self):
        result = sample_lines(LINES, rate=0.5)
        assert len(result) == pytest.approx(10, abs=2)

    def test_rate_tenth_returns_roughly_tenth(self):
        result = sample_lines(LINES, rate=0.1)
        assert 1 <= len(result) <= 4

    def test_invalid_rate_zero_raises(self):
        with pytest.raises(ValueError, match="rate must be between"):
            sample_lines(LINES, rate=0.0)

    def test_invalid_rate_above_one_raises(self):
        with pytest.raises(ValueError, match="rate must be between"):
            sample_lines(LINES, rate=1.5)

    def test_negative_rate_raises(self):
        with pytest.raises(ValueError):
            sample_lines(LINES, rate=-0.1)

    def test_result_is_subset_of_original(self):
        result = sample_lines(LINES, rate=0.5)
        for line in result:
            assert line in LINES


class TestSampleHead:
    def test_returns_first_n_lines(self):
        assert sample_head(LINES, 3) == LINES[:3]

    def test_n_larger_than_list_returns_all(self):
        assert sample_head(LINES, 100) == LINES

    def test_n_zero_returns_empty(self):
        assert sample_head(LINES, 0) == []

    def test_negative_n_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            sample_head(LINES, -1)

    def test_empty_input(self):
        assert sample_head([], 5) == []


class TestSampleTail:
    def test_returns_last_n_lines(self):
        assert sample_tail(LINES, 3) == LINES[-3:]

    def test_n_larger_than_list_returns_all(self):
        assert sample_tail(LINES, 100) == LINES

    def test_n_zero_returns_empty(self):
        assert sample_tail(LINES, 0) == []

    def test_negative_n_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            sample_tail(LINES, -1)

    def test_empty_input(self):
        assert sample_tail([], 5) == []


class TestSampleEveryNth:
    def test_every_first_returns_all(self):
        assert sample_every_nth(LINES, 1) == LINES

    def test_every_second(self):
        result = sample_every_nth(LINES, 2)
        assert result == LINES[::2]
        assert len(result) == 10

    def test_every_fifth(self):
        result = sample_every_nth(LINES, 5)
        assert result == [LINES[0], LINES[5], LINES[10], LINES[15]]

    def test_n_zero_raises(self):
        with pytest.raises(ValueError, match=">= 1"):
            sample_every_nth(LINES, 0)

    def test_empty_input_returns_empty(self):
        assert sample_every_nth([], 3) == []
