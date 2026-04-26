"""Tests for GTO route module."""
import pytest

from skills.gto.models import Finding
from skills.gto.__lib.route import route_finding, route_findings


def _f(gap_type="testgap", **kw):
    defaults = dict(
        id="R-001", title="T", description="D", source_type="detector",
        source_name="test", domain="quality", gap_type=gap_type,
        severity="medium", evidence_level="verified",
    )
    defaults.update(kw)
    return Finding(**defaults)


class TestRouteFinding:
    def test_missingdocs_routes_to_docs(self):
        f = route_finding(_f(gap_type="missingdocs"))
        assert f.owner_skill == "/docs"

    def test_techdebt_routes_to_code(self):
        f = route_finding(_f(gap_type="techdebt"))
        assert f.owner_skill == "/code"

    def test_runtime_error_routes_to_diagnose(self):
        f = route_finding(_f(gap_type="runtime_error"))
        assert f.owner_skill == "/diagnose"

    def test_bug_routes_to_diagnose(self):
        f = route_finding(_f(gap_type="bug"))
        assert f.owner_skill == "/diagnose"

    def test_unknown_gap_type_unrouted(self):
        f = route_finding(_f(gap_type="unknown_thing"))
        assert f.owner_skill is None

    def test_owner_reason_set(self):
        f = route_finding(_f(gap_type="security"))
        assert f.owner_reason is not None
        assert "security" in f.owner_reason

    def test_preserves_other_fields(self):
        original = _f(gap_type="perf", file="app.py", line=10)
        routed = route_finding(original)
        assert routed.file == "app.py"
        assert routed.line == 10
        assert routed.domain == "quality"


class TestRouteFindings:
    def test_batch(self):
        findings = [_f(gap_type="missingdocs"), _f(gap_type="unknown")]
        result = route_findings(findings)
        assert result[0].owner_skill == "/docs"
        assert result[1].owner_skill is None
