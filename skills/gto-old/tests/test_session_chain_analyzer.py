"""Tests for SessionChainAnalyzer and analyze_session_chain function."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from __lib.session_chain_analyzer import (
    ChainAnalysisResult,
    SessionChainAnalyzer,
    analyze_session_chain,
)


@dataclass
class MockChainWalkResult:
    """Minimal mock of ChainWalkResult for testing."""

    entries: list


class TestChainAnalysisResult:
    """Tests for ChainAnalysisResult dataclass."""

    def test_dataclass_fields(self) -> None:
        """Test all dataclass fields are present and correct."""
        result = ChainAnalysisResult(
            focus="implementing auth",
            phase="Phase 2",
            next_steps=["add tests", "write docs"],
            confidence=0.85,
            error=None,
            transcripts_processed=3,
        )
        assert result.focus == "implementing auth"
        assert result.phase == "Phase 2"
        assert result.next_steps == ["add tests", "write docs"]
        assert result.confidence == 0.85
        assert result.error is None
        assert result.transcripts_processed == 3

    def test_dataclass_defaults(self) -> None:
        """Test default values for optional fields."""
        result = ChainAnalysisResult(
            focus="",
            phase="",
            next_steps=[],
            confidence=0.0,
        )
        assert result.error is None
        assert result.transcripts_processed == 0

    def test_dataclass_error_set(self) -> None:
        """Test error field can be set to a string."""
        result = ChainAnalysisResult(
            focus="",
            phase="",
            next_steps=[],
            confidence=0.0,
            error="timeout",
            transcripts_processed=2,
        )
        assert result.error == "timeout"


class TestAnalyzeSessionChainEmptyPaths:
    """Tests for analyze_session_chain with empty/invalid paths."""

    def test_empty_paths_returns_error_result(self) -> None:
        """Empty paths list returns error result with no_transcripts error."""
        result = analyze_session_chain([])

        assert result.focus == ""
        assert result.phase == ""
        assert result.next_steps == []
        assert result.confidence == 0.0
        assert result.error == "no_transcripts"
        assert result.transcripts_processed == 0

    def test_empty_paths_via_analyzer_method(self) -> None:
        """Analyzer.analyze with empty paths returns error result."""
        analyzer = SessionChainAnalyzer()
        result = analyzer.analyze([])

        assert result.error == "no_transcripts"
        assert result.transcripts_processed == 0


class TestAnalyzeSessionChainInvalidPaths:
    """Tests for analyze_session_chain with invalid paths."""

    def test_invalid_path_returns_error_result(self, tmp_path: Path) -> None:
        """Invalid paths return error result with invalid_paths error."""
        invalid_path = tmp_path / "nonexistent.jsonl"
        analyzer = SessionChainAnalyzer(project_root=tmp_path)

        with patch.object(analyzer, "_validate_paths", return_value=[]):
            result = analyzer.analyze([invalid_path])

        assert result.focus == ""
        assert result.phase == ""
        assert result.next_steps == []
        assert result.confidence == 0.0
        assert result.error == "invalid_paths"
        assert result.transcripts_processed == 0


class TestCritiqueGrade:
    """Tests for critique_grade method."""

    def _make_result(
        self,
        focus: str = "implementing feature X",
        phase: str = "Phase 2",
        next_steps: list[str] | None = None,
        confidence: float = 0.85,
        error: str | None = None,
    ) -> ChainAnalysisResult:
        """Helper to create a ChainAnalysisResult."""
        return ChainAnalysisResult(
            focus=focus,
            phase=phase,
            next_steps=next_steps or ["step 1", "step 2"],
            confidence=confidence,
            error=error,
            transcripts_processed=2,
        )

    def test_pass_for_valid_analysis(self, tmp_path: Path) -> None:
        """PASS returned for specific, grounded analysis with sufficient confidence."""
        analyzer = SessionChainAnalyzer(project_root=tmp_path)
        result = self._make_result(
            focus="implementing auth module",
            phase="Phase 2 - implementation",
            next_steps=["add tests", "write integration tests"],
            confidence=0.8,
        )

        with patch.object(
            analyzer,
            "_run_subagent",
            return_value={"grade": "PASS", "feedback": None},
        ):
            grade, feedback = analyzer.critique_grade(result, [])

        assert grade == "PASS"
        assert feedback is None

    def test_fail_for_error_in_result(self, tmp_path: Path) -> None:
        """FAIL returned when result has an error field set."""
        analyzer = SessionChainAnalyzer(project_root=tmp_path)
        result = self._make_result(error="timeout")

        grade, feedback = analyzer.critique_grade(result, [])

        assert grade == "FAIL"
        assert feedback is not None
        assert "timeout" in feedback

    def test_fail_for_empty_analysis(self, tmp_path: Path) -> None:
        """FAIL returned for empty/vague analysis with no focus or next_steps."""
        analyzer = SessionChainAnalyzer(project_root=tmp_path)
        result = self._make_result(focus="", next_steps=[])

        with patch.object(
            analyzer,
            "_run_subagent",
            return_value={"grade": "FAIL", "feedback": "Analysis is empty."},
        ):
            grade, feedback = analyzer.critique_grade(result, [])

        assert grade == "FAIL"
        assert feedback is not None

    def test_fail_for_low_confidence(self, tmp_path: Path) -> None:
        """FAIL returned when confidence is below 0.3 threshold."""
        analyzer = SessionChainAnalyzer(project_root=tmp_path)
        result = self._make_result(confidence=0.2)

        grade, feedback = analyzer.critique_grade(result, [])

        assert grade == "FAIL"
        assert feedback is not None

    def test_pass_for_high_confidence_on_critique_failure(self, tmp_path: Path) -> None:
        """PASS returned by default when critique agent itself fails."""
        analyzer = SessionChainAnalyzer(project_root=tmp_path)
        result = self._make_result(confidence=0.8)

        with patch.object(analyzer, "_run_subagent", side_effect=RuntimeError("boom")):
            grade, feedback = analyzer.critique_grade(result, [])

        assert grade == "PASS"
        assert feedback is None


class TestAnalyzeSessionChainSubagent:
    """Tests for subagent invocation (mocked)."""

    def test_analyze_calls_subagent_with_prompt(self, tmp_path: Path) -> None:
        """Analysis runs subagent and parses structured output."""
        analyzer = SessionChainAnalyzer(project_root=tmp_path)

        mock_result = {
            "focus": "feature development",
            "phase": "Phase 2",
            "next_steps": ["write tests", "review PR"],
            "confidence": 0.75,
        }

        transcript_path = tmp_path / "transcript.jsonl"
        with patch.object(analyzer, "_validate_paths", return_value=[transcript_path]):
            with patch.object(analyzer, "_run_subagent", return_value=mock_result):
                result = analyzer.analyze([transcript_path])

        assert result.focus == "feature development"
        assert result.phase == "Phase 2"
        assert result.next_steps == ["write tests", "review PR"]
        assert result.confidence == 0.75
        assert result.error is None
        assert result.transcripts_processed == 1

    def test_analyze_timeout_returns_partial_result(self, tmp_path: Path) -> None:
        """Timeout returns partial result with error=timeout and transcripts_processed."""
        analyzer = SessionChainAnalyzer(project_root=tmp_path)

        with patch.object(
            analyzer, "_validate_paths", return_value=[tmp_path / "a.jsonl", tmp_path / "b.jsonl"]
        ):
            with patch.object(analyzer, "_run_subagent", side_effect=TimeoutError("timed out")):
                result = analyzer.analyze([tmp_path / "a.jsonl", tmp_path / "b.jsonl"])

        assert result.focus == ""
        assert result.phase == ""
        assert result.next_steps == []
        assert result.confidence == 0.0
        assert result.error == "timeout"
        assert result.transcripts_processed == 2

    def test_analyze_crash_returns_partial_result(self, tmp_path: Path) -> None:
        """Subagent crash returns partial result with error=crash."""
        analyzer = SessionChainAnalyzer(project_root=tmp_path)

        with patch.object(analyzer, "_validate_paths", return_value=[tmp_path / "a.jsonl"]):
            with patch.object(analyzer, "_run_subagent", side_effect=RuntimeError("segfault")):
                result = analyzer.analyze([tmp_path / "a.jsonl"])

        assert result.error == "crash"
        assert result.transcripts_processed == 1


class TestAnalyzeChainResult:
    """Tests for analyze_chain_result method (ChainWalkResult-based)."""

    def test_analyze_chain_result_empty_entries(self, tmp_path: Path) -> None:
        """Empty entries return error result with no_transcripts."""
        analyzer = SessionChainAnalyzer(project_root=tmp_path)
        mock_result = MockChainWalkResult(entries=[])

        result = analyzer.analyze_chain_result(mock_result)

        assert result.focus == ""
        assert result.phase == ""
        assert result.next_steps == []
        assert result.confidence == 0.0
        assert result.error == "no_transcripts"
        assert result.transcripts_processed == 0

    def test_analyze_chain_result_calls_subagent(self, tmp_path: Path) -> None:
        """analyze_chain_result runs subagent and parses structured output."""
        analyzer = SessionChainAnalyzer(project_root=tmp_path)

        mock_chain = MockChainWalkResult(
            entries=[
                {
                    "type": "summary",
                    "sessionId": "abc123",
                    "summary": "User worked on auth",
                    "message": None,
                    "is_origin": False,
                },
                {
                    "type": "message",
                    "sessionId": "def456",
                    "summary": None,
                    "message": "Hello",
                    "is_origin": True,
                },
            ]
        )

        subagent_result = {
            "focus": "authentication feature",
            "phase": "Phase 2 - implementation",
            "next_steps": ["write tests", "review PR"],
            "confidence": 0.8,
        }

        with patch.object(analyzer, "_run_subagent", return_value=subagent_result):
            result = analyzer.analyze_chain_result(mock_chain, query="what was worked on?")

        assert result.focus == "authentication feature"
        assert result.phase == "Phase 2 - implementation"
        assert result.next_steps == ["write tests", "review PR"]
        assert result.confidence == 0.8
        assert result.error is None
        assert result.transcripts_processed == 2

    def test_analyze_chain_result_timeout(self, tmp_path: Path) -> None:
        """Timeout returns partial result with error=timeout."""
        analyzer = SessionChainAnalyzer(project_root=tmp_path)
        mock_chain = MockChainWalkResult(
            entries=[{"type": "msg", "sessionId": "x", "message": "hi"}]
        )

        with patch.object(analyzer, "_run_subagent", side_effect=TimeoutError):
            result = analyzer.analyze_chain_result(mock_chain)

        assert result.error == "timeout"
        assert result.transcripts_processed == 1

    def test_analyze_chain_result_crash(self, tmp_path: Path) -> None:
        """Subagent crash returns partial result with error=crash."""
        analyzer = SessionChainAnalyzer(project_root=tmp_path)
        mock_chain = MockChainWalkResult(
            entries=[{"type": "msg", "sessionId": "x", "message": "hi"}]
        )

        with patch.object(analyzer, "_run_subagent", side_effect=RuntimeError("boom")):
            result = analyzer.analyze_chain_result(mock_chain)

        assert result.error == "crash"
        assert result.transcripts_processed == 1


class TestCritiqueGradeChainResult:
    """Tests for critique_grade_chain_result method."""

    def _make_analysis(
        self,
        focus: str = "auth feature",
        phase: str = "Phase 2",
        next_steps: list[str] | None = None,
        confidence: float = 0.8,
        error: str | None = None,
    ) -> ChainAnalysisResult:
        return ChainAnalysisResult(
            focus=focus,
            phase=phase,
            next_steps=next_steps or ["step 1"],
            confidence=confidence,
            error=error,
            transcripts_processed=2,
        )

    def test_pass_for_valid_analysis(self, tmp_path: Path) -> None:
        """PASS returned for specific analysis with sufficient confidence."""
        analyzer = SessionChainAnalyzer(project_root=tmp_path)
        chain = MockChainWalkResult(
            entries=[
                {
                    "type": "summary",
                    "sessionId": "abc",
                    "summary": "work",
                    "message": None,
                    "is_origin": False,
                },
            ]
        )
        result = self._make_analysis(focus="auth module", phase="Phase 2", confidence=0.85)

        with patch.object(
            analyzer,
            "_run_subagent",
            return_value={"grade": "PASS", "feedback": None},
        ):
            grade, feedback = analyzer.critique_grade_chain_result(result, chain)

        assert grade == "PASS"
        assert feedback is None

    def test_fail_for_error_in_result(self, tmp_path: Path) -> None:
        """FAIL returned when result has an error field."""
        analyzer = SessionChainAnalyzer(project_root=tmp_path)
        chain = MockChainWalkResult(entries=[])
        result = self._make_analysis(error="timeout")

        grade, feedback = analyzer.critique_grade_chain_result(result, chain)

        assert grade == "FAIL"
        assert feedback is not None
        assert "timeout" in feedback

    def test_fail_for_empty_analysis(self, tmp_path: Path) -> None:
        """FAIL returned for empty analysis with no focus or next_steps."""
        analyzer = SessionChainAnalyzer(project_root=tmp_path)
        chain = MockChainWalkResult(entries=[])
        result = self._make_analysis(focus="", next_steps=[])

        with patch.object(
            analyzer,
            "_run_subagent",
            return_value={"grade": "FAIL", "feedback": "Analysis is empty."},
        ):
            grade = analyzer.critique_grade_chain_result(result, chain)[0]

        assert grade == "FAIL"

    def test_fail_for_low_confidence(self, tmp_path: Path) -> None:
        """FAIL returned when confidence is below 0.3 threshold."""
        analyzer = SessionChainAnalyzer(project_root=tmp_path)
        chain = MockChainWalkResult(entries=[])
        result = self._make_analysis(confidence=0.2)

        grade, _feedback = analyzer.critique_grade_chain_result(result, chain)

        assert grade == "FAIL"
        assert _feedback is not None

    def test_pass_on_critique_failure(self, tmp_path: Path) -> None:
        """PASS returned when critique agent itself fails."""
        analyzer = SessionChainAnalyzer(project_root=tmp_path)
        chain = MockChainWalkResult(entries=[])
        result = self._make_analysis(confidence=0.8)

        with patch.object(analyzer, "_run_subagent", side_effect=RuntimeError("boom")):
            grade, feedback = analyzer.critique_grade_chain_result(result, chain)

        assert grade == "PASS"
        assert feedback is None


class TestSessionChainAnalyzerInstantiation:
    """Smoke tests for SessionChainAnalyzer."""

    def test_instantiation_default_root(self) -> None:
        """Analyzer instantiates with default project_root."""
        analyzer = SessionChainAnalyzer()
        assert analyzer is not None
        assert analyzer.project_root == Path.cwd()

    def test_instantiation_custom_root(self, tmp_path: Path) -> None:
        """Analyzer instantiates with custom project_root."""
        analyzer = SessionChainAnalyzer(project_root=tmp_path)
        assert analyzer.project_root == tmp_path
