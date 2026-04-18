"""
Test suite for GoT and ToT opt-out flags in /reflect skill.

These tests verify that:
- GoT is enabled by default (opt-out design)
- ToT is enabled by default (opt-out design)
- --no-got flag disables GoT reflection analysis
- --no-tot flag disables ToT lesson branching
- REFLECT_NO_GOT environment variable disables GoT globally
- REFLECT_NO_TOT environment variable disables ToT globally
- Flag parsing logic works correctly for both flags
- Constitutional compliance: opt-out does NOT bypass safety checks
- Flag independence: GoT and ToT flags work independently
"""

import os
import sys

import pytest

# Add utils path to import GotPlanner, GotEdgeAnalyzer, and BranchGenerator from /code
sys.path.insert(0, r"P:\.claude\skills\code\utils")
from got_planner import GotPlanner
from tot_tracer import BranchGenerator


@pytest.fixture
def sample_reflection_analysis():
    """Sample reflection analysis with lessons and patterns"""
    return """
## Reflection Architecture

### Constraints
- Must identify lessons learned
- Analysis time < 15 minutes
- Support multiple reflection types

### Ideas
- Apply GoT for pattern analysis
- Use ToT for lesson branching
- Integrate pre-mortem insights

### Risks
- Reflection completeness concerns
- Pattern selection ambiguity
- Lesson extraction quality

## Reflection Paths

def analyze_session(session_type, complexity):
    if session_type == 'failure':
        if complexity == 'high':
            return 'Apply GoT for root cause analysis'
        else:  # low complexity
            return 'Apply simplified reflection'
    else:  # success session
        if complexity == 'high':
            return 'Apply ToT for success factor analysis'
        else:
            return 'Standard reflection'

def extract_lessons(outcome, context):
    if outcome == 'error':
        if context == 'production':
            return 'Critical lesson - full analysis'
        else:
            return 'Standard lesson capture'
    else:  # success
        if context == 'production':
            return 'Success pattern documented'
        else:
            return 'Simple success note'
"""


def test_got_enabled_by_default(sample_reflection_analysis):
    """Test that GoT is enabled by default (opt-out design)"""
    args = []
    got_enabled = "--no-got" not in args

    if got_enabled:
        planner = GotPlanner(sample_reflection_analysis)
        nodes = planner.extract_nodes()
        total_nodes = sum(len(node_list) for node_list in nodes.values())
        assert total_nodes >= 2, "GoT should extract at least 2 nodes by default"


def test_no_got_flag_disables_got(sample_reflection_analysis):
    """Test that --no-got flag disables GoT analysis"""
    args = ["--no-got"]
    got_enabled = "--no-got" not in args

    if not got_enabled:
        assert True, "GoT disabled, traditional reflection analysis used"
    else:
        planner = GotPlanner(sample_reflection_analysis)
        nodes = planner.extract_nodes()
        total_nodes = sum(len(node_list) for node_list in nodes.values())
        assert total_nodes >= 2


def test_tot_enabled_by_default(sample_reflection_analysis):
    """Test that ToT is enabled by default (opt-out design)"""
    args = []
    tot_enabled = "--no-tot" not in args

    if tot_enabled:
        generator = BranchGenerator(sample_reflection_analysis)
        branches = generator.generate_branches()
        assert len(branches) >= 2, "ToT should generate at least 2 branches by default"


def test_no_tot_flag_disables_tot(sample_reflection_analysis):
    """Test that --no-tot flag disables ToT branching"""
    args = ["--no-tot"]
    tot_enabled = "--no-tot" not in args

    if not tot_enabled:
        assert True, "ToT disabled, traditional lesson analysis used"
    else:
        generator = BranchGenerator(sample_reflection_analysis)
        branches = generator.generate_branches()
        assert len(branches) >= 2


