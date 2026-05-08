"""Tests for logslice.grouper_cli."""
from __future__ import annotations

import argparse
import io
import textwrap

import pytest

from logslice.grouper_cli import build_grouper_parser, cmd_group


@pytest.fixture()
def log_file(tmp_path):
    content = textwrap.dedent("""\
        2024-01-01 host-a INFO  start
        2024-01-01 host-b ERROR crash
        2024-01-01 host-a WARN  slow
        no-host line
    """)
    p = tmp_path / "test.log"
    p.write_text(content)
    return str(p)


def _ns(**kwargs) -> argparse.Namespace:
    defaults = dict(
        file="-",
        pattern=r"(host-\w+)",
        group=1,
        case_sensitive=False,
        default_key="__ungrouped__",
        separator="---",
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestBuildGrouperParser:
    def test_returns_argument_parser(self):
        assert isinstance(build_grouper_parser(), argparse.ArgumentParser)

    def test_default_group_is_1(self):
        p = build_grouper_parser()
        ns = p.parse_args(["somefile", "--pattern", r"(\w+)"])
        assert ns.group == 1

    def test_default_case_sensitive_is_false(self):
        p = build_grouper_parser()
        ns = p.parse_args(["somefile", "--pattern", r"(\w+)"])
        assert ns.case_sensitive is False

    def test_default_separator_is_dashes(self):
        p = build_grouper_parser()
        ns = p.parse_args(["somefile", "--pattern", r"(\w+)"])
        assert ns.separator == "---"

    def test_default_default_key(self):
        p = build_grouper_parser()
        ns = p.parse_args(["somefile", "--pattern", r"(\w+)"])
        assert ns.default_key == "__ungrouped__"


class TestCmdGroup:
    def test_returns_zero_on_success(self, log_file):
        ns = _ns(file=log_file)
        assert cmd_group(ns, out=io.StringIO()) == 0

    def test_output_contains_host_a(self, log_file):
        ns = _ns(file=log_file)
        out = io.StringIO()
        cmd_group(ns, out=out)
        assert "host-a" in out.getvalue()

    def test_output_contains_host_b(self, log_file):
        ns = _ns(file=log_file)
        out = io.StringIO()
        cmd_group(ns, out=out)
        assert "host-b" in out.getvalue()

    def test_ungrouped_lines_present(self, log_file):
        ns = _ns(file=log_file)
        out = io.StringIO()
        cmd_group(ns, out=out)
        assert "__ungrouped__" in out.getvalue()

    def test_custom_separator_in_output(self, log_file):
        ns = _ns(file=log_file, separator="===")
        out = io.StringIO()
        cmd_group(ns, out=out)
        assert "===" in out.getvalue()

    def test_custom_default_key(self, log_file):
        ns = _ns(file=log_file, default_key="misc")
        out = io.StringIO()
        cmd_group(ns, out=out)
        assert "misc" in out.getvalue()
