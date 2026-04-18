"""Tests for next_steps_formatter module."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from __lib.next_steps_formatter import (
    FormattedNextSteps,
    NextStep,
    NextStepsFormatter,
    format_recommended_next_steps,
)


class TestNextStepsFormatter:
    """Smoke tests for NextStepsFormatter."""

    def test_formatter_instantiation(self) -> None:
        """Test formatter can be instantiated."""
        formatter = NextStepsFormatter()
        assert formatter is not None

    def test_format_empty_gaps(self) -> None:
        """Test formatting with no gaps."""
        result = format_recommended_next_steps([])
        assert isinstance(result, FormattedNextSteps)


class TestNextStep:
    """Tests for NextStep dataclass."""

    def test_dataclass(self) -> None:
        """Test NextStep can be constructed."""
        step = NextStep(
            gap_id="GAP-001",
            description="Test step",
            category="tests",
            priority="high",
            effort_estimate_minutes=5,
            recurrence_count=1,
            file_path=None,
            line_number=None,
        )
        assert step.gap_id == "GAP-001"
        assert step.effort_estimate_minutes == 5


class TestFormattedNextSteps:
    """Tests for FormattedNextSteps dataclass."""

    def test_dataclass(self) -> None:
        """Test FormattedNextSteps can be constructed."""
        result = FormattedNextSteps(
            steps_by_category={"tests": []},
            total_count=0,
            critical_count=0,
            high_count=0,
            medium_count=0,
            low_count=0,
            total_effort_minutes=0,
        )
        assert result.total_count == 0


# ── Tests for _detect_batch_groups ────────────────────────────────────────────

from __lib.next_steps_formatter import (
    GAP_TYPE_REVERSIBILITY,
    GTO_TYPE_TO_RSN_DOMAIN,
    _detect_batch_groups,
    format_rsn_from_gaps,
)


class TestDetectBatchGroupsInputValidation:
    """Input validation for _detect_batch_groups."""

    def test_raises_typeerror_for_non_list(self) -> None:
        """TypeError raised when gaps is not a list."""
        with pytest.raises(TypeError, match="gaps must be a list"):
            _detect_batch_groups(None)  # type: ignore[arg-type]

    def test_raises_typeerror_for_dict(self) -> None:
        """TypeError raised when gaps is a dict."""
        with pytest.raises(TypeError, match="gaps must be a list"):
            _detect_batch_groups({"id": "x"})  # type: ignore[arg-type]

    def test_empty_list_returns_empty(self) -> None:
        """Empty gaps list returns empty results."""
        results = _detect_batch_groups([])
        assert results == []


class TestDetectBatchGroupsStrategy1Location:
    """Strategy 1: Same (file_path, line_number) location batching."""

    def test_two_gaps_same_file_line_batched(self) -> None:
        """Two gaps at same file:line are batched with blast_radius=2."""
        gaps = [
            {
                "id": "G1",
                "type": "test_gap",
                "severity": "HIGH",
                "message": "Error 1",
                "file_path": "foo.py",
                "line_number": 10,
            },
            {
                "id": "G2",
                "type": "test_gap",
                "severity": "HIGH",
                "message": "Error 1",
                "file_path": "foo.py",
                "line_number": 10,
            },
        ]
        results = _detect_batch_groups(gaps)
        assert len(results) == 1
        assert results[0]["is_batch"] is True
        assert results[0]["blast_radius"] == 2
        assert results[0]["batch_count"] == 2
        assert results[0]["gap_ids"] == ["G1", "G2"]

    def test_single_gap_not_batched(self) -> None:
        """A single gap is not batched (passes to Strategy 3)."""
        gaps = [
            {
                "id": "G1",
                "type": "test_gap",
                "severity": "HIGH",
                "message": "Error",
                "file_path": "foo.py",
                "line_number": 10,
            },
        ]
        results = _detect_batch_groups(gaps)
        assert len(results) == 1
        assert results[0]["is_batch"] is False
        assert results[0]["blast_radius"] == 1

    def test_file_path_none_normalized_to_empty(self) -> None:
        """None file_path is normalized to '' for location key."""
        gaps = [
            {
                "id": "G1",
                "severity": "HIGH",
                "message": "Error",
                "file_path": None,
                "line_number": 10,
            },
            {
                "id": "G2",
                "severity": "HIGH",
                "message": "Error",
                "file_path": "",
                "line_number": 10,
            },
        ]
        results = _detect_batch_groups(gaps)
        # Both have file_path None/'' → same key → batched
        assert len(results) == 1
        assert results[0]["is_batch"] is True
        assert results[0]["blast_radius"] == 2

    def test_different_lines_not_batched(self) -> None:
        """Gaps at same file but different lines are not batched."""
        gaps = [
            {
                "id": "G1",
                "severity": "HIGH",
                "message": "Error",
                "file_path": "foo.py",
                "line_number": 10,
            },
            {
                "id": "G2",
                "severity": "HIGH",
                "message": "Error",
                "file_path": "foo.py",
                "line_number": 20,
            },
        ]
        results = _detect_batch_groups(gaps)
        # Both go to Strategy 3 as individual (different locations, not batched)
        assert len(results) == 2
        assert all(r["is_batch"] is False for r in results)

    def test_domain_derived_from_gap_types(self) -> None:
        """Strategy 1 domain is derived from batched gap types (not hardcoded)."""
        gaps = [
            {
                "id": "G1",
                "type": "test_gap",
                "severity": "HIGH",
                "message": "Error",
                "file_path": "foo.py",
                "line_number": 10,
            },
            {
                "id": "G2",
                "type": "test_gap",
                "severity": "HIGH",
                "message": "Error",
                "file_path": "foo.py",
                "line_number": 10,
            },
        ]
        results = _detect_batch_groups(gaps)
        # test_gap → GTO_TYPE_TO_RSN_DOMAIN → "test"
        assert results[0]["domain"] == "test"

    def test_severity_worst_wins_aggregation(self) -> None:
        """Aggregate severity uses worst wins (CRITICAL > HIGH > MEDIUM > LOW)."""
        gaps = [
            {
                "id": "G1",
                "severity": "LOW",
                "message": "Error",
                "file_path": "foo.py",
                "line_number": 10,
            },
            {
                "id": "G2",
                "severity": "CRITICAL",
                "message": "Error",
                "file_path": "foo.py",
                "line_number": 10,
            },
            {
                "id": "G3",
                "severity": "HIGH",
                "message": "Error",
                "file_path": "foo.py",
                "line_number": 10,
            },
        ]
        results = _detect_batch_groups(gaps)
        assert results[0]["severity"] == "CRITICAL"

    def test_severity_none_becomes_low(self) -> None:
        """None severity is treated as LOW (not crashing)."""
        gaps = [
            {
                "id": "G1",
                "severity": None,
                "message": "Error",
                "file_path": "foo.py",
                "line_number": 10,
            },
            {
                "id": "G2",
                "severity": None,
                "message": "Error",
                "file_path": "foo.py",
                "line_number": 10,
            },
        ]
        results = _detect_batch_groups(gaps)
        # Should not crash, severity defaults to LOW
        assert results[0]["severity"] == "LOW"

    def test_severity_mixed_case_normalized(self) -> None:
        """Mixed-case severity values (e.g., 'High', 'critical') are normalized."""
        gaps = [
            {
                "id": "G1",
                "severity": "High",
                "message": "Error",
                "file_path": "foo.py",
                "line_number": 10,
            },
            {
                "id": "G2",
                "severity": "Critical",
                "message": "Error",
                "file_path": "foo.py",
                "line_number": 10,
            },
        ]
        results = _detect_batch_groups(gaps)
        assert results[0]["severity"] == "CRITICAL"

    def test_reversibility_worst_wins_max_aggregation(self) -> None:
        """Strategy 1 reversibility uses worst-wins (max score) aggregation."""
        # missing_test = 1.25, code_quality = 1.75
        gaps = [
            {
                "id": "G1",
                "type": "missing_test",
                "severity": "HIGH",
                "message": "Error",
                "file_path": "foo.py",
                "line_number": 10,
            },
            {
                "id": "G2",
                "type": "code_quality",
                "severity": "HIGH",
                "message": "Error",
                "file_path": "foo.py",
                "line_number": 10,
            },
        ]
        results = _detect_batch_groups(gaps)
        # max(1.25, 1.75) = 1.75
        assert results[0]["reversibility"] == 1.75
        assert GAP_TYPE_REVERSIBILITY["missing_test"] == 1.25
        assert GAP_TYPE_REVERSIBILITY["code_quality"] == 1.75

    def test_reversibility_single_gap_type_from_mapping(self) -> None:
        """Strategy 1 with single gap type uses direct mapping."""
        gaps = [
            {
                "id": "G1",
                "type": "missing_dependency",
                "severity": "HIGH",
                "message": "Error",
                "file_path": "foo.py",
                "line_number": 10,
            },
            {
                "id": "G2",
                "type": "missing_dependency",
                "severity": "HIGH",
                "message": "Error",
                "file_path": "foo.py",
                "line_number": 10,
            },
        ]
        results = _detect_batch_groups(gaps)
        # missing_dependency = 1.5, max of two = 1.5
        assert results[0]["reversibility"] == 1.5

    def test_strategy1_skips_type_ignore_gaps(self) -> None:
        """Strategy 1 must NOT pre-batch # type: ignore gaps — Strategy 2 handles them.

        Regression test: Without this guard, Strategy 1 would batch G3+G4 at
        ("", 10) and ("", 20) separately, but then Strategy 2 would skip them
        because they're already in used_indices, leaving them in wrong batches.
        """
        gaps = [
            # Strategy 2 candidate: same reason (# type: ignore [missing]) at different lines
            {
                "id": "G3",
                "severity": "HIGH",
                "message": "foo.py:10: # type: ignore [missing]",
                "file_path": "foo.py",
                "line_number": 10,
            },
            {
                "id": "G4",
                "severity": "HIGH",
                "message": "bar.py:20: # type: ignore [missing]",
                "file_path": "bar.py",
                "line_number": 20,
            },
        ]
        results = _detect_batch_groups(gaps)
        # Strategy 2 must batch them together despite different lines
        assert len(results) == 1, f"Expected 1 batch, got {len(results)}: {results}"
        assert results[0]["is_batch"] is True
        assert results[0]["blast_radius"] == 2
        assert results[0]["domain"] == "import"


class TestDetectBatchGroupsStrategy2TypeIgnore:
    """Strategy 2: # type: ignore root cause grouping."""

    def test_two_type_ignore_same_reason_batched(self) -> None:
        """Two gaps with same # type: ignore reason are batched."""
        gaps = [
            {
                "id": "G1",
                "severity": "HIGH",
                "message": "foo.py:10: # type: ignore [missing]",
                "file_path": "foo.py",
                "line_number": 10,
            },
            {
                "id": "G2",
                "severity": "HIGH",
                "message": "bar.py:20: # type: ignore [missing]",
                "file_path": "bar.py",
                "line_number": 20,
            },
        ]
        results = _detect_batch_groups(gaps)
        assert len(results) == 1
        assert results[0]["is_batch"] is True
        assert results[0]["blast_radius"] == 2

    def test_type_ignore_different_reasons_separate_batches(self) -> None:
        """Different # type: ignore reasons → Strategy 2 doesn't batch (different reasons),
        Strategy 3 handles individually. At different locations so Strategy 1 also doesn't batch."""
        gaps = [
            {
                "id": "G1",
                "severity": "HIGH",
                "message": "foo.py:10: # type: ignore [missing]",
                "file_path": "foo.py",
                "line_number": 10,
            },
            {
                "id": "G2",
                "severity": "HIGH",
                "message": "bar.py:20: # type: ignore [cannot find]",
                "file_path": "bar.py",
                "line_number": 20,
            },
        ]
        results = _detect_batch_groups(gaps)
        # Different locations → Strategy 1 doesn't batch
        # Different reasons (file path in message) → Strategy 2 doesn't batch
        # Strategy 3 handles individually
        assert len(results) == 2
        assert all(r["is_batch"] is False for r in results)

    def test_type_ignore_domain_from_keyword_missing(self) -> None:
        """# type: ignore [missing] → domain = 'import'."""
        gaps = [
            {
                "id": "G1",
                "severity": "HIGH",
                "message": "foo.py:10: # type: ignore [missing]",
                "file_path": "foo.py",
                "line_number": 10,
            },
            {
                "id": "G2",
                "severity": "HIGH",
                "message": "bar.py:20: # type: ignore [missing]",
                "file_path": "bar.py",
                "line_number": 20,
            },
        ]
        results = _detect_batch_groups(gaps)
        assert results[0]["domain"] == "import"

    def test_type_ignore_domain_from_keyword_cannot_find(self) -> None:
        """# type: ignore [cannot find] → domain = 'code_quality'."""
        gaps = [
            {
                "id": "G1",
                "severity": "HIGH",
                "message": "foo.py:10: # type: ignore [cannot find]",
                "file_path": "foo.py",
                "line_number": 10,
            },
            {
                "id": "G2",
                "severity": "HIGH",
                "message": "bar.py:20: # type: ignore [cannot find]",
                "file_path": "bar.py",
                "line_number": 20,
            },
        ]
        results = _detect_batch_groups(gaps)
        assert results[0]["domain"] == "code_quality"

    def test_type_ignore_non_string_message_skipped(self) -> None:
        """Non-string messages are handled individually (not batched by Strategy 1
        since different locations, and skipped by Strategy 2 since no # type: ignore)."""
        gaps = [
            {
                "id": "G1",
                "severity": "HIGH",
                "message": None,
                "file_path": "foo.py",
                "line_number": 10,
            },  # type: ignore[dict-item]
            {
                "id": "G2",
                "severity": "HIGH",
                "message": None,
                "file_path": "bar.py",
                "line_number": 20,
            },  # type: ignore[dict-item]
        ]
        results = _detect_batch_groups(gaps)
        # Different locations → Strategy 1 doesn't batch
        # message=None → Strategy 2 skips (not a string, no # type: ignore)
        # Strategy 3 handles individually
        assert len(results) == 2
        assert all(r["is_batch"] is False for r in results)

    def test_type_ignore_no_match_skipped(self) -> None:
        """Gap without matching keyword is passed to Strategy 3."""
        gaps = [
            {
                "id": "G1",
                "severity": "HIGH",
                "message": "some other error",
                "file_path": "foo.py",
                "line_number": 10,
            },
        ]
        results = _detect_batch_groups(gaps)
        assert len(results) == 1
        assert results[0]["is_batch"] is False

    def test_type_ignore_reversibility_fixed_1_5(self) -> None:
        """Strategy 2 # type: ignore batches get fixed reversibility = 1.5."""
        gaps = [
            {
                "id": "G1",
                "severity": "HIGH",
                "message": "foo.py:10: # type: ignore [missing]",
                "file_path": "foo.py",
                "line_number": 10,
            },
            {
                "id": "G2",
                "severity": "HIGH",
                "message": "bar.py:20: # type: ignore [missing]",
                "file_path": "bar.py",
                "line_number": 20,
            },
        ]
        results = _detect_batch_groups(gaps)
        # Strategy 2 uses fixed reversibility = 1.5
        assert results[0]["is_batch"] is True
        assert results[0]["reversibility"] == 1.5


