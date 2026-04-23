from __future__ import annotations

from .config import OrchestratorConfig
from .models import (
    ClaimStatus,
    DataClass,
    ExternalQuery,
    ExternalRole,
    MissingCapability,
    ReasoningState,
    Severity,
    TaskType,
)


def should_use_external(state: ReasoningState, config: OrchestratorConfig) -> bool:
    # CLI override: --no-external forces local-only
    if getattr(config, "override_no_external", False):
        return False

    if not config.external_on_for_nontrivial:
        return False

    # Privacy-aware routing: sensitive data stays local
    if state.context.data_class == DataClass.LOCAL_ONLY:
        return False
    elif state.context.data_class == DataClass.LOCAL_OK:
        pass  # proceed to other checks
    elif state.context.data_class == DataClass.REMOTE_ONLY:
        return True
    # REDACT_THEN_REMOTE: treat as local-first, may escalate after redaction

    if not state.task:
        return True

    if state.task.task_type in {
        TaskType.CODEREVIEW, TaskType.PLANNING, TaskType.BRAINSTORM,
        TaskType.RESEARCH, TaskType.DEBUG, TaskType.REFACTOR
    }:
        return True

    if state.high_impact_unproven_count() >= config.high_impact_claim_threshold:
        return True

    return False


def build_external_queries(state: ReasoningState, config: OrchestratorConfig) -> list[ExternalQuery]:
    if not state.task:
        return []

    task_type = state.task.task_type
    missing = set(state.task.missing_capabilities)
    draft = state.internal_draft
    claim_lines = "\n".join([f"- {c.id}: {c.text} [{c.status.value}/{c.impact.value}]" for c in state.claims])
    unknowns = "\n".join([f"- {u}" for u in state.unknowns]) or "- none"

    queries: list[ExternalQuery] = []

    # Grounded verifier: only when freshness or citations are missing
    if (MissingCapability.FRESHNESS in missing or
        MissingCapability.CITATIONS in missing or
        task_type in {TaskType.RESEARCH, TaskType.PLANNING, TaskType.GENERAL, TaskType.BRAINSTORM}):
        queries.append(ExternalQuery(
            role=ExternalRole.VERIFY,
            provider="gemini",
            prompt=f"""You are a verifier.
Review this draft and test its key claims for support, weakness, or overreach.

TASK TYPE: {task_type.value}
DRAFT:
{draft}

CLAIMS:
{claim_lines}

UNKNOWNS:
{unknowns}

Return:
1. supported claims
2. unsupported/overstated claims
3. missing evidence
4. best corrective recommendation
""",
            timeout_seconds=config.provider_configs["gemini"].timeout_seconds
        ))

    # Adversarial reviewer: only when adversarial review is missing or code-related task
    if (MissingCapability.ADVERSARIAL_REVIEW in missing or
        task_type in {TaskType.CODEREVIEW, TaskType.DEBUG, TaskType.REFACTOR, TaskType.PLANNING}):
        queries.append(ExternalQuery(
            role=ExternalRole.REDTEAM,
            provider="pi_m27",
            prompt=f"""You are a red-team critic.
Attack this draft for hidden flaws, edge cases, regressions, brittleness, bad assumptions, and failure modes.

TASK TYPE: {task_type.value}
DRAFT:
{draft}

CLAIMS:
{claim_lines}

Return:
1. highest-risk weaknesses
2. hidden assumptions
3. likely failure scenarios
4. concrete fixes
""",
            timeout_seconds=config.provider_configs["pi_m27"].timeout_seconds
        ))

    # Alternative generator: always included for planning and brainstorm
    if task_type in {TaskType.PLANNING, TaskType.BRAINSTORM, TaskType.REFACTOR}:
        queries.append(ExternalQuery(
            role=ExternalRole.ALTERNATIVE,
            provider="codex",
            prompt=f"""You are an alternative-solution generator.
Propose a materially different viable approach than the draft below.

TASK TYPE: {task_type.value}
DRAFT:
{draft}

CLAIMS:
{claim_lines}

Return:
1. alternate approach
2. why it might be better
3. tradeoffs vs current draft
""",
            timeout_seconds=config.provider_configs["codex"].timeout_seconds
        ))

    return queries


def should_run_second_round(state: ReasoningState, config: OrchestratorConfig, round_number: int) -> bool:
    if round_number >= config.max_external_rounds:
        return False
    return len(state.contradictions) >= config.contradiction_threshold
