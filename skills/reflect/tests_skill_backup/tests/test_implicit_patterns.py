#!/usr/bin/env python
"""
Unit tests for implicit pattern detection.

Tests the retry pattern detection, tool discovery, and
pattern emergence detection in implicit_patterns.py.
"""

import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from implicit_patterns import (
    detect_implicit_patterns,
    extract_learning_from_pair,
    is_tool_failure,
)


def test_retry_pattern_detection():
    """Test that retry patterns are detected when tools fail and succeed."""
    messages = [
        {
            "role": "assistant",
            "content": "I'll use Edit to modify the file",
            "tool_uses": [{"name": "Edit", "result": "Error: File not found"}],
        },
        {
            "role": "assistant",
            "content": "Let me try Write instead",
            "tool_uses": [{"name": "Write", "result": "Success"}],
        },
        {"role": "user", "content": "Great, now add one more test"},
    ]

    signals = detect_implicit_patterns(messages, ["testing"])

    assert len(signals) == 1, f"Expected 1 signal, got {len(signals)}"
    signal = signals[0]

    assert signal["type"] == "implicit_success"
    assert signal["learning_type"] == "retry_success"
    assert signal["confidence"] == "MEDIUM"
    assert signal["confidence_score"] == 0.60
    assert signal["has_implicit_approval"] == True
    assert "Write" in signal["successful_approach"]
    assert "Edit" in str(signal["failed_attempts"])

    print("✓ test_retry_pattern_detection passed")


def test_tool_discovery_pattern():
    """Test that tool discovery patterns are captured."""
    messages = [
        {
            "role": "assistant",
            "content": "I'll search with Grep",
            "tool_uses": [{"name": "Grep", "result": "Error: Results too large, truncated"}],
        },
        {
            "role": "assistant",
            "content": "Let me try a more specific approach with Agent",
            "tool_uses": [{"name": "Agent", "result": "Found relevant files"}],
        },
        {"role": "user", "content": "Perfect, now analyze those files"},
    ]

    signals = detect_implicit_patterns(messages, ["search"])

    assert len(signals) == 1
    signal = signals[0]

    assert signal["type"] == "implicit_success"
    assert "Agent" in signal["successful_approach"]
    assert signal["has_implicit_approval"] == True

    print("✓ test_tool_discovery_pattern passed")


def test_no_implicit_pattern_without_retry():
    """Test that no signal is generated without retry pattern."""
    messages = [
        {
            "role": "assistant",
            "content": "I'll use Read to view the file",
            "tool_uses": [{"name": "Read", "result": "File content here"}],
        },
        {"role": "user", "content": "Thanks, that worked"},
    ]

    signals = detect_implicit_patterns(messages, ["general"])

    # Should not generate implicit signal for single successful attempt
    assert len(signals) == 0, f"Expected 0 signals, got {len(signals)}"

    print("✓ test_no_implicit_pattern_without_retry passed")


def test_is_tool_failure():
    """Test tool failure detection."""
    # Error indicators
    assert is_tool_failure("Error: File not found") == True
    assert is_tool_failure("Failed to execute") == True
    assert is_tool_failure("KeyError: 'missing_key'") == True
    assert is_tool_failure("ValueError: invalid input") == True

    # Success cases
    assert is_tool_failure("Success") == False
    assert is_tool_failure("File content here") == False
    assert is_tool_failure("Complete") == False
    assert is_tool_failure("") == False

    print("✓ test_is_tool_failure passed")


def test_extract_learning_write_vs_edit():
    """Test that Write vs Edit pattern generates correct rule."""
    failed_attempt = {
        "tool": "Edit",
        "context": "Modify config file",
        "result": "Error: File not found",
        "success": False,
    }
    successful_attempt = {
        "tool": "Write",
        "context": "Create new file",
        "result": "Success",
        "success": True,
    }

    learning = extract_learning_from_pair(failed_attempt, successful_attempt)

    assert learning is not None
    assert "Write" in learning["successful_approach"]
    assert "implicit_rule" in learning
    assert "file may not exist" in learning["implicit_rule"].lower()

    print("✓ test_extract_learning_write_vs_edit passed")


def test_extract_learning_agent_vs_direct():
    """Test that Agent vs direct tools pattern generates correct rule."""
    failed_attempt = {
        "tool": "Grep",
        "context": "Search codebase",
        "result": "Error: Too many results, truncated",
        "success": False,
    }
    successful_attempt = {
        "tool": "Agent",
        "context": "Use code-explorer",
        "result": "Success",
        "success": True,
    }

    learning = extract_learning_from_pair(failed_attempt, successful_attempt)

    assert learning is not None
    assert "Agent" in learning["successful_approach"]
    assert "implicit_rule" in learning

    print("✓ test_extract_learning_agent_vs_direct passed")


def test_multiple_skills_in_signal():
    """Test that signals include relevant skills."""
    messages = [
        {
            "role": "assistant",
            "content": "I'll use Edit to modify the test",
            "tool_uses": [{"name": "Edit", "result": "Error: File not found"}],
        },
        {
            "role": "assistant",
            "content": "Let me try Write instead",
            "tool_uses": [{"name": "Write", "result": "Success"}],
        },
        {"role": "user", "content": "Good, continue"},
    ]

    signals = detect_implicit_patterns(messages, ["testing", "code"])

    assert len(signals) == 1
    signal = signals[0]

    # Should include both skills
    assert "testing" in signal["skills"]
    assert "code" in signal["skills"]

    print("✓ test_multiple_skills_in_signal passed")


def test_retry_without_explicit_approval():
    """Test retry pattern detection without explicit user approval."""
    messages = [
        {
            "role": "assistant",
            "content": "I'll use Edit to modify the file",
            "tool_uses": [{"name": "Edit", "result": "Error: File not found"}],
        },
        {
            "role": "assistant",
            "content": "Let me try Write instead",
            "tool_uses": [{"name": "Write", "result": "Success"}],
        },
        # No user response, but retry pattern exists
    ]

    signals = detect_implicit_patterns(messages, ["testing"])

    # Should still detect the retry pattern even without explicit approval
    assert len(signals) == 1
    assert signals[0]["has_implicit_approval"] == False

    print("✓ test_retry_without_explicit_approval passed")


def run_all_tests():
    """Run all unit tests."""
    tests = [
        test_retry_pattern_detection,
        test_tool_discovery_pattern,
        test_no_implicit_pattern_without_retry,
        test_is_tool_failure,
        test_extract_learning_write_vs_edit,
        test_extract_learning_agent_vs_direct,
        test_multiple_skills_in_signal,
        test_retry_without_explicit_approval,
    ]

    print(f"Running {len(tests)} tests for implicit pattern detection...\n")

    failed = []
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed.append(test.__name__)
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed.append(test.__name__)

    print(f"\n{'='*60}")
    if failed:
        print(f"FAILED: {len(failed)}/{len(tests)} tests failed")
        for name in failed:
            print(f"  - {name}")
        return 1
    else:
        print(f"SUCCESS: All {len(tests)} tests passed!")
        return 0


if __name__ == "__main__":
    sys.exit(run_all_tests())
