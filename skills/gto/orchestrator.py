#!/usr/bin/env python3
"""GTO Orchestrator — main entry point for gap analysis runs.

Usage:
    python orchestrator.py [options]

Runs deterministic detectors, optionally dispatches agent subanalyses,
normalizes, deduplicates, routes, and renders findings as RNS-compatible
machine output and human-readable reports.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from .models import GTOArtifact
from .settings import GTOSettings
from .agents import parse_agent_result
from .__lib.context import get_git_sha
from .__lib.detectors import run_basic_detectors
from .__lib.carryover import load_carryover, save_carryover
from .__lib.docs_followup import detect_docs_followup
from .__lib.normalize import normalize_findings
from .__lib.dedupe import dedupe_findings
from .__lib.merge import merge_findings
from .__lib.route import route_findings
from .__lib.dependency_order import order_findings
from .__lib.freshness import classify_freshness
from .__lib.targeting import resolve_target
from .__lib.coverage import compute_coverage
from .__lib.evidence import write_artifact
from .__lib.state import RunState, load_state, save_state
from .__lib.verify import verify_artifact


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GTO Gap Analysis Orchestrator")
    parser.add_argument("--target", help="Target directory or project to analyze")
    parser.add_argument("--mode", choices=["full", "quick", "agent-only"], default="full")
    parser.add_argument("--terminal-id", default="default")
    parser.add_argument("--session-id", default="")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--skip-agents", action="store_true", help="Skip agent subanalyses")
    return parser.parse_args(argv)


def _read_agent_result(result_path: Path, agent_name: str) -> list:
    """Read agent results from a result file if it exists."""
    try:
        result = parse_agent_result(result_path, agent_name)
        return result.findings if result.success else []
    except Exception as exc:
        print(f"GTO: agent {agent_name} result read failed: {exc}", file=sys.stderr)
        return []


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.root.resolve()

    settings = GTOSettings(
        terminal_id=args.terminal_id,
        session_id=args.session_id,
        git_sha=get_git_sha(root),
        root=root,
        mode=args.mode,
    )

    paths = settings.paths
    paths.state_dir.mkdir(parents=True, exist_ok=True)
    paths.outputs_dir.mkdir(parents=True, exist_ok=True)

    # Initialize state
    state_file = paths.state_dir / "run_state.json"
    state = load_state(state_file)
    state.run_id = f"{args.terminal_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    state.phase = "running"
    state.current_target = resolve_target(args.target, None, None)
    state.git_sha = settings.git_sha
    state.verification_required = True
    state.verification_status = "pending"
    save_state(state_file, state)

    # Phase 1: Deterministic detectors
    findings = run_basic_detectors(root, args.terminal_id, args.session_id, settings.git_sha)

    # Phase 2: Load carryover
    carryover = load_carryover(paths.artifacts_dir)
    if carryover:
        findings.extend(carryover)

    # Phase 3: Agent analysis (skipped in quick mode or when --skip-agents)
    agent_findings: list = []
    if args.mode != "quick" and not args.skip_agents:
        # Agent dispatch happens via SKILL.md instructions to Claude Code Agent tool
        # The orchestrator prepares handoff files for agents to read
        inputs_dir = paths.inputs_dir
        inputs_dir.mkdir(parents=True, exist_ok=True)

        handoff = {
            "mode": args.mode,
            "target": state.current_target,
            "root": str(root),
            "terminal_id": args.terminal_id,
            "session_id": args.session_id,
            "git_sha": settings.git_sha,
            "deterministic_findings_count": len(findings),
        }
        handoff_file = inputs_dir / "agent_handoff.json"
        handoff_file.write_text(json.dumps(handoff, indent=2), encoding="utf-8")

        # Phase 3a: Domain analyzer — reads handoff, writes findings
        agent_findings = _read_agent_result(
            inputs_dir / "domain_analyzer_result.json", "domain_analyzer",
        )

        # Phase 3b: Findings reviewer — validates and deduplicates agent findings
        if agent_findings:
            from .agents.findings_reviewer import write_handoff as reviewer_handoff
            reviewer_handoff(inputs_dir / "reviewer_handoff.json", agent_findings)
            reviewed = _read_agent_result(
                inputs_dir / "findings_reviewer_result.json", "findings_reviewer",
            )
            if reviewed:
                agent_findings = reviewed

        # Phase 3c: Action normalizer — ensures valid domains/severities/actions
        if agent_findings:
            from .agents.action_normalizer import write_handoff as normalizer_handoff
            normalizer_handoff(inputs_dir / "normalizer_handoff.json", agent_findings)
            normalized = _read_agent_result(
                inputs_dir / "action_normalizer_result.json", "action_normalizer",
            )
            if normalized:
                agent_findings = normalized

    # Phase 4: Merge, normalize, dedupe, route, order
    all_findings = merge_findings(findings, agent_findings)
    all_findings = normalize_findings(all_findings)

    # Docs follow-up detection
    docs_findings = detect_docs_followup(root, all_findings)
    all_findings.extend(docs_findings)

    all_findings = dedupe_findings(all_findings)
    all_findings = route_findings(all_findings)
    all_findings = order_findings(all_findings)

    # Phase 5: Compute coverage
    coverage = compute_coverage(all_findings)

    # Phase 6: Determine freshness
    freshness = classify_freshness(
        artifact_git_sha=None,
        current_git_sha=settings.git_sha,
        artifact_target=None,
        current_target=state.current_target,
    )

    # Phase 7: Build and write artifact
    artifact = GTOArtifact.empty(
        mode=args.mode,
        terminal_id=args.terminal_id,
        session_id=args.session_id,
        target=state.current_target,
        git_sha=settings.git_sha,
    )
    artifact.freshness = freshness
    artifact.coverage = coverage
    artifact.summary = {
        "total_findings": len(all_findings),
        "by_severity": coverage.get("by_severity", {}),
        "by_domain": coverage.get("by_domain", {}),
    }

    artifact_path = paths.outputs_dir / "artifact.json"
    write_artifact(artifact_path, artifact, all_findings)

    # Phase 8: Save carryover for future runs
    save_carryover(paths.artifacts_dir, all_findings)

    # Phase 9: Update state
    state.phase = "completed"
    state.verification_status = "pending"
    state.last_artifact = str(artifact_path)
    state.expected_artifacts = [str(artifact_path)]
    save_state(state_file, state)

    # Phase 10: Verify
    verification = verify_artifact(artifact_path)
    state.verification_status = "pass" if verification["valid"] else "fail"
    save_state(state_file, state)

    # Output summary
    print(f"GTO complete: {len(all_findings)} findings", file=sys.stderr)
    print(f"Artifact: {artifact_path}", file=sys.stderr)
    print(f"Freshness: {freshness}", file=sys.stderr)

    return 0 if verification["valid"] else 1


if __name__ == "__main__":
    sys.exit(run())
