#!/bin/bash
# Stop hook that triggers reflection (always-on)

SKILL_DIR="$HOME/.claude/skills/reflect"
LOCK_FILE="$SKILL_DIR/.state/reflection.lock"
LOG_FILE="$HOME/.claude/reflect-hook.log"

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

log "Stop hook triggered"

# Always-on reflection - early exit if no learning signals in reflect.py

# Check for stale lock (>10 minutes = 600 seconds)
if [ -f "$LOCK_FILE" ]; then
    if [ "$(uname)" = "Darwin" ]; then
        # macOS
        LOCK_AGE=$(($(date +%s) - $(stat -f %m "$LOCK_FILE")))
    else
        # Linux
        LOCK_AGE=$(($(date +%s) - $(stat -c %Y "$LOCK_FILE")))
    fi

    if [ $LOCK_AGE -lt 600 ]; then
        log "Recent lock exists (age: ${LOCK_AGE}s), skipping"
        exit 0  # Recent lock exists, skip
    fi
    log "Removing stale lock (age: ${LOCK_AGE}s)"
    rm "$LOCK_FILE"  # Remove stale lock
fi

# Create lock
touch "$LOCK_FILE"
log "Lock created"

# Get transcript path from stdin
INPUT=$(cat)
TRANSCRIPT_PATH=$(echo "$INPUT" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('transcript_path', ''))" 2>/dev/null)

log "Transcript path: $TRANSCRIPT_PATH"

# Run reflection in background to avoid timeout
(
    log "Starting background reflection"
    export TRANSCRIPT_PATH="$TRANSCRIPT_PATH"
    export AUTO_REFLECTED="true"

    python3 "$SKILL_DIR/scripts/reflect.py" >> "$LOG_FILE" 2>&1
    REFLECT_EXIT=$?

    if [ $REFLECT_EXIT -eq 0 ]; then
        log "Reflection completed successfully"
        # Could add notification here if needed
        # echo "🧠 Learned from session" >> "$HOME/.claude/session-env/notification"
    else
        log "Reflection failed with exit code $REFLECT_EXIT"
    fi

    rm -f "$LOCK_FILE"
    log "Lock removed"
) &

log "Background process spawned, allowing stop"

# Allow stop immediately (don't block the hook)
exit 0
