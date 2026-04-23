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

# Mode-specific frame overrides (set via --mode flag)
MODE_FRAME_MAP = {
    "review": ("premortem", "adversarial-scan"),
    "design": ("architecture-compare", "failure-containment"),
    "diagnose": ("causal-isolation", "smallest-test"),
    "optimize": ("objective-clarify", "redesign-vs-tuning"),
    "decide": ("regret-minimization", "downside-containment"),
    "explore": ("frame-challenge", "adjacent-problem"),
    "off": ("signal-detect", "mismatch-find"),
    "execute": ("momentum-build", "quick-win"),
}


def select_frames(task_type: TaskType, override_mode: str = "auto") -> tuple[str, str]:
    if override_mode != "auto" and override_mode in MODE_FRAME_MAP:
        return MODE_FRAME_MAP[override_mode]
    return FRAME_MAP.get(task_type, ("decision-tree", "counterexample-hunt"))
