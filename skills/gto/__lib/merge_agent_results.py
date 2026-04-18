#!/usr/bin/env python3
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


def merge_gaps(l1_data: dict, agent_data: dict[str, dict], gap_finder_data: dict | None = None) -> dict[str, Any]:
    """Merge L1 gaps with agent findings and gap_finder results."""
    gaps = l1_data.get("gaps", []).copy()
    seen_ids: set[str] = {g.get("id") for g in gaps if "id" in g}

    # Merge gap_finder results (uses "gaps" key, different schema)
    if gap_finder_data:
        gap_finder_gaps = gap_finder_data.get("gaps", [])
        for gap in gap_finder_gaps:
            gap_id = gap.get("id", "")
            if gap_id and gap_id in seen_ids:
                print(f"WARNING: Duplicate gap ID {gap_id} from gap_finder — skipping", file=sys.stderr)
                continue
            severity = gap.get("severity", "")
            if severity in SEVERITY_MAP:
                severity = SEVERITY_MAP[severity]
            merged_gap: dict[str, Any] = {**gap, "source": "gap_finder", "severity": severity}
            if gap_id:
                seen_ids.add(gap_id)
            gaps.append(merged_gap)

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


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge GTO L1 and agent results")
    parser.add_argument("--l1", required=True, help="Path to L1 output JSON")
    parser.add_argument("--gap-finder", required=False, default=None, help="Path to gap_finder agent JSON")
    parser.add_argument("--agents", required=True, help="Glob pattern for agent JSONs")
    parser.add_argument("--output", required=True, help="Output path for merged artifact")
    parser.add_argument("--validate-schema", action="store_true")
    args = parser.parse_args()

    # Load L1 data
    l1_path = Path(args.l1)
    l1_data = load_json_file(l1_path)
    if "gaps" not in l1_data:
        print(f"ERROR: L1 output missing 'gaps' field: {l1_path}", file=sys.stderr)
        return 1

    # Load gap_finder data (uses "gaps" key, different schema from correctness agents)
    gap_finder_data: dict[str, Any] | None = None
    if args.gap_finder:
        gap_finder_path = Path(args.gap_finder)
        if gap_finder_path.exists():
            gap_finder_data = load_json_file(gap_finder_path)
        else:
            print(f"WARNING: gap_finder file not found: {gap_finder_path}", file=sys.stderr)

    # Load agent data
    # Resolve /tmp Unix-style paths to platform temp directory for Windows compatibility
    agents_arg = args.agents
    if agents_arg.startswith("/tmp/") or agents_arg.startswith("\\tmp\\"):
        system_temp = Path(tempfile.gettempdir())
        # Strip the /tmp or \tmp prefix and join with system temp
        normalized = agents_arg.replace("/tmp/", "").replace("\\tmp\\", "")
        agents_arg = str(system_temp / normalized)
    agent_pattern = Path(agents_arg)
    agent_dir = agent_pattern.parent
    agent_glob = agents_arg.rsplit("/", 1)[-1] if "/" in agents_arg else agents_arg.rsplit("\\", 1)[-1]
    agent_files = list(agent_dir.glob(agent_glob))
    if not agent_files:
        print(f"WARNING: No agent files found matching pattern: {args.agents}", file=sys.stderr)

    agent_data: dict[str, Any] = {}
    seen_sources: dict[str, Path] = {}
    for agent_file in sorted(agent_files):
        try:
            parts = agent_file.stem.split("-")
            if len(parts) >= 3:
                agent_key = parts[2]  # "logic", "quality", "code-critic"
                if agent_key in seen_sources:
                    print(
                        f"WARNING: Duplicate agent source '{agent_key}' — "
                        f"{agent_file.name} overwrites {seen_sources[agent_key].name}",
                        file=sys.stderr,
                    )
                seen_sources[agent_key] = agent_file
                agent_data[agent_key] = load_json_file(agent_file)
            else:
                print(f"WARNING: Agent file does not match expected pattern (gto-correctness-{{type}}-{{terminal_id}}): {agent_file}", file=sys.stderr)
        except Exception as e:
            print(f"WARNING: Failed to load agent file {agent_file}: {e}", file=sys.stderr)
            continue

    # Merge and write
    merged = merge_gaps(l1_data, agent_data, gap_finder_data)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    print(f"INFO: Wrote merged artifact: {output_path} ({len(merged['gaps'])} gaps)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
