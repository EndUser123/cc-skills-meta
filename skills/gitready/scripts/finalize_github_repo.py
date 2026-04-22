#!/usr/bin/env python
"""
finalize_github_repo.py - PHASE 7: Repository Finalization

Automates post-publish tasks that should happen immediately after repo creation:
1. GitHub Pages enablement
2. Initial Release creation
3. Repository Topics/Tags
4. CODEOWNERS file generation

Usage:
    python finalize_github_repo.py <package_name> <target_dir> [options]

Examples:
    python finalize_github_repo.py "search-research" "P:/packages/search-research"
    python finalize_github_repo.py "my-lib" "/path/to/my-lib" --release-version 1.0.0
"""

import argparse
import subprocess
import sys
from pathlib import Path


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
    cmd: list[str], cwd: Path | None = None, check: bool = True
) -> subprocess.CompletedProcess:
    """Run a shell command."""
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, check=check
        )
        return result
    except subprocess.CalledProcessError as e:
        log_error(f"Command failed: {' '.join(cmd)}")
        if e.stderr:
            log_error(f"Error: {e.stderr}")
        raise


def check_gh_cli() -> bool:
    """Check if GitHub CLI is available and authenticated."""
    try:
        # Check if gh command exists
        run_command(["gh", "--version"], check=False)

        # Check if authenticated
        result = run_command(["gh", "auth", "status"], check=False)
        return result.returncode == 0
    except Exception:
        return False


def get_github_username() -> str:
    """Get GitHub username from gh CLI or return placeholder."""
    try:
        result = run_command(["gh", "api", "user", "--jq", ".login"], check=False)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "YOUR_USERNAME"


def get_package_topics(package_type: str) -> list[str]:
    """Get relevant topics based on package type."""
    # Base topics for all packages
    base_topics = ["python", "gitready"]

    # Type-specific topics
    type_topics = {
        "plugin": ["claude-code", "plugin", "automation"],
        "skill": ["claude-code", "skill", "ai-assistant"],
        "mcp": ["mcp", "model-context-protocol", "ai"],
        "library": ["library", "package"],
        "tool": ["tool", "cli", "utility"],
    }

    return base_topics + type_topics.get(package_type, [])


def enable_github_pages(package_name: str, target_dir: Path) -> bool:
    """Enable GitHub Pages for documentation."""
    log_info("=== Enabling GitHub Pages ===")

    if not check_gh_cli():
        log_warning("GitHub CLI not available - skipping Pages enablement")
        return False

    username = get_github_username()
    repo_slug = f"{username}/{package_name}"

    # Check if docs directory exists
    docs_dir = target_dir / "docs"
    has_docs = docs_dir.exists()

    # Determine source branch and directory
    source_branch = "main"
    source_dir = "/"  # Root directory

    if has_docs:
        source_dir = "/docs"
        log_info(f"Found docs/ directory - will serve from {source_dir}")
    else:
        log_info("No docs/ directory - serving from root")

    try:
        # Enable Pages via gh API
        run_command(
            [
                "gh",
                "api",
                "--method",
                "POST",
                f"repos/{repo_slug}/pages",
                "-f",
                f"source[branch]={source_branch}",
                "-f",
                f"source[path]={source_dir}",
            ],
            check=False,
        )

        log_success("GitHub Pages enabled!")
        log_info(f"  Branch: {source_branch}")
        log_info(f"  Path: {source_dir}")
        log_info(f"  URL: https://{username}.github.io/{package_name}/")
        return True

    except subprocess.CalledProcessError:
        log_warning("Failed to enable GitHub Pages via API")
        log_info("Manual enablement: Go to Settings > Pages in GitHub")
        return False


def create_initial_release(
    package_name: str,
    target_dir: Path,
    version: str = "0.1.0",
    generate_notes: bool = True,
) -> bool:
    """Create initial GitHub release."""
    log_info("=== Creating Initial Release ===")

    if not check_gh_cli():
        log_warning("GitHub CLI not available - skipping release creation")
        return False

    username = get_github_username()
    repo_slug = f"{username}/{package_name}"

    # Check if release already exists
    result = run_command(
        ["gh", "release", "view", f"v{version}", "--repo", repo_slug], check=False
    )
    if result.returncode == 0:
        log_warning(f"Release v{version} already exists")
        return False

    # Generate release notes from CHANGELOG
    notes = f"Release {version} of {package_name}\n\n"

    changelog_path = target_dir / "CHANGELOG.md"
    if changelog_path.exists():
        log_info("Extracting notes from CHANGELOG.md")
        try:
            with open(changelog_path) as f:
                content = f.read()
                # Extract the first version section
                lines = content.split("\n")
                in_section = False
                for line in lines:
                    if f"[{version}]" in line or "## [" in line:
                        in_section = True
                    if in_section:
                        notes += line + "\n"
                        if line.startswith("## [") and f"[{version}]" not in line:
                            break
        except Exception:
            log_warning("Could not parse CHANGELOG.md")
    else:
        log_warning("No CHANGELOG.md found - using generic notes")
        notes += f"Initial release of {package_name}.\n\n"
        notes += "See README.md for details."

    try:
        # Create the release
        cmd = [
            "gh",
            "release",
            "create",
            f"v{version}",
            "--title",
            f"v{version}",
            "--notes",
            notes,
            "--repo",
            repo_slug,
        ]

        run_command(cmd)

        log_success(f"Release v{version} created!")
        log_info(f"  URL: https://github.com/{repo_slug}/releases/tag/v{version}")
        return True

    except subprocess.CalledProcessError:
        log_warning("Failed to create release")
        return False


