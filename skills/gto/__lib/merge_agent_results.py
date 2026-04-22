#!/usr/bin/env python
"""Merge GTO L1 gaps with agent findings into unified artifact."""
import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

VALID_SEVERITIES = {"HIGH", "MEDIUM", "LOW", "critical", "high", "medium", "low"}
SEVERITY_MAP = {"critical": "CRITICAL", "high": "HIGH", "medium": "MEDIUM", "low": "LOW"}
REQUIRED_FIELDS = {"id", "severity", "location", "title"}


def load_json_file(path: Path) -> dict[str, Any]:
    """Load JSON with explicit error handling."""
    if not path.exists():
        raise FileNotFoundError(path)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {path}: {e}", file=sys.stderr)
        raise


def validate_finding(finding: dict[str, Any], source: str) -> bool:
    """Validate finding has required fields and valid severity."""
    missing = REQUIRED_FIELDS - finding.keys()
    if missing:
        print(f"WARNING: [{source}] Finding {finding.get('id', 'UNKNOWN')} missing fields: {missing}", file=sys.stderr)
        return False
    severity = finding.get("severity", "")
    if severity not in VALID_SEVERITIES:
        print(f"WARNING: [{source}] Finding {finding['id']} has invalid severity: {severity}", file=sys.stderr)
        return False
    return True


def merge_gaps(l1_data: dict, agent_data: dict[str, dict]) -> dict[str, Any]:
    """Merge L1 gaps with agent findings."""
    gaps = l1_data.get("gaps", []).copy()
    seen_ids: set[str] = {g.get("id") for g in gaps if "id" in g}
    # Merge correctness agent results (use "findings" key)
    for agent_key, data in agent_data.items():
        findings = data.get("findings", [])
        source = f"adversarial-{agent_key}"
        for finding in findings:
            if validate_finding(finding, source):
                gap_id = finding.get("id", "")
                if gap_id and gap_id in seen_ids:
                    print(f"WARNING: Duplicate gap ID {gap_id} from {source} — skipping", file=sys.stderr)
                    continue
                severity = finding.get("severity", "")
                if severity in SEVERITY_MAP:
                    severity = SEVERITY_MAP[severity]
                gap: dict[str, Any] = {**finding, "source": source}
                gap["severity"] = severity
                # Mark correctness agent findings so they map to correctness domain in RNS
                gap["type"] = "correctness_gap"
                gap["domain"] = "correctness"
                if gap_id:
                    seen_ids.add(gap_id)
                gaps.append(gap)
    return {"gaps": gaps}


def _resolve_path(path_str: str) -> Path:
    """Resolve a path, handling /tmp/ Unix-style prefixes on Windows."""
    p = Path(path_str)
    # Already absolute on Windows (e.g. C:\Users\...) or Unix — use as-is
    if p.is_absolute():
        return p
    # Handle /tmp/ prefix on Windows: Python tempfile.gettempdir() uses the system temp,
    # which differs from bash's /tmp/. Resolve by replacing /tmp/ with the actual temp dir.
    if path_str.startswith("/tmp/") or path_str.startswith("\\tmp\\"):
        system_temp = Path(tempfile.gettempdir())
        normalized = path_str.replace("/tmp/", "").replace("\\tmp\\", "")
        return system_temp / normalized
    return p


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge GTO L1 and agent results")
    parser.add_argument("--l1", required=True, help="Path to L1 output JSON")
    parser.add_argument(
        "--agents", dest="agents", action="append", default=[],
        help="Path or glob pattern for agent JSON (may be specified multiple times)",
    )
    parser.add_argument("--output", required=True, help="Output path for merged artifact")
    parser.add_argument("--validate-schema", action="store_true")
    args = parser.parse_args()

    # Load L1 data
    l1_path = _resolve_path(args.l1)
    l1_data = load_json_file(l1_path)
    if "gaps" not in l1_data:
        print(f"ERROR: L1 output missing 'gaps' field: {l1_path}", file=sys.stderr)
        return 1

    # Load agent data from all accumulated paths
    agent_data: dict[str, Any] = {}
    seen_sources: dict[str, Path] = {}
    for agents_arg in args.agents:
        agent_path = _resolve_path(agents_arg)
        if not agent_path.exists():
            print(f"WARNING: Agent path not found: {agents_arg}", file=sys.stderr)
            continue
        if agent_path.is_dir():
            agent_files = list(agent_path.rglob("*"))
        else:
            agent_files = list(agent_path.parent.glob(agent_path.name))
        if not agent_files:
            print(f"WARNING: No agent files found at: {agents_arg}", file=sys.stderr)
            continue
        for agent_file in sorted(agent_files):
            try:
                parts = agent_file.stem.split("-")
                if len(parts) >= 3:
                    agent_key = parts[2]  # "logic", "quality", "code-critic"
                    if agent_key in seen_sources:
                        continue  # skip duplicates silently (first wins)
                    seen_sources[agent_key] = agent_file
                    agent_data[agent_key] = load_json_file(agent_file)
            except Exception as e:
                print(f"WARNING: Failed to load agent file {agent_file}: {e}", file=sys.stderr)
                continue

    # Merge and write
    merged = merge_gaps(l1_data, agent_data)

    # Compute health_score for assertions (0-100, 100 = no gaps)
    gaps = merged["gaps"]
    total = len(gaps)
    if total == 0:
        health_score = 100
    else:
        high_count = sum(1 for g in gaps if g.get("severity") == "HIGH")
        critical_count = sum(1 for g in gaps if g.get("severity") == "CRITICAL")
        health_score = max(0, 100 - (critical_count * 25) - (high_count * 10) - ((total - critical_count - high_count) * 2))
    merged["health_score"] = health_score

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    print(f"INFO: Wrote merged artifact: {output_path} ({len(merged['gaps'])} gaps, health_score={health_score})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
