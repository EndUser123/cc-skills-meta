#!/usr/bin/env python3
"""
Unit tests for CKS schema mapping functionality.

Tests the classification of /reflect signal categories into /r finding types
(PATTERN, REFACTOR, DEBT, DOC, OPT) with appropriate severity weights and
confidence levels.

This module tests the RED phase - implementation does NOT exist yet.
All tests MUST fail initially.

Run with: pytest P:/.claude/skills/reflect/tests/test_cks_schema_mapper.py -v
"""

import sys
from pathlib import Path

# Add scripts directory to path for imports (will fail - module doesn't exist yet)
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

# Import the module - will fail in RED phase, succeed in GREEN phase
from scripts.cks_schema_mapper import (
    ConfidenceLevel,
    FindingType,
    classify_finding_type,
)


def test_classify_finding_type_optimization():
    """
    Test that optimization/performance categories map to OPT finding type.

    Given: A category string containing "optimization" or "performance"
    When: classify_finding_type() is called
    Then: Returns FindingType.OPT with severity_weight 0.6 and HIGH confidence
    """
    # Arrange
    category = "optimization"

    # Act
    result = classify_finding_type(category)

    # Assert
    assert (
        result.finding_type == FindingType.OPT
    ), f"Expected FindingType.OPT, got {result.finding_type}"
    assert (
        result.severity_weight == 0.6
    ), f"Expected severity_weight 0.6, got {result.severity_weight}"
    assert (
        result.category_confidence == ConfidenceLevel.HIGH
    ), f"Expected HIGH confidence, got {result.category_confidence}"

    print("✓ test_classify_finding_type_optimization passed")


def test_classify_finding_type_performance():
    """
    Test that performance category also maps to OPT finding type.

    Given: A category string containing "performance"
    When: classify_finding_type() is called
    Then: Returns FindingType.OPT with severity_weight 0.6 and HIGH confidence
    """
    # Arrange
    category = "performance"

    # Act
    result = classify_finding_type(category)

    # Assert
    assert (
        result.finding_type == FindingType.OPT
    ), f"Expected FindingType.OPT, got {result.finding_type}"
    assert (
        result.severity_weight == 0.6
    ), f"Expected severity_weight 0.6, got {result.severity_weight}"
    assert (
        result.category_confidence == ConfidenceLevel.HIGH
    ), f"Expected HIGH confidence, got {result.category_confidence}"

    print("✓ test_classify_finding_type_performance passed")


def test_classify_finding_type_pattern():
    """
    Test that forgotten/TODO/omission categories map to PATTERN finding type.

    Given: A category string containing "forgotten", "TODO", or "omission"
    When: classify_finding_type() is called
    Then: Returns FindingType.PATTERN with severity_weight 0.7 and HIGH confidence
    """
    # Arrange
    category = "forgotten"

    # Act
    result = classify_finding_type(category)

    # Assert
    assert (
        result.finding_type == FindingType.PATTERN
    ), f"Expected FindingType.PATTERN, got {result.finding_type}"
    assert (
        result.severity_weight == 0.7
    ), f"Expected severity_weight 0.7, got {result.severity_weight}"
    assert (
        result.category_confidence == ConfidenceLevel.HIGH
    ), f"Expected HIGH confidence, got {result.category_confidence}"

    print("✓ test_classify_finding_type_pattern passed")


def test_classify_finding_type_refactor():
    """
    Test that code quality/cleanup/refactor categories map to REFACTOR finding type.

    Given: A category string containing "code quality", "cleanup", or "refactor"
    When: classify_finding_type() is called
    Then: Returns FindingType.REFACTOR with severity_weight 0.5 and MEDIUM confidence
    """
    # Arrange
    category = "code quality"

    # Act
    result = classify_finding_type(category)

    # Assert
    assert (
        result.finding_type == FindingType.REFACTOR
    ), f"Expected FindingType.REFACTOR, got {result.finding_type}"
    assert (
        result.severity_weight == 0.5
    ), f"Expected severity_weight 0.5, got {result.severity_weight}"
    assert (
        result.category_confidence == ConfidenceLevel.MEDIUM
    ), f"Expected MEDIUM confidence, got {result.category_confidence}"

    print("✓ test_classify_finding_type_refactor passed")


