"""Tests for session goal detector — regex goal extraction from transcripts."""
import json
import pytest
from pathlib import Path

from skills.gto.__lib.session_goal_detector import SessionGoalDetector, SessionGoalResult


def _write_transcript(path: Path, messages: list[tuple[str, str]]) -> Path:
    """Write a transcript JSONL with (role, content) pairs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for role, content in messages:
            f.write(json.dumps({"role": role, "content": content}) + "\n")
    return path


class TestDetectGoal:
    def test_detects_today_i_want_to(self, tmp_path):
        t = _write_transcript(tmp_path / "t.jsonl", [
            ("user", "today I want to build a REST API for users."),
        ])
        result = SessionGoalDetector().detect_goal(t)
        assert result.session_goal is not None
        assert "REST API" in result.session_goal
        assert result.confidence == 0.9

    def test_detects_i_need_to(self, tmp_path):
        t = _write_transcript(tmp_path / "t.jsonl", [
            ("user", "I need to fix the authentication bug in the login flow."),
        ])
        result = SessionGoalDetector().detect_goal(t)
        assert result.session_goal is not None
        assert "fix the authentication bug" in result.session_goal
        assert result.confidence == 0.8

    def test_detects_lets_build(self, tmp_path):
        t = _write_transcript(tmp_path / "t.jsonl", [
            ("user", "let's build a caching layer for the API."),
        ])
        result = SessionGoalDetector().detect_goal(t)
        assert result.session_goal is not None
        assert "caching layer" in result.session_goal

    def test_no_goal_found(self, tmp_path):
        t = _write_transcript(tmp_path / "t.jsonl", [
            ("user", "show me the current test coverage."),
            ("assistant", "Here's the coverage report."),
        ])
        result = SessionGoalDetector().detect_goal(t)
        assert result.session_goal is None
        assert result.confidence == 0.0

    def test_ignores_assistant_messages(self, tmp_path):
        t = _write_transcript(tmp_path / "t.jsonl", [
            ("assistant", "today I want to refactor everything."),
        ])
        result = SessionGoalDetector().detect_goal(t)
        assert result.session_goal is None

    def test_empty_transcript(self, tmp_path):
        t = tmp_path / "empty.jsonl"
        t.write_text("", encoding="utf-8")
        result = SessionGoalDetector().detect_goal(t)
        assert result.session_goal is None

    def test_nonexistent_file(self, tmp_path):
        result = SessionGoalDetector().detect_goal(tmp_path / "nope.jsonl")
        assert result.session_goal is None


class TestDetectGoalFromChain:
    def test_uses_oldest_transcript(self, tmp_path):
        old = _write_transcript(tmp_path / "old.jsonl", [
            ("user", "the goal is to implement rate limiting."),
        ])
        new = _write_transcript(tmp_path / "new.jsonl", [
            ("user", "show me the results."),
        ])
        result = SessionGoalDetector().detect_goal_from_chain([str(old), str(new)])
        assert result.session_goal is not None
        assert "rate limiting" in result.session_goal

    def test_empty_chain(self):
        result = SessionGoalDetector().detect_goal_from_chain([])
        assert result.session_goal is None


class TestIsQuestionStyle:
    def test_matches_status_question(self):
        assert SessionGoalDetector().is_question_style("what's the status")

    def test_matches_working_on(self):
        assert SessionGoalDetector().is_question_style("what were we working on")

    def test_no_match_for_statement(self):
        assert not SessionGoalDetector().is_question_style("I need to fix the bug")
