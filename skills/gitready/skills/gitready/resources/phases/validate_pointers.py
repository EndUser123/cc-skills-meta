#!/usr/bin/env python
"""Validate all > READ: pointers in SKILL.md resolve to existing, non-empty files.

Run as a PHASE 0 prerequisite check before any phase that reads bundled resources.
Exits 0 on success, 1 on any failure.

Also validates junction names to prevent problematic characters (like @) that cause
slash command invocation issues on Windows.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Characters that cause problems in Windows junction names or slash command invocation
INVALID_JUNCTION_CHARS = re.compile(r"[@?*:<>|+]")


def sanitize_junction_name(name: str) -> str:
    """Remove invalid characters from junction/skill names.

    Use this before creating junctions to ensure names work with slash commands.
    """
    return INVALID_JUNCTION_CHARS.sub("", name)


def validate_junction_name(name: str) -> list[str]:
    """Validate that a junction/skill name doesn't contain problematic characters.

    Returns list of error messages (empty if valid).
    """
    errors = []
    if INVALID_JUNCTION_CHARS.search(name):
        # Find all invalid characters
        invalid_chars = set(INVALID_JUNCTION_CHARS.findall(name))
        sanitized = sanitize_junction_name(name)
        errors.append(
            f"Junction name '{name}' contains invalid characters: {invalid_chars}. "
            f"These characters cause issues with slash command invocation on Windows. "
            f"Suggested fix: rename to '{sanitized}' before creating junctions."
        )
    return errors


def validate_pointers(skill_md_path: str | Path | None = None) -> list[str]:
    """Validate all > READ: pointers in SKILL.md.

    Returns list of error messages (empty if all valid).
    Pointer paths are resolved relative to SKILL.md's parent directory.
    """
    if skill_md_path is None:
        # Default to this file's parent (resources/phases/) → grandparent (skill root)
        skill_md_path = Path(__file__).parent.parent.parent / "SKILL.md"
    else:
        skill_md_path = Path(skill_md_path)

    errors: list[str] = []

    if not skill_md_path.exists():
        errors.append(f"SKILL.md not found: {skill_md_path}")
        return errors

    skill_dir = skill_md_path.parent
    content = skill_md_path.read_text(encoding="utf-8")

    for line_no, line in enumerate(content.splitlines(), start=1):
        if "> READ:" not in line:
            continue

        # Extract the path after "> READ: " (may be backtick-quoted)
        parts = line.split("> READ:", 1)
        if len(parts) < 2:
            continue
        pointer_path = parts[1].strip().strip("`")
        if not pointer_path:
            errors.append(f"Line {line_no}: empty pointer path")
            continue

        resolved = skill_dir / pointer_path

        if not resolved.exists():
            errors.append(f"Line {line_no}: pointer points to non-existent file: {pointer_path}")
        elif resolved.stat().st_size == 0:
            errors.append(f"Line {line_no}: pointer points to empty file (0 bytes): {pointer_path}")

    return errors


def main() -> int:
    errors = validate_pointers()

    # Also validate junction name from the package structure
    skill_md_path = Path(__file__).parent.parent.parent / "SKILL.md"
    if skill_md_path.exists():
        # The package name is the parent directory name
        package_name = skill_md_path.parent.name
        errors.extend(validate_junction_name(package_name))

    if errors:
        print("VALIDATION FAILED", file=sys.stderr)
        for err in errors:
            print(f"  {err}", file=sys.stderr)
        return 1

    print("All > READ: pointers valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