class TestDetectBatchGroupsStrategy3:
    """Strategy 3: Individual gap handling."""

    def test_individual_gap_blast_radius_one(self) -> None:
        """Individual gaps get blast_radius = 1."""
        gaps = [
            {
                "id": "G1",
                "type": "code_quality",
                "severity": "HIGH",
                "message": "Error",
                "file_path": "foo.py",
                "line_number": 10,
            },
        ]
        results = _detect_batch_groups(gaps)
        assert results[0]["blast_radius"] == 1
        assert results[0]["is_batch"] is False

    def test_domain_from_gto_type_to_rsn_domain(self) -> None:
        """Strategy 3 domain is derived from GTO_TYPE_TO_RSN_DOMAIN."""
        gaps = [
            {"id": "G1", "type": "test_gap", "severity": "HIGH", "message": "Error"},
        ]
        results = _detect_batch_groups(gaps)
        assert results[0]["domain"] == GTO_TYPE_TO_RSN_DOMAIN["test_gap"]

    def test_severity_uppercase_normalized(self) -> None:
        """Strategy 3 severity is uppercased."""
        gaps = [
            {"id": "G1", "severity": "high", "message": "Error"},
        ]
        results = _detect_batch_groups(gaps)
        assert results[0]["severity"] == "HIGH"

    def test_severity_none_becomes_low(self) -> None:
        """None severity defaults to LOW (not crashing)."""
        gaps = [
            {"id": "G1", "severity": None, "message": "Error"},
        ]
        results = _detect_batch_groups(gaps)
        assert results[0]["severity"] == "LOW"

    def test_reversibility_direct_lookup_from_mapping(self) -> None:
        """Strategy 3 reversibility is a direct lookup from GAP_TYPE_REVERSIBILITY."""
        gaps = [
            {"id": "G1", "type": "vulnerable_dependency", "severity": "HIGH", "message": "Error"},
        ]
        results = _detect_batch_groups(gaps)
        # vulnerable_dependency = 1.75
        assert results[0]["reversibility"] == GAP_TYPE_REVERSIBILITY["vulnerable_dependency"]
        assert results[0]["reversibility"] == 1.75

    def test_reversibility_unknown_type_defaults_to_1_75(self) -> None:
        """Strategy 3 reversibility defaults to 1.75 for unknown gap types."""
        gaps = [
            {"id": "G1", "type": "completely_unknown_type", "severity": "HIGH", "message": "Error"},
        ]
        results = _detect_batch_groups(gaps)
        # Unknown types default to 1.75
        assert results[0]["reversibility"] == 1.75

    def test_reversibility_various_gap_types(self) -> None:
        """Strategy 3 correctly maps all gap types to reversibility scores."""
        test_cases = [
            ("git_dirty", 1.0),
            ("missing_lock_file", 1.0),
            ("missing_docs", 1.0),
            ("missing_claude_md", 1.0),
            ("test_failure", 1.25),
            ("missing_test", 1.25),
            ("import_error", 1.5),
            ("missing_dependency", 1.5),
            ("outdated_dependency", 1.5),
            ("vulnerable_dependency", 1.75),
            ("code_quality", 1.75),
        ]
        for gap_type, expected_reversibility in test_cases:
            gaps = [
                {"id": f"G_{gap_type}", "type": gap_type, "severity": "HIGH", "message": "Error"}
            ]
            results = _detect_batch_groups(gaps)
            assert results[0]["reversibility"] == expected_reversibility, (
                f"Expected {gap_type} -> {expected_reversibility}, got {results[0]['reversibility']}"
            )


