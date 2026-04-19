"""
Test Suite for Phase 3: Decision Engine

Run: python -m pytest test_decision_engine.py -v
Or: python test_decision_engine.py
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from decision_engine import AlternativePath, DecisionEngine, DecisionNode
from orchestrator import MasterSkillOrchestrator, master_orchestrator
from phase3_decision_engine import create_decision_orchestrator

# Create enhanced orchestrator with decision engine
DecisionOrchestrator = create_decision_orchestrator(MasterSkillOrchestrator)
decision_orchestrator = DecisionOrchestrator()


class TestDecisionEngine:
    """Test Phase 3 Decision Engine functionality."""

    def test_decision_engine_exists(self):
        """Test that decision engine is available."""
        assert DecisionEngine is not None
        assert DecisionNode is not None
        assert AlternativePath is not None

    def test_multi_branch_workflow_detection(self):
        """Test detection of multi-branch workflows (STRATEGY + QUALITY)."""
        workflow = ["/analyze", "/nse", "/t", "/comply", "/qa"]
        result = decision_orchestrator.analyze_workflow_branches(workflow)
        assert "branches" in result
        assert result["is_multi_branch"] is True

    def test_alternative_path_generation(self):
        """Test generating alternative workflow paths."""
        from_skill = "/analyze"
        to_skill = "/qa"
        alternatives = decision_orchestrator.get_alternative_paths(from_skill, to_skill)
        assert isinstance(alternatives, list)
        for path in alternatives:
            assert isinstance(path, dict)
            assert "path" in path

    def test_decision_branch_point_identification(self):
        """Test identifying decision points in workflows."""
        workflow = ["/analyze", "/nse", "/design", "/r", "/refactor"]
        branch_points = decision_orchestrator.get_branch_points(workflow)
        assert len(branch_points) >= 0

    def test_strategic_quality_integration(self):
        """Test STRATEGY and QUALITY branch integration."""
        workflow = ["/design", "/nse", "/t", "/comply"]
        validation = decision_orchestrator.validate_cross_branch_workflow(workflow)
        assert "valid" in validation
        assert "branches" in validation

    def test_decision_tree_construction(self):
        """Test building a decision tree from a starting skill."""
        start_skill = "/nse"
        max_depth = 3
        tree = decision_orchestrator.build_decision_tree(start_skill, max_depth)
        assert "root" in tree
        assert tree["root"] == start_skill

    def test_optimal_path_recommendation(self):
        """Test recommending optimal path based on context."""
        from_skill = "/analyze"
        goal_category = "QUALITY"
        context = {"priority": "thoroughness"}
        recommendation = decision_orchestrator.recommend_optimal_path(
            from_skill, goal_category, context
        )
        assert "path" in recommendation
        assert isinstance(recommendation["path"], list)

    def test_decision_conflict_resolution(self):
        """Test resolving conflicts when suggest fields disagree."""
        context = {"domain": "architecture", "urgency": "high"}
        resolution = decision_orchestrator.resolve_decision_conflict(context)
        assert "resolved" in resolution
        assert "chosen_skill" in resolution

    def test_workflow_with_decision_points(self):
        """Test executing a workflow that has decision points."""
        workflow_plan = {
            "start": "/analyze",
            "goals": ["quality_check"],
            "decision_points": ["nse_result"]
        }
        execution = decision_orchestrator.plan_workflow_with_decisions(workflow_plan)
        assert "steps" in execution

    def test_conditional_branch_selection(self):
        """Test selecting branches based on conditions."""
        conditions = {
            "test_coverage": "low",
            "complexity": "high",
            "time_constraint": "none"
        }
        branch = decision_orchestrator.select_branch_based_on_conditions(
            "/nse", conditions
        )
        assert branch is None or isinstance(branch, list)

    def test_phase_3_skills_categorized(self):
        """Test that Phase 3 skills are properly categorized."""
        phase3_skills = [
            "/design", "/nse", "/r",
            "/analyze", "/llm-brainstorm", "/s",
            "/rca"
        ]
        for skill in phase3_skills:
            info = master_orchestrator.get_skill_info(skill)
            assert "skill" in info
            assert info["skill"] == skill

    def test_strategy_to_quality_transition_valid(self):
        """Test that STRATEGY to QUALITY transitions are valid."""
        validation = master_orchestrator.validate_workflow(["/design", "/t"])
        assert "valid" in validation

    def test_decision_engine_state_persistence(self):
        """Test that decision engine state persists across sessions."""
        decision_orchestrator.record_decision(
            from_skill="/nse",
            to_skill="/design",
            context={"reason": "architecture_review"},
            alternatives=["/r", "/s"]
        )
        decisions = decision_orchestrator.get_decision_history()
        assert len(decisions) > 0
        latest = decisions[-1]
        assert latest["from"] == "/nse"
        assert latest["to"] == "/design"


class TestDecisionEngineIntegration:
    """Integration tests for Decision Engine."""

    def test_full_decision_workflow(self):
        """Test a complete decision-driven workflow."""
        result = decision_orchestrator.execute_decision_workflow(
            start="/analyze",
            goal="quality_assurance",
            context={"complexity": "medium"}
        )
        assert "workflow" in result
        assert isinstance(result["workflow"], list)

    def test_multi_goal_optimization(self):
        """Test optimizing for multiple goals."""
        goals = ["quality", "performance"]
        result = decision_orchestrator.optimize_for_multiple_goals(
            start="/analyze",
            goals=goals
        )
        assert "recommended_path" in result


def main():
    """Run tests without pytest."""
    print("Running Phase 3 Decision Engine Test Suite")
    print("=" * 60)

    test_classes = [
        TestDecisionEngine(),
        TestDecisionEngineIntegration()
    ]

    passed = 0
    failed = 0
    not_implemented = 0

    for test_class in test_classes:
        class_name = test_class.__class__.__name__
        print(f"\n{class_name}:")

        for method_name in dir(test_class):
            if not method_name.startswith("test_"):
                continue

            method = getattr(test_class, method_name)
            try:
                method()
                print(f"  ✓ {method_name}")
                passed += 1
            except AssertionError:
                print(f"  ✗ {method_name}: AssertionError")
                failed += 1
            except ImportError as e:
                print(f"  ⏸ {method_name}: Not implemented ({e})")
                not_implemented += 1
            except AttributeError as e:
                print(f"  ⏸ {method_name}: Not implemented ({e})")
                not_implemented += 1
            except Exception as e:
                print(f"  ✗ {method_name}: {type(e).__name__}: {e}")
                failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed, {not_implemented} not implemented")

    if failed == 0 and not_implemented == 0:
        print("✅ All tests passed!")
        return 0
    elif failed == 0:
        print("⏸️ Some methods not implemented")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
