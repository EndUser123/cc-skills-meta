from .models import TaskType


FRAME_MAP = {
    TaskType.CODEREVIEW: ("evidence-audit", "premortem"),
    TaskType.PLANNING: ("decision-tree", "constraint-check"),
    TaskType.BRAINSTORM: ("diverge-converge", "kill-list"),
    TaskType.RESEARCH: ("evidence-audit", "contradiction-scan"),
    TaskType.DEBUG: ("causal-isolation", "counterexample-hunt"),
    TaskType.REFACTOR: ("constraint-preserving-rewrite", "regression-risk-review"),
    TaskType.GENERAL: ("decision-tree", "counterexample-hunt"),
}


def select_frames(task_type: TaskType) -> tuple[str, str]:
    return FRAME_MAP.get(task_type, ("decision-tree", "counterexample-hunt"))
