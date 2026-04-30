"""Tests for new GTO detectors: carryover enrichment, anti-recommendations,
staleness waves, invocation tracker, clustering, context boundaries,
impact radius, health score, branch awareness, stuckness, skill ordering."""
import json
import subprocess
import textwrap
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from skills.gto.models import Finding, EvidenceRef
from skills.gto.__lib.carryover import (
    apply_carryover_enrichment,
    SEVERITY_LADDER,
)
from skills.gto.__lib.changelog import (
    classify_change_wave,
    _base_skill,
    detect_changelog_findings,
)
from skills.gto.__lib.invocation_tracker import (
    extract_invoked_skills,
    _normalize_skill,
    check_invocations,
)
from skills.gto.__lib.clustering import cluster_findings, _extract_dir
from skills.gto.__lib.context_boundaries import (
    detect_context_boundaries,
    context_boundary_findings,
)
from skills.gto.__lib.impact_radius import enrich_with_impact_radius
from skills.gto.__lib.coverage import compute_coverage, compute_health_score
from skills.gto.__lib.branch_awareness import adjust_for_branch, get_current_branch
from skills.gto.__lib.stuckness import detect_stuckness
from skills.gto.__lib.dependency_order import order_findings, _skill_order_rank


# ── Carryover Enrichment ──────────────────────────────────────────

class TestCarryoverEnrichment:
    def _make_finding(self, scope="systemic", severity="medium", carry_count=0, file=None):
        return Finding(
            id="TEST-001",
            title="Test finding",
            description="test",
            source_type="carryover",
            source_name="carryover",
            domain="session",
            gap_type="test_gap",
            severity=severity,
            evidence_level="verified",
            scope=scope,
            file=file,
            metadata={"_carry_count": carry_count},
        )

    def test_no_enrichment_under_threshold(self):
        f = self._make_finding(carry_count=1)
        result = apply_carryover_enrichment([f])
        assert len(result) == 1
        assert result[0].severity == "medium"
        assert not result[0].title.startswith("RECURRING")

    def test_escalation_systemic_2_carries(self):
        f = self._make_finding(scope="systemic", severity="medium", carry_count=2)
        result = apply_carryover_enrichment([f])
        assert result[0].severity == "high"
        assert "RECURRING (2x)" in result[0].title

    def test_escalation_architectural_3_carries(self):
        f = self._make_finding(scope="architectural", severity="medium", carry_count=3)
        result = apply_carryover_enrichment([f])
        assert result[0].severity == "high"

    def test_escalation_does_not_apply_to_local(self):
        f = self._make_finding(scope="local", severity="medium", carry_count=5)
        result = apply_carryover_enrichment([f])
        assert result[0].severity == "medium"
        assert not result[0].title.startswith("RECURRING")

    def test_decay_local_with_changed_file(self):
        f = self._make_finding(scope="local", carry_count=3, file="src/main.py")
        result = apply_carryover_enrichment([f], changed_files=["src/main.py"])
        assert "context may have changed" in result[0].description
        assert result[0].evidence_level == "unverified"

    def test_no_decay_without_changed_files(self):
        f = self._make_finding(scope="local", carry_count=3, file="src/main.py")
        result = apply_carryover_enrichment([f])
        assert "context may have changed" not in result[0].description

    def test_no_decay_under_3_carries(self):
        f = self._make_finding(scope="local", carry_count=2, file="src/main.py")
        result = apply_carryover_enrichment([f], changed_files=["src/main.py"])
        assert "context may have changed" not in result[0].description

    def test_severity_ladder(self):
        assert SEVERITY_LADDER["low"] == "medium"
        assert SEVERITY_LADDER["medium"] == "high"
        assert SEVERITY_LADDER["high"] == "critical"
        assert SEVERITY_LADDER["critical"] == "critical"


# ── Staleness Waves ───────────────────────────────────────────────

class TestStalenessWaves:
    def test_incremental(self):
        assert classify_change_wave(1, 1) == "incremental"

    def test_moderate(self):
        assert classify_change_wave(5, 3) == "moderate"

    def test_significant(self):
        assert classify_change_wave(15, 10) == "significant"

    def test_significant_elevates_severity(self):
        """Significant wave should elevate changelog findings to high."""
        files = [f"skills/gto/file_{i}.py" for i in range(12)]
        with patch("subprocess.check_output", return_value="commit\n"), \
             patch("skills.gto.__lib.changelog.get_changed_files", return_value=files), \
             patch("skills.gto.__lib.changelog.get_commit_count", return_value=5):
            result = detect_changelog_findings(
                Path("."), "prev12345678", "curr12345678", "t1", "s1", "sha"
            )
            # Significant wave (12 files) should elevate findings to high
            changelog_findings = [f for f in result if f.id.startswith("CHANGELOG-") and f.owner_skill]
            assert len(changelog_findings) >= 1
            assert changelog_findings[0].severity == "high"


