from __future__ import annotations

from ..models import Finding

SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}
DOMAIN_RANK = {
    "security": 0,
    "quality": 1,
    "tests": 2,
    "performance": 3,
    "docs": 4,
    "deps": 5,
    "git": 6,
    "other": 7,
}


def order_findings(findings: list[Finding]) -> list[Finding]:
    """Order findings by severity (critical first) then domain, stable within groups."""
    return sorted(
        findings,
        key=lambda f: (
            SEVERITY_RANK.get(f.severity, 99),
            DOMAIN_RANK.get(f.domain, 99),
            f.id,
        ),
    )
