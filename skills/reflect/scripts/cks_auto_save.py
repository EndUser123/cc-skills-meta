#!/usr/bin/env python3
"""
Auto-save reflection lessons to CKS.
Saves formatted CKS entries from reflection analysis.
"""

import subprocess
import sys
from pathlib import Path


def save_to_cks(entry: dict) -> bool:
    """Save a single CKS entry.

    Args:
        entry: CKS entry with text, category, severity, context, application

    Returns:
        True if saved successfully, False otherwise
    """
    try:
        # Build CKS CLI command
        cks_cli = Path("__csf/src/cks/cks_cli.py")
        if not cks_cli.exists():
            cks_cli = Path("__csf/src/cks/cks_cli.py").resolve()

        cmd = [
            sys.executable,
            "-m",
            "src.cks.cks_cli",
            "add",
            "--type",
            entry.get("metadata", {}).get("finding_type", "PATTERN"),
            "--severity",
            entry.get("severity", "important"),
            f"{entry.get('text', '')} Application: {entry.get('application', 'N/A')}"
        ]

        # Run CKS CLI
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=Path.cwd()
        )

        if result.returncode == 0:
            return True
        else:
            print(f"Warning: CKS save failed: {result.stderr}")
            return False

    except FileNotFoundError:
        print("Warning: CKS CLI not found. Skipping auto-save.")
        return False
    except subprocess.TimeoutExpired:
        print("Warning: CKS save timed out. Skipping auto-save.")
        return False
    except Exception as e:
        print(f"Warning: CKS save error: {e}")
        return False


def auto_save_cks_entries(entries: list[dict]) -> int:
    """Auto-save multiple CKS entries with graceful failure.

    Args:
        entries: List of CKS entry dictionaries

    Returns:
        Number of entries successfully saved
    """
    if not entries:
        return 0

    print(f"\n📦 Auto-saving {len(entries)} lesson(s) to CKS...")

    success_count = 0
    for entry in entries:
        if save_to_cks(entry):
            success_count += 1

    if success_count == len(entries):
        print(f"✓ All {success_count} lessons saved to CKS")
    elif success_count > 0:
        print(f"✓ {success_count}/{len(entries)} lessons saved to CKS")
    else:
        print("⚠ No lessons saved to CKS (check CKS configuration)")

    return success_count


if __name__ == "__main__":
    # Test with a sample entry
    test_entry = {
        "text": "Test lesson for CKS auto-save",
        "category": "technical",
        "severity": "important",
        "context": "Testing auto-save functionality",
        "application": "Test when CKS auto-save is working",
        "metadata": {
            "finding_type": "PATTERN",
            "severity_weight": 0.7,
            "category_confidence": "HIGH"
        }
    }

    result = auto_save_cks_entries([test_entry])
    print(f"Test result: {result} entries saved")
