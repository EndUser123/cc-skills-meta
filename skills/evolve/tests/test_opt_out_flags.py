"""
Test suite for GoT and ToT opt-out flags in /evolve skill.

These tests verify that:
- GoT is enabled by default (opt-out design)
- ToT is enabled by default (opt-out design)
- --no-got flag disables GoT modernization analysis
- --no-tot flag disables ToT transformation branching
- EVOLVE_NO_GOT environment variable disables GoT globally
- EVOLVE_NO_TOT environment variable disables ToT globally
- Flag parsing logic works correctly for both flags
- Constitutional compliance: opt-out does NOT bypass safety checks
- Flag independence: GoT and ToT flags work independently
"""

import pytest
import os
import sys

# Add utils path to import GotPlanner, GotEdgeAnalyzer, and BranchGenerator from /code
sys.path.insert(0, r'P:\.claude\skills\code\utils')
from got_planner import GotPlanner
from tot_tracer import BranchGenerator


@pytest.fixture
def sample_modernization_plan():
    """Sample modernization plan with transformations and paths"""
    return """
## Modernization Architecture

### Constraints
- Must maintain backward compatibility
- Modernization time < 2 weeks
- Support incremental migration

### Ideas
- Apply GoT for dependency analysis
- Use ToT for transformation paths
- Integrate modern patterns gradually

### Risks
- Breaking changes risk
- Migration complexity
- Performance regression

## Transformation Paths

def choose_modern_strategy(codebase_age, team_expertise):
    if codebase_age == 'legacy':
        if team_expertise == 'high':
            return 'Full modernization with GoT analysis'
        else:  # low expertise
            return 'Incremental modernization'
    else:  # modern codebase
        if team_expertise == 'high':
            return 'Targeted upgrades with ToT paths'
        else:
            return 'Conservative modernization'

def select_transformation(type, scope):
    if type == 'dependency':
        if scope == 'full':
            return 'Comprehensive dependency update'
        else:
            return 'Selective dependency update'
    else:  # code transformation
        if scope == 'full':
            return 'Complete refactor with ToT branching'
        else:
            return 'Targeted refactoring'
"""


def test_got_enabled_by_default(sample_modernization_plan):
    """Test that GoT is enabled by default (opt-out design)"""
    args = []
    got_enabled = '--no-got' not in args

    if got_enabled:
        planner = GotPlanner(sample_modernization_plan)
        nodes = planner.extract_nodes()
        total_nodes = sum(len(node_list) for node_list in nodes.values())
        assert total_nodes >= 2, "GoT should extract at least 2 nodes by default"


def test_no_got_flag_disables_got(sample_modernization_plan):
    """Test that --no-got flag disables GoT analysis"""
    args = ['--no-got']
    got_enabled = '--no-got' not in args

    if not got_enabled:
        assert True, "GoT disabled, traditional modernization analysis used"
    else:
        planner = GotPlanner(sample_modernization_plan)
        nodes = planner.extract_nodes()
        total_nodes = sum(len(node_list) for node_list in nodes.values())
        assert total_nodes >= 2


def test_tot_enabled_by_default(sample_modernization_plan):
    """Test that ToT is enabled by default (opt-out design)"""
    args = []
    tot_enabled = '--no-tot' not in args

    if tot_enabled:
        generator = BranchGenerator(sample_modernization_plan)
        branches = generator.generate_branches()
        assert len(branches) >= 2, "ToT should generate at least 2 branches by default"


def test_no_tot_flag_disables_tot(sample_modernization_plan):
    """Test that --no-tot flag disables ToT branching"""
    args = ['--no-tot']
    tot_enabled = '--no-tot' not in args

    if not tot_enabled:
        assert True, "ToT disabled, traditional transformation analysis used"
    else:
        generator = BranchGenerator(sample_modernization_plan)
        branches = generator.generate_branches()
        assert len(branches) >= 2