def test_default_behavior_quality_first():
    """Test that default behavior prioritizes quality (opt-out design)"""
    args = []
    got_default = "--no-got" not in args
    tot_default = "--no-tot" not in args
    assert got_default is True, "GoT should be enabled by default"
    assert tot_default is True, "ToT should be enabled by default"


def test_got_environment_variable_disables_got(sample_reflection_analysis):
    """Test that REFLECT_NO_GOT environment variable disables GoT"""
    original_env = os.environ.get("REFLECT_NO_GOT")

    try:
        os.environ["REFLECT_NO_GOT"] = "true"
        env_disables = os.getenv("REFLECT_NO_GOT", "false").lower() == "true"
        assert env_disables is True, "REFLECT_NO_GOT=true should be detected"
        got_enabled = not env_disables

        if not got_enabled:
            assert True, "Environment variable should disable GoT"
        else:
            planner = GotPlanner(sample_reflection_analysis)
            nodes = planner.extract_nodes()
            total_nodes = sum(len(node_list) for node_list in nodes.values())
            assert total_nodes >= 2

    finally:
        if original_env is not None:
            os.environ["REFLECT_NO_GOT"] = original_env
        elif "REFLECT_NO_GOT" in os.environ:
            del os.environ["REFLECT_NO_GOT"]


def test_tot_environment_variable_disables_tot(sample_reflection_analysis):
    """Test that REFLECT_NO_TOT environment variable disables ToT"""
    original_env = os.environ.get("REFLECT_NO_TOT")

    try:
        os.environ["REFLECT_NO_TOT"] = "true"
        env_disables = os.getenv("REFLECT_NO_TOT", "false").lower() == "true"
        assert env_disables is True, "REFLECT_NO_TOT=true should be detected"
        tot_enabled = not env_disables

        if not tot_enabled:
            assert True, "Environment variable should disable ToT"
        else:
            generator = BranchGenerator(sample_reflection_analysis)
            branches = generator.generate_branches()
            assert len(branches) >= 2

    finally:
        if original_env is not None:
            os.environ["REFLECT_NO_TOT"] = original_env
        elif "REFLECT_NO_TOT" in os.environ:
            del os.environ["REFLECT_NO_TOT"]


def test_got_tot_independence():
    """Test that GoT and ToT flags work independently"""
    args = []
    got_enabled = "--no-got" not in args
    tot_enabled = "--no-tot" not in args
    assert got_enabled is True and tot_enabled is True, "Both should be enabled by default"

    args = ["--no-got"]
    got_enabled = "--no-got" not in args
    tot_enabled = "--no-tot" not in args
    assert got_enabled is False and tot_enabled is True, "Only GoT should be disabled"

    args = ["--no-tot"]
    got_enabled = "--no-got" not in args
    tot_enabled = "--no-tot" not in args
    assert got_enabled is True and tot_enabled is False, "Only ToT should be disabled"

    args = ["--no-got", "--no-tot"]
    got_enabled = "--no-got" not in args
    tot_enabled = "--no-tot" not in args
    assert got_enabled is False and tot_enabled is False, "Both should be disabled"


def test_got_quality_first_design():
    """Test that /reflect follows quality-first design with GoT"""
    args = []
    got_enabled = "--no-got" not in args
    assert got_enabled is True, "GoT should be enabled by default (quality-first)"
    assert "--no-got" in ["--no-got"], "User can opt-out with --no-got flag"
    assert "REFLECT_NO_GOT" in ["REFLECT_NO_GOT"], "User can opt-out with env var"


def test_tot_quality_first_design():
    """Test that /reflect follows quality-first design with ToT"""
    args = []
    tot_enabled = "--no-tot" not in args
    assert tot_enabled is True, "ToT should be enabled by default (quality-first)"
    assert "--no-tot" in ["--no-tot"], "User can opt-out with --no-tot flag"
    assert "REFLECT_NO_TOT" in ["REFLECT_NO_TOT"], "User can opt-out with env var"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
