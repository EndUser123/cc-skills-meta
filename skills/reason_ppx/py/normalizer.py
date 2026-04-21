from __future__ import annotations

import re
from .models import ExternalRole, ExternalResult, Finding, Severity


def infer_severity(text: str) -> Severity:
    t = text.lower()
    if any(k in t for k in ["critical", "high risk", "severe", "break", "wrong"]):
        return Severity.HIGH
    if any(k in t for k in ["risk", "concern", "issue", "weakness"]):
        return Severity.MEDIUM
    return Severity.LOW


def normalize_external_result(result: ExternalResult, config=None) -> ExternalResult:
    text = (result.stdout or "").strip()
    if not text:
        return result

    max_bullets = getattr(config, "max_bullets_per_result", 6) if config else 6
    max_chars = getattr(config, "max_chars_per_bullet", 300) if config else 300

    bullets = [b.strip("-* \n\t") for b in re.split(r"\n+", text) if b.strip()]
    findings = []
    for bullet in bullets[:max_bullets]:
        findings.append(Finding(
            role=result.role,
            provider=result.provider,
            summary=bullet[:max_chars],
            severity=infer_severity(bullet),
            raw_text=bullet[:max_chars]
        ))
    result.normalized = findings
    return result
