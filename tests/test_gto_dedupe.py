"""Tests for GTO deduplication."""
import pytest

from skills.gto.models import Finding
from skills.gto.__lib.dedupe import dedupe_findings


def _f(domain="quality", title="Test", file=None, **kw):
    defaults = dict(
        id="D-001", description="D", source_type="detector",
        source_name="test", gap_type="g", severity="medium",
        evidence_level="verified", domain=domain, title=title, file=file,
    )
    defaults.update(kw)
    return Finding(**defaults)


class TestDedupeFindings:
    def test_no_duplicates(self):
        a = _f(domain="quality", title="A")
        b = _f(domain="tests", title="B")
        result = dedupe_findings([a, b])
        assert len(result) == 2

    def test_exact_duplicate_removed(self):
        a = _f(domain="quality", title="Same")
        b = _f(domain="quality", title="Same")
        result = dedupe_findings([a, b])
        assert len(result) == 1

    def test_same_domain_different_title_kept(self):
        a = _f(domain="quality", title="A")
        b = _f(domain="quality", title="B")
        result = dedupe_findings([a, b])
        assert len(result) == 2

    def test_same_title_different_file_kept(self):
        a = _f(domain="quality", title="Same", file="a.py")
        b = _f(domain="quality", title="Same", file="b.py")
        result = dedupe_findings([a, b])
        assert len(result) == 2

    def test_keeps_first_occurrence(self):
        a = _f(domain="quality", title="Same", severity="high")
        b = _f(domain="quality", title="Same", severity="low")
        result = dedupe_findings([a, b])
        assert len(result) == 1
        assert result[0].severity == "high"

    def test_empty_list(self):
        assert dedupe_findings([]) == []
