"""Tests for logslice.profiler_cli."""

from __future__ import annotations

import argparse
import io
import os
import tempfile

import pytest

from logslice.profiler_cli import build_profile_parser, cmd_profile


LOG_CONTENT = (
    "2024-03-01 09:00:01 INFO  start\n"
    "2024-03-01 09:00:45 INFO  middle\n"
    "2024-03-01 09:01:10 ERROR boom\n"
    "plain line without timestamp\n"
)


@pytest.fixture()
def log_file(tmp_path):
    p = tmp_path / "sample.log"
    p.write_text(LOG_CONTENT)
    return str(p)


def _ns(file, bucket=60, bar_width=40):
    return argparse.Namespace(file=file, bucket=bucket, bar_width=bar_width)


class TestBuildProfileParser:
    def test_returns_argument_parser(self):
        p = build_profile_parser()
        assert isinstance(p, argparse.ArgumentParser)

    def test_default_bucket_is_60(self):
        p = build_profile_parser()
        args = p.parse_args(["myfile.log"])
        assert args.bucket == 60

    def test_default_bar_width_is_40(self):
        p = build_profile_parser()
        args = p.parse_args(["myfile.log"])
        assert args.bar_width == 40

    def test_bucket_can_be_overridden(self):
        p = build_profile_parser()
        args = p.parse_args(["myfile.log", "--bucket", "300"])
        assert args.bucket == 300

    def test_bar_width_can_be_overridden(self):
        p = build_profile_parser()
        args = p.parse_args(["myfile.log", "--bar-width", "20"])
        assert args.bar_width == 20


class TestCmdProfile:
    def test_returns_zero_on_success(self, log_file):
        out = io.StringIO()
        code = cmd_profile(_ns(log_file), out=out)
        assert code == 0

    def test_output_contains_peak(self, log_file):
        out = io.StringIO()
        cmd_profile(_ns(log_file), out=out)
        assert "Peak" in out.getvalue()

    def test_missing_file_returns_one(self):
        out = io.StringIO()
        code = cmd_profile(_ns("/no/such/file.log"), out=out)
        assert code == 1

    def test_missing_file_prints_error(self):
        out = io.StringIO()
        cmd_profile(_ns("/no/such/file.log"), out=out)
        assert "error" in out.getvalue().lower()

    def test_invalid_bucket_returns_one(self, log_file):
        out = io.StringIO()
        code = cmd_profile(_ns(log_file, bucket=0), out=out)
        assert code == 1

    def test_custom_bucket_reflected_in_output(self, log_file):
        out = io.StringIO()
        cmd_profile(_ns(log_file, bucket=300), out=out)
        assert "300" in out.getvalue()
