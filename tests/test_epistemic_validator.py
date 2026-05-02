"""Tests for epistemic_validator.py."""

import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).parent.parent / "hooks"
LIB_DIR = HOOKS_DIR / "__lib"
sys.path.insert(0, str(LIB_DIR))

from epistemic_validator import (  # type: ignore
    EpistemicIssue,
    EpistemicConfig,
    validate_missing_direct_answer,
    validate_non_english_output,
    run_all_checks,
    is_concrete_question,
    has_direct_answer,
    is_substantially_non_english,
    is_repairable,
    build_repair_prompt,
)


def test_concrete_question_detection() -> None:
    """Test that concrete questions are detected."""

    assert is_concrete_question("Does /reason create output?") is True
    assert is_concrete_question("Is this working?") is True
    assert is_concrete_question("Can you help?") is True
    assert is_concrete_question("Should I do this?") is True
    assert is_concrete_question("What is this?") is True
    assert is_concrete_question("Why does this happen?") is True
    assert is_concrete_question("Brainstorm approaches to X") is False
    assert is_concrete_question("Help me with Y") is False


def test_has_direct_answer() -> None:
    """Test that direct answers are detected."""

    # Clear yes/no answers
    assert has_direct_answer("Yes, /reason creates output.") is True
    assert has_direct_answer("No, it does not.") is True
    assert has_direct_answer("Probably yes.") is True

    # Direct answer pattern
    assert has_direct_answer("Direct answer: Yes, it does.") is True
    assert has_direct_answer("The answer is: it works.") is True

    # No direct answer
    assert has_direct_answer("[FACT]\n- something here") is False
    assert has_direct_answer("Let me think about this.") is False


def test_missing_direct_answer_detected() -> None:
    """Test that missing direct answer is flagged."""

    user_input = "Does /reason create output?"
    response = """
[FACT]
- /reason has output (source: SKILL.md)

[RECOMMENDATION]
- Use /reason for analysis
"""

    config = EpistemicConfig()
    issue = validate_missing_direct_answer(user_input, response, config)

    assert issue is not None
    assert issue.type == "missing_direct_answer"
    assert issue.section == "__GLOBAL__"
    assert "Direct answer" in issue.message


def test_missing_direct_answer_not_flagged_when_present() -> None:
    """Test that direct answer prevents the issue."""

    user_input = "Does /reason create output?"
    response = """Direct answer: Yes, /reason creates output at least as useful as /reason_openai.

[FACT]
- /reason is a superset (source: analysis)
"""

    config = EpistemicConfig()
    issue = validate_missing_direct_answer(user_input, response, config)

    assert issue is None


def test_missing_direct_answer_not_triggered_for_non_concrete() -> None:
    """Test that non-concrete prompts don't trigger the check."""

    user_input = "Brainstorm approaches to improve /reason"
    response = """
[RECOMMENDATION]
- Add more features
"""

    config = EpistemicConfig()
    issue = validate_missing_direct_answer(user_input, response, config)

    assert issue is None


def test_run_all_checks() -> None:
    """Test the main check runner."""

    # Concrete question, no direct answer
    user_input = "Is this working?"
    response = "[FACT]\n- some fact"

    config = EpistemicConfig()
    issues = run_all_checks(user_input, response, config)

    assert len(issues) >= 1
    assert any(i.type == "missing_direct_answer" for i in issues)


def test_config_treat_as_ignore() -> None:
    """Test that ignore config skips the check."""

    user_input = "Does it work?"
    response = "Some response without direct answer"

    config = EpistemicConfig(treat_missing_direct_answer_as="ignore")
    issues = run_all_checks(user_input, response, config)

    assert len(issues) == 0


if __name__ == "__main__":
    test_concrete_question_detection()
    print("PASS: test_concrete_question_detection")

    test_has_direct_answer()
    print("PASS: test_has_direct_answer")

    test_missing_direct_answer_detected()
    print("PASS: test_missing_direct_answer_detected")

    test_missing_direct_answer_not_flagged_when_present()
    print("PASS: test_missing_direct_answer_not_flagged_when_present")

    test_missing_direct_answer_not_triggered_for_non_concrete()
    print("PASS: test_missing_direct_answer_not_triggered_for_non_concrete")

    test_run_all_checks()
    print("PASS: test_run_all_checks")

    test_config_treat_as_ignore()
    print("PASS: test_config_treat_as_ignore")

    print("\nAll tests passed!")


# ---------------------------------------------------------------------------
# non_english_output tests
# ---------------------------------------------------------------------------


def test_cjk_response_detected() -> None:
    """Substantial CJK text triggers non-English detection."""
    response = "这是一个用中文写的回复。它包含了很多中文字符，这些不是英文内容。"
    assert is_substantially_non_english(response) is True


def test_cyrillic_response_detected() -> None:
    """Substantial Cyrillic text triggers non-English detection."""
    response = "Это ответ на русском языке. Он содержит много русских слов и предложений."
    assert is_substantially_non_english(response) is True