def add_repository_topics(package_name: str, package_type: str) -> bool:
    """Add repository topics for discoverability."""
    log_info("=== Adding Repository Topics ===")

    if not check_gh_cli():
        log_warning("GitHub CLI not available - skipping topics")
        return False

    username = get_github_username()
    repo_slug = f"{username}/{package_name}"

    topics = get_package_topics(package_type)

    try:
        # Add topics via gh API
        topics_str = ",".join(topics)
        run_command(
            [
                "gh",
                "api",
                "--method",
                "PUT",
                f"repos/{repo_slug}/topics",
                "-f",
                f"names={topics_str}",
            ]
        )

        log_success("Topics added!")
        log_info(f"  Topics: {', '.join(topics)}")
        return True

    except subprocess.CalledProcessError:
        log_warning("Failed to add topics")
        return False


def generate_codeowners(
    package_name: str, target_dir: Path, username: str | None
) -> bool:
    """Generate CODEOWNERS file."""
    log_info("=== Generating CODEOWNERS File ===")

    if username is None:
        username = get_github_username()

    codeowners_path = target_dir / "CODEOWNERS"

    if codeowners_path.exists():
        log_warning("CODEOWNERS file already exists - skipping")
        return False

    try:
        with open(codeowners_path, "w") as f:
            f.write("# CODEOWNERS\n\n")
            f.write("# Default code owner\n")
            f.write(f"* @{username}\n")

        log_success("CODEOWNERS file created!")
        log_info(f"  Path: {codeowners_path}")
        log_info(f"  Owner: @{username}")

        # Commit the file
        run_command(["git", "add", "CODEOWNERS"], cwd=target_dir, check=False)
        run_command(
            ["git", "commit", "-m", "docs: Add CODEOWNERS file"],
            cwd=target_dir,
            check=False,
        )

        return True

    except Exception as e:
        log_error(f"Failed to create CODEOWNERS: {e}")
        return False


def generate_security_md(package_name: str, target_dir: Path) -> bool:
    """Generate SECURITY.md file if not present."""
    log_info("=== Generating SECURITY.md ===")

    security_path = target_dir / "SECURITY.md"

    if security_path.exists():
        log_warning("SECURITY.md already exists - skipping")
        return False

    try:
        with open(security_path, "w") as f:
            f.write(f"# Security Policy for {package_name}\n\n")
            f.write("## Supported Versions\n\n")
            f.write("| Version | Supported          |\n")
            f.write("| ------- | ------------------ |\n")
            f.write("| 0.1.x   | :white_check_mark: |\n\n")
            f.write("## Reporting a Vulnerability\n\n")
            f.write("If you discover a security vulnerability, please email ")
            f.write("us directly. Do not open a public issue.\n\n")
            f.write("Please include as much detail as possible to help us ")
            f.write("understand and reproduce the issue.\n")

        log_success("SECURITY.md file created!")
        log_info(f"  Path: {security_path}")

        # Commit the file
        run_command(["git", "add", "SECURITY.md"], cwd=target_dir, check=False)
        run_command(
            ["git", "commit", "-m", "docs: Add SECURITY.md"],
            cwd=target_dir,
            check=False,
        )

        return True

    except Exception as e:
        log_error(f"Failed to create SECURITY.md: {e}")
        return False


def push_updates(target_dir: Path) -> bool:
    """Push any commits to GitHub."""
    log_info("=== Pushing Updates ===")

    try:
        # Check if there are any commits to push
        result = run_command(
            ["git", "log", "origin/main..HEAD"], cwd=target_dir, check=False
        )

        if result.returncode != 0 or not result.stdout.strip():
            log_info("No new commits to push")
            return True

        run_command(["git", "push", "origin", "main"], cwd=target_dir)
        log_success("Updates pushed to GitHub")
        return True

    except subprocess.CalledProcessError:
        log_warning("Failed to push updates")
        return False


