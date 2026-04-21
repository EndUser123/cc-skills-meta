#!/usr/bin/env python3
"""
extract_from_monorepo.py - Extract package from monorepo for GitHub publication

This script handles two extraction methods:
1. Subtree split: Preserves git history from the monorepo
2. Fresh init: Creates a clean git history without monorepo artifacts

Usage:
    python extract_from_monorepo.py <target_dir> <package_name> [--fresh-init]

Examples:
    python extract_from_monorepo.py P:/packages/search-research search-research
    python extract_from_monorepo.py P:/packages/my-package my-package --fresh-init
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


class Colors:
    """ANSI color codes for terminal output."""

    BLUE = "\033[0;34m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    RED = "\033[0;31m"
    NC = "\033[0m"  # No Color


def log_info(msg: str) -> None:
    """Print info message."""
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {msg}")


def log_success(msg: str) -> None:
    """Print success message."""
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {msg}")


def log_warning(msg: str) -> None:
    """Print warning message."""
    print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {msg}")


def log_error(msg: str) -> None:
    """Print error message."""
    print(f"{Colors.RED}[ERROR]{Colors.NC} {msg}")


def run_command(
    cmd: list[str], cwd: Optional[Path] = None, check: bool = True
) -> subprocess.CompletedProcess:
    """Run a shell command."""
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, check=check
        )
        return result
    except subprocess.CalledProcessError as e:
        log_error(f"Command failed: {' '.join(cmd)}")
        log_error(f"Error: {e.stderr}")
        raise


def check_monorepo(target_dir: Path) -> bool:
    """Check if target is in a monorepo."""
    if not (target_dir / ".git").exists():
        log_info("Not in a git repository - treating as standalone")
        return False

    # Check if this is part of the P: monorepo
    try:
        result = run_command(
            ["git", "remote", "get-url", "origin"], cwd=target_dir, check=False
        )
        remote_url = result.stdout.strip()

        if "P.git" in remote_url or "monorepo" in remote_url:
            log_info(f"Detected monorepo membership (remote: {remote_url})")
            return True
    except Exception:
        pass

    # Check if we're inside a packages/ directory
    if "/packages/" in str(target_dir) or "\\packages\\" in str(target_dir):
        log_info("Detected packages/ directory structure - likely monorepo member")
        return True

    return False


def get_package_path(target_dir: Path) -> Optional[str]:
    """Get relative path from monorepo root."""
    try:
        result = run_command(["git", "rev-parse", "--show-toplevel"], cwd=target_dir)
        monorepo_root = Path(result.stdout.strip())

        # Get relative path from monorepo root to target
        package_path = os.path.relpath(target_dir, monorepo_root)
        return package_path
    except Exception:
        log_error("Cannot determine monorepo root")
        return None


def extract_subtree_split(target_dir: Path, package_name: str) -> bool:
    """Method 1: Subtree split (preserves history)."""
    log_info("=== Method 1: Subtree Split (preserves history) ===")

    package_path = get_package_path(target_dir)
    if not package_path:
        log_error("Failed to determine package path")
        return False

    log_info(f"Package path in monorepo: {package_path}")

    # Check if git subtree is available
    try:
        run_command(["git", "subtree", "--help"], check=False)
    except Exception:
        log_error("git subtree not available. Install git 2.30+ or use --fresh-init")
        return False

    monorepo_root = target_dir
    while (monorepo_root / ".git").exists() and (
        monorepo_root.parent / ".git"
    ).exists():
        monorepo_root = monorepo_root.parent

    # Create a temporary branch for the split
    split_branch = f"split-{package_name}"

    log_info(f"Creating split branch: {split_branch}")

    try:
        run_command(
            [
                "git",
                "subtree",
                "split",
                "--prefix",
                package_path,
                "--branch",
                split_branch,
            ],
            cwd=monorepo_root,
        )
    except subprocess.CalledProcessError:
        log_error("Subtree split failed. Package may not have meaningful history.")
        log_warning("Falling back to fresh init...")
        return False

    log_success(f"Subtree split complete. Branch: {split_branch}")

    # Remove existing .git if present
    if (target_dir / ".git").exists():
        log_warning("Removing existing .git directory")
        import shutil

        shutil.rmtree(target_dir / ".git")

    # Initialize new repo
    log_info("Creating new git repository in target directory")
    run_command(["git", "init"], cwd=target_dir)

    # Copy files from split branch
    # Export the tree from the split branch
    import tempfile

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / package_name
        temp_path.mkdir(parents=True, exist_ok=True)

        # Checkout files from split branch to temp location
        try:
            run_command(
                ["git", "checkout", split_branch, "--", "."],
                cwd=monorepo_root,
                check=False,
            )
        except Exception:
            pass

        # Copy files
        import shutil

        if (monorepo_root / package_path).exists():
            for item in (monorepo_root / package_path).iterdir():
                dest = target_dir / item.name
                if dest.exists():
                    if dest.is_dir():
                        shutil.rmtree(dest)
                    else:
                        dest.unlink()
                shutil.copy2(item, dest)

    # Initial commit
    run_command(["git", "add", "-A"], cwd=target_dir)
    try:
        run_command(
            [
                "git",
                "commit",
                "-m",
                f"Initial commit of {package_name}\n\n"
                f"Extracted from monorepo using git subtree split.\n"
                f"Preserves git history from original development.",
            ],
            cwd=target_dir,
        )
    except subprocess.CalledProcessError:
        log_warning("No files to commit")

    # Cleanup
    try:
        run_command(
            ["git", "branch", "-D", split_branch], cwd=monorepo_root, check=False
        )
    except Exception:
        pass

    log_success("Subtree extraction complete")
    return True


def extract_fresh_init(target_dir: Path, package_name: str) -> bool:
    """Method 2: Fresh init (clean slate)."""
    log_info("=== Method 2: Fresh Init (clean slate) ===")

    # Backup existing .git if present
    if (target_dir / ".git").exists():
        import time
        import shutil

        backup_dir = target_dir / f".git.backup-{int(time.time())}"
        log_warning(f"Backing up existing .git to: {backup_dir}")
        shutil.move(target_dir / ".git", backup_dir)

    # Initialize new git repository
    log_info("Initializing new git repository")
    run_command(["git", "init"], cwd=target_dir)

    # Create initial commit
    log_info("Creating initial commit")
    run_command(["git", "add", "-A"], cwd=target_dir)

    # Check if there are any files to commit
    result = run_command(
        ["git", "diff", "--cached", "--quiet"], cwd=target_dir, check=False
    )
    if result.returncode == 0:
        log_warning("No files to commit. Repository initialized but empty.")
        return True

    run_command(
        [
            "git",
            "commit",
            "-m",
            f"Initial commit of {package_name}\n\n"
            f"Fresh initialization for GitHub publication.\n"
            f"Clean git history without monorepo artifacts.",
        ],
        cwd=target_dir,
    )

    log_success("Fresh init complete")
    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Extract package from monorepo for GitHub publication"
    )
    parser.add_argument("target_dir", type=Path, help="Target directory to extract")
    parser.add_argument("package_name", help="Name of the package")
    parser.add_argument(
        "--fresh-init",
        action="store_true",
        help="Use fresh init instead of subtree split",
    )

    args = parser.parse_args()

    target_dir = args.target_dir.resolve()
    package_name = args.package_name

    log_info("=== Monorepo Extraction ===")
    log_info(f"Target: {target_dir}")
    log_info(f"Package: {package_name}")

    # Verify target directory exists
    if not target_dir.exists():
        log_error(f"Target directory does not exist: {target_dir}")
        sys.exit(1)

    # Check if we need to extract from monorepo
    if check_monorepo(target_dir):
        log_info("Package is in a monorepo - extraction required")

        if args.fresh_init:
            log_info("Using fresh init method (--fresh-init flag specified)")
            if not extract_fresh_init(target_dir, package_name):
                log_error("Extraction failed")
                sys.exit(1)
        else:
            # Try subtree split first, fall back to fresh init
            if not extract_subtree_split(target_dir, package_name):
                log_warning("Subtree split failed, falling back to fresh init")
                if not extract_fresh_init(target_dir, package_name):
                    log_error("Extraction failed")
                    sys.exit(1)
    else:
        log_info("Package is standalone - no extraction needed")
        # Just ensure git is initialized
        if not (target_dir / ".git").exists():
            run_command(["git", "init"], cwd=target_dir)
            run_command(["git", "add", "-A"], cwd=target_dir)
            result = run_command(
                ["git", "diff", "--cached", "--quiet"], cwd=target_dir, check=False
            )
            if result.returncode != 0:
                run_command(
                    ["git", "commit", "-m", f"Initial commit of {package_name}"],
                    cwd=target_dir,
                )

    # Set main branch
    try:
        run_command(["git", "branch", "-M", "main"], cwd=target_dir, check=False)
    except Exception:
        pass

    log_success("=== Extraction Complete ===")
    log_info(f"Git repository ready at: {target_dir}")
    log_info("Branch: main")

    # Show git status
    print()
    log_info("Git status:")
    result = run_command(["git", "status", "--short"], cwd=target_dir, check=False)
    print(result.stdout)


if __name__ == "__main__":
    main()
