"""Tests for gto_assertions module."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from evals.gto_assertions import GTOAssertions, _get_default_terminal_id


class TestGetDefaultTerminalId:
    """Tests for _get_default_terminal_id function."""

    def test_returns_string(self) -> None:
        """Test that _get_default_terminal_id returns a string."""
        result = _get_default_terminal_id()
        assert isinstance(result, str)
        assert len(result) > 0


class TestGTOAssertions:
    """Smoke tests for GTOAssertions class."""

    def test_class_construction(self, tmp_path: Path) -> None:
        """Test GTOAssertions can be constructed."""
        assertions = GTOAssertions(tmp_path, "test_terminal")
        assert assertions.project_root == tmp_path.resolve()
        assert assertions.terminal_id == "test_terminal"

    def test_check_a1_artifacts_exist_no_artifacts(self, tmp_path: Path) -> None:
        """Test A1 check returns False when .evidence exists but has no valid artifacts."""
        evidence_dir = tmp_path / ".evidence"
        evidence_dir.mkdir()
        assertions = GTOAssertions(tmp_path, "test_terminal")
        passed, msg = assertions.check_a1_artifacts_exist()
        assert passed is False
        assert "No valid GTO artifacts" in msg

    def test_check_a2_health_score_no_artifacts(self, tmp_path: Path) -> None:
        """Test A2 check returns False when .evidence exists but has no health score."""
        evidence_dir = tmp_path / ".evidence"
        evidence_dir.mkdir()
        assertions = GTOAssertions(tmp_path, "test_terminal")
        passed, msg = assertions.check_a2_health_score()
        assert passed is False
        assert "No valid health score" in msg

    def test_check_a3_viability_passed_no_check(self, tmp_path: Path) -> None:
        """Test A3 returns True when no viability check exists."""
        assertions = GTOAssertions(tmp_path, "test_terminal")
        passed, msg = assertions.check_a3_viability_passed()
        assert passed is True
        assert "No viability check" in msg

    def test_check_a4_git_repository_no_git(self, tmp_path: Path) -> None:
        """Test A4 returns False when no git repository exists."""
        assertions = GTOAssertions(tmp_path, "test_terminal")
        passed, msg = assertions.check_a4_git_repository()
        assert passed is False
        assert "Not a git repository" in msg

    def test_check_a5_state_accessible_no_state(self, tmp_path: Path) -> None:
        """Test A5 returns True when state directory not created."""
        assertions = GTOAssertions(tmp_path, "test_terminal")
        passed, msg = assertions.check_a5_state_accessible()
        assert passed is True
        assert "not created" in msg

    def test_run_all_returns_dict(self, tmp_path: Path) -> None:
        """Test run_all returns expected dictionary structure."""
        assertions = GTOAssertions(tmp_path, "test_terminal")
        result = assertions.run_all()
        assert isinstance(result, dict)
        assert "passed" in result
        assert "total" in result
        assert "score" in result
        assert "all_passed" in result
        assert "assertions" in result


class TestExtractHealthScore:
    """Tests for _extract_health_score extraction paths."""

    def test_health_score_at_top_level(self, tmp_path: Path) -> None:
        """Path 1: Top-level health_score field."""
        assertions = GTOAssertions(tmp_path, "test_terminal")
        data = {"health_score": 86.0}
        assert assertions._extract_health_score(data) == 86.0

    def test_overall_score_at_root(self, tmp_path: Path) -> None:
        """Path 2: overall_score at root (GTO monorepo format)."""
        assertions = GTOAssertions(tmp_path, "test_terminal")
        data = {"overall_score": 0.86}
        assert assertions._extract_health_score(data) == 86.0

    def test_health_report_overall_score(self, tmp_path: Path) -> None:
        """Path 3: health_report.overall_score (GTO orchestrator)."""
        assertions = GTOAssertions(tmp_path, "test_terminal")
        data = {"health_report": {"overall_score": 86}}
        assert assertions._extract_health_score(data) == 86.0

    def test_health_overall_score(self, tmp_path: Path) -> None:
        """Path 4: health.overall_score (GTO v3 artifact format)."""
        assertions = GTOAssertions(tmp_path, "test_terminal")
        data = {"health": {"overall_score": 0.79}}
        assert assertions._extract_health_score(data) == 79.0

    def test_metrics_overall(self, tmp_path: Path) -> None:
        """Path 5a: metrics.overall (GTO v3)."""
        assertions = GTOAssertions(tmp_path, "test_terminal")
        data = {"metrics": {"overall": 92}}
        assert assertions._extract_health_score(data) == 92.0

    def test_metrics_test_coverage(self, tmp_path: Path) -> None:
        """Path 5b: metrics.test_coverage fallback."""
        assertions = GTOAssertions(tmp_path, "test_terminal")
        data = {"metrics": {"test_coverage": 75}}
        assert assertions._extract_health_score(data) == 75.0

    def test_legacy_score_field(self, tmp_path: Path) -> None:
        """Path 6: Legacy score or health_score at root."""
        assertions = GTOAssertions(tmp_path, "test_terminal")
        data = {"score": 88}
        assert assertions._extract_health_score(data) == 88.0


class TestNormalizeScore:
    """Tests for _normalize_score decimal handling."""

    def test_decimal_below_threshold(self, tmp_path: Path) -> None:
        """Score < 1.0 is treated as decimal and multiplied by 100."""
        assertions = GTOAssertions(tmp_path, "test_terminal")
        assert assertions._normalize_score(0.86) == 86.0

    def test_integer_percentage_unchanged(self, tmp_path: Path) -> None:
        """Score >= 1.0 is treated as percentage and returned unchanged."""
        assertions = GTOAssertions(tmp_path, "test_terminal")
        assert assertions._normalize_score(86) == 86.0

    def test_decimal_exact_boundary(self, tmp_path: Path) -> None:
        """Score == 1.0 is at the boundary — treated as percentage."""
        assertions = GTOAssertions(tmp_path, "test_terminal")
        assert assertions._normalize_score(1.0) == 1.0

    def test_decimal_just_below_boundary(self, tmp_path: Path) -> None:
        """Score == 0.999 is just below boundary — treated as decimal."""
        assertions = GTOAssertions(tmp_path, "test_terminal")
        assert assertions._normalize_score(0.999) == 99.9

    def test_negative_returns_none(self, tmp_path: Path) -> None:
        """Negative scores return None."""
        assertions = GTOAssertions(tmp_path, "test_terminal")
        assert assertions._normalize_score(-5) is None

    def test_over_100_returns_none(self, tmp_path: Path) -> None:
        """Scores over 100 return None."""
        assertions = GTOAssertions(tmp_path, "test_terminal")
        assert assertions._normalize_score(150) is None

    def test_none_input_returns_none(self, tmp_path: Path) -> None:
        """None input returns None."""
        assertions = GTOAssertions(tmp_path, "test_terminal")
        assert assertions._normalize_score(None) is None

    def test_string_input_returns_none(self, tmp_path: Path) -> None:
        """String input returns None."""
        assertions = GTOAssertions(tmp_path, "test_terminal")
        assert assertions._normalize_score("86") is None
