#!/usr/bin/env bash
# GTO Verification Stop Hook
#
# Blocks session exit (exit 2) until GTO assertions pass.
# Exit 0: Verification passed, session can end
# Exit 2: Verification failed, must retry

set -e

# Get terminal ID from first argument or environment
# Skill-based hooks receive terminal_id as argument from wrapper
# Settings-based hooks use CLAUDE_TERMINAL_ID environment variable
_raw_terminal="${1:-${CLAUDE_TERMINAL_ID:-}}"
if [ -z "$_raw_terminal" ]; then
    echo "{\"decision\": \"block\", \"reason\": \"Terminal ID not provided. Multi-terminal isolation requires unique terminal ID.\"}"
    exit 2
fi
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-.}"

# Sanitize terminal_id: only allow alphanumeric, dash, underscore; max 64 chars
# This prevents path injection (SEC-001) and shell injection (SEC-002)
TERMINAL_ID=$(echo "$_raw_terminal" | tr -cd 'a-zA-Z0-9_-' | cut -c1-64)
if [ -z "$TERMINAL_ID" ]; then
    echo "{\"decision\": \"block\", \"reason\": \"TERMINAL_ID contains no valid characters after sanitization. Must contain alphanumeric, dash, or underscore only.\"}"
    exit 2
fi

# Path to assertions script
ASSERTIONS_SCRIPT=".claude/skills/gto/evals/gto-assertions.py"

# GTO Scope Guard: Only run assertions if GTO artifacts exist
# This prevents blocking the session when /gto was never run (LOGIC-003)
STATE_DIR="$PROJECT_ROOT/.evidence/gto-state-$TERMINAL_ID"
if [ ! -d "$STATE_DIR" ]; then
    # No state directory = /gto was never run in this terminal
    echo "GTO scope guard: No GTO state found, skipping verification."
    exit 0
fi

# Check for recent artifacts (within last 2 hours)
RECENT_ARTIFACTS=$(find "$STATE_DIR" -name "*.md" -mmin -120 2>/dev/null | wc -l)
if [ "$RECENT_ARTIFACTS" -eq 0 ]; then
    # No recent artifacts = /gto hasn't run recently
    echo "GTO scope guard: No recent GTO artifacts found, skipping verification."
    exit 0
fi

# Run assertions with timeout (PERF-001: prevent hangs)
# Using 30 second timeout to match Claude Code's own timeout conventions
# Pass session start time for artifact recency check
SESSION_START=$(date -Iseconds 2>/dev/null || date +"%Y-%m-%dT%H:%M:%S")
ASSERTION_OUTPUT=$(python "$ASSERTIONS_SCRIPT" --terminal "$TERMINAL_ID" --project-root "$PROJECT_ROOT" --session-start "$SESSION_START" 2>&1) || true
ASSERTION_EXIT=$?

if [ $ASSERTION_EXIT -eq 0 ]; then
    echo "GTO verification passed. Session complete."
    echo "$ASSERTION_OUTPUT"
    exit 0
else
    # Assertions failed - block session exit
    echo "GTO assertions failed. Run manually:"
    echo "python $ASSERTIONS_SCRIPT --terminal $TERMINAL_ID --project-root $PROJECT_ROOT"
    echo ""
    echo "Last output:"
    echo "$ASSERTION_OUTPUT"
    exit 2
fi
