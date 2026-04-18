"""Tests for gap_resolution_tracker loop closure functionality."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import Mock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from __lib.gap_resolution_tracker import (
    ResolutionRecord,
    ResolutionVerificationRecord,
    _append_resolution_record,
    _append_verification_record,
    _get_previous_gaps_path,
    _get_resolution_log_path,
    _get_verification_log_path,
    _normalize_gap_key,
    _read_resolution_log,
    _read_verification_log,
    _save_previous_gaps,
    _verify_past_resolutions,
    get_skill_effectiveness_score,
    track_gap_resolutions,
)


class TestGapResolutionNormalize:
    """Tests for gap ID normalization."""

    def test_normalize_gap_key_strips_numeric_suffix(self) -> None:
        """Test that gap IDs with numeric suffixes are normalized."""
        assert _normalize_gap_key("TEST-001") == "TEST-001"
        assert _normalize_gap_key("TEST-001-1") == "TEST-001"
        assert _normalize_gap_key("TEST-001-2") == "TEST-001"
        assert _normalize_gap_key("SESSION-abc-003") == "SESSION-abc"
        assert _normalize_gap_key("DOC-gap-003") == "DOC-gap"


class TestTrackGapResolutions:
    """Tests for track_gap_resolutions with loop closure."""

    def test_no_previous_gaps(self, tmp_path: Path, monkeypatch: Mock) -> None:
        """Test tracking when no previous gaps snapshot exists."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        current_gaps = [
            {"id": "TEST-001", "type": "test_gap", "message": "Missing test"},
            {"id": "DOC-001", "type": "doc_gap", "message": "Missing docs"},
        ]

        result = track_gap_resolutions(current_gaps, "test_target", "term_abc")

        assert result.resolved_count == 0
        assert result.new_count == 2
        assert result.persistent_count == 0
        assert result.verified_count == 0
        assert result.failed_count == 0
        assert result.credited_skill is None

    def test_resolved_gaps_credited_to_skill(self, tmp_path: Path, monkeypatch: Mock) -> None:
        """Test that resolved gaps are credited to the most recent skill."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        target = "test_target"
        terminal = "term_xyz"

        # Create previous gaps snapshot
        prev_path = _get_previous_gaps_path(target, terminal)
        prev_gaps = [
            {"id": "TEST-001", "type": "test_gap", "message": "Missing test"},
            {"id": "DOC-001", "type": "doc_gap", "message": "Missing docs"},
        ]
        _save_previous_gaps(prev_path, prev_gaps, terminal)

        # Simulate skill coverage log entry
        log_path = tmp_path / ".evidence" / "skill_coverage"
        log_path.mkdir(parents=True, exist_ok=True)
        coverage_file = log_path / f"{target}.jsonl"
        coverage_file.write_text('{"skill": "/critique", "timestamp": "2026-03-27T10:00:00"}\n')

        # Current gaps - TEST-001 is now absent (resolved)
        current_gaps = [{"id": "DOC-001", "type": "doc_gap", "message": "Missing docs"}]

        result = track_gap_resolutions(current_gaps, target, terminal)

        assert result.resolved_count == 1
        assert "TEST-001" in result.resolved_gap_ids
        assert result.new_count == 0
        assert result.credited_skill == "/critique"

        # Verify resolution record was written
        res_log = _get_resolution_log_path(target)
        assert res_log.exists()
        records = _read_resolution_log(res_log)
        assert len(records) == 1
        assert records[0].skill == "/critique"
        assert "TEST-001" in records[0].gap_ids_resolved

    def test_verification_integrated_in_result(self, tmp_path: Path, monkeypatch: Mock) -> None:
        """Test that track_gap_resolutions populates verified_count and failed_count."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        target = "integrated_verify"
        terminal = "term_int"

        # Pre-write a resolution record (from a prior run where gap was resolved)
        res_log = _get_resolution_log_path(target)
        res_log.parent.mkdir(parents=True, exist_ok=True)
        record = ResolutionRecord(
            skill="/critique",
            gap_ids_resolved=["OLD-001"],
            gap_types_resolved=["test_gap"],
            timestamp="2026-03-27T09:00:00",
            terminal_id=terminal,
        )
        _append_resolution_record(target, record)

        # Create previous gaps snapshot with OLD-001
        prev_path = _get_previous_gaps_path(target, terminal)
        prev_gaps = [{"id": "OLD-001", "type": "test_gap", "message": "Old gap"}]
        _save_previous_gaps(prev_path, prev_gaps, terminal)

        # Current gaps - OLD-001 still present (persistent, not resolved).
        # _verify_past_resolutions will see OLD-001 has a resolution record
        # but is still present -> marks it as FAILED (gap_reappeared).
        current_gaps = [{"id": "OLD-001", "type": "test_gap", "message": "Old gap"}]

        result = track_gap_resolutions(current_gaps, target, terminal)

        # OLD-001 was in prev and still in curr = persistent (not resolved)
        assert result.persistent_count == 1
        assert result.resolved_count == 0
        # OLD-001 had a resolution record but reappeared -> failed verification
        assert result.failed_count == 1
        assert result.verified_count == 0


