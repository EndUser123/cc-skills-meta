"""Tests for GTO merge — deterministic vs agent finding deduplication."""
import pytest

from skills.gto.models import Finding
from skills.gto.__lib.merge import merge_findings


def _f(domain="quality", gap_type="missing", title="Test", source_type="detector", **kw):
    defaults = dict(
        id="D-001", description="D", source_type=source_type,
        source_name="test", domain=domain, gap_type=gap_type,
        title=title, severity="medium", evidence_level="verified",
    )
    defaults.update(kw)
    return Finding(**defaults)


class TestMergeFindings:
    def test_no_overlap_keeps_all(self):
        det = [_f(domain="quality", title="A")]
        agent = [_f(domain="tests", title="B", source_type="agent")]
        result = merge_findings(det, agent)
        assert len(result) == 2

    def test_exact_duplicate_agent_dropped(self):
        det = [_f(domain="quality", gap_type="missing", title="Same")]
        agent = [_f(domain="quality", gap_type="missing", title="Same", source_type="agent")]
        result = merge_findings(det, agent)
        assert len(result) == 1
        assert result[0].source_type == "detector"

    def test_same_domain_gap_type_different_title_kept(self):
        det = [_f(domain="quality", gap_type="missing", title="Gap A")]
        agent = [_f(domain="quality", gap_type="missing", title="Gap B", source_type="agent")]
        result = merge_findings(det, agent)
        assert len(result) == 2

    def test_same_domain_gap_type_multiple_agent_findings(self):
        det = [_f(domain="quality", gap_type="missing", title="Gap A")]
        agent = [
            _f(domain="quality", gap_type="missing", title="Gap B", source_type="agent"),
            _f(domain="quality", gap_type="missing", title="Gap C", source_type="agent"),
        ]
        result = merge_findings(det, agent)
        assert len(result) == 3

    def test_empty_deterministic(self):
        agent = [_f(source_type="agent")]
        result = merge_findings([], agent)
        assert len(result) == 1

    def test_empty_agent(self):
        det = [_f()]
        result = merge_findings(det, [])
        assert len(result) == 1

    def test_both_empty(self):
        assert merge_findings([], []) == []
