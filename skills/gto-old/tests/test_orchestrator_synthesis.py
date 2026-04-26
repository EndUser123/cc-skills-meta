"""Tests for GTO orchestrator two-stage synthesis integration."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from gto_orchestrator import GTOOrchestrator, OrchestratorConfig


class TestDetectQuestionStyleFromTranscript:
    """Tests for _detect_question_style_from_transcript method."""

    def _write_transcript_with_messages(
        self, path: Path, messages: list[dict[str, str]]
    ) -> None:
        """Write a transcript JSONL file with given messages."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            for msg in messages:
                f.write(json.dumps(msg) + "\n")

    def test_question_pattern_returns_true(self, tmp_path: Path) -> None:
        """Question patterns return True from _detect_question_style_from_transcript."""
        transcript = tmp_path / "transcript.jsonl"
        self._write_transcript_with_messages(transcript, [
            {"role": "user", "content": "let's implement the feature"},
            {"role": "assistant", "content": "Sure, I'll help with that."},
            {"role": "user", "content": "what are we doing?"},
        ])

        orchestrator = GTOOrchestrator(config=OrchestratorConfig(project_root=tmp_path))
        is_question, message = orchestrator._detect_question_style_from_transcript(transcript)

        assert is_question is True
        assert message is not None
        assert "what are we doing" in message.lower()

    def test_status_question_returns_true(self, tmp_path: Path) -> None:
        """what's the status pattern returns True."""
        transcript = tmp_path / "transcript.jsonl"
        self._write_transcript_with_messages(transcript, [
            {"role": "user", "content": "what's the status?"},
        ])

        orchestrator = GTOOrchestrator(config=OrchestratorConfig(project_root=tmp_path))
        is_question, message = orchestrator._detect_question_style_from_transcript(transcript)

        assert is_question is True

    def test_whats_needed_next_returns_true(self, tmp_path: Path) -> None:
        """what's needed next pattern returns True."""
        transcript = tmp_path / "transcript.jsonl"
        self._write_transcript_with_messages(transcript, [
            {"role": "user", "content": "what's needed next?"},
        ])

        orchestrator = GTOOrchestrator(config=OrchestratorConfig(project_root=tmp_path))
        is_question, message = orchestrator._detect_question_style_from_transcript(transcript)

        assert is_question is True

    def test_non_question_returns_false(self, tmp_path: Path) -> None:
        """Non-question statements return False."""
        transcript = tmp_path / "transcript.jsonl"
        self._write_transcript_with_messages(transcript, [
            {"role": "user", "content": "let's build the auth module"},
            {"role": "assistant", "content": "I'll start working on that."},
        ])

        orchestrator = GTOOrchestrator(config=OrchestratorConfig(project_root=tmp_path))
        is_question, message = orchestrator._detect_question_style_from_transcript(transcript)

        assert is_question is False

    def test_imperative_statement_returns_false(self, tmp_path: Path) -> None:
        """Imperative statements return False."""
        transcript = tmp_path / "transcript.jsonl"
        self._write_transcript_with_messages(transcript, [
            {"role": "user", "content": "I need to fix the bug in the parser"},
        ])

        orchestrator = GTOOrchestrator(config=OrchestratorConfig(project_root=tmp_path))
        is_question, message = orchestrator._detect_question_style_from_transcript(transcript)

        assert is_question is False

    def test_empty_transcript_returns_false(self, tmp_path: Path) -> None:
        """Empty transcript returns False with None message."""
        transcript = tmp_path / "empty.jsonl"
        transcript.parent.mkdir(parents=True, exist_ok=True)
        transcript.write_text("", encoding="utf-8")

        orchestrator = GTOOrchestrator(config=OrchestratorConfig(project_root=tmp_path))
        is_question, message = orchestrator._detect_question_style_from_transcript(transcript)

        assert is_question is False
        assert message is None

    def test_missing_transcript_file_returns_false(self, tmp_path: Path) -> None:
        """Missing transcript file returns False."""
        orchestrator = GTOOrchestrator(config=OrchestratorConfig(project_root=tmp_path))
        is_question, message = orchestrator._detect_question_style_from_transcript(
            tmp_path / "nonexistent.jsonl"
        )

        assert is_question is False
        assert message is None


