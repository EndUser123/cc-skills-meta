"""Tests for GTO normalization."""
import pytest

from skills.gto.models import Finding
from skills.gto.__lib.normalize import normalize_finding, normalize_findings


def _f(**overrides):
    defaults = dict(
        id="N-001", title="T", description="D", source_type="detector",
        source_name="test", domain="quality", gap_type="g",
        severity="medium", evidence_level="verified",
    )
    defaults.update(overrides)
    return Finding(**defaults)


class TestNormalizeFinding:
    def test_valid_fields_unchanged(self):
        f = _f(domain="quality", severity="high", action="recover", priority="medium")
        n = normalize_finding(f)
        assert n.domain == "quality"
        assert n.severity == "high"

    def test_domain_alias(self):
        f = _f(domain="code_quality")
        assert normalize_finding(f).domain == "quality"

    def test_domain_alias_testing(self):
        f = _f(domain="testing")
        assert normalize_finding(f).domain == "tests"

    def test_invalid_severity_normalized(self):
        f = _f(severity="urgent")
        assert normalize_finding(f).severity == "medium"

    def test_invalid_action_normalized(self):
        f = _f(action="delete")
        assert normalize_finding(f).action == "recover"

    def test_invalid_priority_normalized(self):
        f = _f(priority="asap")
        assert normalize_finding(f).priority == "medium"

    def test_preserves_optional_fields(self):
        f = _f(file="app.py", line=42, unverified=True)
        n = normalize_finding(f)
        assert n.file == "app.py"
        assert n.line == 42
        assert n.unverified is True


class TestNormalizeFindings:
    def test_batch(self):
        findings = [_f(id="1"), _f(id="2", domain="documentation")]
        result = normalize_findings(findings)
        assert len(result) == 2
        assert result[1].domain == "docs"
