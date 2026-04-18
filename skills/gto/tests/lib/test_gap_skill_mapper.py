"""Tests for gap_skill_mapper module."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from __lib.gap_skill_mapper import (
    GAP_TYPE_TO_CATEGORIES,
    format_recommendations_for_rsn,
    generate_skill_recommendations,
    inject_skill_context_for_gaps,
)


class TestGapSkillMapper:
    """Smoke tests for GapSkillMapper."""

    def test_gap_type_to_categories_constant(self) -> None:
        """Test GAP_TYPE_TO_CATEGORIES is a dict."""
        assert isinstance(GAP_TYPE_TO_CATEGORIES, dict)
        assert len(GAP_TYPE_TO_CATEGORIES) > 0
        assert "test_gap" in GAP_TYPE_TO_CATEGORIES
        assert "missing_test" in GAP_TYPE_TO_CATEGORIES

    def test_inject_skill_context_for_gaps(self) -> None:
        """Test inject_skill_context_for_gaps function."""
        gaps = []
        result = inject_skill_context_for_gaps(gaps)
        assert isinstance(result, list)

    def test_generate_skill_recommendations(self) -> None:
        """Test generate_skill_recommendations function."""
        gaps = []
        result = generate_skill_recommendations(gaps)
        assert isinstance(result, list)

    def test_format_recommendations_for_rsn(self) -> None:
        """Test format_recommendations_for_rsn function."""
        recommendations = []
        result = format_recommendations_for_rsn(recommendations)
        assert isinstance(result, str)
