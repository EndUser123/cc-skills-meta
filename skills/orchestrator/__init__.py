"""
Master Skill Orchestrator Package

Public API for skill orchestration and workflow routing.
"""

from .orchestrator import master_orchestrator, MasterSkillOrchestrator
from .suggest_parser import suggest_parser, SuggestFieldParser
from .skill_router import skill_router, SkillRouter
from .workflow_state import workflow_state, WorkflowStateMachine

__all__ = [
    'master_orchestrator',
    'MasterSkillOrchestrator',
    'suggest_parser',
    'SuggestFieldParser',
    'skill_router',
    'SkillRouter',
    'workflow_state',
    'WorkflowStateMachine',
]

# Public API functions
def invoke_skill(skill_name: str, args=None, context=None):
    """Invoke a skill through the orchestrator."""
    return master_orchestrator.invoke_skill(skill_name, args, context)

def get_suggestions(skill_name: str):
    """Get suggested next skills."""
    return master_orchestrator.get_workflow_suggestions(skill_name)

def get_audit_trail():
    """Get decision audit trail."""
    return master_orchestrator.get_decision_audit_trail()

def get_stats():
    """Get workflow statistics."""
    return master_orchestrator.get_workflow_stats()

def get_skill_info(skill_name: str):
    """Get comprehensive information about a skill."""
    return master_orchestrator.get_skill_info(skill_name)

def validate_workflow(workflow):
    """Validate a proposed workflow sequence."""
    return master_orchestrator.validate_workflow(workflow)

def suggest_workflow(starting_skill: str, max_depth: int = 3):
    """Generate possible workflows starting from a given skill."""
    return master_orchestrator.suggest_workflow(starting_skill, max_depth)


def main():
    """CLI entry point."""
    from .cli import run_cli
    return run_cli()