# ── Anti-Recommendations ──────────────────────────────────────────

class TestAntiRecommendations:
    def test_base_skill_normalizes(self):
        assert _base_skill("/sqa --layer=L7") == "/sqa"
        assert _base_skill("/docs") == "/docs"
        assert _base_skill("pytest") == "pytest"

    @patch("subprocess.check_output")
    @patch("skills.gto.__lib.changelog.get_changed_files")
    def test_anti_recommendation_fires_for_incremental(self, mock_changed, mock_cat):
        mock_cat.return_value = "commit\n"
        # Only .md file changed — /sqa and /deps should be anti-recommended
        mock_changed.return_value = ["README.md"]
        result = detect_changelog_findings(
            Path("."), "prev12345678", "curr12345678", "t1", "s1", "sha"
        )
        anti = [f for f in result if f.id == "CHANGELOG-ANTI-001"]
        assert len(anti) == 1
        assert anti[0].action == "skip"
        assert "/sqa" in anti[0].evidence[0].value or "pytest" in anti[0].evidence[0].value

    @patch("subprocess.check_output")
    @patch("skills.gto.__lib.changelog.get_changed_files")
    def test_no_anti_for_significant_wave(self, mock_changed, mock_cat):
        mock_cat.return_value = "commit\n"
        # 15 files — significant wave, no anti-recommendation
        mock_changed.return_value = [f"file_{i}.py" for i in range(15)]
        result = detect_changelog_findings(
            Path("."), "prev12345678", "curr12345678", "t1", "s1", "sha"
        )
        anti = [f for f in result if f.id == "CHANGELOG-ANTI-001"]
        assert len(anti) == 0


# ── Invocation Tracker ───────────────────────────────────────────

class TestInvocationTracker:
    def test_normalize_skill(self):
        assert _normalize_skill("/sqa --layer=L7") == "/sqa"
        assert _normalize_skill("pytest") == "pytest"
        assert _normalize_skill(None) is None

    def test_extract_invoked_skills_none_path(self):
        assert extract_invoked_skills(None) == set()

    def test_extract_invoked_skills_nonexistent(self):
        assert extract_invoked_skills(Path("/nonexistent")) == set()

    def test_extract_invoked_skills_from_transcript(self, tmp_path):
        transcript = tmp_path / "test.jsonl"
        transcript.write_text(textwrap.dedent("""\
            {"role": "user", "content": "let's run /sqa and /docs"}
            {"role": "assistant", "content": "ok running them"}
            {"role": "user", "content": "now try /deps --check"}
        """))
        skills = extract_invoked_skills(transcript)
        assert "/sqa" in skills
        assert "/docs" in skills
        assert "/deps" in skills

    def test_check_invocations_actioned(self, tmp_path):
        transcript = tmp_path / "test.jsonl"
        transcript.write_text('{"role": "user", "content": "run /sqa"}\n')
        rec = Finding(
            id="REC-001", title="Run /sqa", description="test",
            source_type="detector", source_name="test", domain="session",
            gap_type="test", severity="medium", evidence_level="verified",
            owner_skill="/sqa",
        )
        result = check_invocations(transcript, [rec])
        resolved = [f for f in result if f.status == "resolved"]
        assert len(resolved) == 1

    def test_check_invocations_unactioned(self, tmp_path):
        transcript = tmp_path / "test.jsonl"
        transcript.write_text('{"role": "user", "content": "hello"}\n')
        rec = Finding(
            id="REC-001", title="Run /sqa", description="test",
            source_type="detector", source_name="test", domain="session",
            gap_type="test", severity="medium", evidence_level="verified",
            owner_skill="/sqa",
        )
        result = check_invocations(transcript, [rec])
        unactioned = [f for f in result if f.id == "INVOCATION-UNACTIONED-001"]
        assert len(unactioned) == 1

    def test_check_invocations_empty_recs(self, tmp_path):
        transcript = tmp_path / "test.jsonl"
        transcript.write_text('{"role": "user", "content": "run /sqa"}\n')
        assert check_invocations(transcript, []) == []


# ── Finding Clustering ────────────────────────────────────────────

