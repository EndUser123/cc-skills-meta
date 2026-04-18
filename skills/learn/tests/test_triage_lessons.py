#!/usr/bin/env python3
"""
Unit tests for triage lesson parsing in learn.py.

These tests verify that triage correction lessons are parsed correctly
and integrated with the CKS storage system.

Test Categories:
- Triage Lesson Parsing: Extract finding_id, corrected_triage, original_triage from text
- Category Mapping: Triage lessons map to "triage" category
- Scoring: Triage lessons receive appropriate scores based on context
- CKS Integration: Parsed lessons store correctly to CKS

All tests should FAIL initially (RED phase) - parse_triage_lesson() not implemented yet.

Run with: pytest P:/.claude/skills/learn/tests/test_triage_lessons.py -v
"""

import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))


def test_triage_lesson_parser_exists():
    """
    Test that parse_triage_lesson() function is defined.

    Given: learn.py module
    When: Importing and checking for parse_triage_lesson function
    Then: Should exist and be callable
    """
    from learn import parse_triage_lesson

    assert callable(parse_triage_lesson), "parse_triage_lesson should be a callable function"


def test_triage_lesson_parse_basic_format():
    """
    Test parsing of basic triage lesson format.

    Given: parse_triage_lesson() and lesson text "SEC-001 nit - fix_before_merge - User corrected"
    When: Parsing the lesson text
    Then: Should extract finding_id="SEC-001", corrected_triage="nit", original_triage="fix_before_merge"
    """
    from learn import parse_triage_lesson

    text = "SEC-001 nit - fix_before_merge - User corrected during review"
    result = parse_triage_lesson(text)

    assert result is not None, "Should parse triage lesson successfully"
    assert result.get("finding_id") == "SEC-001", "Should extract finding_id"
    assert result.get("corrected_triage") == "nit", "Should extract corrected_triage"
    assert result.get("original_triage") == "fix_before_merge", "Should extract original_triage"


def test_triage_lesson_parse_pre_existing():
    """
    Test parsing of pre-existing triage lesson.

    Given: parse_triage_lesson() and lesson text "QUAL-003 pre-existing - nit - False positive"
    When: Parsing the lesson text
    Then: Should extract finding_id, corrected_triage="pre-existing", original_triage="nit"
    """
    from learn import parse_triage_lesson

    text = "QUAL-003 pre-existing - nit - False positive, issue existed before"
    result = parse_triage_lesson(text)

    assert result is not None, "Should parse pre-existing lesson"
    assert result.get("finding_id") == "QUAL-003", "Should extract finding_id"
    assert result.get("corrected_triage") == "pre-existing", "Should extract corrected_triage"
    assert result.get("original_triage") == "nit", "Should extract original_triage"


def test_triage_lesson_parse_fix_before_merge():
    """
    Test parsing of fix_before_merge triage lesson.

    Given: parse_triage_lesson() and lesson text about critical bug
    When: Parsing the lesson text
    Then: Should extract finding_id, corrected_triage="fix_before_merge"
    """
    from learn import parse_triage_lesson

    text = "BUG-001 fix_before_merge - nit - Critical issue requiring immediate fix"
    result = parse_triage_lesson(text)

    assert result is not None, "Should parse fix_before_merge lesson"
    assert result.get("finding_id") == "BUG-001", "Should extract finding_id"
    assert result.get("corrected_triage") == "fix_before_merge", "Should extract corrected_triage"
    assert result.get("original_triage") == "nit", "Should extract original_triage"


def test_triage_lesson_category_mapping():
    """
    Test that triage lessons map to "triage" category.

    Given: parse_triage_lesson() that returns lesson data
    When: Checking the category field
    Then: Should return "triage" as the category
    """
    from learn import parse_triage_lesson

    text = "SEC-001 nit - fix_before_merge - User correction"
    result = parse_triage_lesson(text)

    assert result is not None, "Should parse triage lesson"
    assert result.get("category") == "triage", "Should map to 'triage' category"


def test_triage_lesson_scoring_high_confidence():
    """
    Test that explicit user corrections receive high scores.

    Given: parse_triage_lesson() and explicit user correction text
    When: Scoring the lesson
    Then: Should assign score >= 6 (high confidence)
    """
    from learn import parse_triage_lesson

    text = "SEC-001 nit - fix_before_merge - User explicitly corrected during review"
    result = parse_triage_lesson(text)

    assert result is not None, "Should parse triage lesson"
    score = result.get("score")
    assert score is not None, "Should include score"
    assert score >= 6, f"Explicit corrections should have high score (≥6), got {score}"


def test_triage_lesson_scoring_context_dependent():
    """
    Test that scores vary based on context confidence.

    Given: parse_triage_lesson() and varying context descriptions
    When: Scoring lessons with different confidence levels
    Then: Should assign appropriate scores based on context
    """
    from learn import parse_triage_lesson

    # High confidence: explicit correction
    high_conf_text = "SEC-001 nit - fix_before_merge - User corrected during adversarial review"
    high_conf_result = parse_triage_lesson(high_conf_text)
    high_score = high_conf_result.get("score")

    # Medium confidence: pattern observation
    med_conf_text = "SEC-001 nit - fix_before_merge - Pattern noticed in similar findings"
    med_conf_result = parse_triage_lesson(med_conf_text)
    med_score = med_conf_result.get("score")

    assert high_score >= med_score, f"High confidence ({high_score}) should be ≥ medium ({med_score})"


def test_triage_lesson_reject_invalid_format():
    """
    Test that invalid formats are rejected.

    Given: parse_triage_lesson() and non-triage lesson text
    When: Attempting to parse invalid formats
    Then: Should return None
    """
    from learn import parse_triage_lesson

    # Not a triage lesson format
    invalid_texts = [
        "This is a regular code lesson about refactoring",
        "nit - fix_before_merge - missing finding_id",  # Missing finding_id
        "SEC-001 - User feedback",  # Missing triage categories
        "",  # Empty string
    ]

    for text in invalid_texts:
        result = parse_triage_lesson(text)
        assert result is None, f"Should reject invalid format: '{text}'"


def test_triage_lesson_whitespace_tolerance():
    """
    Test that parser handles whitespace variations.

    Given: parse_triage_lesson() and text with variable whitespace
    When: Parsing lessons with extra spaces
    Then: Should parse correctly regardless of whitespace
    """
    from learn import parse_triage_lesson

    # Extra spaces around dashes
    text = "SEC-001  nit  -  fix_before_merge  -  User corrected"
    result = parse_triage_lesson(text)

    assert result is not None, "Should handle extra whitespace"
    assert result.get("finding_id") == "SEC-001", "Should extract finding_id with whitespace tolerance"


def test_triage_lesson_all_three_categories():
    """
    Test that all three triage categories are recognized.

    Given: parse_triage_lesson() and lessons for each category
    When: Parsing nit, fix_before_merge, and pre-existing lessons
    Then: Should correctly identify all three categories
    """
    from learn import parse_triage_lesson

    test_cases = [
        ("SEC-001 nit - fix_before_merge - context", "nit", "fix_before_merge"),
        ("BUG-002 fix_before_merge - pre-existing - context", "fix_before_merge", "pre-existing"),
        ("QUAL-003 pre-existing - nit - context", "pre-existing", "nit"),
    ]

    for text, expected_corrected, expected_original in test_cases:
        result = parse_triage_lesson(text)
        assert result is not None, f"Should parse: '{text}'"
        assert result.get("corrected_triage") == expected_corrected, f"Should extract corrected_triage as {expected_corrected}"
        assert result.get("original_triage") == expected_original, f"Should extract original_triage as {expected_original}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