def test_english_response_not_flagged() -> None:
    """Pure English response is not flagged."""
    response = "This is a normal English response. It contains only English words and standard punctuation."
    assert is_substantially_non_english(response) is False


def test_code_with_english_not_flagged() -> None:
    """English response with code blocks is not flagged."""
    response = "Here is the solution:\n```python\ndef foo():\n    return 'bar'\n```\nThis should work."
    assert is_substantially_non_english(response) is False


def test_mixed_code_with_cjk_flagged() -> None:
    """Response with code but substantial CJK prose is flagged."""
    response = "这是解决方案：\n```python\ndef foo():\n    return 'bar'\n```\n这个代码可以正常工作，没有问题。"
    assert is_substantially_non_english(response) is True


def test_non_english_output_validator_issues_warning() -> None:
    """validate_non_english_output returns issue for non-English in english session."""
    response = "这是一个用中文写的回复。它包含了很多中文字符。"
    config = EpistemicConfig(session_language="english")
    issue = validate_non_english_output(response, config)
    assert issue is not None
    assert issue.type == "non_english_output"
    assert issue.section == "__GLOBAL__"


def test_non_english_output_skipped_for_non_english_session() -> None:
    """No issue when session language is not english."""
    response = "这是一个用中文写的回复。它包含了很多中文字符。"
    config = EpistemicConfig(session_language="chinese")
    issue = validate_non_english_output(response, config)
    assert issue is None


def test_non_english_output_skipped_when_ignored() -> None:
    """No issue when treat_non_english_output_as is 'ignore'."""
    response = "这是一个用中文写的回复。它包含了很多中文字符。"
    config = EpistemicConfig(treat_non_english_output_as="ignore")
    issue = validate_non_english_output(response, config)
    assert issue is None


def test_empty_response_not_flagged() -> None:
    """Empty or whitespace-only response is not flagged."""
    assert is_substantially_non_english("") is False
    assert is_substantially_non_english("   ") is False


# ---------------------------------------------------------------------------
# Repair path tests
# ---------------------------------------------------------------------------


def test_repairable_with_only_language_and_direct_answer() -> None:
    """Issues that are only non_english_output and/or missing_direct_answer are repairable."""
    issues = [
        EpistemicIssue(type="non_english_output", section="__GLOBAL__", bullet_index=-1, message=""),
        EpistemicIssue(type="missing_direct_answer", section="__GLOBAL__", bullet_index=-1, message=""),
    ]
    assert is_repairable(issues) is True


def test_not_repairable_with_other_issue_types() -> None:
    """Mixed issues with non-repairable types are not repairable."""
    issues = [
        EpistemicIssue(type="non_english_output", section="__GLOBAL__", bullet_index=-1, message=""),
        EpistemicIssue(type="unsupported_fact", section="[FACT]", bullet_index=0, message=""),
    ]
    assert is_repairable(issues) is False


def test_not_repairable_with_empty_issues() -> None:
    """Empty issue list is not repairable."""
    assert is_repairable([]) is False


def test_build_repair_prompt_returns_content() -> None:
    """Repair prompt includes instructions and reasons."""
    issues = [
        EpistemicIssue(type="non_english_output", section="__GLOBAL__", bullet_index=-1, message=""),
        EpistemicIssue(type="missing_direct_answer", section="__GLOBAL__", bullet_index=-1, message=""),
    ]
    prompt = build_repair_prompt(issues)
    assert prompt is not None
    assert "REPAIR INSTRUCTIONS" in prompt
    assert "English" in prompt
    assert "first sentence" in prompt


def test_build_repair_prompt_returns_none_for_mixed() -> None:
    """Repair prompt returns None for non-repairable issues."""
    issues = [
        EpistemicIssue(type="unsupported_fact", section="[FACT]", bullet_index=0, message=""),
    ]
    assert build_repair_prompt(issues) is None


def test_build_repair_prompt_single_issue() -> None:
    """Repair prompt works with a single repairable issue type."""
    issues = [
        EpistemicIssue(type="non_english_output", section="__GLOBAL__", bullet_index=-1, message=""),
    ]
    prompt = build_repair_prompt(issues)
    assert prompt is not None
    assert "non-English" in prompt


# ---------------------------------------------------------------------------
# run_all_checks integration with non_english_output
# ---------------------------------------------------------------------------


def test_run_all_checks_detects_non_english() -> None:
    """run_all_checks catches non-English output."""
    user_input = "What does this code do?"
    response = "这段代码实现了一个简单的功能。它返回一个字符串。"
    config = EpistemicConfig(session_language="english")
    issues = run_all_checks(user_input, response, config)
    assert any(i.type == "non_english_output" for i in issues)


def test_run_all_checks_detects_both_issues() -> None:
    """run_all_checks catches both missing_direct_answer and non_english_output."""
    user_input = "Is this working?"
    response = "这是一个中文回复，没有直接回答。"
    config = EpistemicConfig(session_language="english")
    issues = run_all_checks(user_input, response, config)
    types = {i.type for i in issues}
    assert "non_english_output" in types
    assert "missing_direct_answer" in types
