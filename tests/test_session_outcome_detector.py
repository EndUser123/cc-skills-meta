"""Tests for session outcome detector — uncompleted goals, open questions, deferred items."""
import json
import pytest
from pathlib import Path

from skills.gto.__lib.session_outcome_detector import (
    SessionOutcomeDetector,
    SessionOutcomeItem,
    SessionOutcomeResult,
    detect_session_outcomes,
)


def _write_transcript(path: Path, messages: list[tuple[str, str]]) -> Path:
    """Write a transcript JSONL with (role, content) pairs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for role, content in messages:
            f.write(json.dumps({"role": role, "content": content}) + "\n")
    return path


class TestDetectTaskIntent:
    def test_detects_i_want_to(self, tmp_path):
        t = _write_transcript(tmp_path / "t.jsonl", [
            ("user", "I want to build a rate limiter for the API endpoints."),
        ])
        result = SessionOutcomeDetector().detect(t)
        assert result.total_count >= 1
        assert any("rate limiter" in item.content for item in result.items)
        assert any(item.category == "uncompleted_goal" for item in result.items)

    def test_detects_we_should(self, tmp_path):
        t = _write_transcript(tmp_path / "t.jsonl", [
            ("user", "we should add error handling for the database connection pool."),
        ])
        result = SessionOutcomeDetector().detect(t)
        assert any("error handling" in item.content for item in result.items)

    def test_detects_lets_build(self, tmp_path):
        t = _write_transcript(tmp_path / "t.jsonl", [
            ("user", "let's build a caching layer for the user service module."),
        ])
        result = SessionOutcomeDetector().detect(t)
        assert any("caching layer" in item.content for item in result.items)

    def test_ignores_assistant_messages(self, tmp_path):
        t = _write_transcript(tmp_path / "t.jsonl", [
            ("assistant", "I want to build a new module for the system."),
        ])
        result = SessionOutcomeDetector().detect(t)
        assert result.total_count == 0

    def test_ignores_short_messages(self, tmp_path):
        t = _write_transcript(tmp_path / "t.jsonl", [
            ("user", "I want to build"),
        ])
        result = SessionOutcomeDetector().detect(t)
        # Too short (< 20 chars) to be meaningful
        assert result.total_count == 0

    def test_skips_completion_signals(self, tmp_path):
        t = _write_transcript(tmp_path / "t.jsonl", [
            ("user", "I'm done building the rate limiter, it works now."),
        ])
        result = SessionOutcomeDetector().detect(t)
        assert result.total_count == 0


class TestDetectQuestions:
    def test_detects_uncertainty(self, tmp_path):
        t = _write_transcript(tmp_path / "t.jsonl", [
            ("user", "not sure how to handle the edge case with null values in the response."),
        ])
        result = SessionOutcomeDetector().detect(t)
        assert any(item.category == "open_question" for item in result.items)

    def test_detects_need_to_check(self, tmp_path):
        t = _write_transcript(tmp_path / "t.jsonl", [
            ("user", "we need to verify the database migration worked correctly on staging."),
        ])
        result = SessionOutcomeDetector().detect(t)
        assert any(item.category == "open_question" for item in result.items)


class TestDetectDeferred:
    def test_detects_for_now(self, tmp_path):
        t = _write_transcript(tmp_path / "t.jsonl", [
            ("user", "for now we'll use the simple implementation without caching."),
        ])
        result = SessionOutcomeDetector().detect(t)
        assert any(item.category == "deferred_item" for item in result.items)

    def test_detects_come_back_to(self, tmp_path):
        t = _write_transcript(tmp_path / "t.jsonl", [
            ("user", "let's come back to the performance optimization later."),
        ])
        result = SessionOutcomeDetector().detect(t)
        assert any(item.category == "deferred_item" for item in result.items)


class TestDeduplication:
    def test_dedupes_same_intent_different_turns(self, tmp_path):
        t = _write_transcript(tmp_path / "t.jsonl", [
            ("user", "I want to add rate limiting to the API."),
            ("assistant", "OK, let me check the code."),
            ("user", "I need to add rate limiting to the API."),
        ])
        result = SessionOutcomeDetector().detect(t)
        assert result.total_count == 1
        assert result.items[0].recurrence_count == 2

    def test_keeps_different_intents(self, tmp_path):
        t = _write_transcript(tmp_path / "t.jsonl", [
            ("user", "I want to add rate limiting to the API."),
            ("assistant", "Done."),
            ("user", "we should fix the authentication bug in the login flow."),
        ])
        result = SessionOutcomeDetector().detect(t)
        assert result.total_count == 2


class TestSessionCategorization:
    def test_current_session_items(self, tmp_path):
        t = _write_transcript(tmp_path / "t.jsonl", [
            ("user", "I want to implement the new payment module for checkout."),
        ])
        result = SessionOutcomeDetector().detect(t)
        assert len(result.current_session_items) >= 1
        assert len(result.prior_session_items) == 0

    def test_empty_transcript(self, tmp_path):
        t = tmp_path / "empty.jsonl"
        t.write_text("", encoding="utf-8")
        result = SessionOutcomeDetector().detect(t)
        assert result.total_count == 0

    def test_nonexistent_transcript(self, tmp_path):
        result = SessionOutcomeDetector().detect(tmp_path / "nope.jsonl")
        assert result.total_count == 0

    def test_none_transcript(self, tmp_path):
        result = SessionOutcomeDetector().detect(None)
        assert result.total_count == 0


class TestAcknowledgment:
    def test_prior_outcomes_marked_acknowledged(self, tmp_path, monkeypatch):
        evidence_dir = tmp_path / "evidence"
        evidence_dir.mkdir()

        # Pre-populate prior outcomes — content must normalize to same key as detected item
        prior_path = evidence_dir / "gto-outcomes-test.json"
        prior_path.write_text(json.dumps({
            "items": [{"content": "add rate limiting to the API", "acknowledged": True, "category": "uncompleted_goal"}]
        }), encoding="utf-8")

        t = _write_transcript(tmp_path / "t.jsonl", [
            ("user", "I want to add rate limiting to the API."),
        ])

        detector = SessionOutcomeDetector()
        detector._get_prior_outcomes_path = lambda tid: prior_path

        result = detector.detect(t, terminal_id="test")
        assert any(item.acknowledged for item in result.items)


class TestToGaps:
    def test_converts_to_gap_format(self, tmp_path):
        t = _write_transcript(tmp_path / "t.jsonl", [
            ("user", "I want to implement the new caching layer for performance."),
        ])
        result = SessionOutcomeDetector().detect(t)
        gaps = result.to_gaps()
        assert len(gaps) >= 1
        assert gaps[0]["id"].startswith("SESSION-")
        assert gaps[0]["severity"] in ("low", "medium", "high")

    def test_recurrence_bumps_severity(self, tmp_path):
        t = _write_transcript(tmp_path / "t.jsonl", [
            ("user", "I want to add rate limiting to the API."),
            ("assistant", "OK"),
            ("user", "I need to add rate limiting to the API."),
            ("assistant", "Sure"),
            ("user", "we should add rate limiting to the API."),
        ])
        result = SessionOutcomeDetector().detect(t)
        gaps = result.to_gaps()
        assert any(g["severity"] == "high" for g in gaps)


class TestConvenienceFunction:
    def test_detect_session_outcomes(self, tmp_path):
        t = _write_transcript(tmp_path / "t.jsonl", [
            ("user", "I want to build a health check endpoint for the service."),
        ])
        result = detect_session_outcomes(t, project_root=tmp_path)
        assert result.total_count >= 1


class TestNormalizeContent:
    def test_normalizes_for_comparison(self):
        n = SessionOutcomeDetector._normalize_content
        assert n("Add Rate Limiting!") == n("add rate limiting")
        assert n("Fix the Bug (critical)") == n("fix the bug critical")

    def test_truncates_long_content(self):
        n = SessionOutcomeDetector._normalize_content
        long = "x" * 200
        assert len(n(long)) == 80
