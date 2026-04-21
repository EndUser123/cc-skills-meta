from __future__ import annotations

from typing import Dict, List

from .models import ClassificationResult, MissingCapability, TaskType


KEYWORDS: Dict[TaskType, List[str]] = {
    TaskType.CODEREVIEW: ["review", "code review", "bug", "security", "smell", "issue"],
    TaskType.PLANNING: ["plan", "roadmap", "steps", "milestones", "implement"],
    TaskType.BRAINSTORM: ["ideas", "brainstorm", "options", "what could", "explore"],
    TaskType.RESEARCH: ["research", "compare", "investigate", "evidence", "sources"],
    TaskType.DEBUG: ["debug", "failing", "error", "stack trace", "why"],
    TaskType.REFACTOR: ["refactor", "simplify", "restructure", "cleanup"],
    TaskType.GENERAL: [],
}


def classify_task(query: str) -> ClassificationResult:
    q = query.lower()
    scores: Dict[str, float] = {}
    for task_type, words in KEYWORDS.items():
        score = 0.0
        for w in words:
            if w in q:
                score += 0.2
        scores[task_type.value] = min(score, 1.0)

    best = max(scores, key=scores.get)
    best_score = scores[best]

    # Detect missing capabilities first — before any early returns
    missing_caps: list[MissingCapability] = []
    if any(k in q for k in ["latest", "current", "recent", "fresh", "today", "now"]):
        missing_caps.append(MissingCapability.FRESHNESS)
    if any(k in q for k in ["cite", "source", "evidence", "reference", "according to"]):
        missing_caps.append(MissingCapability.CITATIONS)
    if any(k in q for k in ["review", "criticize", "attack", "challenge", "adversarial", "risk"]):
        missing_caps.append(MissingCapability.ADVERSARIAL_REVIEW)
    if any(k in q for k in ["implement", "build", "write code", "coding", "long-run", "complex"]):
        missing_caps.append(MissingCapability.LONG_HORIZON)

    if best_score == 0:
        return ClassificationResult(
            task_type=TaskType.GENERAL,
            confidence=0.2,
            scores=scores,
            rationale="No strong keyword signal; defaulting to GENERAL.",
            missing_capabilities=missing_caps
        )

    if "ideas" in q or "brainstorm" in q or "what could" in q:
        if scores.get(TaskType.BRAINSTORM.value, 0) >= scores.get(TaskType.PLANNING.value, 0):
            return ClassificationResult(
                task_type=TaskType.BRAINSTORM,
                confidence=max(best_score, 0.5),
                scores=scores,
                rationale="Conceptual language suggests BRAINSTORM.",
                missing_capabilities=missing_caps
            )

    return ClassificationResult(
        task_type=TaskType(best),
        confidence=best_score,
        scores=scores,
        rationale=f"Best keyword match: {best}.",
        missing_capabilities=missing_caps
    )
