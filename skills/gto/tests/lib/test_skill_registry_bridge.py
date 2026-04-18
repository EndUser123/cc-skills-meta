"""Tests for skill_registry_bridge module."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from __lib.skill_registry_bridge import (
    SkillSummary,
    find_skills_for_gap,
    format_skill_context,
    get_skill_recommendation_context,
    load_skill_catalog,
)


class TestSkillSummary:
    """Tests for SkillSummary dataclass."""

    def test_dataclass_construction(self) -> None:
        """Test SkillSummary can be constructed."""
        summary = SkillSummary(
            name="/test",
            description="Test skill",
            category="testing",
            triggers=["test"],
        )
        assert summary.name == "/test"
        assert summary.primary_trigger == "test"

    def test_primary_trigger(self) -> None:
        """Test primary_trigger property."""
        summary = SkillSummary(
            name="/test",
            description="Test",
            category="testing",
            triggers=["primary", "secondary"],
        )
        assert summary.primary_trigger == "primary"


class TestSkillRegistryBridge:
    """Smoke tests for skill registry bridge functions."""

    def test_find_skills_for_gap(self) -> None:
        """Test find_skills_for_gap function."""
        result = find_skills_for_gap({"type": "test_gap", "message": "test"})
        assert isinstance(result, list)

    def test_format_skill_context(self) -> None:
        """Test format_skill_context function."""
        skills = []
        result = format_skill_context(skills)
        assert isinstance(result, str)

    def test_get_skill_recommendation_context(self) -> None:
        """Test get_skill_recommendation_context function."""
        result = get_skill_recommendation_context()
        assert isinstance(result, str)

    def test_load_skill_catalog(self) -> None:
        """Test load_skill_catalog function."""
        result = load_skill_catalog()
        # May return empty dict if registry not available
        assert isinstance(result, dict)
