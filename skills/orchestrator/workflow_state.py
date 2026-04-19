"""
Workflow State Machine

Enforces valid skill sequences based on suggest fields from SKILL.md files.
Maintains workflow stack for nested skill invocations.
"""



class WorkflowStateMachine:
    """
    Enforce valid skill sequences based on suggest fields.

    Valid sequences are dynamically loaded from suggest fields in each skill's SKILL.md.
    """

    def __init__(self) -> None:
        self.current_skill: str | None = None
        self.stack: list[str | None] = []
        self.valid_transitions: dict[tuple[str, str], bool] = {}

    def load_transitions_from_graph(self, skills_graph: dict[str, list[str]]) -> None:
        """
        Load valid transitions from suggest field graph.

        Args:
            skills_graph: Dict of {skill: [suggested_skills]} from suggest parser
        """
        for from_skill, to_skills in skills_graph.items():
            for to_skill in to_skills:
                key = (from_skill, to_skill)
                self.valid_transitions[key] = True

    def is_valid_transition(self, from_skill: str, to_skill: str) -> bool:
        """Check if transition is valid based on suggest fields."""
        # Normalize skill names
        if from_skill and not from_skill.startswith('/'):
            from_skill = f'/{from_skill}'
        if to_skill and not to_skill.startswith('/'):
            to_skill = f'/{to_skill}'

        return self.valid_transitions.get((from_skill, to_skill), False)

    def enter_skill(self, skill_name: str) -> bool:
        """
        Attempt to enter a skill.

        Returns True if valid, False if transition blocked.
        """
        # Normalize skill name
        if not skill_name.startswith('/'):
            skill_name = f'/{skill_name}'

        # Check if transition is valid (only enforce if transitions are loaded)
        if self.current_skill and self.valid_transitions:
            if not self.is_valid_transition(self.current_skill, skill_name):
                return False

        # Push current onto stack and set new
        if self.current_skill is not None:
            self.stack.append(self.current_skill)
        self.current_skill = skill_name
        return True

    def exit_skill(self) -> str | None:
        """Exit current skill, return to previous."""
        previous = self.stack.pop() if self.stack else None
        self.current_skill = previous
        return previous

    def get_valid_next_skills(self, current_skill: str) -> set[str]:
        """Get all valid next skills from current skill."""
        if not current_skill.startswith('/'):
            current_skill = f'/{current_skill}'

        return {
            to_skill for (from_skill, to_skill) in self.valid_transitions.keys()
            if from_skill == current_skill
        }

    def get_workflow_path(self) -> list[str]:
        """Get current workflow path (stack + current)."""
        path = [s for s in self.stack if s is not None]
        if self.current_skill:
            path.append(self.current_skill)
        return path

    def reset(self) -> None:
        """Reset the workflow state machine."""
        self.current_skill = None
        self.stack = []

    def get_state_summary(self) -> dict[str, any]:
        """Get a summary of current state."""
        return {
            "current_skill": self.current_skill,
            "stack_depth": len(self.stack),
            "workflow_path": self.get_workflow_path(),
            "total_valid_transitions": len(self.valid_transitions)
        }


# Singleton instance
workflow_state = WorkflowStateMachine()
