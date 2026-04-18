#!/usr/bin/env python3
"""
Unit tests for technical pattern detection in extract_signals.py.

These tests verify that new technical pattern categories capture
implementation learnings that are missed by conversational-only patterns.

Test Categories:
- IMPLEMENTATION_PATTERNS: Code-level fixes with specific mechanisms
- ARCHITECTURE_PATTERNS: Structural/system-level learnings
- TEST_PATTERNS: Testing insights and validation
- DOCUMENTATION_PATTERNS: Documentation-driven learnings

All tests should FAIL initially (RED phase) - patterns not implemented yet.

Run with: pytest P:/.claude/skills/reflect/tests/test_extract_signals_technical.py -v
"""

import re
import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))


def test_implementation_pattern_constants_exist():
    """
    Test that IMPLEMENTATION_PATTERNS constant is defined.

    Given: extract_signals.py module
    When: Importing and checking for IMPLEMENTATION_PATTERNS
    Then: Should exist and be a non-empty list
    """
    from extract_signals import IMPLEMENTATION_PATTERNS

    assert isinstance(IMPLEMENTATION_PATTERNS, list), "IMPLEMENTATION_PATTERNS should be a list"
    assert len(IMPLEMENTATION_PATTERNS) >= 1, "IMPLEMENTATION_PATTERNS should not be empty"


def test_architecture_pattern_constants_exist():
    """
    Test that ARCHITECTURE_PATTERNS constant is defined.

    Given: extract_signals.py module
    When: Importing and checking for ARCHITECTURE_PATTERNS
    Then: Should exist and be a non-empty list
    """
    from extract_signals import ARCHITECTURE_PATTERNS

    assert isinstance(ARCHITECTURE_PATTERNS, list), "ARCHITECTURE_PATTERNS should be a list"
    assert len(ARCHITECTURE_PATTERNS) >= 1, "ARCHITECTURE_PATTERNS should not be empty"


def test_test_pattern_constants_exist():
    """
    Test that TEST_PATTERNS constant is defined.

    Given: extract_signals.py module
    When: Importing and checking for TEST_PATTERNS
    Then: Should exist and be a non-empty list
    """
    from extract_signals import TEST_PATTERNS

    assert isinstance(TEST_PATTERNS, list), "TEST_PATTERNS should be a list"
    assert len(TEST_PATTERNS) >= 1, "TEST_PATTERNS should not be empty"


def test_documentation_pattern_constants_exist():
    """
    Test that DOCUMENTATION_PATTERNS constant is defined.

    Given: extract_signals.py module
    When: Importing and checking for DOCUMENTATION_PATTERNS
    Then: Should exist and be a non-empty list
    """
    from extract_signals import DOCUMENTATION_PATTERNS

    assert isinstance(DOCUMENTATION_PATTERNS, list), "DOCUMENTATION_PATTERNS should be a list"
    assert len(DOCUMENTATION_PATTERNS) >= 1, "DOCUMENTATION_PATTERNS should not be empty"


def test_implementation_pattern_positive_simple_override():
    """
    Test that IMPLEMENTATION_PATTERNS detect simple keyword override fixes.

    Given: IMPLEMENTATION_PATTERNS and text "simple keyword override fixed false positives"
    When: Running regex pattern matching
    Then: Should match at least one IMPLEMENTATION pattern
    """
    from extract_signals import IMPLEMENTATION_PATTERNS

    text = "Simple keyword override fixed false positives in search results"
    matched = False

    for pattern in IMPLEMENTATION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            matched = True
            break

    assert matched, f"IMPLEMENTATION_PATTERNS should match '{text}'"


def test_implementation_pattern_positive_lines_eliminated():
    """
    Test that IMPLEMENTATION_PATTERNS detect code elimination successes.

    Given: IMPLEMENTATION_PATTERNS and text "9 lines of code eliminated bugs"
    When: Running regex pattern matching
    Then: Should match at least one IMPLEMENTATION pattern
    """
    from extract_signals import IMPLEMENTATION_PATTERNS

    text = "9 lines of code eliminated bugs in the edge case handling"
    matched = False

    for pattern in IMPLEMENTATION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            matched = True
            break

    assert matched, f"IMPLEMENTATION_PATTERNS should match '{text}'"


