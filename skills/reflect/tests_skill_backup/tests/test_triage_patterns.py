#!/usr/bin/env python3
"""
Unit tests for triage correction pattern detection in extract_signals.py.

These tests verify that triage correction patterns capture user corrections
about finding triage classifications (Fix Before Merge / Nit / Pre-existing).

Test Categories:
- TRIAGE_CORRECTION_PATTERNS: User corrections of triage classifications
- ReDoS Protection: Catastrophic backtracking protection
- Triage Categories: fix_before_merge, nit, pre-existing

All tests should FAIL initially (RED phase) - patterns not implemented yet.

Run with: pytest P:/.claude/skills/reflect/tests/test_triage_patterns.py -v
"""

import re
import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))


def test_triage_correction_patterns_exist():
    """
    Test that TRIAGE_CORRECTION_PATTERNS constant is defined.

    Given: extract_signals.py module
    When: Importing and checking for TRIAGE_CORRECTION_PATTERNS
    Then: Should exist and be a non-empty list
    """
    from extract_signals import TRIAGE_CORRECTION_PATTERNS

    assert isinstance(
        TRIAGE_CORRECTION_PATTERNS, list
    ), "TRIAGE_CORRECTION_PATTERNS should be a list"
    assert (
        len(TRIAGE_CORRECTION_PATTERNS) >= 3
    ), "TRIAGE_CORRECTION_PATTERNS should have at least 3 patterns"


def test_triage_correction_positive_case_not_fix_before_merge_but_nit():
    """
    Test detection of "not fix_before_merge, actually nit" corrections.

    Given: TRIAGE_CORRECTION_PATTERNS and user says "SEC-001 is not fix_before_merge, it's a nit"
    When: Running regex pattern matching
    Then: Should detect the triage correction from fix_before_merge to nit
    """
    from extract_signals import TRIAGE_CORRECTION_PATTERNS

    text = "SEC-001 is not fix_before_merge, it's actually a nit"
    matched = False

    for pattern in TRIAGE_CORRECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            matched = True
            break

    assert matched, f"Should detect triage correction in: '{text}'"


def test_triage_correction_positive_case_pre_existing_not_nit():
    """
    Test detection of "pre-existing, not nit" corrections.

    Given: TRIAGE_CORRECTION_PATTERNS and user says "This is pre-existing, not a nit"
    When: Running regex pattern matching
    Then: Should detect the triage correction from nit to pre-existing
    """
    from extract_signals import TRIAGE_CORRECTION_PATTERNS

    text = "QUAL-003 is pre-existing, not a nit - the bug existed before this change"
    matched = False

    for pattern in TRIAGE_CORRECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            matched = True
            break

    assert matched, f"Should detect triage correction in: '{text}'"


def test_triage_correction_positive_case_should_be_fix_before_merge():
    """
    Test detection of "should be fix_before_merge" corrections.

    Given: TRIAGE_CORRECTION_PATTERNS and user says "This should be fix_before_merge, not pre-existing"
    When: Running regex pattern matching
    Then: Should detect the triage correction to fix_before_merge
    """
    from extract_signals import TRIAGE_CORRECTION_PATTERNS

    text = "BUG-001 should be fix_before_merge, not pre-existing - it's a critical issue"
    matched = False

    for pattern in TRIAGE_CORRECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            matched = True
            break

    assert matched, f"Should detect triage correction in: '{text}'"


def test_triage_correction_negative_case_regular_correction():
    """
    Test that triage patterns don't trigger on regular code corrections.

    Given: TRIAGE_CORRECTION_PATTERNS and user says "use dict instead of list"
    When: Running regex pattern matching
    Then: Should NOT match (this is not a triage correction)
    """
    from extract_signals import TRIAGE_CORRECTION_PATTERNS

    text = "Don't use list, use dict instead for better lookup performance"
    matched = False

    for pattern in TRIAGE_CORRECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            matched = True
            break

    assert not matched, f"Should NOT match regular code correction: '{text}'"


def test_triage_correction_negative_case_no_triage_keywords():
    """
    Test that triage patterns don't trigger without triage keywords.

    Given: TRIAGE_CORRECTION_PATTERNS and text without triage keywords
    When: Running regex pattern matching
    Then: Should NOT match
    """
    from extract_signals import TRIAGE_CORRECTION_PATTERNS

    text = "This is a simple code change that fixes a bug"
    matched = False

    for pattern in TRIAGE_CORRECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            matched = True
            break

    assert not matched, f"Should NOT match text without triage keywords: '{text}'"


