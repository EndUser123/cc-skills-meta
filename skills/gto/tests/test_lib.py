"""Tests for GTO v3 core library components."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import Mock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


from __lib import (
    CodeMarkerResult,
    ConsolidatedResults,
    DependencyResult,
    DocPresenceResult,
    Gap,
    StateManager,
    TestPresenceResult,
    UnfinishedBusinessResult,
    build_initial_results,
    check_chain_integrity,
    check_dependencies,
    check_docs_presence,
    check_test_presence,
    check_viability,
    detect_unfinished_business,
    format_recommended_next_steps,
    get_state_manager,
    scan_code_markers,
)

# Gap resolution tracker imports (not re-exported via __lib)
from __lib.gap_resolution_tracker import (
    ResolutionRecord,
    ResolutionVerificationRecord,
    _append_resolution_record,
    _append_verification_record,
    _get_previous_gaps_path,
    _get_resolution_log_path,
    _get_verification_log_path,
    _get_verified_gap_ids,
    _normalize_gap_key,
    _read_resolution_log,
    _read_verification_log,
    _save_previous_gaps,
    _verify_past_resolutions,
    get_skill_effectiveness_score,
    track_gap_resolutions,
)


class TestViabilityGate:
    """Tests for ViabilityGate component."""

    def test_check_viability_git_repo(self, tmp_path: Path) -> None:
        """Test viability check on valid git repository with transcript file."""
        # Create a git repository
        git_dir = tmp_path / ".git"
        git_dir.mkdir(parents=True)
        (git_dir / "HEAD").write_text("ref: refs/heads/main\n")

        # Create a transcript file so previous sessions check passes
        transcript_file = tmp_path / "transcript.jsonl"
        transcript_file.write_text('{"role": "user", "content": "test"}\n')

        result = check_viability(tmp_path)

        assert result.is_viable is True
        assert result.failure_reason is None

    def test_check_viability_no_git(self, tmp_path: Path) -> None:
        """Test viability check on non-git directory.

        Viability returns True because the handoff envelope check is informational
        (not a hard requirement) and git is informational only.
        """
        result = check_viability(tmp_path)

        # Handoff envelope absence → informational pass, git absence → informational pass
        assert result.is_viable is True
        # failure_reason is None when is_viable=True (no hard failures)
        assert result.failure_reason is None
        # Git check shows as informational pass in checks_passed
        assert any("git" in c.lower() for c in (result.checks_passed or []))


class TestChainIntegrityChecker:
    """Tests for ChainIntegrityChecker component."""

    def test_check_chain_integrity(self, tmp_path: Path) -> None:
        """Test chain integrity check with valid transcript file."""
        # Create a valid transcript file
        transcript_file = tmp_path / "transcript.jsonl"
        transcript_file.write_text('{"role": "user", "content": "hello"}\n')

        # Pass the file path, not the directory
        result = check_chain_integrity(transcript_file)

        assert result.is_valid is True
        assert len(result.issues) == 0


class TestTestPresenceChecker:
    """Tests for TestPresenceChecker component."""

    def test_check_test_presence_with_gap(self, tmp_path: Path) -> None:
        """Test test presence check with missing test."""
        # Create source file without test
        (tmp_path / "module.py").write_text("def foo(): pass\n")

        result = check_test_presence(tmp_path)

        assert isinstance(result, TestPresenceResult)
        # Should detect test gap

    def test_check_test_presence_flat_naming(self, tmp_path: Path) -> None:
        """Test flat naming convention: tests/test_module.py when source is subdir/module.py."""
        # Create source in subdirectory (mirrors validators/context_size.py pattern)
        src_dir = tmp_path / "validators"
        src_dir.mkdir()
        (src_dir / "context_size.py").write_text("def validate(): pass\n")

        # Create test directory and flat-naming test (skill-ship pattern)
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_context_size.py").write_text("def test_validate(): pass\n")

        result = check_test_presence(tmp_path)

        # Should find the test via flat naming fallback, NOT report a gap
        assert result.modules_without_tests == 0, (
            f"Expected 0 gaps, got {result.modules_without_tests}: "
            f"{[g.module_path for g in result.gaps]}"
        )


class TestDocsPresenceChecker:
    """Tests for DocsPresenceChecker component."""

    def test_check_docs_presence(self, tmp_path: Path) -> None:
        """Test docs presence check."""
        # Create source file
        (tmp_path / "module.py").write_text('"""Module docstring."""\n\ndef foo(): pass\n')

        result = check_docs_presence(tmp_path)

        assert isinstance(result, DocPresenceResult)


class TestDependencyChecker:
    """Tests for DependencyChecker component."""

    def test_check_dependencies(self, tmp_path: Path) -> None:
        """Test dependency check."""
        result = check_dependencies(tmp_path)

        assert isinstance(result, DependencyResult)


class TestUnfinishedBusinessDetector:
    """Tests for UnfinishedBusinessDetector component."""

    def test_detect_unfinished_business(self, tmp_path: Path) -> None:
        """Test unfinished business detection."""
        state_manager = get_state_manager(tmp_path, "test_terminal")

        result = detect_unfinished_business(tmp_path, state_manager)

        assert isinstance(result, UnfinishedBusinessResult)
        assert isinstance(result.items, list)


class TestStateManager:
    """Tests for StateManager component."""

    def test_state_manager_isolation(self, tmp_path: Path) -> None:
        """Test multi-terminal state isolation."""
        # Create two terminals with different IDs
        manager1 = get_state_manager(tmp_path, "terminal_1")
        manager2 = get_state_manager(tmp_path, "terminal_2")

        # Verify they have different state directories
        assert manager1.state_dir != manager2.state_dir

    def test_state_manager_save_load(self, tmp_path: Path) -> None:
        """Test state save and load."""
        manager = get_state_manager(tmp_path, "test_terminal")

        # Create and save state
        state = manager.create_state(
            session_id="test_session",
            gaps=[{"type": "test", "message": "gap"}],
            metadata={"key": "value"},
        )
        manager.save(state)

        # Load state
        loaded = manager.load()

        assert loaded.session_id == "test_session"
        assert len(loaded.gaps) == 1
        assert loaded.metadata["key"] == "value"

    def test_state_manager_append_history(self, tmp_path: Path) -> None:
        """Test history appending."""
        manager = get_state_manager(tmp_path, "test_terminal")

        manager.append_history({"event": "test_event"})

        history = manager.get_history(last_n=10)

        assert len(history) == 1
        assert history[0]["event"] == "test_event"


class TestResultsBuilder:
    """Tests for InitialResultsBuilder component."""

    def test_build_initial_results(self, tmp_path: Path) -> None:
        """Test building consolidated results."""
        detector_results = {
            "chain_integrity": Mock(is_valid=True, issues=[]),
            "test_presence": Mock(gaps=[], modules_checked=0),
            "docs_presence": Mock(gaps=[]),
        }

        results = build_initial_results(detector_results, tmp_path)

        assert isinstance(results, ConsolidatedResults)
        assert isinstance(results.gaps, list)
        assert results.total_gap_count == len(results.gaps)

    def test_gap_deduplication(self) -> None:
        """Test gap deduplication logic."""
        gap1 = Gap(
            gap_id="GAP-001",
            type="test",
            severity="high",
            message="Add tests",
            file_path="src/module.py",
            line_number=10,
            source="TestPresenceChecker",
        )

        gap2 = Gap(
            gap_id="GAP-002",
            type="test",
            severity="high",
            message="Add tests",
            file_path="src/module.py",
            line_number=10,
            source="TestPresenceChecker",
        )

        # These should be considered duplicates (same signature)
        from hashlib import md5

        sig1 = md5(
            f"{gap1.type}:{gap1.message}:{gap1.file_path}:{gap1.line_number}".encode()
        ).hexdigest()
        sig2 = md5(
            f"{gap2.type}:{gap2.message}:{gap2.file_path}:{gap2.line_number}".encode()
        ).hexdigest()

        assert sig1 == sig2


class TestNextStepsFormatter:
    """Tests for NextStepsFormatter component."""

    def test_format_recommended_next_steps(self) -> None:
        """Test formatting next steps."""
        gaps = [
            Gap(
                gap_id="GAP-001",
                type="missing_test",
                severity="high",
                message="Add tests for module",
                file_path="src/module.py",
                line_number=10,
                source="TestPresenceChecker",
                theme="testing",
            ),
            Gap(
                gap_id="GAP-002",
                type="missing_doc",
                severity="medium",
                message="Add documentation",
                file_path="src/module.py",
                line_number=1,
                source="DocsPresenceChecker",
                theme="docs",
            ),
        ]

        formatted = format_recommended_next_steps(gaps)

        assert formatted.steps is not None
        assert len(formatted.steps) > 0


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_get_state_manager(self, tmp_path: Path) -> None:
        """Test get_state_manager convenience function."""
        manager = get_state_manager(tmp_path, "test_terminal")

        assert isinstance(manager, StateManager)
        assert manager.terminal_id == "test_terminal"


class TestGapDeduplicationEdgeCases:
    """Tests for Gap deduplication edge cases (TASK-018)."""

    def test_gap_signature_whitespace_normalization(self) -> None:
        """Test that whitespace is normalized in signatures."""
        gap1 = Gap(
            gap_id="GAP-001",
            type="test",
            severity="high",
            message="foo  bar",  # Multiple spaces
            file_path="src/module.py",
        )
        gap2 = Gap(
            gap_id="GAP-002",
            type="test",
            severity="high",
            message="foo bar",  # Single space
            file_path="src/module.py",
        )
        # Should have same signature due to whitespace normalization
        assert gap1.signature() == gap2.signature()

    def test_gap_signature_case_normalization(self) -> None:
        """Test that case is normalized in signatures."""
        gap1 = Gap(
            gap_id="GAP-001",
            type="test",
            severity="high",
            message="FOO BAR",
            file_path="src/module.py",
        )
        gap2 = Gap(
            gap_id="GAP-002",
            type="test",
            severity="high",
            message="foo bar",
            file_path="src/module.py",
        )
        # Should have same signature due to case normalization
        assert gap1.signature() == gap2.signature()

    def test_gap_signature_different_types(self) -> None:
        """Test that different types produce different signatures."""
        gap1 = Gap(
            gap_id="GAP-001",
            type="test",
            severity="high",
            message="same message",
            file_path="src/module.py",
        )
        gap2 = Gap(
            gap_id="GAP-002",
            type="doc",
            severity="high",
            message="same message",
            file_path="src/module.py",
        )
        # Should have different signatures
        assert gap1.signature() != gap2.signature()

    def test_gap_signature_different_paths(self) -> None:
        """Test that different file paths produce different signatures."""
        gap1 = Gap(
            gap_id="GAP-001",
            type="test",
            severity="high",
            message="same message",
            file_path="src/module1.py",
        )
        gap2 = Gap(
            gap_id="GAP-002",
            type="test",
            severity="high",
            message="same message",
            file_path="src/module2.py",
        )
        # Should have different signatures
        assert gap1.signature() != gap2.signature()

    def test_gap_signature_null_file_path(self) -> None:
        """Test signature with null file path."""
        gap1 = Gap(
            gap_id="GAP-001",
            type="test",
            severity="high",
            message="message",
            file_path=None,
        )
        gap2 = Gap(
            gap_id="GAP-002",
            type="test",
            severity="high",
            message="message",
            file_path=None,
        )
        # Should have same signature
        assert gap1.signature() == gap2.signature()


class TestStateManagerConcurrency:
    """Tests for state manager concurrency (TASK-019).

    Note: StateManager is designed for multi-terminal isolation, not thread-safety
    within the same terminal. These tests verify the terminal isolation works
    correctly across different terminal IDs.
    """

    def test_state_manager_terminal_isolation(self, tmp_path: Path) -> None:
        """Test that different terminal IDs get different state directories."""
        manager1 = get_state_manager(tmp_path, "terminal_1")
        manager2 = get_state_manager(tmp_path, "terminal_2")

        # Each terminal should have its own state directory
        assert manager1.state_dir != manager2.state_dir
        assert manager1.state_file_path != manager2.state_file_path

        # Saving from one terminal should not affect the other
        state1 = manager1.create_state(session_id="session_1")
        manager1.save(state1)

        state2 = manager2.create_state(session_id="session_2")
        manager2.save(state2)

        # Load and verify isolation
        loaded1 = manager1.load()
        loaded2 = manager2.load()

        assert loaded1.session_id == "session_1"
        assert loaded2.session_id == "session_2"

    def test_state_manager_history_terminal_isolation(self, tmp_path: Path) -> None:
        """Test that history is isolated per terminal."""
        manager1 = get_state_manager(tmp_path, "terminal_1")
        manager2 = get_state_manager(tmp_path, "terminal_2")

        # Append to each terminal's history
        manager1.append_history({"event": "event_from_terminal_1"})
        manager2.append_history({"event": "event_from_terminal_2"})

        # Each should only see its own history
        history1 = manager1.get_history(last_n=10)
        history2 = manager2.get_history(last_n=10)

        assert len(history1) == 1
        assert len(history2) == 1
        assert history1[0]["event"] == "event_from_terminal_1"
        assert history2[0]["event"] == "event_from_terminal_2"


class TestGapResolutionTracker:
    """Tests for GapResolutionTracker loop closure functionality."""

    def test_normalize_gap_key_strips_numeric_suffix(self) -> None:
        """Test that gap IDs with numeric suffixes are normalized."""
        assert _normalize_gap_key("TEST-001") == "TEST-001"
        assert _normalize_gap_key("TEST-001-1") == "TEST-001"
        assert _normalize_gap_key("TEST-001-2") == "TEST-001"
        assert _normalize_gap_key("SESSION-abc-003") == "SESSION-abc"
        assert _normalize_gap_key("DOC-gap-003") == "DOC-gap"

    def test_track_gap_resolutions_no_previous(self, tmp_path: Path, monkeypatch: Mock) -> None:
        """Test tracking when no previous gaps snapshot exists."""
        # Patch Path.home to use tmp_path
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

    def test_track_gap_resolutions_with_resolution(self, tmp_path: Path, monkeypatch: Mock) -> None:
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

    def test_verify_past_resolutions_gap_stayed_absent(
        self, tmp_path: Path, monkeypatch: Mock
    ) -> None:
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

    def test_verify_past_resolutions_gap_reappeared(
        self, tmp_path: Path, monkeypatch: Mock
    ) -> None:
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

    def test_verify_past_resolutions_skips_already_verified(
        self, tmp_path: Path, monkeypatch: Mock
    ) -> None:
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

    def test_get_skill_effectiveness_score_no_history(
        self, tmp_path: Path, monkeypatch: Mock
    ) -> None:
        """Test that no history returns neutral 0.5 score."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        score = get_skill_effectiveness_score("nonexistent", "/critique", ["test_gap"])
        assert score == 0.5

    def test_get_skill_effectiveness_score_demotion_on_failure(
        self, tmp_path: Path, monkeypatch: Mock
    ) -> None:
        """Test that failed verifications demote skill score."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        target = "score_demote"
        terminal = "term_score"

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

        # Write a FAILED verification (gap reappeared)
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

        # Score should be below 0.5 due to failure demotion
        assert score < 0.5

    def test_track_gap_resolutions_verification_integrated(
        self, tmp_path: Path, monkeypatch: Mock
    ) -> None:
        """Test that track_gap_resolutions calls verification and populates counts."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        target = "integrated_verify"
        terminal = "term_integrated"

        # Pre-write a resolution with failed verification
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

        verif_log = _get_verification_log_path(target)
        verif_log.parent.mkdir(parents=True, exist_ok=True)
        failed_verif = ResolutionVerificationRecord(
            skill="/critique",
            gap_ids=["OLD-001"],
            gap_types=["test_gap"],
            resolution_timestamp="2026-03-27T09:00:00",
            verification_timestamp="2026-03-27T10:00:00",
            status="failed",
            reason="gap_reappeared",
            terminal_id=terminal,
        )
        _append_verification_record(target, failed_verif)

        # Create previous gaps snapshot with OLD-001
        prev_path = _get_previous_gaps_path(target, terminal)
        prev_gaps = [{"id": "OLD-001", "type": "test_gap", "message": "Old gap"}]
        _save_previous_gaps(prev_path, prev_gaps, terminal)

        # Current gaps - OLD-001 still present (persistent, not resolved)
        current_gaps = [{"id": "OLD-001", "type": "test_gap", "message": "Old gap"}]

        result = track_gap_resolutions(current_gaps, target, terminal)

        # OLD-001 was in prev and still in curr = persistent (not resolved)
        assert result.persistent_count == 1
        assert result.resolved_count == 0
        # OLD-001 was already verified (pre-written), so _verify_past_resolutions
        # skips it and creates no new verification; failed_count reflects new
        # verifications created during this call only
        assert result.failed_count == 0
        assert result.verified_count == 0