def test_implementation_pattern_negative_too_vague():
    """
    Test that IMPLEMENTATION_PATTERNS reject vague changes.

    Given: IMPLEMENTATION_PATTERNS and text "simple code change"
    When: Running regex pattern matching
    Then: Should NOT match any IMPLEMENTATION pattern
    """
    from extract_signals import IMPLEMENTATION_PATTERNS

    text = "simple code change"
    matched = False

    for pattern in IMPLEMENTATION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            matched = True
            break

    assert not matched, f"IMPLEMENTATION_PATTERNS should NOT match vague text '{text}'"


def test_implementation_pattern_negative_no_outcome():
    """
    Test that IMPLEMENTATION_PATTERNS reject changes without outcomes.

    Given: IMPLEMENTATION_PATTERNS and text "wrote some code"
    When: Running regex pattern matching
    Then: Should NOT match any IMPLEMENTATION pattern
    """
    from extract_signals import IMPLEMENTATION_PATTERNS

    text = "wrote some code"
    matched = False

    for pattern in IMPLEMENTATION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            matched = True
            break

    assert not matched, f"IMPLEMENTATION_PATTERNS should NOT match text without outcome '{text}'"


def test_architecture_pattern_positive_repo_indicator():
    """
    Test that ARCHITECTURE_PATTERNS detect repo-level learnings.

    Given: ARCHITECTURE_PATTERNS and text "repo indicator overrides code keywords"
    When: Running regex pattern matching
    Then: Should match at least one ARCHITECTURE pattern
    """
    from extract_signals import ARCHITECTURE_PATTERNS

    text = "repo indicator overrides code keywords in search routing"
    matched = False

    for pattern in ARCHITECTURE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            matched = True
            break

    assert matched, f"ARCHITECTURE_PATTERNS should match '{text}'"


def test_architecture_pattern_positive_phrase_context():
    """
    Test that ARCHITECTURE_PATTERNS detect phrase-level context patterns.

    Given: ARCHITECTURE_PATTERNS and text "phrase-level context detection worked"
    When: Running regex pattern matching
    Then: Should match at least one ARCHITECTURE pattern
    """
    from extract_signals import ARCHITECTURE_PATTERNS

    text = "phrase-level context detection worked perfectly for disambiguation"
    matched = False

    for pattern in ARCHITECTURE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            matched = True
            break

    assert matched, f"ARCHITECTURE_PATTERNS should match '{text}'"


def test_architecture_pattern_negative_too_generic():
    """
    Test that ARCHITECTURE_PATTERNS reject generic architecture terms.

    Given: ARCHITECTURE_PATTERNS and text "code architecture"
    When: Running regex pattern matching
    Then: Should NOT match any ARCHITECTURE pattern
    """
    from extract_signals import ARCHITECTURE_PATTERNS

    text = "code architecture"
    matched = False

    for pattern in ARCHITECTURE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            matched = True
            break

    assert not matched, f"ARCHITECTURE_PATTERNS should NOT match generic term '{text}'"


def test_test_pattern_positive_regression_caught():
    """
    Test that TEST_PATTERNS detect regression catching.

    Given: TEST_PATTERNS and text "all tests passing, test caught regression"
    When: Running regex pattern matching
    Then: Should match at least one TEST pattern
    """
    from extract_signals import TEST_PATTERNS

    text = "all tests passing, test caught regression in the parser"
    matched = False

    for pattern in TEST_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            matched = True
            break

    assert matched, f"TEST_PATTERNS should match '{text}'"


def test_test_pattern_positive_pytest_revealed():
    """
    Test that TEST_PATTERNS detect pytest insights.

    Given: TEST_PATTERNS and text "pytest revealed edge case"
    When: Running regex pattern matching
    Then: Should match at least one TEST pattern
    """
    from extract_signals import TEST_PATTERNS

    text = "pytest revealed edge case in validation logic"
    matched = False

    for pattern in TEST_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            matched = True
            break

    assert matched, f"TEST_PATTERNS should match '{text}'"


