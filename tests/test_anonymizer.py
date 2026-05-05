"""Tests for logslice.anonymizer."""

import pytest
from logslice.anonymizer import (
    anonymize_emails,
    anonymize_ips,
    anonymize_line,
    anonymize_lines,
    anonymize_tokens,
)


class TestAnonymizeIps:
    def test_single_ip_replaced(self):
        assert anonymize_ips("connect from 192.168.1.1") == "connect from <IP>"

    def test_multiple_ips_replaced(self):
        result = anonymize_ips("src=10.0.0.1 dst=10.0.0.2")
        assert result == "src=<IP> dst=<IP>"

    def test_no_ip_unchanged(self):
        line = "no address here"
        assert anonymize_ips(line) == line

    def test_custom_placeholder(self):
        assert anonymize_ips("1.2.3.4", placeholder="[REDACTED]") == "[REDACTED]"


class TestAnonymizeEmails:
    def test_single_email_replaced(self):
        assert anonymize_emails("user alice@example.com logged in") == "user <EMAIL> logged in"

    def test_multiple_emails_replaced(self):
        result = anonymize_emails("from a@b.com to c@d.org")
        assert "<EMAIL>" in result
        assert "@" not in result

    def test_no_email_unchanged(self):
        line = "no email in this line"
        assert anonymize_emails(line) == line

    def test_custom_placeholder(self):
        assert anonymize_emails("x@y.io", placeholder="ANON") == "ANON"


class TestAnonymizeTokens:
    def test_bearer_token_replaced(self):
        result = anonymize_tokens("Authorization: Bearer abc123xyz")
        assert "<TOKEN>" in result
        assert "abc123xyz" not in result

    def test_api_key_replaced(self):
        result = anonymize_tokens("api_key=supersecret")
        assert "<TOKEN>" in result
        assert "supersecret" not in result

    def test_no_token_unchanged(self):
        line = "ordinary log message"
        assert anonymize_tokens(line) == line


class TestAnonymizeLine:
    def test_all_categories_applied(self):
        line = "user a@b.com from 1.2.3.4 token=mytoken"
        result = anonymize_line(line)
        assert "<IP>" in result
        assert "<EMAIL>" in result
        assert "<TOKEN>" in result

    def test_skip_ips(self):
        line = "addr 1.2.3.4"
        result = anonymize_line(line, ips=False)
        assert "1.2.3.4" in result

    def test_skip_emails(self):
        line = "user a@b.com"
        result = anonymize_line(line, emails=False)
        assert "a@b.com" in result

    def test_empty_line_unchanged(self):
        assert anonymize_line("") == ""


class TestAnonymizeLines:
    def test_returns_same_length(self):
        lines = ["1.2.3.4", "a@b.com", "plain"]
        result = anonymize_lines(lines)
        assert len(result) == 3

    def test_empty_input_returns_empty(self):
        assert anonymize_lines([]) == []

    def test_original_list_not_mutated(self):
        original = ["1.2.3.4"]
        anonymize_lines(original)
        assert original == ["1.2.3.4"]
