# Essential Commands Reference

## Health & Status

```bash
# Full system health check (real-time memory, hooks, databases)
/main

# Hook health specifically
python P:/.claude/hooks/hook_health_check.py

# Save hook baseline after modifications
python P:/.claude/hooks/hook_health_check.py --save-baseline
```

## Knowledge Operations

```bash
# Search chat history
/chs "query here"

# Store learning to CKS (via Python)
cks.ingest_learning(title="Topic", content="...", source="session")

# Ask universal router
/ask "your question"
```

## Development Workflow

```bash
# Root Cause Analysis
/debug "what went wrong"

# Research with web search
/research "topic"

# Code review and analysis
/analyze <path> --focus quality

# Explore codebase intelligently
/discover "pattern or question"
```

## Planning & Execution

```bash
# Plan mode for complex implementations
/breakdown

# Execute CWO15 workflow (validates steps 1-7)
/exec <task description>

# CWO12 comprehensive orchestration
/cwo12
```

## Git Workflow with Sapling

```bash
# Sapling commands (faster than git)
P:/__csf/tools/sapling/sl status
P:/__csf/tools/sapling/sl commit -m "message"
P:/__csf/tools/sapling/sl log

# Git still works for standard operations
git status
git diff
```

## Health Check Interpretation

| Exit Code | Meaning | Action |
|-----------|---------|--------|
| 0 | All healthy | None |
| 1 | Some unhealthy | Investigate warnings |
| 2 | Critical failures | Immediate attention |
| 3 | Unapproved changes | Review changes, save baseline if done |

## Session Continuity

On session start, run:
```bash
python "P:/.claude/skills/_tools/update_registry.py" --if-stale
```

This enables next-command hints and workflow routing.

## File Conventions

### Path Format

**Always use forward slashes in bash commands:**
```bash
# Correct
ls -la "P:/__csf/docs/"

# Wrong (backslashes get escaped)
ls -la P:\__csf\docs\
```

### Python Imports

```python
# CKS import
from cognitive_keystone import CognitiveKeystone
cks = CognitiveKeystone()

# CHS import
from chat_history_search import search_history
results = search_history("query")
```