def test_test_pattern_negative_too_generic():
    """
    Test that TEST_PATTERNS reject generic test mentions.

    Given: TEST_PATTERNS and text "tests"
    When: Running regex pattern matching
    Then: Should NOT match any TEST pattern
    """
    from extract_signals import TEST_PATTERNS

    text = "tests"
    matched = False

    for pattern in TEST_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            matched = True
            break

    assert not matched, f"TEST_PATTERNS should NOT match generic mention '{text}'"


def test_documentation_pattern_positive_validation_prevented():
    """
    Test that DOCUMENTATION_PATTERNS detect documentation preventing bugs.

    Given: DOCUMENTATION_PATTERNS and text "pattern validation documentation prevented bugs"
    When: Running regex pattern matching
    Then: Should match at least one DOCUMENTATION pattern
    """
    from extract_signals import DOCUMENTATION_PATTERNS

    text = "pattern validation documentation prevented bugs in production"
    matched = False

    for pattern in DOCUMENTATION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            matched = True
            break

    assert matched, f"DOCUMENTATION_PATTERNS should match '{text}'"


def test_documentation_pattern_positive_skill_updated():
    """
    Test that DOCUMENTATION_PATTERNS detect SKILL.md updates.

    Given: DOCUMENTATION_PATTERNS and text "SKILL.md updated with lessons"
    When: Running regex pattern matching
    Then: Should match at least one DOCUMENTATION pattern
    """
    from extract_signals import DOCUMENTATION_PATTERNS

    text = "SKILL.md updated with lessons from this session"
    matched = False

    for pattern in DOCUMENTATION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            matched = True
            break

    assert matched, f"DOCUMENTATION_PATTERNS should match '{text}'"


def test_documentation_pattern_negative_too_vague():
    """
    Test that DOCUMENTATION_PATTERNS reject vague doc updates.

    Given: DOCUMENTATION_PATTERNS and text "updated docs"
    When: Running regex pattern matching
    Then: Should NOT match any DOCUMENTATION pattern
    """
    from extract_signals import DOCUMENTATION_PATTERNS

    text = "updated docs"
    matched = False

    for pattern in DOCUMENTATION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            matched = True
            break

    assert not matched, f"DOCUMENTATION_PATTERNS should NOT match vague update '{text}'"


def test_backward_compatibility_correction_still_works():
    """
    Test that existing CORRECTION_PATTERNS still work after adding technical patterns.

    Given: CORRECTION_PATTERNS and text "no, don't use X, use Y"
    When: Running regex pattern matching
    Then: Should match at least one CORRECTION pattern (backward compatibility)
    """
    from extract_signals import CORRECTION_PATTERNS

    text = "no, don't use grep, use Agent instead"
    matched = False

    for pattern in CORRECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            matched = True
            break

    assert (
        matched
    ), f"CORRECTION_PATTERNS should still work (backward compatibility), failed to match '{text}'"


def test_backward_compatibility_approval_still_works():
    """
    Test that existing APPROVAL_PATTERNS still work.

    Given: APPROVAL_PATTERNS and text "yes, that's perfect"
    When: Running regex pattern matching
    Then: Should match at least one APPROVAL pattern (backward compatibility)
    """
    from extract_signals import APPROVAL_PATTERNS

    text = "yes, that's perfect"
    matched = False

    for pattern in APPROVAL_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            matched = True
            break

    assert (
        matched
    ), f"APPROVAL_PATTERNS should still work (backward compatibility), failed to match '{text}'"


def test_backward_compatibility_question_still_works():
    """
    Test that existing QUESTION_PATTERNS still work.

    Given: QUESTION_PATTERNS and text "have you considered X"
    When: Running regex pattern matching
    Then: Should match at least one QUESTION pattern (backward compatibility)
    """
    from extract_signals import QUESTION_PATTERNS

    text = "have you considered using pytest instead"
    matched = False

    for pattern in QUESTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            matched = True
            break

    assert (
        matched
    ), f"QUESTION_PATTERNS should still work (backward compatibility), failed to match '{text}'"


if __name__ == "__main__":
    import pytest

    sys.exit(pytest.main([__file__, "-v"]))


# =============================================================================
# Negative Pattern Tests (False Positive Prevention)
# =============================================================================