def verify_finalization(package_name: str) -> dict[str, bool]:
    """Verify that finalization tasks were successful."""
    log_info("=== Verifying Finalization ===")

    if not check_gh_cli():
        log_warning("GitHub CLI not available - cannot verify")
        return {}

    username = get_github_username()
    repo_slug = f"{username}/{package_name}"

    results = {}

    # Check Pages status
    try:
        result = run_command(
            [
                "gh",
                "api",
                f"repos/{repo_slug}/pages",
                "--jq",
                ".status",
            ],
            check=False,
        )
        results["pages"] = result.returncode == 0
    except Exception:
        results["pages"] = False

    # Check release
    try:
        result = run_command(
            ["gh", "release", "list", "--repo", repo_slug, "--limit", "1"],
            check=False,
        )
        results["release"] = result.returncode == 0 and bool(result.stdout.strip())
    except Exception:
        results["release"] = False

    # Check topics
    try:
        result = run_command(
            ["gh", "repo", "view", repo_slug, "--json", "topics", "--jq", ".topics"],
            check=False,
        )
        topics = result.stdout.strip().strip("[]").replace('"', "").replace(", ", ",")
        results["topics"] = bool(topics)
    except Exception:
        results["topics"] = False

    # Print summary
    print()
    log_info("Finalization Status:")
    for task, status in results.items():
        status_str = (
            f"{Colors.GREEN}✓{Colors.NC}" if status else f"{Colors.YELLOW}○{Colors.NC}"
        )
        print(f"  {status_str} {task.capitalize()}")

    return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="PHASE 7: Repository Finalization - Post-publish automation"
    )
    parser.add_argument("package_name", help="Name of the package/repository")
    parser.add_argument(
        "target_dir", type=Path, help="Target directory with git repository"
    )
    parser.add_argument(
        "--package-type",
        default="library",
        choices=["plugin", "skill", "mcp", "library", "tool"],
        help="Type of package (for topics)",
    )
    parser.add_argument(
        "--release-version",
        default="0.1.0",
        help="Version for initial release (default: 0.1.0)",
    )
    parser.add_argument(
        "--username",
        help="GitHub username for CODEOWNERS (default: from gh CLI)",
    )
    parser.add_argument(
        "--skip-pages",
        action="store_true",
        help="Skip GitHub Pages enablement",
    )
    parser.add_argument(
        "--skip-release",
        action="store_true",
        help="Skip initial release creation",
    )
    parser.add_argument(
        "--skip-topics",
        action="store_true",
        help="Skip adding repository topics",
    )
    parser.add_argument(
        "--skip-codeowners",
        action="store_true",
        help="Skip CODEOWNERS file generation",
    )
    parser.add_argument(
        "--skip-security",
        action="store_true",
        help="Skip SECURITY.md generation",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify finalization status and exit",
    )

    args = parser.parse_args()

    package_name = args.package_name
    target_dir = args.target_dir.resolve()

    log_info("=== PHASE 7: Repository Finalization ===")
    log_info(f"Package: {package_name}")
    log_info(f"Target: {target_dir}")

    # Verify target directory is a git repo
    if not (target_dir / ".git").exists():
        log_error(f"Target directory is not a git repository: {target_dir}")
        sys.exit(1)

    # Check for gh CLI
    if not check_gh_cli():
        log_warning("GitHub CLI not available or not authenticated")
        log_warning("Some features will be skipped")
        log_info("Install and authenticate: https://cli.github.com/")

    # Verify mode
    if args.verify:
        verify_finalization(package_name)
        sys.exit(0)

    # Run finalization steps
    tasks_completed = []

    if not args.skip_pages:
        if enable_github_pages(package_name, target_dir):
            tasks_completed.append("GitHub Pages")

    if not args.skip_release:
        if create_initial_release(package_name, target_dir, args.release_version):
            tasks_completed.append("Initial Release")

    if not args.skip_topics:
        if add_repository_topics(package_name, args.package_type):
            tasks_completed.append("Topics")

    if not args.skip_codeowners:
        if generate_codeowners(package_name, target_dir, args.username):
            tasks_completed.append("CODEOWNERS")

    if not args.skip_security:
        if generate_security_md(package_name, target_dir):
            tasks_completed.append("SECURITY.md")

    # Push updates if any files were created
    if not args.skip_codeowners or not args.skip_security:
        push_updates(target_dir)

    # Verify and show summary
    print()
    log_success("=== Finalization Complete ===")
    if tasks_completed:
        log_info(f"Completed tasks: {', '.join(tasks_completed)}")
    else:
        log_warning("No tasks were completed")

    print()
    log_info("Next steps:")
    log_info("  1. Visit your repository on GitHub")
    log_info("  2. Check Settings > Pages for deployment status")
    log_info("  3. Review the initial release")
    log_info("  4. Update topics if needed")

    # Run verification
    verify_finalization(package_name)


if __name__ == "__main__":
    main()