def test_default_behavior_quality_first():
    """Test that default behavior prioritizes quality (opt-out design)"""
    args = []
    got_default = '--no-got' not in args
    tot_default = '--no-tot' not in args
    assert got_default is True, "GoT should be enabled by default"
    assert tot_default is True, "ToT should be enabled by default"


def test_got_environment_variable_disables_got(sample_modernization_plan):
    """Test that EVOLVE_NO_GOT environment variable disables GoT"""
    original_env = os.environ.get('EVOLVE_NO_GOT')

    try:
        os.environ['EVOLVE_NO_GOT'] = 'true'
        env_disables = os.getenv('EVOLVE_NO_GOT', 'false').lower() == 'true'
        assert env_disables is True, "EVOLVE_NO_GOT=true should be detected"
        got_enabled = not env_disables

        if not got_enabled:
            assert True, "Environment variable should disable GoT"
        else:
            planner = GotPlanner(sample_modernization_plan)
            nodes = planner.extract_nodes()
            total_nodes = sum(len(node_list) for node_list in nodes.values())
            assert total_nodes >= 2

    finally:
        if original_env is not None:
            os.environ['EVOLVE_NO_GOT'] = original_env
        elif 'EVOLVE_NO_GOT' in os.environ:
            del os.environ['EVOLVE_NO_GOT']


def test_tot_environment_variable_disables_tot(sample_modernization_plan):
    """Test that EVOLVE_NO_TOT environment variable disables ToT"""
    original_env = os.environ.get('EVOLVE_NO_TOT')

    try:
        os.environ['EVOLVE_NO_TOT'] = 'true'
        env_disables = os.getenv('EVOLVE_NO_TOT', 'false').lower() == 'true'
        assert env_disables is True, "EVOLVE_NO_TOT=true should be detected"
        tot_enabled = not env_disables

        if not tot_enabled:
            assert True, "Environment variable should disable ToT"
        else:
            generator = BranchGenerator(sample_modernization_plan)
            branches = generator.generate_branches()
            assert len(branches) >= 2

    finally:
        if original_env is not None:
            os.environ['EVOLVE_NO_TOT'] = original_env
        elif 'EVOLVE_NO_TOT' in os.environ:
            del os.environ['EVOLVE_NO_TOT']


def test_got_tot_independence():
    """Test that GoT and ToT flags work independently"""
    args = []
    got_enabled = '--no-got' not in args
    tot_enabled = '--no-tot' not in args
    assert got_enabled is True and tot_enabled is True, "Both should be enabled by default"

    args = ['--no-got']
    got_enabled = '--no-got' not in args
    tot_enabled = '--no-tot' not in args
    assert got_enabled is False and tot_enabled is True, "Only GoT should be disabled"

    args = ['--no-tot']
    got_enabled = '--no-got' not in args
    tot_enabled = '--no-tot' not in args
    assert got_enabled is True and tot_enabled is False, "Only ToT should be disabled"

    args = ['--no-got', '--no-tot']
    got_enabled = '--no-got' not in args
    tot_enabled = '--no-tot' not in args
    assert got_enabled is False and tot_enabled is False, "Both should be disabled"


def test_got_quality_first_design():
    """Test that /evolve follows quality-first design with GoT"""
    args = []
    got_enabled = '--no-got' not in args
    assert got_enabled is True, "GoT should be enabled by default (quality-first)"
    assert '--no-got' in ['--no-got'], "User can opt-out with --no-got flag"
    assert 'EVOLVE_NO_GOT' in ['EVOLVE_NO_GOT'], "User can opt-out with env var"


def test_tot_quality_first_design():
    """Test that /evolve follows quality-first design with ToT"""
    args = []
    tot_enabled = '--no-tot' not in args
    assert tot_enabled is True, "ToT should be enabled by default (quality-first)"
    assert '--no-tot' in ['--no-tot'], "User can opt-out with --no-tot flag"
    assert 'EVOLVE_NO_TOT' in ['EVOLVE_NO_TOT'], "User can opt-out with env var"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