def test_negative_pattern_constants_exist():
    """
    Test that NEGATIVE_PATTERNS constant is defined.

    Given: extract_signals.py module
    When: Importing and checking for NEGATIVE_PATTERNS
    Then: Should exist and be a non-empty list
    """
    from extract_signals import NEGATIVE_PATTERNS

    assert isinstance(NEGATIVE_PATTERNS, list), "NEGATIVE_PATTERNS should be a list"
    assert len(NEGATIVE_PATTERNS) >= 1, "NEGATIVE_PATTERNS should not be empty"


def test_negative_pattern_filters_simple_code_change():
    """
    Test that NEGATIVE_PATTERNS filter out "simple code change".

    Given: NEGATIVE_PATTERNS and text "simple code change"
    When: Running regex pattern matching
    Then: Should match negative pattern (filter out)
    """
    from extract_signals import NEGATIVE_PATTERNS

    text = "simple code change"
    matched = False

    for pattern in NEGATIVE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            matched = True
            break

    assert matched, f"NEGATIVE_PATTERNS should filter out '{text}'"


def test_negative_pattern_filters_wrote_some_code():
    """
    Test that NEGATIVE_PATTERNS filter out "wrote some code".

    Given: NEGATIVE_PATTERNS and text "wrote some code"
    When: Running regex pattern matching
    Then: Should match negative pattern (filter out)
    """
    from extract_signals import NEGATIVE_PATTERNS

    text = "wrote some code"
    matched = False

    for pattern in NEGATIVE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            matched = True
            break

    assert matched, f"NEGATIVE_PATTERNS should filter out '{text}'"


def test_negative_pattern_filters_fixed_bug_without_mechanism():
    """
    Test that NEGATIVE_PATTERNS filter out "fixed bug" (no mechanism).

    Given: NEGATIVE_PATTERNS and text "fixed bug"
    When: Running regex pattern matching
    Then: Should match negative pattern (filter out)
    """
    from extract_signals import NEGATIVE_PATTERNS

    text = "fixed bug"
    matched = False

    for pattern in NEGATIVE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            matched = True
            break

    assert matched, f"NEGATIVE_PATTERNS should filter out generic '{text}'"


def test_negative_pattern_allows_specific_fix():
    """
    Test that NEGATIVE_PATTERNS allow specific fixes through.

    Given: NEGATIVE_PATTERNS and text "simple keyword override fixed false positives"
    When: Running regex pattern matching
    Then: Should NOT match negative patterns (allow through)
    """
    from extract_signals import NEGATIVE_PATTERNS

    text = "simple keyword override fixed false positives"
    matched = False

    for pattern in NEGATIVE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            matched = True
            break

    assert not matched, f"NEGATIVE_PATTERNS should NOT filter specific fix '{text}'"


# =============================================================================
# Feature Flag Tests
# =============================================================================


def test_feature_flags_constants_exist():
    """
    Test that FEATURE_FLAGS constant is defined.

    Given: extract_signals.py module
    When: Importing and checking for FEATURE_FLAGS
    Then: Should exist as a dict with all 4 categories
    """
    from extract_signals import FEATURE_FLAGS

    assert isinstance(FEATURE_FLAGS, dict), "FEATURE_FLAGS should be a dict"
    assert "implementation" in FEATURE_FLAGS, "FEATURE_FLAGS should have 'implementation' key"
    assert "architecture" in FEATURE_FLAGS, "FEATURE_FLAGS should have 'architecture' key"
    assert "test" in FEATURE_FLAGS, "FEATURE_FLAGS should have 'test' key"
    assert "documentation" in FEATURE_FLAGS, "FEATURE_FLAGS should have 'documentation' key"


def test_feature_flags_all_enabled_by_default():
    """
    Test that all feature flags are enabled by default.

    Given: FEATURE_FLAGS constant
    When: Checking values
    Then: All should be True (enabled by default)
    """
    from extract_signals import FEATURE_FLAGS

    assert (
        FEATURE_FLAGS.get("implementation") is True
    ), "implementation should be enabled by default"
    assert FEATURE_FLAGS.get("architecture") is True, "architecture should be enabled by default"
    assert FEATURE_FLAGS.get("test") is True, "test should be enabled by default"
    assert FEATURE_FLAGS.get("documentation") is True, "documentation should be enabled by default"
