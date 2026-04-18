"""Tests for merge_agent_results module."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from __lib.merge_agent_results import load_json_file, merge_gaps
import pytest


class TestMergeGapsTypeAndDomain:
    """Tests for correctness_gap type and domain field setting."""

    def test_logic_agent_sets_correctness_gap_type(self) -> None:
        """Logic agent findings should get type=correctness_gap."""
        l1 = {"gaps": []}
        agent_data = {
            "logic": {
                "findings": [
                    {
                        "id": "LOGIC-001",
                        "severity": "HIGH",
                        "location": "test.py:1",
                        "title": "Test finding",
                    }
                ]
            }
        }
        result = merge_gaps(l1, agent_data)
        assert len(result["gaps"]) == 1
        gap = result["gaps"][0]
        assert gap["type"] == "correctness_gap", f"Expected 'correctness_gap', got {gap.get('type')}"
        assert gap["domain"] == "correctness", f"Expected 'correctness', got {gap.get('domain')}"

    def test_quality_agent_sets_correctness_gap_type(self) -> None:
        """Quality agent findings should get type=correctness_gap."""
        l1 = {"gaps": []}
        agent_data = {
            "quality": {
                "findings": [
                    {
                        "id": "QUAL-001",
                        "severity": "MEDIUM",
                        "location": "test.py:2",
                        "title": "Test finding",
                    }
                ]
            }
        }
        result = merge_gaps(l1, agent_data)
        assert len(result["gaps"]) == 1
        gap = result["gaps"][0]
        assert gap["type"] == "correctness_gap"
        assert gap["domain"] == "correctness"

    def test_code_critic_agent_sets_correctness_gap_type(self) -> None:
        """Code critic agent findings should get type=correctness_gap."""
        l1 = {"gaps": []}
        agent_data = {
            "code-critic": {
                "findings": [
                    {
                        "id": "CAUSE-001",
                        "severity": "HIGH",
                        "location": "test.py:3",
                        "title": "Test finding",
                    }
                ]
            }
        }
        result = merge_gaps(l1, agent_data)
        assert len(result["gaps"]) == 1
        gap = result["gaps"][0]
        assert gap["type"] == "correctness_gap"
        assert gap["domain"] == "correctness"

    def test_multiple_agents_all_get_correctness_gap(self) -> None:
        """All correctness agents should set correctness_gap type."""
        l1 = {"gaps": []}
        agent_data = {
            "logic": {
                "findings": [
                    {"id": "LOGIC-001", "severity": "HIGH", "location": "x.py:1", "title": "T1"}
                ]
            },
            "quality": {
                "findings": [
                    {"id": "QUAL-001", "severity": "MEDIUM", "location": "y.py:2", "title": "T2"}
                ]
            },
            "code-critic": {
                "findings": [
                    {"id": "CAUSE-001", "severity": "HIGH", "location": "z.py:3", "title": "T3"}
                ]
            },
        }
        result = merge_gaps(l1, agent_data)
        assert len(result["gaps"]) == 3
        for gap in result["gaps"]:
            assert gap["type"] == "correctness_gap"
            assert gap["domain"] == "correctness"

    def test_correctness_gap_maps_to_correctness_rns_domain(self) -> None:
        """correctness_gap type should map to correctness RNS domain."""
        from __lib.next_steps_formatter import GTO_TYPE_TO_RSN_DOMAIN

        assert "correctness_gap" in GTO_TYPE_TO_RSN_DOMAIN
        assert GTO_TYPE_TO_RSN_DOMAIN["correctness_gap"] == "correctness"


class TestWindowsPathHandling:
    """Regression tests for Windows path handling in agent JSON output.

    GTO agents running on Windows produce JSON with Windows paths containing
    backslashes (e.g. C:\\Users\\...). These paths must not cause JSON decode
    errors when loaded by merge_agent_results.py.
    """

    def test_quality_agent_findings_with_windows_path(self) -> None:
        """Quality agent output with Windows path should parse without error.

        Symptom: When quality agent writes findings with evidence field containing
        a Windows path (e.g. C:\\Users\\brsth\\AppData\\...), the backslashes
        trigger invalid \\u escape sequences during JSON parsing. merge_gaps
        silently returns 0 gaps because the JSON is invalid but the error is
        caught by the try/except and the file is skipped entirely.

        This test validates that Windows paths in findings are handled correctly.
        """
        # Simulate quality agent output with Windows path in evidence field
        quality_output = {
            "findings": [
                {
                    "id": "QUAL-001",
                    "severity": "MEDIUM",
                    "location": "gap_resolution_tracker.py:644-648",
                    "title": "Deeply nested regex normalization function",
                    "description": "Function get_gap_decay_metrics() contains deeply nested logic.",
                    "evidence": "def get_gap_decay_metrics(target_key: str) -> dict[str, GapDecayMetrics]:"
                }
            ]
        }
        # Merge should succeed without raising JSONDecodeError
        l1 = {"gaps": []}
        result = merge_gaps(l1, {"quality": quality_output})
        assert len(result["gaps"]) == 1
        assert result["gaps"][0]["id"] == "QUAL-001"

    def test_gap_finder_output_with_windows_file_path(self) -> None:
        """Gap finder output with Windows file paths should parse without error.

        Symptom: Gap finder running on Windows writes gap files with paths like
        C:\\Users\\brsth\\AppData\\Local\\Temp\\gto-xterm-...\\gto-gap-finder-....json.
        The backslashes in paths can trigger JSON decode failures if written
        as string literals with unescaped backslashes.
        """
        gap_finder_output = {
            "gaps": [
                {
                    "id": "GAP-00000001",
                    "type": "code_quality",
                    "message": "TODO: Add tests",
                    "file_path": "C:\\Users\\brsth\\AppData\\Local\\Temp\\gto-test\\test.py",
                    "line_number": 10,
                    "severity": "medium",
                    "metadata": {}
                }
            ],
            "files_scanned": 100,
            "gaps_found": 1
        }
        l1 = {"gaps": []}
        result = merge_gaps(l1, {}, gap_finder_output)
        assert len(result["gaps"]) == 1
        assert result["gaps"][0]["id"] == "GAP-00000001"


class TestInvalidJSONHandling:
    """Tests for merge behavior when agent output files contain invalid JSON.

    These tests validate fail-fast behavior: when an agent output file contains
    invalid JSON (e.g. corrupted, truncated, or malformed), merge should NOT
    silently produce 0 gaps. It should either raise or report the error clearly.
    """

    def test_invalid_json_in_quality_agent_file_raises_decode_error(self) -> None:
        """Invalid JSON in quality agent file should raise JSONDecodeError.

        Symptom: The quality agent (subagent ae5f09b7250c8eb77) wrote a JSON file
        that produced "Invalid \\escape: line 88 column 65 (char 5010)" during
        merge. The file appeared to exist but contained malformed JSON. merge_gaps
        should raise JSONDecodeError rather than silently returning 0 gaps.
        """
        # Write a JSON file with an invalid escape sequence (simulates corrupted output)
        # \x is not a valid JSON escape sequence
        invalid_json_content = '{"findings": [{"id": "QUAL-001", "severity": "MEDIUM", ' \
            '"location": "test.py:1", "title": "Test", "evidence": "path\\xinvalid"}]}'

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            f.write(invalid_json_content)
            temp_path = Path(f.name)

        try:
            with pytest.raises(json.JSONDecodeError):
                load_json_file(temp_path)
        finally:
            temp_path.unlink(missing_ok=True)