class TestVerifyPastResolutions:
    """Tests for _verify_past_resolutions function."""

    def test_gap_stayed_absent_verified(self, tmp_path: Path, monkeypatch: Mock) -> None:
        """Test verification when a resolved gap stayed absent."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        target = "verify_target"
        terminal = "term_verify"

        # Write a resolution record
        res_log = _get_resolution_log_path(target)
        res_log.parent.mkdir(parents=True, exist_ok=True)
        record = ResolutionRecord(
            skill="/critique",
            gap_ids_resolved=["TEST-001"],
            gap_types_resolved=["test_gap"],
            timestamp="2026-03-27T10:00:00",
            terminal_id=terminal,
        )
        _append_resolution_record(target, record)

        # Current gaps - TEST-001 is NOT present (stayed absent = verified)
        current_gap_ids: set[str] = set()

        verified, failed = _verify_past_resolutions(target, current_gap_ids, terminal)

        assert verified == 1
        assert failed == 0

        # Verify verification record was written
        verif_log = _get_verification_log_path(target)
        assert verif_log.exists()
        verifs = _read_verification_log(verif_log)
        assert len(verifs) == 1
        assert verifs[0].status == "verified"
        assert verifs[0].reason == "gap_still_absent"

    def test_gap_reappeared_failed(self, tmp_path: Path, monkeypatch: Mock) -> None:
        """Test verification when a previously resolved gap reappeared (failed)."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        target = "verify_target_fail"
        terminal = "term_verify_fail"

        # Write a resolution record
        res_log = _get_resolution_log_path(target)
        res_log.parent.mkdir(parents=True, exist_ok=True)
        record = ResolutionRecord(
            skill="/critique",
            gap_ids_resolved=["TEST-001"],
            gap_types_resolved=["test_gap"],
            timestamp="2026-03-27T10:00:00",
            terminal_id=terminal,
        )
        _append_resolution_record(target, record)

        # Current gaps - TEST-001 IS present (reappeared = failed)
        current_gap_ids = {"TEST-001"}

        verified, failed = _verify_past_resolutions(target, current_gap_ids, terminal)

        assert verified == 0
        assert failed == 1

        # Verify verification record was written
        verif_log = _get_verification_log_path(target)
        verifs = _read_verification_log(verif_log)
        assert len(verifs) == 1
        assert verifs[0].status == "failed"
        assert verifs[0].reason == "gap_reappeared"

    def test_skips_already_verified(self, tmp_path: Path, monkeypatch: Mock) -> None:
        """Test that already-verified gaps are not re-verified."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        target = "skip_verify"
        terminal = "term_skip"

        # Write a resolution record
        res_log = _get_resolution_log_path(target)
        res_log.parent.mkdir(parents=True, exist_ok=True)
        record = ResolutionRecord(
            skill="/critique",
            gap_ids_resolved=["TEST-001"],
            gap_types_resolved=["test_gap"],
            timestamp="2026-03-27T10:00:00",
            terminal_id=terminal,
        )
        _append_resolution_record(target, record)

        # Pre-write a verification record (already verified)
        verif_log = _get_verification_log_path(target)
        verif_log.parent.mkdir(parents=True, exist_ok=True)
        prev_verif = ResolutionVerificationRecord(
            skill="/critique",
            gap_ids=["TEST-001"],
            gap_types=["test_gap"],
            resolution_timestamp="2026-03-27T10:00:00",
            verification_timestamp="2026-03-27T11:00:00",
            status="verified",
            reason="gap_still_absent",
            terminal_id=terminal,
        )
        _append_verification_record(target, prev_verif)

        # Gap stayed absent - but should NOT be re-verified
        current_gap_ids: set[str] = set()

        verified, failed = _verify_past_resolutions(target, current_gap_ids, terminal)

        assert verified == 0
        assert failed == 0


class TestGetSkillEffectivenessScore:
    """Tests for get_skill_effectiveness_score with demotion."""

    def test_no_history_returns_neutral(self, tmp_path: Path, monkeypatch: Mock) -> None:
        """Test that no history returns neutral 0.5 score."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        score = get_skill_effectiveness_score("nonexistent", "/critique", ["test_gap"])
        assert score == 0.5

    def test_failed_verification_demotes_score(self, tmp_path: Path, monkeypatch: Mock) -> None:
        """Test that failed verifications demote skill score below 0.5."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        target = "score_demote"
        terminal = "term_score"

        # Write a FAILED verification (gap reappeared after being credited as resolved).
        # No resolution record means no history boost — failure demotion drops score below 0.5.
        verif_log = _get_verification_log_path(target)
        verif_log.parent.mkdir(parents=True, exist_ok=True)
        failed_verif = ResolutionVerificationRecord(
            skill="/critique",
            gap_ids=["TEST-001"],
            gap_types=["test_gap"],
            resolution_timestamp="2026-03-27T10:00:00",
            verification_timestamp="2026-03-27T11:00:00",
            status="failed",
            reason="gap_reappeared",
            terminal_id=terminal,
        )
        _append_verification_record(target, failed_verif)

        score = get_skill_effectiveness_score(target, "/critique", ["test_gap"])

        # Score should be below 0.5 due to failure demotion (base=0 + 0 boost - 0.2 demotion = 0.0)
        assert score < 0.5
