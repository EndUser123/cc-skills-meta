# Skill Coverage Log

GTO maintains an append-only log of skill executions per target for routing suggestions.

## Location

`~/.claude/.evidence/skill_coverage/{target_key}.jsonl`

## Format (one JSON object per line)

```json
{"skill": "/critique", "target": "skills/usm", "terminal_id": "console_abc123", "timestamp": "2026-03-24T...", "git_sha": "abc1234"}
```

## Key Properties

- **Append-only**: New entries are always added, never modified
- **Per-target isolation**: Each project/folder gets its own log file
- **No TTL**: Freshness determined by git state -- if target changed since last run, coverage is stale
- **Auto-rotation**: Log rotates when >1MB (keeps last 100 entries)

## How It Works

1. When gaps=0, GTO reads the skill coverage log for the target
2. Checks git state to detect staleness (file changed since skill run)
3. Classifies project type and suggests relevant skills that haven't been run
4. Suggestions appear as RSN findings with `action_type: "Use /skill"`

## Reference

`lib/skill_coverage_detector.py` -- `detect_skill_coverage()` function
