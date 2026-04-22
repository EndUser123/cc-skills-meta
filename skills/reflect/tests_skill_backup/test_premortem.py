#!/usr/bin/env python
"""Tests for pre-mortem conversation analysis."""

import json
import os
import sys
import tempfile
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from premortem import (
    check_contradictions,
    check_missing_error_handling,
    check_vague_requirements,
    detect_conversation_state,
    run_premortem_analysis,
)


def create_test_transcript(messages):
    """Helper to create a temporary transcript file."""
    temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
    for msg in messages:
        temp_file.write(json.dumps(msg) + "\n")
    temp_file.close()
    return temp_file.name


def test_detect_conversation_state_early():
    """Test conversation state detection for early conversations."""
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"},
        {"role": "user", "content": "Help me with X"},
    ]

    state = detect_conversation_state(messages)
    assert state["phase"] == "early"
    assert state["turns"] == 3
    assert state["user_turns"] == 2
    print("✓ test_detect_conversation_state_early")


def test_check_vague_requirements():
    """Test detection of vague requirements."""
    messages = [
        {"role": "user", "content": "Improve the performance"},
        {"role": "assistant", "content": "How?"},
        {"role": "user", "content": "Make it faster"},
    ]

    issues = check_vague_requirements(messages)
    assert len(issues) >= 1
    assert any("vague_requirements" in i.get("type", "") for i in issues)
    print("✓ test_check_vague_requirements")


def test_check_contradictions():
    """Test detection of contradictory statements."""
    messages = [
        {"role": "user", "content": "Always use uv"},
        {"role": "assistant", "content": "OK"},
        {"role": "user", "content": "Never use uv, use pip instead"},
    ]

    issues = check_contradictions(messages)
    assert len(issues) >= 1
    assert any("contradiction" in i.get("type", "") for i in issues)
    print("✓ test_check_contradictions")


def test_check_missing_error_handling():
    """Test detection of missing error handling."""
    messages = [
        {"role": "user", "content": "Implement the API endpoint"},
        {"role": "assistant", "content": "Sure"},
        {"role": "user", "content": "Write the code to handle requests"},
    ]

    issues = check_missing_error_handling(messages)
    assert len(issues) >= 1
    print("✓ test_check_missing_error_handling")


def test_run_premortem_analysis():
    """Test complete pre-mortem analysis workflow."""
    messages = [
        {"role": "user", "content": "Improve the system performance"},
        {"role": "assistant", "content": "How?"},
        {"role": "user", "content": "Always use uv"},
        {"role": "assistant", "content": "OK"},
        {"role": "user", "content": "Actually, never use uv"},
    ]

    temp_file = create_test_transcript(messages)

    try:
        analysis = run_premortem_analysis(temp_file)

        assert "state" in analysis
        assert "findings" in analysis
        assert analysis["state"]["turns"] == 5
        assert analysis["state"]["phase"] == "early"
        assert len(analysis["findings"]) >= 1

        print("✓ test_run_premortem_analysis")
    finally:
        os.unlink(temp_file)


def test_check_self_verification():
    """Test detection of unverified suggestions (Step 3.8 meta-pattern)."""
    from premortem import check_self_verification

    # Case 1: AI suggests without evidence - should flag
    messages = [
        {"role": "user", "content": "Build this feature"},
        {"role": "assistant", "content": "We should add integration tests for this."},
    ]

    issues = check_self_verification(messages)
    assert len(issues) >= 1
    assert issues[0]["type"] == "unverified_suggestion"
    assert issues[0]["suggestion_type"] == "add tests"
    print("✓ test_check_self_verification detects unverified suggestions")

    # Case 2: AI checks first, then suggests - should NOT flag
    # Note: The function checks for evidence keywords in the SAME message as the suggestion
    messages_with_evidence = [
        {"role": "user", "content": "Build this feature"},
        {
            "role": "assistant",
            "content": "Let me check what tests exist first. I found unit tests but no integration tests. We should add those.",
        },
    ]

    issues = check_self_verification(messages_with_evidence)
    # Should not flag since evidence was gathered in same message
    unverified = [i for i in issues if i["type"] == "unverified_suggestion"]
    # This message has "check" which is an evidence pattern, so it should NOT flag
    assert len(unverified) == 0, f"Expected no unverified suggestions, got {unverified}"
    print("✓ test_check_self_verification allows evidence-based suggestions")

    # Case 3: Meta-suggestion about verification gets HIGH severity
    meta_messages = [
        {"role": "user", "content": "Improve the pre-mortem checks"},
        {"role": "assistant", "content": "We should add more verification patterns."},
    ]

    issues = check_self_verification(meta_messages)
    assert len(issues) >= 1
    assert issues[0]["severity"] == "HIGH"  # Meta-suggestions get high severity
    print("✓ test_check_self_verification elevates meta-suggestions to HIGH")


if __name__ == "__main__":
    print("Running pre-mortem tests...\n")

    test_detect_conversation_state_early()
    test_check_vague_requirements()
    test_check_contradictions()
    test_check_missing_error_handling()
    test_run_premortem_analysis()
    test_check_self_verification()

    print("\n✅ All pre-mortem tests passed!")