class TestFormatOutputWithChainAnalysis:
    """Tests for format_output with chain_analysis metadata."""

    def _make_result(
        self,
        chain_analysis: dict | None = None,
        session_goal: dict | None = None,
    ) -> MagicMock:
        """Helper to create a mock OrchestratorResult with metadata."""
        from gto_orchestrator import OrchestratorResult

        result = MagicMock(spec=OrchestratorResult)
        result.success = True
        result.error = None
        result.results = MagicMock()
        result.results.total_gap_count = 5
        result.metadata = {
            "project_root": str(tmp_path := Path("/tmp/project")),
            "timestamp": "2026-03-30T12:00:00Z",
        }
        if session_goal:
            result.metadata["session_goal"] = session_goal
        if chain_analysis:
            result.metadata["chain_analysis"] = chain_analysis
        result.health_report = None
        return result

    def test_format_output_renders_session_context_section(
        self, tmp_path: Path
    ) -> None:
        """format_output with chain_analysis renders Session Context section."""
        orchestrator = GTOOrchestrator(config=OrchestratorConfig(project_root=tmp_path))

        chain_meta = {
            "focus": "implementing authentication",
            "phase": "Phase 2 - auth module",
            "next_steps": ["add OAuth support", "write tests"],
            "confidence": 0.8,
            "error": None,
            "transcripts_processed": 3,
        }

        mock_result = self._make_result(chain_analysis=chain_meta)

        with patch.object(orchestrator, "_detect_question_style_from_transcript", return_value=(False, None)):
            output = orchestrator.format_output(mock_result, user_query="what are we doing?")

        assert "## Session Context" in output
        assert "implementing authentication" in output
        assert "Phase 2 - auth module" in output
        assert "add OAuth support" in output
        assert "confidence: 80%" in output

    def test_format_output_with_error_renders_confidence_note(
        self, tmp_path: Path
    ) -> None:
        """format_output with error in chain_analysis renders confidence note."""
        orchestrator = GTOOrchestrator(config=OrchestratorConfig(project_root=tmp_path))

        chain_meta = {
            "focus": "",
            "phase": "",
            "next_steps": [],
            "confidence": 0.0,
            "error": "timeout",
            "transcripts_processed": 2,
        }

        mock_result = self._make_result(chain_analysis=chain_meta)

        with patch.object(orchestrator, "_detect_question_style_from_transcript", return_value=(False, None)):
            output = orchestrator.format_output(mock_result, user_query="what's the status?")

        assert "## Session Context" in output
        assert "analysis degraded: timeout" in output
        assert "confidence: 0%" in output

    def test_format_output_renders_next_steps_list(
        self, tmp_path: Path
    ) -> None:
        """format_output renders next_steps as bullet list."""
        orchestrator = GTOOrchestrator(config=OrchestratorConfig(project_root=tmp_path))

        chain_meta = {
            "focus": "refactoring API layer",
            "phase": "Phase 3",
            "next_steps": ["extract helper functions", "add type hints", "run tests"],
            "confidence": 0.9,
            "error": None,
            "transcripts_processed": 4,
        }

        mock_result = self._make_result(chain_analysis=chain_meta)

        with patch.object(orchestrator, "_detect_question_style_from_transcript", return_value=(False, None)):
            output = orchestrator.format_output(mock_result)

        assert "## Session Context" in output
        assert "- **Next steps:**" in output
        assert "extract helper functions" in output
        assert "add type hints" in output
        assert "run tests" in output

    def test_format_output_without_chain_analysis_no_session_context(
        self, tmp_path: Path
    ) -> None:
        """format_output without chain_analysis omits Session Context section."""
        orchestrator = GTOOrchestrator(config=OrchestratorConfig(project_root=tmp_path))

        mock_result = self._make_result(chain_analysis=None)

        with patch.object(orchestrator, "_detect_question_style_from_transcript", return_value=(False, None)):
            output = orchestrator.format_output(mock_result)

        assert "## Session Context" not in output

    def test_format_output_not_yet_determined_next_steps(
        self, tmp_path: Path
    ) -> None:
        """format_output shows 'not yet determined' when next_steps is empty."""
        orchestrator = GTOOrchestrator(config=OrchestratorConfig(project_root=tmp_path))

        chain_meta = {
            "focus": "some work",
            "phase": "Phase 1",
            "next_steps": [],
            "confidence": 0.5,
            "error": None,
            "transcripts_processed": 1,
        }

        mock_result = self._make_result(chain_analysis=chain_meta)

        with patch.object(orchestrator, "_detect_question_style_from_transcript", return_value=(False, None)):
            output = orchestrator.format_output(mock_result)

        assert "_(not yet determined)_" in output