class TestDetectBatchGroupsSafeMsg:
    """_safe_msg sanitization for unhashable message types."""

    def test_non_string_message_repr(self) -> None:
        """Non-string message is converted via repr()."""
        gaps = [
            {
                "id": "G1",
                "severity": "HIGH",
                "message": {"nested": "dict"},
                "file_path": "foo.py",
                "line_number": 10,
            },
            {
                "id": "G2",
                "severity": "HIGH",
                "message": {"nested": "dict"},
                "file_path": "foo.py",
                "line_number": 10,
            },
        ]
        # Should not crash (repr handles unhashable type)
        results = _detect_batch_groups(gaps)
        assert len(results) == 1


class TestFormatRsnFromGaps:
    """Integration tests for format_rsn_from_gaps()."""

    def test_end_to_end_with_gaps(self) -> None:
        """format_rsn_from_gaps produces GTO-native RNS text with reversibility tiers."""
        gaps = [
            {
                "id": "G1",
                "type": "test_gap",
                "severity": "HIGH",
                "message": "Fix this",
                "file_path": "foo.py",
                "line_number": 10,
            },
        ]
        result = format_rsn_from_gaps(gaps, intent_summary="Test analysis")
        assert isinstance(result, str)
        assert len(result) > 0
        # GTO-native format: reversibility-tier section + domain emoji + generated ID
        assert "DEFER" in result or "TRIVIAL" in result or "MODERATE" in result
        assert "TEST" in result
        # Does NOT produce the old RSNFormatter header
        assert "Recommended Next Steps" not in result

    def test_empty_gaps_empty_output(self) -> None:
        """Empty gaps list produces empty string (no header from formatter)."""
        result = format_rsn_from_gaps([])
        assert isinstance(result, str)
        assert result == ""


import pytest  # noqa: E402  (must be imported after tests that don't use it)
