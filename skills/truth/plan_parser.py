"""Plan parser for /truth skill - extracts metadata and verification criteria from plan files.

Item 15: Plan-aware truth validation.
"""

import re
from pathlib import Path
from typing import Any


def extract_plan_metadata(plan_path: Path) -> dict[str, Any]:
    """Extract metadata from plan file header.

    Args:
        plan_path: Path to plan markdown file

    Returns:
        Dict with status, created, completed, last_reviewed fields

    Raises:
        FileNotFoundError: If plan file doesn't exist
    """
    if not plan_path.exists():
        raise FileNotFoundError(f"Plan file not found: {plan_path}")

    content = plan_path.read_text(encoding="utf-8")

    metadata = {
        "status": "unknown",
        "created": None,
        "completed": None,
        "last_reviewed": None,
    }

    # Extract metadata from header (first 30 lines)
    for line in content.split("\n")[:30]:
        if "**Status:**" in line:
            # Extract status value
            status_match = line.split("**Status:**")[1].strip()
            # Handle emojis and normalize status
            status_value = status_match.split()[0] if status_match else "unknown"
            # Remove common emoji prefixes
            status_value = status_value.lstrip("✅❌⏳🔄")
            status_value = status_value.strip().lower()
            # Map common status values
            if status_value in ["completed", "✅"]:
                metadata["status"] = "completed"
            elif status_value in ["pending", "⏳"]:
                metadata["status"] = "pending"
            elif status_value in ["abandoned", "❌"]:
                metadata["status"] = "abandoned"
            else:
                metadata["status"] = status_value or "unknown"
        elif "**Created:**" in line:
            metadata["created"] = line.split("**Created:**")[1].strip()
        elif "**Completed:**" in line:
            metadata["completed"] = line.split("**Completed:**")[1].strip()
        elif "**Last Reviewed:**" in line:
            metadata["last_reviewed"] = line.split("**Last Reviewed:**")[1].strip()

    return metadata


def extract_documentation_requirements(plan_path: Path) -> list[dict[str, str]]:
    """Extract documentation update requirements from plan file.

    Looks for sections like:
    - Documentation Updates Required
    - Files to Update
    - Documentation

    Args:
        plan_path: Path to plan markdown file

    Returns:
        List of dicts with 'task' and 'file' keys
    """
    if not plan_path.exists():
        raise FileNotFoundError(f"Plan file not found: {plan_path}")

    content = plan_path.read_text(encoding="utf-8")

    requirements = []

    # Look for documentation section headers
    doc_section_patterns = [
        r"## Documentation Updates Required",
        r"## Files to Create",
        r"## Files to Modify",
        r"## Documentation",
        r"### Documentation",
    ]

    # Find the start of a documentation section
    doc_section_start = -1
    for pattern in doc_section_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match and (doc_section_start == -1 or match.start() < doc_section_start):
            doc_section_start = match.start()

    if doc_section_start == -1:
        return requirements

    # Extract the documentation section content
    doc_content = content[doc_section_start:]

    # Stop at next major section (##)
    next_section = re.search(r"\n## ", doc_content[10:])  # Skip past the header we found
    if next_section:
        doc_content = doc_content[:next_section.start() + 10]

    # Parse bullet points for tasks and files
    lines = doc_content.split("\n")
    current_task = None

    for line in lines:
        line = line.strip()

        # Skip empty lines and headers
        if not line or line.startswith("#"):
            continue

        # Check for file path (contains slashes or .md/.py extension)
        if "/" in line or "\\" in line or line.endswith(".md") or line.endswith(".py"):
            # Extract file path
            file_match = re.search(r'([A-Za-z]:[/\\][^`\n]+|[^`\n]+\.[a-z]{2,})', line)
            if file_match:
                file_path = file_match.group(1).strip()
                # Use current task if available, otherwise create from line
                task = current_task if current_task else f"Update {file_path}"
                requirements.append({"task": task, "file": file_path})
        elif line.startswith("-") or line.startswith("*"):
            # Bullet point - might be a task description
            current_task = line.lstrip("-*").strip()

    return requirements


def extract_success_criteria(plan_path: Path) -> list[dict[str, str]]:
    """Extract success criteria from plan file.

    Looks for sections like:
    - Success Criteria
    - Acceptance Criteria
    - Verification

    Args:
        plan_path: Path to plan markdown file

    Returns:
        List of dicts with 'description' and optional 'verification' keys
    """
    if not plan_path.exists():
        raise FileNotFoundError(f"Plan file not found: {plan_path}")

    content = plan_path.read_text(encoding="utf-8")

    criteria = []

    # Look for success criteria section headers
    criteria_section_patterns = [
        r"## Success Criteria",
        r"## Acceptance Criteria",
        r"## Verification",
        r"### Success Criteria",
    ]

    # Find the start of a criteria section
    criteria_section_start = -1
    for pattern in criteria_section_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match and (criteria_section_start == -1 or match.start() < criteria_section_start):
            criteria_section_start = match.start()

    if criteria_section_start == -1:
        return criteria

    # Extract the criteria section content
    criteria_content = content[criteria_section_start:]

    # Stop at next major section (##)
    next_section = re.search(r"\n## ", criteria_content[10:])
    if next_section:
        criteria_content = criteria_content[:next_section.start() + 10]

    # Parse bullet points or numbered lists
    lines = criteria_content.split("\n")

    for line in lines:
        line = line.strip()

        # Skip empty lines and headers
        if not line or line.startswith("#"):
            continue

        # Check for list items
        if line.startswith("-") or line.startswith("*") or re.match(r"^\d+\.", line):
            # Remove list marker
            description = re.sub(r"^[-*]|\d+\.", "", line).strip()

            # Split on "verification:" or similar
            verification = None
            if ":" in description.lower():
                parts = description.split(":", 1)
                if len(parts) == 2 and any(kw in parts[0].lower() for kw in ["verify", "check", "test", "validation"]):
                    verification = parts[1].strip()
                    description = parts[0].strip()

            criterion = {"description": description}
            if verification:
                criterion["verification"] = verification

            criteria.append(criterion)

    return criteria
