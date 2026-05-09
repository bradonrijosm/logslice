"""Tests for logslice.extractor_cli."""
from __future__ import annotations

import argparse
import io
import sys
import pytest

from logslice.extractor_cli import build_extractor_parser, cmd_extract, _parse_rules
from logslice.extractor import ExtractRule


@pytest.fixture()
def log_file(tmp_path):
    p = tmp_path / "sample.log"
    p.write_text(
        "2024-01-01 ERROR 192.168.0.1 disk full\n"
        "2024-01-02 INFO  10.0.0.5 startup complete\n"
        "2024-01-03 WARN  172.16.0.3 high memory\n"
    )
    return p


def _ns(**kwargs):
    defaults = dict(
        logfile="-",
        fields=[],
        separator="\t",
        missing="-",
        case_sensitive=False,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestBuildExtractorParser:
    def test_returns_argument_parser(self):
        assert isinstance(build_extractor_parser(), argparse.ArgumentParser)

    def test_default_separator_is_tab(self):
        p = build_extractor_parser()
        ns = p.parse_args(["dummy.log"])
        assert ns.separator == "\t"

    def test_default_missing_is_dash(self):
        p = build_extractor_parser()
        ns = p.parse_args(["dummy.log"])
        assert ns.missing == "-"

    def test_default_case_sensitive_is_false(self):
        p = build_extractor_parser()
        ns = p.parse_args(["dummy.log"])
        assert ns.case_sensitive is False

    def test_field_flag_appends(self):
        p = build_extractor_parser()
        ns = p.parse_args(["dummy.log", "--field", "ip:(\\d+)", "--field", "lvl:(ERROR)"])
        assert len(ns.fields) == 2


class TestParseRules:
    def test_valid_spec_returns_rule(self):
        rules = _parse_rules(["ip:(\\d+)"], case_sensitive=False)
        assert len(rules) == 1
        assert rules[0].name == "ip"

    def test_invalid_spec_raises(self):
        with pytest.raises(ValueError):
            _parse_rules(["badspec"], case_sensitive=False)

    def test_case_sensitive_propagated(self):
        rules = _parse_rules(["x:(x)"], case_sensitive=True)
        assert rules[0].case_sensitive is True


class TestCmdExtract:
    def test_returns_zero_on_success(self, log_file, capsys):
        ns = _ns(logfile=str(log_file), fields=["ip:(\\d+\\.\\d+\\.\\d+\\.\\d+)"])
        rc = cmd_extract(ns)
        assert rc == 0

    def test_prints_extracted_values(self, log_file, capsys):
        ns = _ns(logfile=str(log_file), fields=["ip:(\\d+\\.\\d+\\.\\d+\\.\\d+)"])
        cmd_extract(ns)
        out = capsys.readouterr().out
        assert "192.168.0.1" in out
        assert "10.0.0.5" in out

    def test_missing_placeholder_used(self, log_file, capsys):
        ns = _ns(
            logfile=str(log_file),
            fields=["token:(Bearer \\S+)"],
            missing="NONE",
        )
        cmd_extract(ns)
        out = capsys.readouterr().out
        assert "NONE" in out

    def test_no_fields_returns_one(self, log_file, capsys):
        ns = _ns(logfile=str(log_file), fields=[])
        rc = cmd_extract(ns)
        assert rc == 1
