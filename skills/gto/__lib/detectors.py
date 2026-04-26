from __future__ import annotations

from pathlib import Path
import re

from ..models import EvidenceRef, Finding


TODO_PATTERN = re.compile(r"(?:TODO|FIXME|HACK|XXX)\b", re.IGNORECASE)


def run_basic_detectors(
    root: Path, terminal_id: str, session_id: str, git_sha: str | None
) -> list[Finding]:
    findings: list[Finding] = []

    if not (root / ".git").exists():
        findings.append(
            Finding(
                id="GIT-001",
                title="Repository metadata missing",
                description="Target directory does not contain a .git directory.",
                source_type="detector",
                source_name="basic_detectors",
                domain="git",
                gap_type="invalidrepo",
                severity="high",
                evidence_level="verified",
                scope="systemic",
                terminal_id=terminal_id,
                session_id=session_id,
                git_sha=git_sha,
                evidence=[EvidenceRef(kind="path", value=str(root / ".git"))],
            )
        )

    readme = root / "README.md"
    if not readme.exists():
        findings.append(
            Finding(
                id="DOC-001",
                title="README missing",
                description="Project root does not contain a README.md.",
                source_type="detector",
                source_name="basic_detectors",
                domain="docs",
                gap_type="missingdocs",
                severity="medium",
                evidence_level="verified",
                scope="local",
                terminal_id=terminal_id,
                session_id=session_id,
                git_sha=git_sha,
                evidence=[EvidenceRef(kind="path", value=str(readme))],
            )
        )

    todo_count = _count_todos(root)
    if todo_count > 0:
        findings.append(
            Finding(
                id="QUAL-001",
                title=f"{todo_count} TODO/FIXME markers found",
                description=f"Source contains {todo_count} TODO, FIXME, HACK, or XXX markers.",
                source_type="detector",
                source_name="basic_detectors",
                domain="quality",
                gap_type="techdebt",
                severity="low",
                evidence_level="verified",
                action="prevent",
                priority="low",
                terminal_id=terminal_id,
                session_id=session_id,
                git_sha=git_sha,
                evidence=[EvidenceRef(kind="count", value=str(todo_count))],
            )
        )

    return findings


def _count_todos(root: Path, max_files: int = 200) -> int:
    count = 0
    checked = 0
    for p in root.rglob("*.py"):
        if checked >= max_files:
            break
        if ".git" in p.parts or "__pycache__" in p.parts or "node_modules" in p.parts:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
            count += len(TODO_PATTERN.findall(text))
            checked += 1
        except Exception:
            continue
    return count
