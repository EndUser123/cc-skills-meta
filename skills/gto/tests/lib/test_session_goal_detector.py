"""Tests for session_goal_detector module."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from __lib.session_goal_detector import (
    SessionGoalDetector,
    SessionGoalResult,
)


class TestSessionGoalDetector:
    """Smoke tests for SessionGoalDetector."""

    def test_detector_instantiation(self, tmp_path: Path) -> None:
        """Test detector can be instantiated."""
        detector = SessionGoalDetector(tmp_path)
        assert detector is not None


class TestIsQuestionStyle:
    """Tests for is_question_style method."""

    def test_question_patterns(self, tmp_path: Path) -> None:
        """Test all question-style patterns return True."""
        detector = SessionGoalDetector(tmp_path)

        # All patterns from QUESTION_PATTERNS
        assert detector.is_question_style("what are we doing") is True
        assert detector.is_question_style("What's the status?") is True
        assert detector.is_question_style("what's needed next") is True
        assert detector.is_question_style("what were we working on") is True
        assert detector.is_question_style("how's it going") is True
        assert detector.is_question_style("how is it going?") is True

    def test_case_insensitive(self, tmp_path: Path) -> None:
        """Test is_question_style is case insensitive."""
        detector = SessionGoalDetector(tmp_path)

        assert detector.is_question_style("WHAT ARE WE DOING") is True
        assert detector.is_question_style("WHAT'S THE STATUS") is True
        assert detector.is_question_style("HOW'S IT GOING") is True

    def test_non_question_returns_false(self, tmp_path: Path) -> None:
        """Test non-question statements return False."""
        detector = SessionGoalDetector(tmp_path)

        assert detector.is_question_style("let's build a feature") is False
        assert detector.is_question_style("the goal is to fix the bug") is False
        assert detector.is_question_style("I need to implement auth") is False

    def test_why_question_returns_false(self, tmp_path: Path) -> None:
        """Test 'why' questions return False (not a status question)."""
        detector = SessionGoalDetector(tmp_path)

        assert detector.is_question_style("why are we doing this") is False
        assert detector.is_question_style("why is the test failing") is False

    def test_subagent_path_trigger(self, tmp_path: Path) -> None:
        """Test that question-style triggers subagent path."""
        detector = SessionGoalDetector(tmp_path)

        # These should trigger subagent path
        assert detector.is_question_style("what are we doing") is True
        assert detector.is_question_style("what's the status") is True

        # Imperative should not trigger
        assert detector.is_question_style("let's fix this") is False


class TestSessionGoalResult:
    """Tests for SessionGoalResult dataclass."""

    def test_dataclass(self) -> None:
        """Test SessionGoalResult can be constructed."""
        result = SessionGoalResult(
            session_goal="Test goal",
            source_turn=1,
            confidence=0.9,
        )
        assert result.session_goal == "Test goal"
        assert result.source_turn == 1
        assert result.confidence == 0.9

    def test_dataclass_null(self) -> None:
        """Test SessionGoalResult with null fields."""
        result = SessionGoalResult(
            session_goal=None,
            source_turn=None,
            confidence=0.0,
        )
        assert result.session_goal is None
