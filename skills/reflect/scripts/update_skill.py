#!/usr/bin/env python
"""
Safely updates skill files with validation and backups.
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


def update_skill(change: dict[str, Any]) -> bool:
    """
    Safely update a skill file with the proposed change.

    change = {
        'skill_name': 'python-project-creator',
        'signals': [...],
        'proposed_updates': {
            'high_confidence': [...],
            'medium_confidence': [...],
            'low_confidence': [...]
        }
    }

    Returns True if update succeeded, False otherwise.
    """
    skill_name = change["skill_name"]
    skill_path = Path.home() / ".claude" / "skills" / skill_name / "SKILL.md"

    if not skill_path.exists():
        print(f"✗ Skill not found: {skill_path}")
        return False

    # 1. Create backup
    backup_path = create_backup(skill_path)
    if not backup_path:
        print(f"✗ Failed to create backup for {skill_name}")
        return False

    try:
        # 2. Parse existing skill
        with open(skill_path) as f:
            content = f.read()

        frontmatter, body = parse_skill_file(content)

        # 3. Apply updates based on confidence
        proposed_updates = change.get("proposed_updates", {})

        for signal in proposed_updates.get("high_confidence", []):
            body = apply_high_confidence_update(body, signal)

        for signal in proposed_updates.get("medium_confidence", []):
            body = apply_medium_confidence_update(body, signal)

        for signal in proposed_updates.get("low_confidence", []):
            body = apply_low_confidence_update(body, signal)

        # 4. Reconstruct file
        updated_content = reconstruct_skill_file(frontmatter, body)

        # 5. Validate YAML
        validate_skill_yaml(updated_content)

        # 6. Write atomically
        with open(skill_path, "w") as f:
            f.write(updated_content)

        print(f"✓ Updated {skill_name}")

        # 7. Sync to multi-target CLAUDE.md files
        try:
            from pathlib import Path as PathlibPath

            from multi_target_sync import sync_learning_to_targets

            # Prepare learning dict for multi-target sync
            learning = {
                "content": _extract_learning_content(change),
                "confidence": _extract_confidence(change),
                "skill_name": skill_name,
                "learning_type": "correction",
                "timestamp": datetime.now().isoformat(),
            }

            # Sync to appropriate CLAUDE.md files
            target_paths = sync_learning_to_targets(learning)
            if target_paths:
                print(f"  → Synced to {len(target_paths)} CLAUDE.md file(s)")
        except ImportError:
            # multi_target_sync not available, skip
            pass
        except Exception as e:
            # Non-critical, don't fail the skill update
            print(f"  Warning: Multi-target sync failed: {e}")

        return True

    except Exception as e:
        # Rollback on error
        shutil.copy(backup_path, skill_path)
        print(f"✗ Error updating {skill_name}: {e}")
        print(f"  Rolled back to backup: {backup_path}")
        return False


def create_backup(skill_path: Path) -> Path:
    """Create timestamped backup"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = skill_path.parent / ".backups"
        backup_dir.mkdir(exist_ok=True)
        backup_path = backup_dir / f"SKILL_{timestamp}.md"
        shutil.copy(skill_path, backup_path)

        # Clean old backups (keep last 30 days)
        cleanup_old_backups(backup_dir, days=30)

        return backup_path
    except Exception as e:
        print(f"Error creating backup: {e}")
        return None


def cleanup_old_backups(backup_dir: Path, days: int = 30):
    """Remove backups older than specified days"""
    try:
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        for backup in backup_dir.glob("SKILL_*.md"):
            if backup.stat().st_mtime < cutoff:
                backup.unlink()
    except Exception:
        # Non-critical, don't fail on cleanup errors
        pass


def parse_skill_file(content: str) -> tuple:
    """Split YAML frontmatter and markdown body"""
    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError("Invalid SKILL.md format: missing YAML frontmatter")

    frontmatter = yaml.safe_load(parts[1])
    body = parts[2].strip()
    return frontmatter, body


def apply_high_confidence_update(body: str, signal: dict[str, Any]) -> str:
    """Apply correction with warning about old approach"""
    description = signal.get("description", "Correction")
    old_approach = signal.get("old_approach", "Previous approach")
    new_approach = signal.get("new_approach", "New approach")

    # Create correction entry
    correction = f"**{description}**\n\n"
    correction += f"- ✗ Don't: {old_approach}\n"
    correction += f"- ✓ Do: {new_approach}\n\n"

    if "## Critical Corrections" in body:
        # Append to existing section (after the header)
        parts = body.split("## Critical Corrections", 1)
        before = parts[0]
        after = parts[1]

        # Find the end of the section header and any existing content
        # Insert before next section or at end
        next_section = after.find("\n## ")
        if next_section > 0:
            section_content = after[:next_section]
            rest = after[next_section:]
            updated_after = section_content + correction + rest
        else:
            updated_after = after + "\n" + correction

        body = before + "## Critical Corrections" + updated_after
    else:
        # Add new section at the beginning of the body
        body = "## Critical Corrections\n\n" + correction + "\n" + body

    return body


