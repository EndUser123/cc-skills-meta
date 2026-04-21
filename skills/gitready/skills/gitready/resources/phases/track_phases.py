#!/usr/bin/env python3
"""
Track phase completion in the target package's changelog.

Reads the target's references/changelog.md to determine which phases have
already completed, and appends phase completion markers after each run.

Format in changelog:
  ## v5.25.0 (2026-04-14)
  - PHASE 1: Diagnose and Prep -- COMPLETED
  - PHASE 1.5: Detect Package Type -- COMPLETED
"""

import argparse
import re
import sys
from pathlib import Path


def find_changelog(target_dir: Path) -> Path | None:
    """Find changelog.md in the target package.

    Preference order:
    1. references/changelog.md (gitready convention) -- if references/ exists, always use this path
    2. changelog.md (root level)
    3. CHANGELOG.md (root level, uppercase)
    """
    # If references/ exists, always use it as the canonical path (even if file doesn't exist yet)
    refs_dir = target_dir / "references"
    if refs_dir.exists() and refs_dir.is_dir():
        return refs_dir / "changelog.md"

    candidates = [
        target_dir / "changelog.md",
        target_dir / "CHANGELOG.md",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def parse_completed_phases(changelog_path: Path) -> dict[str, str]:
    """Parse the changelog and return dict of phase -> status."""
    phases = {}
    if not changelog_path.exists():
        return phases

    content = changelog_path.read_text(encoding="utf-8")
    pattern = re.compile(r"^\s*-\s*(PHASE\s+[\d.]+):\s*.*--\s*(COMPLETED|SKIPPED)", re.IGNORECASE)
    for line in content.splitlines():
        match = pattern.match(line)
        if match:
            phase_match = re.search(r"(PHASE\s+[\d.]+)", line, re.IGNORECASE)
            status_match = re.search(r"--\s*(COMPLETED|SKIPPED)", line, re.IGNORECASE)
            if phase_match and status_match:
                phases[phase_match.group(1).upper()] = status_match.group(1).upper()
    return phases


def append_phase_completion(changelog_path: Path, phase_name: str, phase_desc: str, status: str = "COMPLETED") -> None:
    """Append a phase completion marker to the changelog."""
    marker = f"- PHASE {phase_name}: {phase_desc} -- {status}"

    if changelog_path.exists():
        content = changelog_path.read_text(encoding="utf-8")
    else:
        # Create minimal changelog if none exists
        content = "# Changelog\n\n"

    # Normalize line endings
    content = content.rstrip() + "\n"

    # If content doesn't end with newline, add one
    if content and not content.endswith("\n"):
        content += "\n"

    content += marker + "\n"
    changelog_path.write_text(content, encoding="utf-8")


PHASE_DEFINITIONS = {
    "1": "Diagnose and Prep",
    "1.5": "Detect Package Type",
    "1.6": "Brownfield Conversion",
    "1.6.5": "Intentional Exception Registry",
    "1.7": "Plugin Standards Validation",
    "1.8": "Stale Location Cleanup and Junction/Symlink Setup",
    "2": "Build Structure",
    "3": "Generate Templates",
    "4": "Validate",
    "4.5": "Code Review and Meta-Review",
    "4.6": "Quality Scanning",
    "4.7": "Media Generation",
    "4.8": "Interactive Course",
    "5": "Portfolio Polish",
    "6": "GitHub Publication",
    "7": "Repository Finalization",
    "8": "Cleanup",
    "9": "Git Ready",
    "10": "Recruiter Readiness Validation",
}


def get_package_type(target_dir: Path) -> str | None:
    """Detect package type from target directory."""
    if (target_dir / ".claude-plugin").exists():
        return "claude-plugin"
    if (target_dir / "src").exists() and (target_dir / "pyproject.toml").exists():
        return "brownfield-plugin"
    if (target_dir / "skill" / "SKILL.md").exists():
        return "claude-skill"
    if (target_dir / "pyproject.toml").exists():
        return "python-library"
    return None


def get_auto_skip_reasons(target_dir: Path) -> dict[str, str]:
    """Return dict of phase -> auto-skip reason based on package state."""
    reasons = {}
    pkg_type = get_package_type(target_dir)
    if pkg_type != "brownfield-plugin":
        reasons["1.6"] = f"not brownfield-plugin ({pkg_type})"
    if not (target_dir / "references").exists():
        reasons["1.6.5"] = "no .gitready/exceptions.json needed"
    if not (target_dir / "scripts" / "hooks").exists():
        reasons["1.8"] = "no hooks to clean up"
    if pkg_type in ("claude-plugin", "brownfield-plugin"):
        reasons["4.5"] = "requires code-review plugin"
    reasons["4.7"] = "requires NotebookLM auth"
    reasons["4.8"] = "requires NotebookLM auth"
    reasons["6"] = "requires --publish flag"
    reasons["7"] = "requires --finalize flag"
    return reasons


def print_status_report(target_dir: Path, changelog_path: Path | None) -> None:
    """Print full phase status report."""
    pkg_type = get_package_type(target_dir)
    resolved = target_dir.resolve()
    print(f"\n=== gitready Status: {resolved} ===")
    print(f"Package type: {pkg_type or 'unknown'}\n")

    if changelog_path is None or not changelog_path.exists():
        print("No changelog found -- all phases PENDING")
        print("\nRun `/gitready` to start the pipeline.\n")
        return

    tracked = parse_completed_phases(changelog_path)
    auto_skips = get_auto_skip_reasons(target_dir)

    print(f"{'Phase':<8} {'Description':<45} {'Status':<12}")
    print("-" * 70)

    for num, desc in PHASE_DEFINITIONS.items():
        key = f"PHASE {num}"
        if key in tracked:
            status = tracked[key]
            marker = "✓" if status == "COMPLETED" else "⏭"
            print(f"PHASE {num:<4} {desc:<45} {marker} {status}")
        elif num in auto_skips:
            reason = auto_skips[num]
            if "not brownfield-plugin" in reason or "no .gitready" in reason:
                display_status = "N/A"
                print(f"PHASE {num:<4} {desc:<45} ⏭ {display_status:6} ({reason})")
            else:
                print(f"PHASE {num:<4} {desc:<45} ⏭ SKIPPED   ({reason})")
        else:
            print(f"PHASE {num:<4} {desc:<45} ○ PENDING")

    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Track gitready phase completion in changelog")
    parser.add_argument("target_dir", help="Target package directory")
    parser.add_argument("--read", action="store_true", help="Read completed phases from changelog")
    parser.add_argument("--status", action="store_true", help="Show full status report for target package")
    parser.add_argument("--write", help="Write completed phase (e.g. '1' or '1.5')")
    parser.add_argument("--write-status", default="COMPLETED", help="Status: COMPLETED or SKIPPED (default: COMPLETED)")
    parser.add_argument("--list", action="store_true", help="List all phase definitions")
    args = parser.parse_args()

    target = Path(args.target_dir)

    if args.list:
        for num, desc in PHASE_DEFINITIONS.items():
            print(f"PHASE {num}: {desc}")
        return

    changelog = find_changelog(target)

    if args.status:
        print_status_report(target, changelog)
        return

    if args.read:
        if changelog is None:
            print("No changelog found -- all phases pending", file=sys.stderr)
            print("ALL_PENDING")
            return
        completed = parse_completed_phases(changelog)
        if not completed:
            print("No phases completed yet", file=sys.stderr)
            print("ALL_PENDING")
            return
        print(f"COMPLETED: {','.join(sorted(completed))}")
        return

    if args.write:
        phase_num = args.write
        if phase_num not in PHASE_DEFINITIONS:
            print(f"Unknown phase: {phase_num}", file=sys.stderr)
            sys.exit(1)

        if changelog is None:
            changelog = target / "references" / "changelog.md"
            changelog.parent.mkdir(parents=True, exist_ok=True)

        append_phase_completion(changelog, phase_num, PHASE_DEFINITIONS[phase_num], args.write_status)
        print(f"Tracked: PHASE {phase_num} -- {args.write_status} in {changelog}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
