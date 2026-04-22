from __future__ import annotations

from collections import defaultdict
from .models import ClaimStatus, ReasoningState, Severity


def reconcile(state: ReasoningState) -> ReasoningState:
    provider_views = defaultdict(list)
    for res in state.external_results:
        if res.ok and res.normalized:
            for finding in res.normalized:
                provider_views[finding.provider].append(finding)

    contradictions = []
    all_text = " ".join(
        f.summary.lower()
        for r in state.external_results
        for f in r.normalized
    )

    for claim in state.claims:
        cid = claim.id.lower()
        challenged = False
        for res in state.external_results:
            for finding in res.normalized:
                summary = finding.summary.lower()
                # Precise check for claim ID with word boundaries to avoid substring collisions (e.g., C1 vs C10)
                import re
                id_pattern = rf"\b{re.escape(cid)}\b"
                if re.search(id_pattern, summary) and any(word in summary for word in ["unsupported", "overstated", "wrong", "fragile", "risky"]):
                    challenged = True
                    claim.notes.append(f"Challenged by {finding.provider}: {finding.summary}")
                    break
            if challenged:
                break

        if challenged:
            if claim.impact == Severity.HIGH:
                claim.status = ClaimStatus.INFERRED if claim.status == ClaimStatus.VERIFIED else ClaimStatus.UNPROVEN
                claim.notes.append("Downgraded after external challenge.")
                contradictions.append(f"High-impact claim challenged: {claim.text}")

                # Prescriptive detector: force strategy shift
                if not getattr(state, "strategy_shift", ""):
                    state.strategy_shift = (
                        "SHIFT: High-impact contradiction detected. "
                        "Abandoning 'decision-tree' for 'causal-isolation' and 'counterexample-hunt'."
                    )

    state.contradictions = contradictions
    state.provider_views = provider_views  # store for finalize_answer
    return state


def finalize_answer(state: ReasoningState) -> str:
    verified = [c for c in state.claims if c.status == ClaimStatus.VERIFIED]
    inferred = [c for c in state.claims if c.status == ClaimStatus.INFERRED]
    unproven = [c for c in state.claims if c.status == ClaimStatus.UNPROVEN]

    lines = []
    lines.append(state.internal_draft.strip())
    lines.append("")

    # External challenger findings
    successful = [r for r in state.external_results if r.ok and r.normalized]
    if successful:
        lines.append("External challenger findings:")
        provider_views = getattr(state, "provider_views", {})
        for res in successful:
            role_label = res.role.value.upper()
            findings = provider_views.get(res.provider, [])
            if findings:
                lines.append(f"  [{role_label} via {res.provider}]")
                for f in findings:
                    severity_marker = f"[{f.severity.value.upper()}]" if hasattr(f, "severity") else ""
                    lines.append(f"  - {severity_marker} {f.summary}".strip())
        lines.append("")

    # Execution Warnings for failed external calls
    failed = [r for r in state.external_results if not r.ok]
    if failed:
        lines.append("Execution Warnings (External verification failed):")
        for f in failed:
            role_label = f.role.value.upper()
            lines.append(f"  - [{role_label} via {f.provider}] {f.error_type or 'error'}: {f.stderr or 'No output'}")
        lines.append("")

    lines.append("Assumptions and uncertainty:")
    if state.assumptions:
        for a in state.assumptions:
            lines.append(f"- Assumption: {a}")
    if state.unknowns:
        for u in state.unknowns:
            lines.append(f"- Unknown: {u}")

    if state.contradictions:
        lines.append("")
        lines.append("External challenges that materially affected confidence:")
        for c in state.contradictions:
            lines.append(f"- {c}")

    strategy_shift = getattr(state, "strategy_shift", "") or ""
    if strategy_shift:
        lines.append("")
        lines.append("STRATEGY SHIFT:")
        lines.append(f"!!! {strategy_shift}")

    lines.append("")
    lines.append("Claim status summary:")
    for c in verified:
        lines.append(f"- VERIFIED: {c.text}")
    for c in inferred:
        lines.append(f"- INFERRED: {c.text}")
    for c in unproven:
        lines.append(f"- UNPROVEN: {c.text}")

    lines.append("")
    lines.append("Next step:")
    if state.unknowns:
        lines.append(f"- Run the smallest discriminating check on: {state.unknowns[0]}")
    else:
        lines.append("- Proceed with the recommendation and verify the top challenged assumption first.")

    return "\n".join(lines).strip()
