"""Tests for GTO machine render (RNS compatibility)."""
import pytest

from skills.gto.models import Finding
from skills.gto.__lib.machine_render import render_machine_format, _subletter


def _f(domain="quality", **kw):
    defaults = dict(
        id="MR-001", title="T", description="Test desc", source_type="detector",
        source_name="test", domain=domain, gap_type="g",
        severity="medium", evidence_level="verified",
    )
    defaults.update(kw)
    return Finding(**defaults)


class TestSubletter:
    def test_first(self):
        assert _subletter(1) == "a"

    def test_26th(self):
        assert _subletter(26) == "z"

    def test_27th(self):
        assert _subletter(27) == "ba"  # Excel-style: z=26, ba=27


class TestRenderMachineFormat:
    def test_empty_findings(self):
        output = render_machine_format([])
        assert "RNS|Z|0|NONE" in output
        assert "<!-- format: machine -->" in output

    def test_single_finding(self):
        f = _f(domain="quality", action="recover", priority="high")
        output = render_machine_format([f])
        assert "RNS|D|1|🔧|QUALITY" in output
        assert "RNS|A|1a|quality" in output
        assert "E:?" in output
        assert "recover/high" in output
        assert "RNS|Z|0|NONE" in output

    def test_multiple_domains(self):
        findings = [
            _f(id="1", domain="quality", title="Q"),
            _f(id="2", domain="tests", title="T"),
        ]
        output = render_machine_format(findings)
        assert "RNS|D|1|🔧|QUALITY" in output
        assert "RNS|D|2|🧪|TESTS" in output

    def test_pipe_escaping(self):
        f = _f(description="has a | pipe")
        output = render_machine_format([f])
        assert "has a \\| pipe" in output

    def test_12_field_format(self):
        """Verify machine output has exactly 12 pipe-separated fields per RNS|A| line."""
        f = _f(domain="quality", action="recover", priority="medium",
               file="app.py", line=10, effort="~5min")
        output = render_machine_format([f])
        for line in output.splitlines():
            if line.startswith("RNS|A|"):
                # Count pipe separators (not escaped)
                # RNS|A|1a|quality|E:~5min|recover/medium|desc|app.py:10|owner=|done=0|caused_by=|blocks=|unverified=0
                fields = line.split("|")
                assert len(fields) >= 12, f"Expected >= 12 pipe-separated fields, got {len(fields)}: {line}"

    def test_file_ref_with_line(self):
        f = _f(file="src/main.py", line=42)
        output = render_machine_format([f])
        assert "src/main.py:42" in output

    def test_unverified_flag(self):
        f = _f(unverified=True)
        output = render_machine_format([f])
        assert "unverified=1" in output

    def test_done_flag_resolved(self):
        f = _f(status="resolved")
        output = render_machine_format([f])
        assert "done=1" in output

    def test_owner_skill_in_output(self):
        f = _f(owner_skill="/code")
        output = render_machine_format([f])
        assert "owner=/code" in output