def apply_medium_confidence_update(body: str, signal: dict[str, Any]) -> str:
    """Add to Best Practices section"""
    pattern = signal.get("pattern", "Pattern")
    description = signal.get("description", signal.get("pattern", "Best practice"))

    section_line = f"- {description}\n"

    if "## Best Practices" in body:
        # Find section and append
        parts = body.split("## Best Practices", 1)
        before = parts[0]
        after_header = parts[1]

        # Insert after header, before next section
        next_section = after_header.find("\n## ")
        if next_section > 0:
            section_content = after_header[:next_section]
            rest = after_header[next_section:]
            updated_after = section_content + section_line + rest
        else:
            updated_after = after_header + "\n" + section_line

        body = before + "## Best Practices" + updated_after
    else:
        # Create new section at end
        body += "\n\n## Best Practices\n\n" + section_line

    return body


def apply_low_confidence_update(body: str, signal: dict[str, Any]) -> str:
    """Add to Considerations section"""
    suggestion = signal.get("suggestion", "Consideration")

    section_line = f"- Consider: {suggestion}\n"

    if "## Advanced Considerations" in body:
        parts = body.split("## Advanced Considerations", 1)
        before = parts[0]
        after_header = parts[1]

        # Insert after header, before next section
        next_section = after_header.find("\n## ")
        if next_section > 0:
            section_content = after_header[:next_section]
            rest = after_header[next_section:]
            updated_after = section_content + section_line + rest
        else:
            updated_after = after_header + "\n" + section_line

        body = before + "## Advanced Considerations" + updated_after
    else:
        # Create new section at end
        body += "\n\n## Advanced Considerations\n\n" + section_line

    return body


def reconstruct_skill_file(frontmatter: dict, body: str) -> str:
    """Reconstruct SKILL.md with YAML frontmatter"""
    yaml_str = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False)
    return f"---\n{yaml_str}---\n\n{body}"


def validate_skill_yaml(content: str):
    """Validate YAML frontmatter is parseable"""
    try:
        parts = content.split("---", 2)
        if len(parts) < 3:
            raise ValueError("Missing YAML frontmatter delimiters")

        frontmatter = yaml.safe_load(parts[1])

        # Validate required fields
        if "name" not in frontmatter:
            raise ValueError("Missing required 'name' field in frontmatter")
        if "description" not in frontmatter:
            raise ValueError("Missing required 'description' field in frontmatter")

    except Exception as e:
        raise ValueError(f"Invalid YAML after update: {e}")


def _extract_learning_content(change: dict[str, Any]) -> str:
    """Extract learning content from change dict"""
    proposed_updates = change.get("proposed_updates", {})

    # Try high confidence first, then medium, then low
    for confidence_level in ["high_confidence", "medium_confidence", "low_confidence"]:
        signals = proposed_updates.get(confidence_level, [])
        if signals:
            signal = signals[0]
            # Extract description or suggestion
            if "description" in signal:
                return signal["description"]
            elif "suggestion" in signal:
                return signal["suggestion"]
            elif "old_approach" in signal and "new_approach" in signal:
                return f"Use {signal['new_approach']} instead of {signal['old_approach']}"

    return "Learning from skill update"


def _extract_confidence(change: dict[str, Any]) -> float:
    """Extract confidence score from change dict"""
    proposed_updates = change.get("proposed_updates", {})

    # Map confidence levels to scores
    if proposed_updates.get("high_confidence"):
        return 0.85
    elif proposed_updates.get("medium_confidence"):
        return 0.70
    elif proposed_updates.get("low_confidence"):
        return 0.60
    else:
        return 0.70  # Default to medium


if __name__ == "__main__":
    # Test mode
    import sys

    if len(sys.argv) > 1:
        skill_name = sys.argv[1]
        test_change = {
            "skill_name": skill_name,
            "proposed_updates": {
                "high_confidence": [
                    {
                        "description": "Test correction",
                        "old_approach": "Old way",
                        "new_approach": "New way",
                    }
                ]
            },
        }
        update_skill(test_change)
    else:
        print("Usage: python update_skill.py <skill-name>")