class TestClustering:
    def test_extract_dir(self):
        assert _extract_dir("skills/gto/orchestrator.py") == "skills/gto"
        assert _extract_dir("README.md") is None
        assert _extract_dir(None) is None

    def test_no_cluster_under_threshold(self):
        findings = [
            Finding(
                id=f"TEST-{i}", title="t", description="d",
                source_type="detector", source_name="test", domain="session",
                gap_type="test", severity="medium", evidence_level="verified",
                file=f"skills/gto/file{i}.py", owner_skill="/sqa",
            )
            for i in range(2)
        ]
        result = cluster_findings(findings)
        clusters = [f for f in result if f.id.startswith("CLUSTER-")]
        assert len(clusters) == 0

    def test_creates_cluster_at_3(self):
        findings = [
            Finding(
                id=f"TEST-{i}", title=f"Issue {i}", description="d",
                source_type="detector", source_name="test", domain="session",
                gap_type="test", severity="medium", evidence_level="verified",
                file=f"skills/gto/file{i}.py", owner_skill="/sqa",
            )
            for i in range(3)
        ]
        result = cluster_findings(findings)
        clusters = [f for f in result if f.id.startswith("CLUSTER-")]
        assert len(clusters) == 1
        assert "skills/gto" in clusters[0].title

    def test_no_file_passes_through(self):
        f = Finding(
            id="NOFILE", title="t", description="d",
            source_type="detector", source_name="test", domain="session",
            gap_type="test", severity="medium", evidence_level="verified",
        )
        result = cluster_findings([f])
        assert len(result) == 1
        assert result[0].id == "NOFILE"


# ── Context Boundaries ───────────────────────────────────────────

class TestContextBoundaries:
    def test_no_boundaries_none_path(self):
        assert detect_context_boundaries(None) == []

    def test_detects_context_switch(self, tmp_path):
        transcript = tmp_path / "test.jsonl"
        transcript.write_text(textwrap.dedent("""\
            {"role": "user", "content": "let's fix the auth bug"}
            {"role": "assistant", "content": "fixed it"}
            {"role": "user", "content": "now let's update the docs"}
        """))
        result = detect_context_boundaries(transcript)
        assert len(result) == 1
        assert "update the docs" in result[0].goal_phrase

    def test_boundary_findings_emitted(self, tmp_path):
        transcript = tmp_path / "test.jsonl"
        transcript.write_text(textwrap.dedent("""\
            {"role": "user", "content": "actually let's refactor this instead"}
        """))
        result = context_boundary_findings(transcript, "t1", "s1", "sha")
        assert len(result) == 1
        assert result[0].gap_type == "context_switch"


# ── Impact Radius ────────────────────────────────────────────────

class TestImpactRadius:
    def test_no_file_unchanged(self):
        f = Finding(
            id="NOFILE", title="t", description="d",
            source_type="detector", source_name="test", domain="session",
            gap_type="test", severity="medium", evidence_level="verified",
        )
        result = enrich_with_impact_radius(Path("."), [f])
        assert result[0].severity == "medium"

    @patch("skills.gto.__lib.impact_radius.count_references", return_value=5)
    def test_medium_radius_no_escalation(self, mock_count):
        f = Finding(
            id="MED", title="t", description="d",
            source_type="detector", source_name="test", domain="session",
            gap_type="test", severity="medium", evidence_level="verified",
            file="src/utils.py",
        )
        result = enrich_with_impact_radius(Path("."), [f])
        assert result[0].metadata["impact_radius"] == 5
        assert result[0].severity == "medium"

    @patch("skills.gto.__lib.impact_radius.count_references", return_value=12)
    def test_high_radius_escalates(self, mock_count):
        f = Finding(
            id="HIGH", title="t", description="d",
            source_type="detector", source_name="test", domain="session",
            gap_type="test", severity="medium", evidence_level="verified",
            file="src/core.py",
        )
        result = enrich_with_impact_radius(Path("."), [f])
        assert result[0].severity == "high"
        assert "impact radius: 12" in result[0].description


# ── Health Score ──────────────────────────────────────────────────

class TestHealthScore:
    def test_perfect_score_no_findings(self):
        result = compute_health_score([], "fresh")
        assert result["score"] == 100
        assert result["grade"] == "A"

    def test_score_with_open_findings(self):
        findings = [
            Finding(
                id=f"F-{i}", title="t", description="d",
                source_type="detector", source_name="test", domain="session",
                gap_type="test", severity="medium", evidence_level="verified",
            )
            for i in range(5)
        ]
        result = compute_health_score(findings, "fresh")
        assert result["score"] < 100
        assert result["open"] == 5
        assert result["total"] == 5

    def test_score_with_resolved(self):
        findings = [
            Finding(
                id="F-1", title="t", description="d",
                source_type="detector", source_name="test", domain="session",
                gap_type="test", severity="medium", evidence_level="verified",
                status="resolved",
            ),
            Finding(
                id="F-2", title="t", description="d",
                source_type="detector", source_name="test", domain="session",
                gap_type="test", severity="medium", evidence_level="verified",
                status="open",
            ),
        ]
        result = compute_health_score(findings, "fresh")
        assert result["resolution_rate"] == 0.5
        assert result["resolved"] == 1

    def test_staleness_penalty(self):
        findings = [
            Finding(
                id="F-1", title="t", description="d",
                source_type="detector", source_name="test", domain="session",
                gap_type="test", severity="low", evidence_level="verified",
                status="resolved",
            ),
        ]
        fresh = compute_health_score(findings, "fresh")
        stale = compute_health_score(findings, "stale-git")
        assert fresh["score"] > stale["score"]

    def test_critical_penalty(self):
        findings = [
            Finding(
                id="F-1", title="t", description="d",
                source_type="detector", source_name="test", domain="session",
                gap_type="test", severity="critical", evidence_level="verified",
            ),
        ]
        result = compute_health_score(findings, "fresh")
        assert result["critical_open"] == 1
        assert result["score"] < 100