def test_classify_finding_type_debt():
    """
    Test that violation/compliance/technical debt categories map to DEBT finding type.

    Given: A category string containing "violation", "compliance", or "technical debt"
    When: classify_finding_type() is called
    Then: Returns FindingType.DEBT with severity_weight 0.8 and HIGH confidence
    """
    # Arrange
    category = "violation"

    # Act
    result = classify_finding_type(category)

    # Assert
    assert (
        result.finding_type == FindingType.DEBT
    ), f"Expected FindingType.DEBT, got {result.finding_type}"
    assert (
        result.severity_weight == 0.8
    ), f"Expected severity_weight 0.8, got {result.severity_weight}"
    assert (
        result.category_confidence == ConfidenceLevel.HIGH
    ), f"Expected HIGH confidence, got {result.category_confidence}"

    print("✓ test_classify_finding_type_debt passed")


def test_classify_finding_type_doc():
    """
    Test that documentation/doc/readme categories map to DOC finding type.

    Given: A category string containing "documentation", "doc", or "readme"
    When: classify_finding_type() is called
    Then: Returns FindingType.DOC with severity_weight 0.4 and MEDIUM confidence
    """
    # Arrange
    category = "documentation"

    # Act
    result = classify_finding_type(category)

    # Assert
    assert (
        result.finding_type == FindingType.DOC
    ), f"Expected FindingType.DOC, got {result.finding_type}"
    assert (
        result.severity_weight == 0.4
    ), f"Expected severity_weight 0.4, got {result.severity_weight}"
    assert (
        result.category_confidence == ConfidenceLevel.MEDIUM
    ), f"Expected MEDIUM confidence, got {result.category_confidence}"

    print("✓ test_classify_finding_type_doc passed")


def test_classify_finding_type_unknown_defaults_to_pattern():
    """
    Test that unknown categories default to PATTERN finding type with LOW confidence.

    Given: A category string that doesn't match any known pattern
    When: classify_finding_type() is called
    Then: Returns FindingType.PATTERN with severity_weight 0.7, LOW confidence, and warning logged
    """
    # Arrange
    category = "unknown"

    # Act
    result = classify_finding_type(category)

    # Assert
    assert (
        result.finding_type == FindingType.PATTERN
    ), f"Expected FindingType.PATTERN as default, got {result.finding_type}"
    assert (
        result.severity_weight == 0.7
    ), f"Expected severity_weight 0.7, got {result.severity_weight}"
    assert (
        result.category_confidence == ConfidenceLevel.LOW
    ), f"Expected LOW confidence for unknown category, got {result.category_confidence}"
    # Note: Warning logging should happen but can't be tested in unit test without capture

    print("✓ test_classify_finding_type_unknown_defaults_to_pattern passed")


def run_all_tests():
    """Run all unit tests and report results."""
    tests = [
        test_classify_finding_type_optimization,
        test_classify_finding_type_performance,
        test_classify_finding_type_pattern,
        test_classify_finding_type_refactor,
        test_classify_finding_type_debt,
        test_classify_finding_type_doc,
        test_classify_finding_type_unknown_defaults_to_pattern,
    ]

    print(f"Running {len(tests)} tests for CKS schema mapping (RED phase)...\n")
    print("=" * 70)
    print("EXPECTED: All tests should FAIL (implementation does not exist yet)")
    print("=" * 70)
    print()

    failed = []
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed.append(test.__name__)
        except NameError as e:
            # Expected in RED phase - functions don't exist yet
            print(f"✗ {test.__name__} failed: {e}")
            failed.append(test.__name__)
        except ImportError as e:
            # Expected in RED phase - module doesn't exist yet
            print(f"✗ {test.__name__} failed: {e}")
            failed.append(test.__name__)
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed.append(test.__name__)

    print(f"\n{'='*70}")
    if failed:
        print(f"RED PHASE COMPLETE: {len(failed)}/{len(tests)} tests failing (as expected)")
        print("\nFailing tests:")
        for name in failed:
            print(f"  - {name}")
        print("\nNext: Implement scripts/cks_schema_mapper.py to make tests pass (GREEN phase)")
        return 0  # Return 0 because failures are EXPECTED in RED phase
    else:
        print(f"UNEXPECTED: All {len(tests)} tests passed!")
        print("This should not happen in RED phase - tests must fail before implementation")
        return 1  # Return 1 because passing tests in RED phase is wrong


if __name__ == "__main__":
    sys.exit(run_all_tests())
