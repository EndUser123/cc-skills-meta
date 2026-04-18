#!/usr/bin/env python3
"""GTO Failure Capture Hook - PostToolUseFailure

Classifies GTO failures and logs structured entries to .claude/failure-patterns/
for recovery context and learning.

Usage: Registered as PostToolUseFailure hook for Bash tool
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path


def classify_gto_failure(command: str, error: str) -> dict:
    """Classify GTO failure into category and remediation."""
    command_lower = command.lower()
    error_lower = error.lower()

    # Viability gate failures
    if "viability" in command_lower and "valueerror" in error_lower:
        return {
            "category": "viability-validation",
            "severity": "high",
            "remediation": "Check project-root path. Must be a valid directory with .git, not the config root (P:\\).",
            "pattern": "Invalid project root or missing git repository",
        }

    # Import errors
    if "importerror" in error_lower or "modulenotfounderror" in error_lower:
        missing_module = extract_missing_module(error)
        return {
            "category": "dependency-missing",
            "severity": "high",
            "remediation": f"Install missing dependency: pip install {missing_module}",
            "pattern": f"Missing module: {missing_module}",
        }

    # Handoff chain issues
    if "handoff" in command_lower and ("timeout" in error_lower or "hang" in error_lower):
        return {
            "category": "handoff-timeout",
            "severity": "medium",
            "remediation": "Check handoff chain depth. May need circuit breaker or timeout adjustment.",
            "pattern": "Handoff chain timeout or hang",
        }

    # State file corruption
    if "state" in command_lower and ("permission" in error_lower or "corrupt" in error_lower):
        return {
            "category": "state-access-error",
            "severity": "high",
            "remediation": "Check state directory permissions. Terminal isolation may be broken.",
            "pattern": "State file access error",
        }

    # Git context failures
    if "git" in command_lower and ("notfound" in error_lower or "repository" in error_lower):
        return {
            "category": "git-repository-error",
            "severity": "medium",
            "remediation": "Verify project_root is a valid git repository. Run: git init if needed.",
            "pattern": "Git repository not found or invalid",
        }

    # Generic GTO failure
    return {
        "category": "gto-unknown",
        "severity": "medium",
        "remediation": "Check full error message and GTO logs for details.",
        "pattern": "Unknown GTO failure",
    }


def extract_missing_module(error: str) -> str:
    """Extract missing module name from ImportError."""
    # Common patterns: "No module named 'X'", "cannot import name 'X'"
    import re

    match = re.search(r"No module named ['\"]([^'\"]+)['\"]", error)
    if match:
        return match.group(1)
    match = re.search(r"cannot import name ['\"]([^'\"]+)['\"]", error)
    if match:
        return match.group(1)
    return "<unknown>"


def log_failure_pattern(failure_data: dict) -> Path:
    """Log structured failure pattern to .claude/failure-patterns/."""
    patterns_dir = Path(".claude/failure-patterns")
    patterns_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"gto-{failure_data['category']}-{timestamp}.json"
    filepath = patterns_dir / filename

    with open(filepath, "w") as f:
        json.dump(
            {
                "timestamp": datetime.now().isoformat(),
                "category": failure_data["category"],
                "severity": failure_data["severity"],
                "remediation": failure_data["remediation"],
                "pattern": failure_data["pattern"],
                "raw_error": failure_data.get("raw_error", "")[:500],  # Truncate long errors
            },
            f,
            indent=2,
        )

    return filepath


def main():
    """Main entry point for PostToolUseFailure hook."""
    # Read hook input from stdin with error handling
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        # Return valid JSON even on parse failure - hooks must never crash
        print(
            json.dumps({"additionalContext": f"GTO failure capture: Hook input parse error - {e}"})
        )
        return 0

    command = input_data.get("command", "")
    error = input_data.get("error", "")
    tool = input_data.get("tool", "")

    # Only process GTO-related failures
    if "gto" not in command.lower():
        # Not a GTO failure, pass through
        print(json.dumps({"additionalContext": ""}))
        return 0

    # Classify the failure
    failure_data = classify_gto_failure(command, error)
    failure_data["raw_error"] = error

    # Log the failure pattern
    log_path = log_failure_pattern(failure_data)

    # Generate additional context for Claude
    context = f"""
GTO Failure Detected:

Category: {failure_data["category"]}
Severity: {failure_data["severity"]}
Pattern: {failure_data["pattern"]}

Remediation: {failure_data["remediation"]}

Logged: {log_path}

Before retrying, address the remediation above.
"""

    # Output additional context (must be valid JSON)
    print(json.dumps({"additionalContext": context}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