def test_triage_correction_redos_protection_input_length():
    """
    Test ReDoS protection via input length validation.

    Given: TRIAGE_CORRECTION_PATTERNS with ReDoS protection
    When: Processing extremely long input (>1000 chars)
    Then: Should either reject input or complete quickly (<1 second)
    """
    import time

    from extract_signals import TRIAGE_CORRECTION_PATTERNS

    # Create malicious input with repeated pattern to trigger backtracking
    malicious_input = "SEC-001 is not " + "A" * 10000 + ", it's actually a nit"

    start_time = time.time()
    matched = False

    # Manual timeout protection: don't use re.TIMEOUT (not available in Python 3.14)
    for pattern in TRIAGE_CORRECTION_PATTERNS:
        # Check elapsed time manually before each pattern match
        if time.time() - start_time > 1.0:
            break  # Timeout protection
        try:
            if re.search(pattern, malicious_input, re.IGNORECASE):
                matched = True
        except Exception:
            # Any exception is acceptable - ReDoS protection working
            matched = False
            break

    elapsed_time = time.time() - start_time

    # Should either reject input or complete quickly
    assert elapsed_time < 2.0, f"ReDoS protection failed - took {elapsed_time:.2f}s (should be <2s)"


def test_triage_correction_redos_protection_nested_quantifiers():
    """
    Test ReDoS protection against nested quantifiers.

    Given: TRIAGE_CORRECTION_PATTERNS with ReDoS protection
    When: Processing input with nested quantifiers
    Then: Should complete quickly without catastrophic backtracking
    """
    import time

    from extract_signals import TRIAGE_CORRECTION_PATTERNS

    # Create input designed to trigger catastrophic backtracking
    malicious_input = (
        "SEC-001 is not " + "(((" * 100 + "fix_before_merge" + ")))" * 100 + ", it's nit"
    )

    start_time = time.time()
    matched = False

    # Manual timeout protection: don't use re.TIMEOUT (not available in Python 3.14)
    for pattern in TRIAGE_CORRECTION_PATTERNS:
        # Check elapsed time manually before each pattern match
        if time.time() - start_time > 1.0:
            break  # Timeout protection
        try:
            if re.search(pattern, malicious_input, re.IGNORECASE):
                matched = True
        except Exception:
            # Any exception is acceptable - ReDoS protection working
            matched = False
            break

    elapsed_time = time.time() - start_time

    # Should complete quickly or timeout
    assert elapsed_time < 2.0, f"ReDoS protection failed - took {elapsed_time:.2f}s (should be <2s)"


def test_triage_correction_extract_groups():
    """
    Test that triage patterns extract finding_id and corrected_triage.

    Given: TRIAGE_CORRECTION_PATTERNS with capture groups
    When: Matching triage correction text
    Then: Should extract finding_id and corrected_triage from match groups
    """
    from extract_signals import TRIAGE_CORRECTION_PATTERNS

    text = "SEC-001 is not fix_before_merge, it's actually a nit"

    finding_id = None
    corrected_triage = None

    for pattern in TRIAGE_CORRECTION_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match and match.groups():
            # Extract finding_id (first group) and corrected_triage (second group)
            if len(match.groups()) >= 2:
                finding_id = match.group(1)
                corrected_triage = match.group(2)
                break

    assert finding_id is not None, "Should extract finding_id from match"
    assert corrected_triage is not None, "Should extract corrected_triage from match"
    assert (
        "SEC" in finding_id or "nit" in corrected_triage.lower()
    ), f"Unexpected extraction: finding_id={finding_id}, triage={corrected_triage}"


def test_triage_correction_all_triage_categories():
    """
    Test that patterns detect all three triage categories.

    Given: TRIAGE_CORRECTION_PATTERNS
    When: Testing against fix_before_merge, nit, and pre-existing
    Then: Should detect corrections for all three categories
    """
    from extract_signals import TRIAGE_CORRECTION_PATTERNS

    test_cases = [
        ("SEC-001 should be fix_before_merge, not nit", "fix_before_merge"),
        ("BUG-002 is actually a nit, not fix_before_merge", "nit"),
        ("QUAL-003 is pre-existing, not nit", "pre-existing"),
    ]

    detected_categories = set()

    for text, expected_category in test_cases:
        for pattern in TRIAGE_CORRECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                detected_categories.add(expected_category)
                break

    assert (
        len(detected_categories) == 3
    ), f"Should detect all triage categories, detected: {detected_categories}"


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
