#!/usr/bin/env python3
r"""Run GTO analysis on monorepo subdirectories.

This script bypasses the viability gate's git repository check
to allow GTO analysis on monorepo subdirectories that don't have
their own .git directory.

Usage (CLI):
    python run_gto_monorepo.py --project-root "P:\.claude\skills\gto"

Usage (as module):
    from run_gto_monorepo import run_gto_analysis
    results = run_gto_analysis(Path("P:\.claude\skills\gto"))
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from __lib import (
    build_initial_results,
    format_rsn_from_gaps,
)


def run_gto_analysis(
    project_root: Path,
    output_dir: Path | None = None,
) -> dict:
    r"""Run GTO analysis on a project directory.

    Args:
        project_root: Path to the project to analyze
        output_dir: Optional output directory. Defaults to ~/.claude/.evidence/gto-outputs/

    Returns:
        Dict with analysis results including gaps and metadata
    """
    if output_dir is None:
        output_dir = Path.home() / ".evidence" / "gto-outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Running GTO analysis on: {project_root}")
    print("=" * 80)

    # Step 1: Run all detectors
    print("\n[1/5] Running detectors...")
    detector_results = {}

    # Chain integrity check expects transcript file paths, not a project directory.
    # For monorepo analysis (project_root is a directory), skip this check.
    # It is only relevant for handoff transcript analysis.
    from __lib.chain_integrity_checker import ChainIntegrityResult

    detector_results["chain_integrity"] = ChainIntegrityResult(
        paths=[],
        partial_scope=False,
        excluded=[],
        warnings=[],
    )
    # Re-enable by uncommenting below:
    # marker_results = scan_code_markers(project_root)
    # detector_results["code_markers"] = marker_results
    # detector_results["test_presence"] = check_test_presence(project_root)
    # detector_results["docs_presence"] = check_docs_presence(project_root)
    # detector_results["dependencies"] = check_dependencies(project_root)
    # print(f"  - Code markers: {marker_results.total_count} found in {marker_results.files_with_markers} files")
    # print(f"  - Test presence: {detector_results['test_presence']}")
    # print(f"  - Docs presence: {detector_results['docs_presence']}")
    # print(f"  - Dependencies: {detector_results['dependencies']}")

    # Step 2: Build initial results
    print("\n[2/5] Building results...")
    results = build_initial_results(detector_results, project_root)
    print(f"  - Total gaps found: {results.total_gap_count}")
    print(f"  - Critical: {results.critical_count}")
    print(f"  - High: {results.high_count}")
    print(f"  - Medium: {results.medium_count}")
    print(f"  - Low: {results.low_count}")

    # Step 3: Format recommended next steps
    print("\n[3/5] Formatting recommended next steps...")
    from __lib.skill_coverage_detector import detect_skill_coverage

    # Compute target_key same way as gto_orchestrator.py
    try:
        target_key = str(project_root.relative_to(Path.cwd()))
    except ValueError:
        target_key = str(project_root)

    gaps_as_dicts = [gap.to_dict() for gap in results.gaps]
    coverage_findings = detect_skill_coverage(
        project_root, target_key=target_key, gaps=gaps_as_dicts
    )
    all_findings = gaps_as_dicts + coverage_findings

    rns_md = format_rsn_from_gaps(all_findings, show_effort=True)

    # Compute RNS counts from findings (format_rsn_from_gaps returns markdown only)
    total_rns = len(all_findings)
    critical_rns = sum(1 for f in all_findings if f.get("severity", "").upper() == "CRITICAL")
    high_rns = sum(1 for f in all_findings if f.get("severity", "").upper() == "HIGH")
    medium_rns = sum(1 for f in all_findings if f.get("severity", "").upper() == "MEDIUM")
    low_rns = sum(1 for f in all_findings if f.get("severity", "").upper() == "LOW")
    total_effort = sum(f.get("effort_estimate_minutes", 0) for f in all_findings)

    print(f"  - Generated {total_rns} recommendations")
    print(f"  - Estimated effort: {total_effort} minutes")

    # Group gaps by category for reporting
    from collections import defaultdict

    gaps_by_category = defaultdict(list)
    for gap in results.gaps:
        gaps_by_category[gap.type].append(gap)

    # Step 5: Save results
    print("\n[5/5] Saving results...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    md_file = output_dir / f"gto-report-{timestamp}.md"

    with open(md_file, "w", encoding="utf-8") as f:
        # Use project name from directory
        project_name = project_root.name
        f.write(f"# GTO Analysis Report: {project_name}\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Project Root:** `{project_root}`\n")
        f.write("**Analysis Type:** Monorepo subdirectory (viability check bypassed)\n\n")
        f.write("## Summary\n\n")
        f.write(f"- **Total Gaps:** {results.total_gap_count}\n")
        f.write(f"- **Critical:** {results.critical_count}\n")
        f.write(f"- **High:** {results.high_count}\n")
        f.write(f"- **Medium:** {results.medium_count}\n")
        f.write(f"- **Low:** {results.low_count}\n\n")
        f.write("## Gaps by Category\n\n")
        for category, gaps in sorted(gaps_by_category.items()):
            f.write(f"### {category}\n\n")
            for gap in gaps[:5]:  # First 5 gaps per category
                f.write(
                    f"- [{gap.severity.upper()}] {gap.message} ({gap.file_path}:{gap.line_number})\n"
                )
            if len(gaps) > 5:
                f.write(f"- ... and {len(gaps) - 5} more\n")
            f.write("\n")
        f.write("## Recommended Next Steps\n\n")
        f.write(rns_md)

    print(f"  - Saved markdown report: {md_file}")

    # Save JSON artifact
    json_file = output_dir / f"gto-artifact-{timestamp}.json"
    artifact = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(project_root),
            "gto_version": "3.1.0",
            "analysis_type": "monorepo_subdirectory",
        },
        "summary": {
            "total_gaps": results.total_gap_count,
            "critical_count": results.critical_count,
            "high_count": results.high_count,
            "medium_count": results.medium_count,
            "low_count": results.low_count,
            "by_category": {k: len(v) for k, v in gaps_by_category.items()},
        },
        "gaps": [g.to_dict() for g in results.gaps],
        "recommended_next_steps": rns_md,
        "next_steps_summary": {
            "total_count": total_rns,
            "critical_count": critical_rns,
            "high_count": high_rns,
            "medium_count": medium_rns,
            "low_count": low_rns,
            "total_effort_minutes": total_effort,
        },
    }

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2, default=str)

    print(f"  - Saved JSON artifact: {json_file}")

    # Log skill run to shared skill-usage log
    from __lib.state_manager import get_state_manager

    sm = get_state_manager(project_root=project_root)

    # Serialize Gap objects and other non-JSON types in metadata
    def _to_serializable(obj: Any) -> Any:
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        if isinstance(obj, list):
            return [_to_serializable(i) for i in obj]
        if isinstance(obj, dict):
            return {k: _to_serializable(v) for k, v in obj.items()}
        return obj

    try:
        sm.log_skill_run(
            {
                "type": "skill_run",
                "skill": "gto",
                "timestamp": datetime.now().isoformat(),
                "status": "complete",
                "gaps_detected": results.total_gap_count,
                "metadata": {
                    "gaps_by_category": _to_serializable(dict(gaps_by_category)),
                },
            }
        )
        print(f"  - Logged skill run to: {sm.skill_usage_log_path}")
    except OSError as e:
        print(f"  - WARNING: Could not acquire skill-usage lock: {e}")
        print(f"    (Skill usage log is non-critical — continuing without logging)")

    print("\n" + "=" * 80)
    print("Analysis complete!")
    print(f"Results saved to: {output_dir}")

    # Also save a copy with consistent names for easy access
    (output_dir / "gto-report-latest.md").write_text(md_file.read_text())
    (output_dir / "gto-artifact-latest.json").write_text(json_file.read_text())
    print("  - Also saved as: gto-report-latest.md")
    print("  - Also saved as: gto-artifact-latest.json")

    return {
        "summary": {
            "total_gaps": results.total_gap_count,
            "critical_count": results.critical_count,
            "high_count": results.high_count,
            "medium_count": results.medium_count,
            "low_count": results.low_count,
        },
        "gaps": [g.to_dict() for g in results.gaps],
        "artifact_path": str(json_file),
        "report_path": str(md_file),
    }


def main() -> None:
    r"""CLI entry point for GTO analysis.

    Parses command-line arguments and runs the analysis.
    """
    parser = argparse.ArgumentParser(description="Run GTO analysis on a project directory")
    parser.add_argument(
        "--project-root",
        type=Path,
        required=True,
        help="Path to the project directory to analyze",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional output directory (defaults to ~/.claude/.evidence/gto-outputs/)",
    )

    args = parser.parse_args()

    # Run the analysis
    run_gto_analysis(
        project_root=args.project_root,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
