"""
Version Synchronization Script for gitready

Ensures version consistency across all project artifacts by treating
core/__init__.py as the single source of truth.

Usage:
    python core/sync.py

What it does:
    1. Reads version from core/__init__.py (source of truth)
    2. Updates .claude-plugin/plugin.json
    3. Updates README.md (all version references)
    4. Validates all changes were applied

Author: gitready automation script
"""

import json
import re
from pathlib import Path


# Version extraction patterns
VERSION_PATTERN = re.compile(r'__version__\s*=\s*["\']([^"\']+)["\']')
README_VERSION_PATTERN = re.compile(r'v?(\d+\.\d+\.\d+[-\w.]*)')


def get_source_version() -> str:
    """
    Read version from core/__init__.py (source of truth).

    Returns:
        Version string (e.g., "5.5.0")

    Raises:
        ValueError: If version cannot be found or parsed
    """
    init_path = Path("core/__init__.py")

    if not init_path.exists():
        raise ValueError(
            "core/__init__.py not found. "
            "Cannot determine source version."
        )

    content = init_path.read_text(encoding='utf-8')

    match = VERSION_PATTERN.search(content)

    if not match:
        raise ValueError(
            "Could not find __version__ in core/__init__.py. "
            "Expected format: __version__ = \"X.Y.Z\""
        )

    return match.group(1)


def update_plugin_json(version: str) -> bool:
    """
    Update version in .claude-plugin/plugin.json.

    Adds 'version' field if it doesn't exist.

    Args:
        version: Version string to write

    Returns:
        True if file was modified, False if no changes needed
    """
    plugin_path = Path(".claude-plugin/plugin.json")

    if not plugin_path.exists():
        print("⚠️  Warning: .claude-plugin/plugin.json not found, skipping")
        return False

    with open(plugin_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ Error: Failed to parse plugin.json: {e}")
            return False

    # Check if version already matches
    if data.get('version') == version:
        print(f"✓ plugin.json version already synchronized ({version})")
        return False

    # Update version
    data['version'] = version

    # Write back with nice formatting
    with open(plugin_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
        f.write('\n')  # Add trailing newline

    print(f"✓ Updated .claude-plugin/plugin.json → {version}")
    return True


def update_readme(version: str) -> bool:
    """
    Update all version references in README.md.

    Updates patterns like:
    - v5.5.0 → version
    - version-5.5.0-blue → version-X.X.X-blue
    - Version: 5.5.0 → Version: version

    Args:
        version: Version string to write

    Returns:
        True if file was modified, False if no changes needed
    """
    readme_path = Path("README.md")

    if not readme_path.exists():
        print("⚠️  Warning: README.md not found, skipping")
        return False

    content = readme_path.read_text(encoding='utf-8')
    original_content = content

    # Apply each pattern individually with error handling
    patterns = [
        ("Pattern 1", r'(?<=v)(\d+\.\d+\.\d+)(?=[\s\]\)|,|\s])', version),
        ("Pattern 2", r'version-(\d+\.\d+\.\d+)', f'version-{version}'),
        ("Pattern 3", r'Version:\s*\d+\.\d+\.\d+', f'Version: {version}'),
        ("Pattern 4", r'alt="Version badge-\d+\.\d+\.\d+', f'alt="Version badge-{version}"'),
    ]

    for name, pattern, replacement in patterns:
        try:
            content = re.sub(pattern, replacement, content)
        except re.error as e:
            print(f"⚠️  Warning: {name} failed: {e}")
            print(f"   Pattern: {pattern}")
            print("   Skipping README version update")
            return False

    if content == original_content:
        print(f"✓ README.md already synchronized ({version})")
        return False

    readme_path.write_text(content, encoding='utf-8')
    print(f"✓ Updated README.md version references → {version}")
    return True


def validate_sync(version: str) -> bool:
    """
    Validate that all files now have the correct version.

    Args:
        version: Expected version string

    Returns:
        True if all validations pass, False otherwise
    """
    all_valid = True

    # Validate plugin.json
    plugin_path = Path(".claude-plugin/plugin.json")
    if plugin_path.exists():
        with open(plugin_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            plugin_version = data.get('version')
            if plugin_version != version:
                print(f"❌ Validation failed: plugin.json has version '{plugin_version}', expected '{version}'")
                all_valid = False

    # Validate README.md
    readme_path = Path("README.md")
    if readme_path.exists():
        content = readme_path.read_text(encoding='utf-8')
        # Check for version patterns that DON'T match the expected version
        # This catches cases where old versions weren't updated
        version_pattern = re.compile(r'\bv?\d+\.\d+\.\d+[-\w.]*\b')

        for match in version_pattern.finditer(content):
            found_version = match.group()
            # Extract just the X.Y.Z part
            version_match = re.match(r'(\d+\.\d+\.\d+)', found_version)
            if version_match:
                extracted_version = version_match.group(1)
                # Skip if this is the expected version
                if extracted_version == version:
                    continue
                # Skip badge URLs and shields.io (those are correct)
                if 'shields.io' in content[match.start()-30:match.end()] or '.svg' in found_version:
                    continue
                # Found an outdated version!
                print(f"❌ Validation failed: README.md contains version '{found_version}', expected '{version}'")
                all_valid = False

    return all_valid


def main() -> int:
    """
    Main entry point for version synchronization.

    Returns:
        Exit code (0 = success, 1 = error)
    """
    try:
        print("=== gitready Version Sync ===\n")

        # Step 1: Get source version
        print("📖 Reading version from core/__init__.py...")
        version = get_source_version()
        print(f"   Source version: {version}\n")

        # Step 2: Update plugin.json
        print("📝 Updating .claude-plugin/plugin.json...")
        update_plugin_json(version)

        # Step 3: Update README.md
        print("📝 Updating README.md...")
        update_readme(version)

        # Step 4: Validate
        print("\n✅ Validating synchronization...")
        if validate_sync(version):
            print(f"\n✅ Success! All artifacts synchronized to v{version}")
            return 0
        else:
            print("\n❌ Validation failed. Please check errors above.")
            return 1

    except ValueError as e:
        print(f"\n❌ Error: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
