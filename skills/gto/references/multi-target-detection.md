# Multi-Target Auto-Detection

## How Multi-Target Auto-Detection Works

When no `--project-root` is provided:

1. **Find transcript**: Locate the current session's transcript JSONL file via `_auto_detect_transcript_path()`
2. **Scan for file paths**: Read all transcript entries, extract file paths from tool results (Read, Edit, Write, Bash output)
3. **Resolve to targets**: For each file path, find its nearest valid GTO target (skill dir -> package dir -> git repo)
4. **Deduplicate**: Return unique targets sorted by path depth (deepest first)

## Target Resolution Hierarchy

- **Skill directory**: `.claude/skills/<name>/` -- confirmed by `SKILL.md` presence
- **Package directory**: `packages/<name>/` -- confirmed by `.git` or `pyproject.toml`
- **Git repository root**: fallback, confirmed by `.git` directory

**Example**: If the session modified `P:\.claude\skills\gto\lib\foo.py` and `P:\.claude\skills\gto\SKILL.md`, the resolved target is `P:\.claude\skills\gto` (one target, not two files).

## Target Selection Priority (for single-target mode)

When `--project-root` IS provided explicitly, use this priority:

| Priority | Signal | Example Target |
|----------|--------|---------------|
| 1 | **Explicit --project-root** | The path provided on CLI |
| 2 | **Recent file edits** -- session modified files in a specific skill/package | `P:\.claude\skills\{skill}` |
| 3 | **Skill invocation target** -- `/critique on X`, `/pre-mortem on X`, `/debugRCA on X` | The explicit target of the skill |
| 4 | **Handoff/RESTORE_CONTEXT** -- explicit target stated in session restore | From `transcript_path` or `current_goal` |
| 5 | **Recent evidence files** -- premortem, adversarial review, or gap analysis artifacts | `P:\.claude\hooks\evidence\{name}` |
| 6 | **Last resort: cwd** -- only if no other signal exists | `P:\.claude\hooks` |

**Anti-pattern to avoid**: Picking `P:\.claude\hooks` just because it's the current working directory, when the session was actually focused on a specific hook or skill within it.

**When genuinely ambiguous**: Ask the user to confirm the target.

**Examples:**
```
# Explicit single target
/gto --project-root "P:\.claude\skills\gto"

/gto --project-root "P:\packages\handoff"

/gto --project-root "P:\.claude\hooks"
```

**WARNING:** P:\ is the config root, not a valid target. Running GTO on P:\ will fail with an error explaining why.
