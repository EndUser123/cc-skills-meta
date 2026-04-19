#!/bin/bash
# Master Skill Orchestrator CLI Wrapper
#
# This wrapper handles the Git Bash path translation issue on Windows.
# When using Git Bash, paths like /nse get interpreted as Windows paths.
#
# Usage:
#   ./orchestrator.sh suggest nse          (no leading / needed)
#   ./orchestrator.sh info arch
#   ./orchestrator.sh validate "nse,r"
#   ./orchestrator.sh workflow nse --depth 2

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to add leading / to skill names if missing
normalize_skill_names() {
    local args=("$@")
    local normalized=()

    for arg in "${args[@]}"; do
        # Add leading / to skill names if they look like skills (alphanumeric with hyphens)
        # Skip if already starts with /, or is a flag/option
        if [[ ! "$arg" =~ ^[-/] ]] && [[ "$arg" =~ ^[a-zA-Z0-9_-]+$ ]]; then
            normalized+=("/$arg")
        else
            normalized+=("$arg")
        fi
    done

    echo "${normalized[@]}"
}

# Normalize all arguments
NORMALIZED_ARGS=$(normalize_skill_names "$@")

# Run the Python CLI with normalized arguments
python "$SCRIPT_DIR/cli.py" $NORMALIZED_ARGS
