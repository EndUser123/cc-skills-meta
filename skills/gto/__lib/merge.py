from __future__ import annotations

from ..models import Finding


def merge_findings(deterministic: list[Finding], agent: list[Finding]) -> list[Finding]:
    """Merge deterministic detector findings with agent findings.

    Agent findings that duplicate a deterministic finding (same domain+gap_type)
    are dropped in favor of the deterministic version, which has higher evidence level.
    """
    deterministic_keys = {(f.domain, f.gap_type) for f in deterministic}
    merged = list(deterministic)
    for f in agent:
        if (f.domain, f.gap_type) not in deterministic_keys:
            merged.append(f)
    return merged
