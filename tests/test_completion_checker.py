"""Tests for completion checker — filters session outcomes that were actually completed."""
import json
import pytest
from pathlib import Path

from skills.gto.__lib.completion_checker import check_completions
from skills.gto.__lib.session_outcome_detector import SessionOutcomeItem


def _write_transcript(path: Path, messages: list[tuple[str, str]]) -> Path:
    """Write a transcript JSONL with (role, content) pairs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for role, content in messages:
            f.write(json.dumps({"role": role, "content": content}) + "\n")
    return path


def _item(turn: int, content: str, category: str = "uncompleted_goal") -> SessionOutcomeItem:
    return SessionOutcomeItem(
        category=category,
        content=content,
        turn_number=turn,
        session_age=0,
        confidence=0.8,
    )


class TestFiltersCompleted:
    def test_filters_explicitly_completed_goal(self, tmp_path):
        t = _write_transcript(tmp_path / "t.jsonl", [
            ("user", "I want to build a rate limiter for the API."),
            ("assistant", "I've finished implementing the rate limiter module."),
            ("user", "show me the results."),
        ])
        items = [_item(1, "build a rate limiter for the API")]
        result = check_completions(t, items)
        assert len(result) == 0

    def test_filters_user_confirmed(self, tmp_path):
        t = _write_transcript(tmp_path / "t.jsonl", [
            ("user", "I want to add error handling for the database pool."),
            ("assistant", "I've added error handling for the database connection pool."),
            ("user", "looks good, works now."),
        ])
        items = [_item(1, "add error handling for the database pool")]
        result = check_completions(t, items)
        assert len(result) == 0

    def test_filters_successful_creation(self, tmp_path):
        t = _write_transcript(tmp_path / "t.jsonl", [
            ("user", "I want to create a health check endpoint for the service."),
            ("assistant", "Successfully created the health check endpoint."),
        ])
        items = [_item(1, "create a health check endpoint for the service")]
        result = check_completions(t, items)
        assert len(result) == 0


class TestKeepsUncompleted:
    def test_keeps_unaddressed_goal(self, tmp_path):
        t = _write_transcript(tmp_path / "t.jsonl", [
            ("user", "I want to build a rate limiter for the API."),
            ("assistant", "OK, let me check the codebase first."),
            ("user", "show me the current architecture."),
        ])
        items = [_item(1, "build a rate limiter for the API")]
        result = check_completions(t, items)
        assert len(result) == 1

    def test_keeps_partial_completion(self, tmp_path):
        t = _write_transcript(tmp_path / "t.jsonl", [
            ("user", "I want to build a caching layer for the user service."),
            ("assistant", "I've started working on the caching layer."),
            ("user", "how's it going?"),
        ])
        items = [_item(1, "build a caching layer for the user service")]
        result = check_completions(t, items)
        assert len(result) == 1

    def test_keeps_unrelated_completion(self, tmp_path):
        t = _write_transcript(tmp_path / "t.jsonl", [
            ("user", "I want to add rate limiting to the API."),
            ("assistant", "I've finished implementing the authentication middleware."),
            ("user", "looks good."),
        ])
        items = [_item(1, "add rate limiting to the API")]
        result = check_completions(t, items)
        assert len(result) == 1


class TestEdgeCases:
    def test_handles_none_transcript(self, tmp_path):
        items = [_item(1, "build something")]
        result = check_completions(None, items)
        assert len(result) == 1

    def test_handles_empty_transcript(self, tmp_path):
        t = tmp_path / "empty.jsonl"
        t.write_text("", encoding="utf-8")
        items = [_item(1, "build something")]
        result = check_completions(t, items)
        assert len(result) == 1

    def test_handles_nonexistent_file(self, tmp_path):
        items = [_item(1, "build something")]
        result = check_completions(tmp_path / "nope.jsonl", items)
        assert len(result) == 1

    def test_empty_items_list(self, tmp_path):
        t = _write_transcript(tmp_path / "t.jsonl", [
            ("user", "hello"),
        ])
        result = check_completions(t, [])
        assert result == []


class TestWindowBoundary:
    def test_signal_beyond_window_keeps_item(self, tmp_path):
        messages = [("user", "I want to build a caching layer.")]
        for i in range(11):
            messages.append(("assistant", f"filler turn {i}"))
        messages.append(("assistant", "finished implementing the caching layer."))
        t = _write_transcript(tmp_path / "t.jsonl", messages)

        items = [_item(1, "build a caching layer")]
        result = check_completions(t, items, window=10)
        assert len(result) == 1

    def test_signal_at_edge_of_window_filters(self, tmp_path):
        messages = [("user", "I want to build a caching layer.")]
        for i in range(9):
            messages.append(("assistant", f"filler turn {i}"))
        messages.append(("assistant", "finished implementing the caching layer."))
        t = _write_transcript(tmp_path / "t.jsonl", messages)

        items = [_item(1, "build a caching layer")]
        result = check_completions(t, items, window=10)
        assert len(result) == 0


class TestMultipleItems:
    def test_mix_of_completed_and_uncompleted(self, tmp_path):
        t = _write_transcript(tmp_path / "t.jsonl", [
            ("user", "I want to build a rate limiter for the API."),
            ("assistant", "I've finished implementing the rate limiter module."),
            ("user", "I need to add error handling for the database pool."),
            ("assistant", "Let me check the existing error handling."),
            ("user", "show me what we have."),
        ])
        items = [
            _item(1, "build a rate limiter for the API"),
            _item(3, "add error handling for the database pool"),
        ]
        result = check_completions(t, items)
        assert len(result) == 1
        assert "error handling" in result[0].content

    def test_all_completed(self, tmp_path):
        t = _write_transcript(tmp_path / "t.jsonl", [
            ("user", "I want to build a rate limiter."),
            ("assistant", "Finished implementing the rate limiter."),
            ("user", "I need to fix the auth bug."),
            ("assistant", "Fixed the authentication bug in the login flow."),
            ("user", "looks good."),
        ])
        items = [
            _item(1, "build a rate limiter"),
            _item(3, "fix the auth bug"),
        ]
        result = check_completions(t, items)
        assert len(result) == 0