# ── Branch Awareness ─────────────────────────────────────────────

class TestBranchAwareness:
    def _make_finding(self, skill="/docs"):
        return Finding(
            id="BR-001", title="t", description="d",
            source_type="detector", source_name="test", domain="docs",
            gap_type="test", severity="medium", evidence_level="verified",
            owner_skill=skill, priority="high",
        )

    @patch("skills.gto.__lib.branch_awareness.get_current_branch", return_value="feature/x")
    def test_feature_branch_deprioritizes_docs(self, mock_branch):
        f = self._make_finding("/docs")
        result = adjust_for_branch(Path("."), [f])
        assert result[0].priority == "low"
        assert result[0].metadata.get("branch_adjusted") is True

    @patch("skills.gto.__lib.branch_awareness.get_current_branch", return_value="main")
    def test_main_branch_no_adjustment(self, mock_branch):
        f = self._make_finding("/docs")
        result = adjust_for_branch(Path("."), [f])
        assert result[0].priority == "high"

    @patch("skills.gto.__lib.branch_awareness.get_current_branch", return_value="feature/x")
    def test_sqa_not_deprioritized(self, mock_branch):
        f = self._make_finding("/sqa")
        result = adjust_for_branch(Path("."), [f])
        assert result[0].priority == "high"

    @patch("subprocess.check_output", return_value="feature/test\n")
    def test_get_current_branch(self, mock_run):
        assert get_current_branch(Path(".")) == "feature/test"

    @patch("subprocess.check_output", side_effect=subprocess.CalledProcessError(1, "git"))
    def test_get_current_branch_error(self, mock_run):
        assert get_current_branch(Path(".")) is None


# ── Stuckness Detection ──────────────────────────────────────────

class TestStuckness:
    def test_no_chain_returns_empty(self):
        result = detect_stuckness(Path("."), [], [], "t1", "s1", "sha")
        assert result == []

    def test_short_chain_no_stuckness(self):
        result = detect_stuckness(Path("."), ["transcript1"], [], "t1", "s1", "sha")
        assert result == []

    def test_recurring_carryover_triggers_finding(self):
        f = Finding(
            id="STALE-001", title="Old issue", description="d",
            source_type="carryover", source_name="carryover", domain="session",
            gap_type="test", severity="medium", evidence_level="verified",
            metadata={"_carry_count": 4},
        )
        result = detect_stuckness(
            Path("."), ["transcript1", "transcript2"],
            [f], "t1", "s1", "sha",
        )
        carry_stuck = [r for r in result if r.id == "STUCK-CARRYOVER-001"]
        assert len(carry_stuck) == 1
        assert carry_stuck[0].gap_type == "stuckness"


# ── Skill Ordering ───────────────────────────────────────────────

class TestSkillOrdering:
    def test_base_skills_come_first(self):
        assert _skill_order_rank("/sqa") == 1
        assert _skill_order_rank("/diagnose") == 1
        assert _skill_order_rank("pytest") == 1

    def test_dependent_skills_come_later(self):
        assert _skill_order_rank("/docs") == 3
        assert _skill_order_rank("/deps") == 3

    def test_unknown_skills_last(self):
        assert _skill_order_rank("/unknown") == 5
        assert _skill_order_rank(None) == 5

    def test_order_findings_respects_skill_deps(self):
        docs_finding = Finding(
            id="DOCS-001", title="t", description="d",
            source_type="detector", source_name="test", domain="docs",
            gap_type="test", severity="medium", evidence_level="verified",
            owner_skill="/docs",
        )
        sqa_finding = Finding(
            id="SQA-001", title="t", description="d",
            source_type="detector", source_name="test", domain="quality",
            gap_type="test", severity="medium", evidence_level="verified",
            owner_skill="/sqa",
        )
        result = order_findings([docs_finding, sqa_finding])
        # Same severity+domain but /sqa has lower skill rank
        assert result[0].owner_skill == "/sqa"
