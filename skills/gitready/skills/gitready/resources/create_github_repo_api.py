#!/usr/bin/env python
"""Create GitHub repository via GitHub API.
==========================================

Alternative to gh CLI for repository creation.
Uses GitHub REST API with personal access token.

Usage:
    python create_github_repo.py <repo_name> <description> [--private] [--token TOKEN]

Environment:
    GITHUB_TOKEN - GitHub personal access token (defaults to ghp_* from git config)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from urllib.parse import quote

try:
    import requests
except ImportError:
    print("ERROR: requests module required. Install with: pip install requests")
    sys.exit(1)


def get_github_token() -> str:
    """Get GitHub token from git config or environment."""
    # Try environment variable first
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token

    # Try extracting from git remote URL
    try:
        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            url = result.stdout.strip()
            # Extract token from URL like https://ghp_TOKEN@github.com/...
            if "@" in url and "github.com" in url:
                token_part = url.split("@")[0]
                if "ghp_" in token_part:
                    return token_part.split("//")[-1]
    except Exception:
        pass

    return ""


def create_repo(name: str, description: str, token: str, private: bool = False) -> dict:
    """Create a GitHub repository via API.

    Args:
        name: Repository name
        description: Repository description
        token: GitHub personal access token
        private: Whether repo should be private (default: public)

    Returns:
        Dict with status and repo URL or error message.
    """
    url = "https://api.github.com/user/repos"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }

    data = {
        "name": name,
        "description": description,
        "private": private,
        "has_issues": True,
        "has_projects": False,
        "has_wiki": False,
        "auto_init": False,  # Don't create README (we have content to push)
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)

        if response.status_code == 201:
            repo_data = response.json()
            return {
                "status": "success",
                "url": repo_data["html_url"],
                "clone_url": repo_data["clone_url"],
                "name": repo_data["name"],
            }
        elif response.status_code == 401:
            return {"status": "error", "message": "Authentication failed. Check your token has 'repo' scope."}
        elif response.status_code == 422:
            error_detail = response.json().get("errors", [{}])[0].get("message", "Unknown validation error")
            return {"status": "error", "message": f"Validation failed: {error_detail}"}
        else:
            return {"status": "error", "message": f"HTTP {response.status_code}: {response.text}"}

    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": f"Network error: {e}"}


def check_repo_exists(name: str, token: str, owner: str | None = None) -> dict:
    """Check if a GitHub repository already exists.

    Args:
        name: Repository name
        token: GitHub personal access token
        owner: Repository owner (defaults to token owner)

    Returns:
        Dict with exists boolean and repo URL if True.
    """
    if not owner:
        # Get authenticated user
        try:
            response = requests.get(
                "https://api.github.com/user",
                headers={"Authorization": f"token {token}"},
                timeout=10,
            )
            if response.status_code == 200:
                owner = response.json().get("login")
            else:
                return {"exists": False, "error": "Could not determine repo owner"}
        except Exception:
            return {"exists": False, "error": "Could not determine repo owner"}

    url = f"https://api.github.com/repos/{owner}/{name}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return {"exists": True, "url": response.json().get("html_url")}
        return {"exists": False}
    except Exception:
        return {"exists": False, "error": "Network error checking repo"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Create GitHub repository via API")
    parser.add_argument("name", help="Repository name")
    parser.add_argument("description", help="Repository description")
    parser.add_argument("--private", action="store_true", help="Create private repository")
    parser.add_argument("--token", help="GitHub personal access token (overrides auto-detection)")
    parser.add_argument("--owner", help="Repository owner (defaults to authenticated user)")
    parser.add_argument("--check-only", action="store_true", help="Only check if repo exists, don't create")

    args = parser.parse_args()

    # Get token
    token = args.token or get_github_token()
    if not token:
        print("ERROR: No GitHub token found. Set GITHUB_TOKEN or configure git remote with token.")
        sys.exit(1)

    # Check if repo exists
    check_result = check_repo_exists(args.name, token, args.owner)
    if check_result.get("exists"):
        print(f"Repository '{args.name}' already exists: {check_result.get('url')}")
        sys.exit(0)

    # Exit if check-only
    if args.check_only:
        print(f"Repository '{args.name}' does not exist. Create with: python create_github_repo.py {args.name} '{args.description}'")
        sys.exit(1)

    # Create repo
    print(f"Creating repository '{args.name}'...")
    result = create_repo(args.name, args.description, token, args.private)

    if result["status"] == "success":
        print(f"✅ Repository created: {result['url']}")
        print(f"   Clone URL: {result['clone_url']}")
        print(f"\nNext steps:")
        print(f"   git remote add origin {result['clone_url']}")
        print(f"   git push -u origin main")
    else:
        print(f"❌ Failed to create repository: {result.get('message', 'Unknown error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
