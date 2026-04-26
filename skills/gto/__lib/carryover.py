from __future__ import annotations

import json
from pathlib import Path

from ..models import Finding, EvidenceRef
from .util import atomic_write_json


def load_carryover(artifacts_dir: Path) -> list[Finding]:
    """Load carryover findings from prior GTO runs in this terminal scope.

    Looks for `carryover.json` in the artifacts directory.
    Returns empty list if file doesn't exist or is unparseable.
    """
    path = artifacts_dir / "carryover.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    findings: list[Finding] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        evidence = [
            EvidenceRef(
                kind=e.get("kind", ""),
                value=e.get("value", ""),
                detail=e.get("detail"),
            )
            for e in item.get("evidence", [])
            if isinstance(e, dict)
        ]
        findings.append(
            Finding(
                id=item.get("id", "CARRY-???"),
                title=item.get("title", "Carryover finding"),
                description=item.get("description", ""),
                source_type="carryover",
                source_name="carryover",
                domain=item.get("domain", "other"),
                gap_type=item.get("gap_type", "carryover"),
                severity=item.get("severity", "medium"),
                evidence_level=item.get("evidence_level", "unverified"),
                action=item.get("action", "recover"),
                priority=item.get("priority", "medium"),
                status=item.get("status", "open"),
                scope=item.get("scope", "local"),
                owner_skill=item.get("owner_skill"),
                owner_reason=item.get("owner_reason"),
                file=item.get("file"),
                line=item.get("line"),
                symbol=item.get("symbol"),
                reversibility=item.get("reversibility"),
                effort=item.get("effort"),
                target=item.get("target"),
                depends_on=item.get("depends_on", []),
                evidence=evidence,
                tags=item.get("tags", []),
                terminal_id=item.get("terminal_id"),
                session_id=item.get("session_id"),
                git_sha=item.get("git_sha"),
                freshness=item.get("freshness"),
                unverified=item.get("unverified", True),
                metadata=item.get("metadata", {}),
            )
        )
    return findings


def save_carryover(artifacts_dir: Path, findings: list[Finding]) -> None:
    """Save unresolved findings as carryover for future runs."""
    carryover = [f for f in findings if f.status == "open"]
    path = artifacts_dir / "carryover.json"
    data = [f.to_dict() for f in carryover]
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(path, data)
