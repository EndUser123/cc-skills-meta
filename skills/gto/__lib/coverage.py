from __future__ import annotations

from ..models import Finding


def compute_coverage(findings: list[Finding]) -> dict[str, Any]:
    """Compute coverage summary for a list of findings.

    Returns a dict with domain coverage, severity breakdown, and routing stats.
    """
    from typing import Any

    by_domain: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    by_action: dict[str, int] = {}
    routed = 0
    unrouted = 0
    verified = 0
    unverified_count = 0

    for f in findings:
        by_domain[f.domain] = by_domain.get(f.domain, 0) + 1
        by_severity[f.severity] = by_severity.get(f.severity, 0) + 1
        by_action[f.action] = by_action.get(f.action, 0) + 1
        if f.owner_skill:
            routed += 1
        else:
            unrouted += 1
        if f.unverified:
            unverified_count += 1
        else:
            verified += 1

    return {
        "total": len(findings),
        "by_domain": by_domain,
        "by_severity": by_severity,
        "by_action": by_action,
        "routed": routed,
        "unrouted": unrouted,
        "verified": verified,
        "unverified": unverified_count,
    }
