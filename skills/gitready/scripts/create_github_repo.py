#!/usr/bin/env python3
"""
create_github_repo.py - Create GitHub repository and push code

This script handles GitHub repository creation via:
1. GitHub CLI (gh) - preferred method
2. Manual instructions with curl API fallback

Usage:
    python create_github_repo.py <package_name> <target_dir> [description]

Examples:
    python create_github_repo.py "search-research" "P:/packages/search-research" "Unified search provider"
    python create_github_repo.py "my-lib" "/path/to/my-lib" "My awesome library"
"""

import argparse
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


def create_with_gh_cli(package_name: str, target_dir: Path, description: str) -> bool:
    """Method 1: Create repo using GitHub CLI."""
    log_info("=== Creating GitHub Repository using GitHub CLI ===")

    # Check if gh is available and authenticated
    if not check_gh_cli():
        log_error("GitHub CLI not available or not authenticated")
        return False

    username = get_github_username()

    log_info(f"Username: {username}")
    log_info(f"Repository: {package_name}")
    log_info(f"Description: {description}")

    # Check if repo already exists
    result = run_command(
        ["gh", "repo", "view", f"{username}/{package_name}"], check=False
    )
    if result.returncode == 0:
        log_warning(f"Repository {username}/{package_name} already exists")
        log_info("Will add remote and push instead")

        # Add remote
        run_command(
            [
                "git",
                "remote",
                "add",
                "origin",
                f"https://github.com/{username}/{package_name}.git",
            ],
            cwd=target_dir,
            check=False,
        )
        run_command(
            [
                "git",
                "remote",
                "set-url",
                "origin",
                f"https://github.com/{username}/{package_name}.git",
            ],
            cwd=target_dir,
            check=False,
        )

        # Push to existing repo
        log_info("Pushing to existing repository...")
        run_command(["git", "push", "-u", "origin", "main"], cwd=target_dir)

        log_success("Pushed to existing repository")
        return True

    # Create new repository
    log_info("Creating new public repository...")

    try:
        run_command(
            [
                "gh",
                "repo",
                "create",
                package_name,
                "--public",
                f"--description={description}",
                f"--source={target_dir}",
                "--remote=origin",
                "--push",
            ]
        )
        log_success("Repository created and pushed")
        return True
    except subprocess.CalledProcessError:
        log_error("Failed to create repository with gh CLI")
        return False


def show_manual_instructions(
    package_name: str, target_dir: Path, description: str
) -> None:
    """Method 2: Show manual instructions with curl API."""
    username = get_github_username()

    log_info("=== Manual GitHub Repository Creation ===")
    print()
    print("GitHub CLI not available. Please create repository manually:")
    print()
    print("Option 1: Using GitHub web interface")
    print("  1. Visit: https://github.com/new")
    print(f"  2. Repository name: {package_name}")
    print(f"  3. Description: {description}")
    print("  4. Visibility: Public")
    print("  5. DO NOT initialize with README (we have one)")
    print("  6. Click 'Create repository'")
    print("  7. Run the commands shown below")
    print()
    print("Option 2: Using curl API (requires GitHub personal access token)")
    print()
    print("  # Set your token (create at: https://github.com/settings/tokens)")
    print('  export GITHUB_TOKEN="your_token_here"')
    print()
    print("  # Create the repository")
    print("  curl -X POST \\")
    print('    -H "Authorization: token $GITHUB_TOKEN" \\')
    print('    -H "Accept: application/vnd.github.v3+json" \\')
    print("    https://api.github.com/user/repos \\")
    print("    -d '{")
    print(f'      "name": "{package_name}",')
    print(f'      "description": "{description}",')
    print('      "private": false,')
    print('      "auto_init": false')
    print("    }'")
    print()
    print("  # Add remote and push")
    print(f'  cd "{target_dir}"')
    print(f"  git remote add origin https://github.com/$USERNAME/{package_name}.git")
    print("  git branch -M main")
    print("  git push -u origin main")
    print()
    print("After creating the repository, it will be available at:")
    print(f"  https://github.com/{username}/{package_name}")


def verify_repository(package_name: str) -> bool:
    """Verify repository was created successfully."""
    log_info("=== Verifying Repository ===")

    if not check_gh_cli():
        log_warning("GitHub CLI not available - cannot verify")
        return True

    username = get_github_username()

    result = run_command(
        ["gh", "repo", "view", f"{username}/{package_name}"], check=False
    )
    if result.returncode == 0:
        # Get repo URL
        url_result = run_command(
            [
                "gh",
                "repo",
                "view",
                f"{username}/{package_name}",
                "--json",
                "url",
                "--jq",
                ".url",
            ]
        )
        repo_url = url_result.stdout.strip()

        log_success("Repository verified!")
        log_info(f"URL: {repo_url}")

        # Check visibility
        visibility_result = run_command(
            [
                "gh",
                "repo",
                "view",
                f"{username}/{package_name}",
                "--json",
                "isPublic",
                "--jq",
                ".isPublic",
            ]
        )
        is_public = visibility_result.stdout.strip()

        if is_public == "true":
            log_success("Visibility: Public")
        else:
            log_warning("Visibility: Private (change to Public in repo settings)")

        return True
    else:
        log_warning("Could not verify repository creation")
        log_info("It may still have been created - check GitHub manually")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create GitHub repository and push code"
    )
    parser.add_argument("package_name", help="Name of the package/repository")
    parser.add_argument(
        "target_dir", type=Path, help="Target directory with git repository"
    )
    parser.add_argument(
        "description",
        nargs="?",
        default="A Claude Code package",
        help="Repository description",
    )

    args = parser.parse_args()

    package_name = args.package_name
    target_dir = args.target_dir.resolve()
    description = args.description

    log_info("=== GitHub Repository Creation ===")
    log_info(f"Package: {package_name}")
    log_info(f"Target: {target_dir}")
    log_info(f"Description: {description}")

    # Verify target directory is a git repo
    if not (target_dir / ".git").exists():
        log_error(f"Target directory is not a git repository: {target_dir}")
        log_info("Run extract_from_monorepo.py first")
        sys.exit(1)

    # Try GitHub CLI first
    if create_with_gh_cli(package_name, target_dir, description):
        verify_repository(package_name)
        log_success("=== Repository Creation Complete ===")
    else:
        # Fall back to manual instructions
        show_manual_instructions(package_name, target_dir, description)
        log_info("=== Follow Manual Instructions Above ===")
        sys.exit(1)


if __name__ == "__main__":
    main()
