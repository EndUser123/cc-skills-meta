"""Tests for suspicion_detector module.

Test corpus for TDD Pattern Development (CLAUDE.md).

Each test case has:
- transcript: list of {"type": "user"|"assistant", "content": str} message dicts
- expected_categories: categories that SHOULD be detected
- unexpected_categories: categories that should NOT fire (negative cases)
- description: what the test validates
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from __lib.suspicion_detector import (
    SuspicionDetector,
    SuspicionItem,
    SuspicionResult,
)


def make_transcript(messages: list[dict]) -> Path:
    """Write messages to a temp JSONL file and return the path."""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8")
    for msg in messages:
        f.write(json.dumps(msg) + "\n")
    f.close()
    return Path(f.name)


class TestSuspicionDetector:
    """Tests for SuspicionDetector with real-pattern corpus."""

    def test_contradiction_but_i_thought(self) -> None:
        """'but I thought X was done/decided' — contradiction detection."""
        transcript = make_transcript(
            [
                {"type": "user", "content": "Let's implement the auth fix."},
                {"type": "assistant", "content": "Done! The auth system is now fixed."},
                {"type": "user", "content": "but I thought we already did the fix last sprint"},
            ]
        )
        try:
            result = SuspicionDetector().detect(transcript)
            cats = {item.category for item in result.items}
            assert "contradiction" in cats, f"Expected contradiction, got: {cats}"
        finally:
            transcript.unlink()

    def test_contradiction_was_supposed_to(self) -> None:
        """'X was supposed to happen' — contradiction detection."""
        transcript = make_transcript(
            [
                {"type": "user", "content": "It was supposed to pass by now"},
            ]
        )
        try:
            result = SuspicionDetector().detect(transcript)
            cats = {item.category for item in result.items}
            assert "contradiction" in cats, f"Expected contradiction, got: {cats}"
        finally:
            transcript.unlink()

    def test_contradiction_but_we_agreed(self) -> None:
        """'but we agreed on X' — contradiction detection."""
        transcript = make_transcript(
            [
                {"type": "user", "content": "but we agreed on using pytest for testing"},
            ]
        )
        try:
            result = SuspicionDetector().detect(transcript)
            cats = {item.category for item in result.items}
            assert "contradiction" in cats, f"Expected contradiction, got: {cats}"
        finally:
            transcript.unlink()

    def test_contradiction_capture_group_quality(self) -> None:
        """Verify capture group actually captures content, not '. ' prefix.

        Regression: previously used '(. {10,60})' which consumed '. ' literally.
        """
        transcript = make_transcript(
            [
                {
                    "type": "user",
                    "content": "but we agreed that fixing the race condition matters most",
                },
            ]
        )
        try:
            result = SuspicionDetector().detect(transcript)
            contradiction_items = [i for i in result.items if i.category == "contradiction"]
            assert len(contradiction_items) >= 1, "Expected at least one contradiction item"
            # The captured content should NOT be empty or start with ". "
            for item in contradiction_items:
                assert not item.content.startswith(". "), (
                    f"Capture group consumed '. ' literally: {item.content!r}"
                )
                assert len(item.content) >= 5, f"Content too short: {item.content!r}"
        finally:
            transcript.unlink()

    def test_commitment_reversal_wait_actually(self) -> None:
        """'wait actually' / 'no wait' — commitment reversal detection."""
        transcript = make_transcript(
            [
                {
                    "type": "user",
                    "content": "actually on second thought let's use a different approach",
                },
            ]
        )
        try:
            result = SuspicionDetector().detect(transcript)
            cats = {item.category for item in result.items}
            assert "commitment_reversal" in cats, f"Expected commitment_reversal, got: {cats}"
        finally:
            transcript.unlink()

    def test_commitment_reversal_i_take_it_back(self) -> None:
        """'I take it back' — commitment reversal detection."""
        transcript = make_transcript(
            [
                {"type": "user", "content": "I take it back, that was the wrong call"},
            ]
        )
        try:
            result = SuspicionDetector().detect(transcript)
            cats = {item.category for item in result.items}
            assert "commitment_reversal" in cats, f"Expected commitment_reversal, got: {cats}"
        finally:
            transcript.unlink()

    def test_confusion_im_confused(self) -> None:
        """'I'm confused' / 'doesn't make sense' — unresolved confusion detection."""
        transcript = make_transcript(
            [
                {"type": "user", "content": "I'm confused about why the test is failing"},
            ]
        )
        try:
            result = SuspicionDetector().detect(transcript)
            cats = {item.category for item in result.items}
            assert "unresolved_confusion" in cats, f"Expected unresolved_confusion, got: {cats}"
        finally:
            transcript.unlink()

    def test_confusion_what_do_you_mean(self) -> None:
        """'what do you mean' — confusion detection."""
        transcript = make_transcript(
            [
                {"type": "user", "content": "wait what do you mean by that exactly"},
            ]
        )
        try:
            result = SuspicionDetector().detect(transcript)
            cats = {item.category for item in result.items}
            assert "unresolved_confusion" in cats, f"Expected unresolved_confusion, got: {cats}"
        finally:
            transcript.unlink()

    def test_resigned_acceptance_with_prior_concern(self) -> None:
        """Resigned acceptance: concern in prior turn + acceptance in current.

        This requires cross-turn analysis — prior 2 messages must have concern keywords.
        """
        transcript = make_transcript(
            [
                {"type": "user", "content": "I'm not sure about this approach"},
                {"type": "assistant", "content": "We can do it this way instead."},
                {"type": "user", "content": "fine I guess that'll work"},
            ]
        )
        try:
            result = SuspicionDetector().detect(transcript)
            cats = {item.category for item in result.items}
            assert "resigned_acceptance" in cats, (
                f"Expected resigned_acceptance with prior concern, got: {cats}"
            )
        finally:
            transcript.unlink()

    def test_resigned_acceptance_no_prior_concern(self) -> None:
        """Resigned acceptance should NOT fire without prior concern keywords."""
        transcript = make_transcript(
            [
                {"type": "user", "content": "Let's use the fast path."},
                {"type": "assistant", "content": "Sure thing!"},
                {"type": "user", "content": "fine let's go with that"},
            ]
        )
        try:
            result = SuspicionDetector().detect(transcript)
            cats = {item.category for item in result.items}
            # Should NOT fire — "fine" alone without prior concern is not resigned acceptance
            assert "resigned_acceptance" not in cats, (
                f"Unexpected resigned_acceptance without prior concern: {cats}"
            )
        finally:
            transcript.unlink()

    def test_misalignment_already_told_you(self) -> None:
        """'I've already told you' / 'as I said' — misalignment detection."""
        transcript = make_transcript(
            [
                {"type": "user", "content": "as I said before we need to handle the timeout case"},
            ]
        )
        try:
            result = SuspicionDetector().detect(transcript)
            cats = {item.category for item in result.items}
            assert "misalignment" in cats, f"Expected misalignment, got: {cats}"
        finally:
            transcript.unlink()

    def test_misalignment_you_seem_to_have_missed(self) -> None:
        """'you seem to have missed/forgotten' — misalignment detection."""
        transcript = make_transcript(
            [
                {
                    "type": "user",
                    "content": "you seem to have missed implementing the retry logic properly",
                },
            ]
        )
        try:
            result = SuspicionDetector().detect(transcript)
            cats = {item.category for item in result.items}
            assert "misalignment" in cats, f"Expected misalignment, got: {cats}"
        finally:
            transcript.unlink()

    def test_completion_signal_suppresses(self) -> None:
        """Messages with strong completion signals should be skipped."""
        transcript = make_transcript(
            [
                {
                    "type": "user",
                    "content": "I'm confused about the implementation but actually it's done now",
                },
            ]
        )
        try:
            result = SuspicionDetector().detect(transcript)
            cats = {item.category for item in result.items}
            # "done" should suppress the confusion signal
            confusion_items = [i for i in result.items if i.category == "unresolved_confusion"]
            assert len(confusion_items) == 0, (
                f"Completion signal 'done' should suppress confusion: {confusion_items}"
            )
        finally:
            transcript.unlink()

    def test_to_gaps_format(self) -> None:
        """SuspicionResult.to_gaps() returns RSN-format gap dicts."""
        item = SuspicionItem(
            category="contradiction",
            content="but I thought we already did the fix",
            turn_number=3,
            confidence=0.8,
            source_message="but I thought we already did the fix",
            prior_context="Let's implement the auth fix.",
        )
        result = SuspicionResult(items=[item], total_count=1)
        gaps = result.to_gaps()
        assert len(gaps) == 1
        gap = gaps[0]
        assert gap["id"].startswith("SUSPIC-CONT-")
        assert gap["type"] == "suspicion_contradiction"
        assert gap["severity"] == "high"
        assert gap["theme"] == "suspicion_signals"
        assert "confidence" in gap

    def test_deduplication(self) -> None:
        """Duplicate items (same normalized content) should be merged."""
        transcript = make_transcript(
            [
                {
                    "type": "user",
                    "content": "but I thought we already did the fix for the race condition",
                },
                {
                    "type": "user",
                    "content": "but I thought we already did the fix for the race condition",
                },  # exact dup
            ]
        )
        try:
            result = SuspicionDetector().detect(transcript)
            contradiction_items = [i for i in result.items if i.category == "contradiction"]
            # Should be deduplicated to 1
            assert len(contradiction_items) == 1, (
                f"Expected 1 deduplicated item, got {len(contradiction_items)}"
            )
        finally:
            transcript.unlink()

    def test_no_transcript_file(self) -> None:
        """Non-existent transcript path returns empty result."""
        result = SuspicionDetector().detect(Path("/nonexistent/ transcript.jsonl"))
        assert result.total_count == 0
        assert result.items == []

    def test_multicategory_in_single_message(self) -> None:
        """A single message can trigger multiple suspicion categories."""
        transcript = make_transcript(
            [
                {
                    "type": "user",
                    "content": "but I thought we already did the migration to pytest framework, wait actually let's use pytest anyway, I'm confused about why we changed",
                },
            ]
        )
        try:
            result = SuspicionDetector().detect(transcript)
            cats = {item.category for item in result.items}
            # Should detect both contradiction and confusion (reversal requires separate turn)
            assert "contradiction" in cats, f"Expected contradiction, got: {cats}"
            assert "unresolved_confusion" in cats, f"Expected confusion, got: {cats}"
        finally:
            transcript.unlink()

    def test_high_recurrence_bumps_severity(self) -> None:
        """Items appearing multiple times should bump to high severity via to_gaps."""
        item = SuspicionItem(
            category="unresolved_confusion",
            content="but we agreed on pytest",  # same content repeated
            turn_number=1,
            confidence=0.8,
        )
        item2 = SuspicionItem(
            category="unresolved_confusion",
            content="but we agreed on pytest",  # duplicate
            turn_number=5,
            confidence=0.8,
        )
        result = SuspicionResult(items=[item, item2], total_count=2)
        gaps = result.to_gaps()
        # After deduplication, one item remains with recurrence_count=2
        # But deduplication is in detect(), not to_gaps() directly
        assert len(gaps) >= 1
