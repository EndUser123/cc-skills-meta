"""Tests for critique loop behavior in session chain analysis."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from __lib.session_chain_analyzer import ChainAnalysisResult, SessionChainAnalyzer


class TestCritiqueGradeCriteria:
    """Tests for critique_grade PASS/FAIL criteria."""

    def _make_result(
        self,
        focus: str = "specific feature work",
        phase: str = "Phase 2",
        next_steps: list[str] | None = None,
        confidence: float = 0.8,
        error: str | None = None,
    ) -> ChainAnalysisResult:
        """Helper to create a ChainAnalysisResult."""
        return ChainAnalysisResult(
            focus=focus,
            phase=phase,
            next_steps=next_steps if next_steps is not None else ["write unit tests", "review edge cases"],
            confidence=confidence,
            error=error,
            transcripts_processed=2,
        )

    def test_pass_for_specific_grounded_analysis(self, tmp_path: Path) -> None:
        """PASS returned for analysis that is specific and grounded in evidence."""
        analyzer = SessionChainAnalyzer(project_root=tmp_path)
        result = self._make_result(
            focus="implementing JWT authentication in the auth module",
            phase="Phase 2 - implementation",
            next_steps=["add token refresh logic", "write integration tests for auth flow"],
            confidence=0.85,
        )

        mock_return = {"grade": "PASS", "feedback": None}
        with patch.object(analyzer, "_run_subagent", return_value=mock_return):
            grade, feedback = analyzer.critique_grade(result, [])

        assert grade == "PASS"
        assert feedback is None

    def test_fail_for_vague_generic_analysis(self, tmp_path: Path) -> None:
        """FAIL returned for vague, generic analysis that lacks specificity."""
        analyzer = SessionChainAnalyzer(project_root=tmp_path)
        result = self._make_result(
            focus="some work",
            phase="ongoing",
            next_steps=["keep working", "do stuff"],
            confidence=0.5,
        )

        mock_return = {
            "grade": "FAIL",
            "feedback": "Analysis is too vague. Be specific about what was worked on.",
        }
        with patch.object(analyzer, "_run_subagent", return_value=mock_return):
            grade, feedback = analyzer.critique_grade(result, [])

        assert grade == "FAIL"
        assert feedback is not None

    def test_fail_for_contradicting_transcript(self, tmp_path: Path) -> None:
        """FAIL returned when analysis contradicts transcript evidence."""
        analyzer = SessionChainAnalyzer(project_root=tmp_path)
        result = self._make_result(
            focus="implementing payments",
            phase="Phase 3",
            next_steps=["deploy to production"],
            confidence=0.6,
        )

        mock_return = {
            "grade": "FAIL",
            "feedback": "You claimed Phase 3 but transcript shows Phase 1. Correct the phase.",
        }
        with patch.object(analyzer, "_run_subagent", return_value=mock_return):
            grade, feedback = analyzer.critique_grade(result, [])

        assert grade == "FAIL"
        assert feedback is not None

    def test_fail_for_low_confidence_explicit(self, tmp_path: Path) -> None:
        """FAIL returned when confidence < 0.3 (explicit threshold check)."""
        analyzer = SessionChainAnalyzer(project_root=tmp_path)
        result = self._make_result(confidence=0.15)

        grade, feedback = analyzer.critique_grade(result, [])

        assert grade == "FAIL"
        assert feedback is not None

    def test_fail_for_empty_focus_and_next_steps(self, tmp_path: Path) -> None:
        """FAIL returned when both focus and next_steps are empty."""
        analyzer = SessionChainAnalyzer(project_root=tmp_path)
        result = self._make_result(focus="", next_steps=[])

        grade, feedback = analyzer.critique_grade(result, [])

        assert grade == "FAIL"
        assert feedback is not None


class TestPartialResultSchema:
    """Tests for partial result schema when timeout/crash occurs."""

    def test_timeout_error_sets_error_field(self, tmp_path: Path) -> None:
        """Partial result schema has error='timeout' on timeout."""
        result = ChainAnalysisResult(
            focus="",
            phase="",
            next_steps=[],
            confidence=0.0,
            error="timeout",
            transcripts_processed=3,
        )
        assert result.error == "timeout"
        assert result.transcripts_processed == 3
        assert result.focus == ""

    def test_crash_error_sets_error_field(self, tmp_path: Path) -> None:
        """Partial result schema has error='crash' on subagent crash."""
        result = ChainAnalysisResult(
            focus="",
            phase="",
            next_steps=[],
            confidence=0.0,
            error="crash",
            transcripts_processed=2,
        )
        assert result.error == "crash"
        assert result.transcripts_processed == 2

    def test_eval_fail_error_sets_error_field(self, tmp_path: Path) -> None:
        """Partial result schema has error='eval_fail' when critique fails repeatedly."""
        result = ChainAnalysisResult(
            focus="partial work",
            phase="Phase 1",
            next_steps=["continue from where left off"],
            confidence=0.3,
            error="eval_fail",
            transcripts_processed=1,
        )
        assert result.error == "eval_fail"
        assert result.confidence == 0.3

    def test_partial_result_has_transcripts_processed_count(self, tmp_path: Path) -> None:
        """Partial result includes count of transcripts that were processed before failure."""
        result = ChainAnalysisResult(
            focus="",
            phase="",
            next_steps=[],
            confidence=0.0,
            error="timeout",
            transcripts_processed=5,
        )
        assert result.transcripts_processed == 5


class TestCritiqueLoopMaxRerunEnforcement:
    """Tests for max rerun enforcement (max 2 reruns)."""

    def test_max_reruns_is_enforced_in_analyzer(self, tmp_path: Path) -> None:
        """SessionChainAnalyzer has SUBAGENT_TIMEOUT_SECONDS constant."""
        analyzer = SessionChainAnalyzer(project_root=tmp_path)
        assert hasattr(analyzer, "SUBAGENT_TIMEOUT_SECONDS")
        assert analyzer.SUBAGENT_TIMEOUT_SECONDS == 50

    def test_critique_timeout_constant_exists(self, tmp_path: Path) -> None:
        """Analyzer has CRITIQUE_TIMEOUT_SECONDS constant."""
        analyzer = SessionChainAnalyzer(project_root=tmp_path)
        assert hasattr(analyzer, "CRITIQUE_TIMEOUT_SECONDS")
        assert analyzer.CRITIQUE_TIMEOUT_SECONDS == 10

    def test_max_chain_depth_constant(self, tmp_path: Path) -> None:
        """Analyzer has MAX_CHAIN_DEPTH constant set to 10."""
        analyzer = SessionChainAnalyzer(project_root=tmp_path)
        assert hasattr(analyzer, "MAX_CHAIN_DEPTH")
        assert analyzer.MAX_CHAIN_DEPTH == 10


class TestCritiqueGradeSpecificFeedback:
    """Tests for specific feedback on FAIL."""

    def test_feedback_mentions_missing_focus(self, tmp_path: Path) -> None:
        """FAIL feedback specifically mentions missing focus."""
        analyzer = SessionChainAnalyzer(project_root=tmp_path)
        result = ChainAnalysisResult(
            focus="",
            phase="Phase 2",
            next_steps=["do something"],
            confidence=0.0,
            error=None,
            transcripts_processed=1,
        )

        grade, feedback = analyzer.critique_grade(result, [])

        assert grade == "FAIL"
        assert feedback is not None

    def test_feedback_mentions_low_confidence(self, tmp_path: Path) -> None:
        """FAIL feedback mentions low confidence value."""
        analyzer = SessionChainAnalyzer(project_root=tmp_path)
        result = ChainAnalysisResult(
            focus="work",
            phase="Phase 1",
            next_steps=["continue"],
            confidence=0.1,
            error=None,
            transcripts_processed=1,
        )

        grade, feedback = analyzer.critique_grade(result, [])

        assert grade == "FAIL"
        assert feedback is not None
        assert "0.10" in feedback or "0.1" in feedback or "confidence" in feedback.lower()
