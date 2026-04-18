#!/usr/bin/env python3
"""
CKS Schema Mapper for /reflect to /r Integration.

This module provides the mapping between /reflect signal categories and /r finding
types for CKS (Claude Knowledge Store) pattern storage.

TDD GREEN Phase Implementation: Minimal code to pass existing tests.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class FindingType(Enum):
    """Finding types from /r skill for CKS pattern categorization."""
    PATTERN = "PATTERN"
    REFACTOR = "REFACTOR"
    DEBT = "DEBT"
    DOC = "DOC"
    OPT = "OPT"


class ConfidenceLevel(Enum):
    """Confidence levels for category classification."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class CKSMetadata:
    """Metadata for CKS pattern storage."""
    finding_type: FindingType
    severity_weight: float
    category_confidence: ConfidenceLevel
    warnings: Optional[list[str]] = None


def classify_finding_type(category: str) -> CKSMetadata:
    """
    Map /reflect signal categories to /r finding types for CKS integration.

    Args:
        category: The signal category from /reflect analysis

    Returns:
        CKSMetadata with finding_type, severity_weight, category_confidence
    """
    category_lower = category.lower()

    # OPT: Optimization and performance categories
    if category_lower in ["optimization", "performance"]:
        return CKSMetadata(
            finding_type=FindingType.OPT,
            severity_weight=0.6,
            category_confidence=ConfidenceLevel.HIGH
        )

    # PATTERN: Forgotten items, omissions, TODOs
    if category_lower in ["forgotten", "todo", "omission", "pattern"]:
        return CKSMetadata(
            finding_type=FindingType.PATTERN,
            severity_weight=0.7,
            category_confidence=ConfidenceLevel.HIGH
        )

    # REFACTOR: Code quality, cleanup, refactoring opportunities
    if category_lower in ["code quality", "cleanup", "refactor"]:
        return CKSMetadata(
            finding_type=FindingType.REFACTOR,
            severity_weight=0.5,
            category_confidence=ConfidenceLevel.MEDIUM
        )

    # DEBT: Compliance violations, technical debt
    if category_lower in ["violation", "compliance", "technical debt", "debt"]:
        return CKSMetadata(
            finding_type=FindingType.DEBT,
            severity_weight=0.8,
            category_confidence=ConfidenceLevel.HIGH
        )

    # DOC: Documentation gaps
    if category_lower in ["documentation", "doc", "readme"]:
        return CKSMetadata(
            finding_type=FindingType.DOC,
            severity_weight=0.4,
            category_confidence=ConfidenceLevel.MEDIUM
        )

    # Unknown category: Default to PATTERN with LOW confidence and warning
    logger.warning(f"Unknown category '{category}', defaulting to PATTERN")
    return CKSMetadata(
        finding_type=FindingType.PATTERN,
        severity_weight=0.7,
        category_confidence=ConfidenceLevel.LOW,
        warnings=[f"Unknown category: {category}"]
    )
