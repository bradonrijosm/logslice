"""Tests for logslice.annotator_cli."""
from __future__ import annotations

import argparse
import io
import pytest

from logslice.annotator_cli import build_annotator_parser, cmd_annotate


@pytest.fixture()
def log_file(tmp_path):
    p = tmp_path / "app.log"
    p.write_text(
        "2024-03-01 10:00:00 INFO  boot\n"
        "2024-03-01 10:00:03 DEBUG tick\n"
        "2024-03-01 10:00:07 ERROR crash\n",
        encoding="utf-8",
    )
    return p


def _ns(**kwargs):
    defaults = dict(
        file="-",
        tag=None,
        start=1,
        show_lineno=True,
        show_tag=True,
        show_offset=True,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestBuildAnnotatorParser:
    def test_returns_argument_parser(self):
        assert isinstance(build_annotator_parser(), argparse.ArgumentParser)

    def test_default_tag_is_none(self):
        ns = build_annotator_parser().parse_args(["/dev/null"])
        assert ns.tag is None

    def test_default_start_is_1(self):
        ns = build_annotator_parser().parse_args(["/dev/null"])
        assert ns.start == 1

    def test_tag_flag_sets_tag(self):
        ns = build_annotator_parser().parse_args(["/dev/null", "--tag", "myapp"])
        assert ns.tag == "myapp"

    def test_no_lineno_flag(self):
        ns = build_annotator_parser().parse_args(["/dev/null", "--no-lineno"])
        assert ns.show_lineno is False

    def test_no_offset_flag(self):
        ns = build_annotator_parser().parse_args(["/dev/null", "--no-offset"])
        assert ns.show_offset is False

    def test_no_tag_flag(self):
        ns = build_annotator_parser().parse_args(["/dev/null", "--no-tag"])
        assert ns.show_tag is False


class TestCmdAnnotate:
    def test_returns_zero_on_success(self, log_file):
        out = io.StringIO()
        assert cmd_annotate(_ns(file=str(log_file)), out=out) == 0

    def test_output_line_count_matches_input(self, log_file):
        out = io.StringIO()
        cmd_annotate(_ns(file=str(log_file)), out=out)
        assert len(out.getvalue().splitlines()) == 3

    def test_line_numbers_present_by_default(self, log_file):
        out = io.StringIO()
        cmd_annotate(_ns(file=str(log_file)), out=out)
        assert "[1]" in out.getvalue()

    def test_tag_appears_in_output(self, log_file):
        out = io.StringIO()
        cmd_annotate(_ns(file=str(log_file), tag="srv"), out=out)
        assert "<srv>" in out.getvalue()

    def test_offset_appears_in_output(self, log_file):
        out = io.StringIO()
        cmd_annotate(_ns(file=str(log_file)), out=out)
        assert "+0.0s" in out.getvalue()

    def test_no_lineno_omits_brackets(self, log_file):
        out = io.StringIO()
        cmd_annotate(_ns(file=str(log_file), show_lineno=False), out=out)
        assert "[1]" not in out.getvalue()

    def test_no_offset_omits_seconds(self, log_file):
        out = io.StringIO()
        cmd_annotate(_ns(file=str(log_file), show_offset=False), out=out)
        assert "+0.0s" not in out.getvalue()

    def test_custom_start_lineno(self, log_file):
        out = io.StringIO()
        cmd_annotate(_ns(file=str(log_file), start=100), out=out)
        assert "[100]" in out.getvalue()
