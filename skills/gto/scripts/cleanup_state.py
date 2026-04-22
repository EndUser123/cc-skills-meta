#!/usr/bin/env python
"""GTO State Consolidation Script.

Consolidates scattered GTO state files to centralized location:
~/.claude/.evidence/gto-state-{terminal_id}/

Removes old .evidence directories from:
- Project roots
- Skills directories
- Package directories

Also removes state files older than retention period (default: 7 days).
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from __lib.state_manager import StateManager


def get_current_git_sha(project_root: Path) -> str | None:
    """Get current git SHA for a project root.

    Args:
        project_root: Project root directory

    Returns:
        Git SHA (40-char hex) or None if not a git repo
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def clean_stale_gto_evidence(project_root: Path) -> dict:
    """Evict stale GTO evidence when target hasn't changed since last run.

    Reads the git SHA from each artifact in ~/.claude/.evidence/gto-outputs/.
    If current SHA == artifact's SHA, the target code hasn't changed → evict.

    Args:
        project_root: Project root to check git SHA against

    Returns:
        Dictionary with eviction results: {evicted: int, errors: list}
    """
    results: dict = {"evicted": 0, "errors": [], "skipped": []}

    current_sha = get_current_git_sha(project_root)
    if not current_sha:
        results["skipped"].append("Not a git repository or git unavailable")
        return results

    evidence_dir = Path.home() / ".evidence" / "gto-outputs"
    if not evidence_dir.exists():
        results["skipped"].append("No gto-outputs directory found")
        return results

    artifact_files = list(evidence_dir.glob("gto-artifact-*.json"))
    if not artifact_files:
        results["skipped"].append("No artifact files to check")
        return results

    for artifact_path in artifact_files:
        try:
            with open(artifact_path, encoding="utf-8") as f:
                artifact = json.load(f)

            # Check stored git_sha in metadata
            metadata = artifact.get("metadata", {})
            artifact_sha = metadata.get("git_sha") or metadata.get("git_context", {}).get("sha")

            if artifact_sha and artifact_sha == current_sha:
                # Target unchanged since last run — evidence is stale
                artifact_path.unlink()
                results["evicted"] += 1
        except (OSError, json.JSONDecodeError, PermissionError) as e:
            results["errors"].append(f"{artifact_path}: {e}")

    return results


def cleanup_all_evidence_dirs() -> dict:
    """Clean up all scattered GTO .evidence directories.

    Returns:
        Dictionary with cleanup results
    """
    # Define all project roots to clean up
    project_roots = [
        Path(r"P:\.claude"),  # Claude config root
        Path(r"P:\.claude\skills"),  # Skills directory
        Path(r"P:\.claude\skills\gto"),  # GTO skill directory
        Path(r"P:\p"),  # P: drive root
        Path(r"P:\p\packages"),  # Packages directory
        Path(r"P:\p\packages\handoff"),  # Handoff package
    ]

    results = {"removed": [], "errors": [], "skipped": []}

    for project_root in project_roots:
        if not project_root.exists():
            continue

        # Check for .evidence directory
        evidence_dir = project_root / ".evidence"
        if not evidence_dir.exists():
            continue

        # Find GTO state directories
        gto_state_dirs = list(evidence_dir.glob("gto-state-*"))
        gto_history_files = list(evidence_dir.glob("gto-history-*.jsonl"))

        if not gto_state_dirs and not gto_history_files:
            # Try to remove empty .evidence directory
            try:
                if not list(evidence_dir.iterdir()):
                    evidence_dir.rmdir()
                    results["removed"].append(f"{evidence_dir} (empty)")
                else:
                    results["skipped"].append(f"{evidence_dir} (not empty)")
            except OSError as e:
                results["errors"].append(f"{evidence_dir}: {e}")
            continue

        # Remove GTO state directories
        for state_dir in gto_state_dirs:
            try:
                shutil.rmtree(state_dir)
                results["removed"].append(str(state_dir))
            except OSError as e:
                results["errors"].append(f"{state_dir}: {e}")

        # Remove GTO history files
        for history_file in gto_history_files:
            try:
                history_file.unlink()
                results["removed"].append(str(history_file))
            except OSError as e:
                results["errors"].append(f"{history_file}: {e}")

        # Try to remove .evidence directory if now empty
        try:
            if evidence_dir.exists() and not list(evidence_dir.iterdir()):
                evidence_dir.rmdir()
                results["removed"].append(str(evidence_dir))
        except OSError:
            pass

    return results


def main():
    """Run cleanup and display results."""
    parser = argparse.ArgumentParser(description="GTO State Consolidation and Age-Based Cleanup")
    parser.add_argument(
        "--retention-days",
        type=int,
        default=7,
        help="Number of days to retain state files (default: 7)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without actually removing",
    )

    args = parser.parse_args()

    print("GTO State Consolidation and Cleanup")
    print("=" * 50)
    print()
    print("This script performs two cleanup operations:")
    print()
    print("1. Consolidate scattered .evidence directories to:")
    print("   ~/.claude/.evidence/gto-state-{terminal_id}/")
    print()
    print(f"2. Remove state files older than {args.retention_days} days")
    print()
    if args.dry_run:
        print("** DRY RUN MODE ** - No files will be deleted")
        print()

    # Step 1: Consolidate scattered directories
    print("Step 1: Consolidating scattered directories...")
    print("-" * 50)
    results = cleanup_all_evidence_dirs()

    if results["removed"]:
        print(f"\nWould remove {len(results['removed'])} items:")
        for item in results["removed"]:
            print(f"  ✓ {item}")

    if results["skipped"]:
        print(f"\nSkipped {len(results['skipped'])} items:")
        for item in results["skipped"]:
            print(f"  → {item}")

    if results["errors"]:
        print(f"\nErrors ({len(results['errors'])}):")
        for error in results["errors"]:
            print(f"  ✗ {error}")

    # Step 2: Age-based cleanup
    print()
    print(f"Step 2: Removing state files older than {args.retention_days} days...")
    print("-" * 50)

    state_manager = StateManager()
    age_results = state_manager.cleanup_old_state_files(retention_days=args.retention_days)

    if age_results["removed"]:
        print(f"\nWould remove {len(age_results['removed'])} old items:")
        for item in age_results["removed"]:
            print(f"  ✓ {item}")

    if age_results["errors"]:
        print(f"\nErrors ({len(age_results['errors'])}):")
        for error in age_results["errors"]:
            print(f"  ✗ {error}")

    # Summary
    print()
    print("=" * 50)
    print("Summary")
    print("-" * 50)
    total_removed = len(results["removed"]) + len(age_results["removed"])
    total_errors = len(results["errors"]) + len(age_results["errors"])

    if args.dry_run:
        print(f"DRY RUN: Would remove {total_removed} items")
    else:
        print(f"Removed {total_removed} items")

    if total_errors > 0:
        print(f"Encountered {total_errors} errors")

    print()
    print("New state location: ~/.claude/.evidence/")
    print(f"Retention policy: {args.retention_days} days")

    return 0 if (total_errors == 0 or args.dry_run) else 1


if __name__ == "__main__":
    sys.exit(main())
