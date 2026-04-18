"""Multi-target sync module for routing learnings to appropriate CLAUDE.md files.

This module provides functionality to route learning entries to the appropriate
target files based on their scope (global vs project-specific).

Global scope learnings (model preferences, general patterns) → ~/.claude/CLAUDE.md
Project scope learnings (framework conventions, tool preferences) → ./CLAUDE.md
AGENTS.md is included when present in the project root
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

# Constants
GLOBAL_CLAUDE_MD = Path.home() / ".claude" / "CLAUDE.md"
BACKUP_DIR = Path(".backups")

# Model name patterns for detection
MODEL_PATTERNS = ["gpt-4", "gpt-3.5", "gpt", "claude", "sonnet", "opus", "haiku"]

# Project-specific patterns for detection
PROJECT_PATH_PATTERNS = ["src/", "apps/", "packages/", "lib/", "components/", "utils/"]

PROJECT_TOOL_PATTERNS = ["pnpm", "npm", "yarn", "nx", "turbo", "webpack", "vite", "eslint"]

PROJECT_FRAMEWORK_PATTERNS = ["next.js", "react", "vue", "angular", "svelte", "nestjs", "express"]


def is_model_preference(content: str) -> bool:
    """Detect if content contains model name references.

    Args:
        content: Learning content to analyze

    Returns:
        True if content mentions model names
    """
    content_lower = content.lower()
    return any(pattern in content_lower for pattern in MODEL_PATTERNS)


def is_project_specific(content: str) -> bool:
    """Detect if content contains project-specific keywords.

    Args:
        content: Learning content to analyze

    Returns:
        True if content contains project-specific patterns
    """
    content_lower = content.lower()

    # Check for project paths
    if any(pattern in content_lower for pattern in PROJECT_PATH_PATTERNS):
        return True

    # Check for project tools
    if any(pattern in content_lower for pattern in PROJECT_TOOL_PATTERNS):
        return True

    # Check for framework conventions
    if any(pattern in content_lower for pattern in PROJECT_FRAMEWORK_PATTERNS):
        return True

    return False


def is_general_pattern(content: str) -> bool:
    """Detect if content is a general coding pattern/best practice.

    Args:
        content: Learning content to analyze

    Returns:
        True if content is a general pattern (should be global)
    """
    content_lower = content.lower()

    # General pattern indicators
    general_indicators = ["always ", "prefer ", "use ", "add ", "implement "]

    # Check if content starts with general pattern indicators
    for indicator in general_indicators:
        if content_lower.strip().startswith(indicator):
            # Make sure it's not project-specific
            if not is_project_specific(content) and not is_model_preference(content):
                return True

    return False


def classify_scope(learning: dict[str, Any]) -> str:
    """Classify learning scope as 'global' or 'project'.

    Classification logic:
    - Model preferences (gpt-4, claude, sonnet, haiku) → GLOBAL
    - General patterns (use X, prefer Y) → GLOBAL
    - Framework conventions → PROJECT
    - Tool preferences (pnpm, nx, turbo) → PROJECT
    - Project paths (src/, apps/, packages/) → PROJECT
    - Ambiguous content → PROJECT (default)

    Args:
        learning: Dictionary with content, skill_name, and optional metadata

    Returns:
        'global' or 'project'
    """
    content = learning.get("content", "")
    skill_name = learning.get("skill_name", "").lower()

    # Check for model preferences first (global scope)
    if is_model_preference(content):
        return "global"

    # Check for project-specific patterns
    if is_project_specific(content):
        return "project"

    # Check for general patterns (global scope)
    if is_general_pattern(content):
        return "global"

    # Check skill_name for explicit scope hints
    if skill_name == "global":
        return "global"
    elif skill_name == "project":
        return "project"

    # Default to project scope for ambiguous content
    return "project"


def get_target_paths(scope: str, project_path: Path) -> list[Path]:
    """Get target file paths based on scope.

    Args:
        scope: 'global' or 'project'
        project_path: Root path of the project

    Returns:
        List of Path objects for target files
    """
    # Import module to access patched constants
    import importlib

    try:
        module = importlib.import_module(__name__)
        global_path = module.GLOBAL_CLAUDE_MD
    except (ImportError, KeyError):
        # Fallback to module-level constant
        global_path = GLOBAL_CLAUDE_MD

    targets = []

    if scope == "global":
        # Global scope → only global CLAUDE.md
        targets.append(global_path)
    elif scope == "project":
        # Project scope → project CLAUDE.md
        project_claude = project_path / "CLAUDE.md"
        targets.append(project_claude)

        # Include AGENTS.md if it exists
        agents_md = project_path / "AGENTS.md"
        if agents_md.exists():
            targets.append(agents_md)
    elif scope == "both":
        # Both scopes → global and project
        targets.append(global_path)
        project_claude = project_path / "CLAUDE.md"
        targets.append(project_claude)

        # Include AGENTS.md if it exists
        agents_md = project_path / "AGENTS.md"
        if agents_md.exists():
            targets.append(agents_md)

    # Return paths without normalization to allow test mocking
    # Tests will handle path normalization as needed
    return targets


def create_backup(file_path: Path, backup_dir: Path | None = None) -> Path | None:
    """Create a backup of a file before modification.

    Args:
        file_path: Path to the file to backup
        backup_dir: Directory to store backups (uses module BACKUP_DIR if None)

    Returns:
        Path to backup file, or None if backup failed
    """
    try:
        # Access BACKUP_DIR from module to allow patching
        import sys

        module = sys.modules[__name__]
        if backup_dir is None:
            backup_dir = module.BACKUP_DIR

        # Create backup directory if it doesn't exist
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{file_path.name}.{timestamp}.bak"
        backup_path = backup_dir / backup_filename

        # Copy file to backup location
        shutil.copy2(file_path, backup_path)
        return backup_path
    except Exception:
        return None


def truncate_content(content: str, max_length: int = 100) -> str:
    """Truncate content for display purposes.

    Args:
        content: Content to truncate
        max_length: Maximum length before truncation

    Returns:
        Truncated content with ellipsis if needed
    """
    if len(content) <= max_length:
        return content
    return content[: max_length - 3] + "..."


def format_learning_entry(learning: dict[str, Any]) -> str:
    """Format learning entry for writing to CLAUDE.md.

    Args:
        learning: Dictionary with content and metadata

    Returns:
        Formatted markdown entry
    """
    content = learning.get("content", "")
    skill_name = learning.get("skill_name", "unknown")
    fingerprint = learning.get("fingerprint", "none")
    confidence = learning.get("confidence", 0.0)
    learning_type = learning.get("learning_type", "pattern")
    repo_ids = learning.get("repo_ids", "[]")

    # Parse repo_ids to get count
    try:
        repo_list = json.loads(repo_ids) if isinstance(repo_ids, str) else repo_ids
        repo_count = len(repo_list)
        repo_info = f"{repo_count} repo{'s' if repo_count != 1 else ''}"
    except (json.JSONDecodeError, TypeError):
        repo_info = "unknown repos"

    # Format confidence percentage
    confidence_pct = f"{confidence * 100:.0f}%" if confidence else "N/A"

    # Build metadata comment
    metadata = (
        f"<!-- Skill: {skill_name} | "
        f"Type: {learning_type} | "
        f"Confidence: {confidence_pct} | "
        f"Sources: {repo_info} | "
        f"Fingerprint: {fingerprint} | "
        f"Added: {datetime.now().isoformat()} -->"
    )

    # Build entry
    entry = f"\n{metadata}\n{content}\n"

    return entry


def write_to_target(file_path: Path, entry: str) -> bool:
    """Write learning entry to target file.

    Args:
        file_path: Path to the target file
        entry: Formatted entry to write

    Returns:
        True if successful, False otherwise
    """
    try:
        # Create backup before writing (uses module BACKUP_DIR)
        create_backup(file_path)

        # Read existing content
        if file_path.exists():
            existing_content = file_path.read_text(encoding="utf-8")
        else:
            existing_content = "# CLAUDE.md\n\n"

        # Append new entry
        new_content = existing_content + entry

        # Write back to file
        file_path.write_text(new_content, encoding="utf-8")

        return True
    except Exception:
        return False


def sync_learning_to_targets(
    learning: dict[str, Any],
    project_root: Path | None = None,
    project_path: Path | None = None,
) -> dict[str, Any]:
    """Route learning to appropriate CLAUDE.md files based on scope.

    This is the main entry point for syncing learnings to their targets.
    It classifies the learning scope, determines target files, and writes
    the formatted entry to each target.

    Args:
        learning: Dict with content, scope, skill_name, and optional metadata
            Required fields:
                - content: The learning content
                - skill_name: Name of the skill that generated this learning
            Optional fields:
                - fingerprint: Unique identifier for deduplication
                - confidence: Confidence score (0.0 to 1.0)
                - learning_type: Type of learning (pattern, preference, etc.)
                - repo_ids: JSON string or list of repository IDs
        project_root: Override project root detection (legacy parameter)
        project_path: Path to the project root (preferred parameter)

    Returns:
        Dict with keys:
            - success: bool indicating if sync was successful
            - scope: 'global' or 'project'
            - targets: list of Path objects that were written to
            - formatted_entry: the formatted entry that was written
            - error: error message if success is False
    """
    result = {
        "success": False,
        "scope": None,
        "targets": [],
        "formatted_entry": None,
        "error": None,
    }

    # Validate learning has required fields
    if not learning.get("content"):
        result["error"] = "Learning content is required"
        return result

    # Use project_path if provided, otherwise fall back to project_root
    if project_path is None:
        project_path = project_root or Path.cwd()

    # Ensure project_path is a Path object
    project_path = Path(project_path)

    # Validate project path exists
    if not project_path.exists():
        result["error"] = f"Project path does not exist: {project_path}"
        return result

    # Classify scope
    scope = classify_scope(learning)
    result["scope"] = scope

    # Get target paths
    try:
        targets = get_target_paths(scope, project_path)
    except Exception as e:
        result["error"] = f"Failed to get target paths: {str(e)}"
        return result

    if not targets:
        result["error"] = "No target files found"
        return result

    # Validate target paths exist or can be created
    for target in targets:
        if not target.exists():
            # Check if parent directory exists
            if not target.parent.exists():
                result["error"] = f"Target parent directory does not exist: {target.parent}"
                return result

    # Format entry
    try:
        formatted_entry = format_learning_entry(learning)
        result["formatted_entry"] = truncate_content(formatted_entry, max_length=200)
    except Exception as e:
        result["error"] = f"Failed to format learning entry: {str(e)}"
        return result

    # Write to each target
    successful_writes = []
    failed_writes = []

    for target in targets:
        if write_to_target(target, formatted_entry):
            successful_writes.append(target)
        else:
            failed_writes.append(target)

    if successful_writes:
        result["success"] = True
        result["targets"] = successful_writes

        # Note any failures in warnings
        if failed_writes:
            result["warnings"] = [f"Failed to write to {target}" for target in failed_writes]
    else:
        result["error"] = f"Failed to write to any target. Failed: {failed_writes}"

    return result
