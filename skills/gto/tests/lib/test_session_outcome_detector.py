"""Tests for SessionOutcomeDetector — gap acknowledgment mechanism."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from __lib.session_outcome_detector import (
    SessionOutcomeDetector,
    SessionOutcomeItem,
    SessionOutcomeResult,
)


class TestAcknowledgedField:
    """acknowledged field is present and defaults to False."""

    def test_acknowledged_field_exists(self) -> None:
        item = SessionOutcomeItem(
            category="uncompleted_goal",
            content="test content",
            turn_number=1,
            session_age=0,
            confidence=0.8,
        )
        assert hasattr(item, "acknowledged")
        assert item.acknowledged is False

    def test_acknowledged_can_be_set_true(self) -> None:
        item = SessionOutcomeItem(
            category="uncompleted_goal",
            content="test content",
            turn_number=1,
            session_age=0,
            confidence=0.8,
            acknowledged=True,
        )
        assert item.acknowledged is True


class TestPriorOutcomesPersistence:
    """_load_prior_outcomes / _save_current_outcomes round-trip."""

    def test_save_and_load_round_trip(self, tmp_path: Path) -> None:
        import uuid

        terminal = f"term_round_{uuid.uuid4().hex[:8]}"
        detector = SessionOutcomeDetector(project_root=tmp_path)

        items = [
            SessionOutcomeItem(
                category="uncompleted_goal",
                content=f"fix the login bug for session {uuid.uuid4().hex[:6]}",
                turn_number=1,
                session_age=0,
                confidence=0.8,
                acknowledged=False,
            ),
            SessionOutcomeItem(
                category="open_question",
                content=f"should we add caching for {uuid.uuid4().hex[:6]}",
                turn_number=3,
                session_age=0,
                confidence=0.6,
                acknowledged=True,
            ),
        ]

        # Save
        detector._save_current_outcomes(items, terminal_id=terminal)

        # Load
        loaded = detector._load_prior_outcomes(terminal_id=terminal)

        assert loaded[items[0].content] is False
        assert loaded[items[1].content] is True

        # Clean up
        detector._get_prior_outcomes_path(terminal).unlink(missing_ok=True)

    def test_load_nonexistent_returns_empty_dict(self, tmp_path: Path) -> None:
        detector = SessionOutcomeDetector(project_root=tmp_path)
        result = detector._load_prior_outcomes(terminal_id="nonexistent_term")
        assert result == {}

    def test_normalize_content(self) -> None:
        """_normalize_content strips punctuation and lowercases."""
        detector = SessionOutcomeDetector()
        assert detector._normalize_content("Fix the BUG!") == detector._normalize_content(
            "fix the bug"
        )
        assert "fix the bug" in detector._normalize_content("!!!Fix the BUG???")


class TestAcknowledgmentInDetect:
    """detect() marks items as acknowledged when they appear in prior outcomes."""

    def test_prior_item_marked_acknowledged(self, tmp_path: Path) -> None:
        """An item that was in the prior outcomes file gets acknowledged=True."""
        import uuid

        terminal = f"term_prior_{uuid.uuid4().hex[:8]}"

        detector = SessionOutcomeDetector(project_root=tmp_path)

        # Pre-write prior outcomes (simulating prior session)
        prior_path = detector._get_prior_outcomes_path(terminal)
        prior_path.parent.mkdir(parents=True, exist_ok=True)
        with open(prior_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "items": [
                        {
                            "content": "add user authentication for this app today",
                            "acknowledged": True,
                            "category": "uncompleted_goal",
                        }
                    ]
                },
                f,
            )

        # Create a transcript that extracts EXACTLY the same content
        # Use "for this app" instead of "to the app now" — "to the app now" contains
        # "on to" which matches the completion_re signal, filtering out the item.
        transcript_path = tmp_path / "transcript.jsonl"
        content = "I want to add user authentication for this app today"
        transcript_path.write_text(
            json.dumps({"role": "user", "content": content}) + "\n",
            encoding="utf-8",
        )

        result = detector.detect(transcript_path=transcript_path, terminal_id=terminal)

        # The item should be marked acknowledged
        assert len(result.items) >= 1
        ack_items = [i for i in result.items if "add user authentication" in i.content]
        assert len(ack_items) == 1, (
            f"Expected 1 item with 'add user authentication', got {len(ack_items)}: {ack_items}"
        )
        assert ack_items[0].acknowledged is True

        # Clean up
        prior_path.unlink(missing_ok=True)

    def test_new_item_not_acknowledged(self, tmp_path: Path) -> None:
        """An item that was NOT in prior outcomes gets acknowledged=False."""
        import uuid

        terminal = f"term_new_{uuid.uuid4().hex[:8]}"

        detector = SessionOutcomeDetector(project_root=tmp_path)

        # No prior outcomes file for this unique terminal

        # Create a transcript with a unique item (never in any prior outcomes)
        transcript_path = tmp_path / "transcript.jsonl"
        unique_content = f"build a unique widget component {uuid.uuid4().hex[:8]}"
        transcript_path.write_text(
            json.dumps({"role": "user", "content": f"I want to {unique_content}"}) + "\n",
            encoding="utf-8",
        )

        result = detector.detect(transcript_path=transcript_path, terminal_id=terminal)

        # The item should NOT be acknowledged
        assert len(result.items) >= 1
        new_items = [i for i in result.items if "unique widget" in i.content]
        assert len(new_items) == 1
        assert new_items[0].acknowledged is False


class TestToGapsAcknowledged:
    """to_gaps() includes acknowledged in metadata."""

    def test_acknowledged_in_metadata(self) -> None:
        item = SessionOutcomeItem(
            category="uncompleted_goal",
            content="fix the bug",
            turn_number=1,
            session_age=0,
            confidence=0.8,
            acknowledged=True,
        )
        result = SessionOutcomeResult(items=[item], total_count=1)
        gaps = result.to_gaps()

        assert len(gaps) == 1
        assert gaps[0]["metadata"]["acknowledged"] is True

    def test_not_acknowledged_in_metadata(self) -> None:
        item = SessionOutcomeItem(
            category="uncompleted_goal",
            content="fix the bug",
            turn_number=1,
            session_age=0,
            confidence=0.8,
            acknowledged=False,
        )
        result = SessionOutcomeResult(items=[item], total_count=1)
        gaps = result.to_gaps()

        assert len(gaps) == 1
        assert gaps[0]["metadata"]["acknowledged"] is False
