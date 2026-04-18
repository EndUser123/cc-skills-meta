---
name: dream
description: Memory consolidation pass — synthesize recent learnings into organized durable memories. Use when session has yielded significant learnings, before long sessions, or when memory feels cluttered. Triggers automatically on session end via SessionStart hook.
category: memory
triggers:
  - /dream
  - "consolidate memory"
  - "memory hygiene"
  - "clean up memory"
version: "1.0.0"
status: "stable"
enforcement: advisory
---

# Dream — Memory Consolidation

Performs a 4-phase memory consolidation pass to synthesize recent learnings into organized, durable memories.

## Memory Architecture (This Codebase)

**Two-tier system:**
- `MEMORY.md` — Index file, ≤200 lines, auto-loaded
- Topic files — Detailed docs, loaded on demand from `memory/` directory

**Critical constraint:** MEMORY.md is truncated at 200 lines. Lines 201+ never reach context.

## When to Run

**Trigger signals:**
- Session produced significant learnings or corrections
- MEMORY.md approaching 200-line limit (>180 lines)
- Topic files have drifted or duplicated content
- After `/reflect` reveals memory gaps or contradictions
- Before major sessions (architecture decisions, complex features)

**Skip if:**
- Session was routine with no new learnings
- Recent `/dream` already ran (< 24 hours)

## 4-Phase Process

### Phase 1 — Orient

List the memory directory to see what exists:
```
Glob pattern: memory/*.md
Read: memory/MEMORY.md
```

Understand current structure by reading MEMORY.md and scanning topic files for:
- What patterns are already captured
- What might be stale or contradicted
- Gaps in coverage

### Phase 2 — Gather Signal

Priority order for finding worth-saving information:

1. **Daily logs** — Check `memory/logs/YYYY/MM/YYYY-MM-DD.md` if they exist
2. **Recent session transcript** — Look for corrections, learnings, new patterns
3. **Existing memories that may have drifted** — Re-read topic files you've visited recently
4. **Grep for contradictions** — Search for patterns like "but actually", "correction", "wait —"
5. **Dreaming daemon insights** — Read `P:/.claude/state/dreaming-insights.json` (or `.md`)
   - Check `principle_stats` for high-count violations (context_reuse, grounded_changes, etc.)
   - Check `patterns` for `high_violation_principle` entries
   - Treat high-count principles as lesson candidates for Phase 3

**Key guidance:** Don't exhaustively read transcripts. Look only for things you already suspect matter. Bias toward action over completeness.

### Phase 3 — Consolidate

**Write or update memory files at the top level using established conventions:**

From `memory_management.md`:
- Use lowercase_with_underscores for topic file names
- One-line descriptions linking to topic files (index, not dump)
- Add new topic files to MEMORY.md table

**Merge signal into existing topics rather than creating duplicates:**
- Don't create `new_topic.md` if `existing_topic.md` covers it
- Extend existing files, don't fragment

**Convert relative dates to absolute dates:**
- "yesterday" → "2026-03-23"
- "last week" → "2026-03-17"
- "recently" → specific date when known

**Delete contradicted facts:**
- If MEMORY.md says X but you learned Y, remove X entirely
- Don't keep contradicting entries side-by-side

**Daemon-derived insights:**
- High-count principle violations from `dreaming-insights.json` are lesson candidates
- Example: `context_reuse` with count=10 → write/update `context_reuse.md` in memory/ with violation pattern, examples, and corrective action
- Use the `graduate` pass: if a daemon insight appears repeatedly, promote it to a hook rule or validator

### Phase 4 — Prune and Index

**Keep MEMORY.md under 200 lines:**
- Count current lines before editing
- If adding content would exceed limit, extract to topic file first

**Maintain index quality:**
- One-line descriptions only — it's an index
- Remove stale pointers to deleted files
- Demote verbose entries to topic files
- Add new memories as topic files with table entries

**Resolve contradictions:**
- If two topic files disagree, pick the correct one
- Delete or update the wrong entry
- Note the correction in your summary

## Output

Return a brief summary of what was consolidated:

```
## Dream Summary

**Consolidated:**
- [List of files written/updated]

**Pruned:**
- [List of files or entries removed]

**Learned:**
- [2-3 key learnings from this session's work]
```

## Memory Locations

| Memory Type | Path |
|------------|------|
| Index | `C:\Users\brsth\.claude\projects\P--\memory\MEMORY.md` |
| Topic files | `C:\Users\brsth\.claude\projects\P--\memory\*.md` |
| Daily logs | `memory/logs/YYYY/MM/YYYY-MM-DD.md` |

## Integration

**SessionStart hook** (`SessionStart_memory_monitor.py`) warns when MEMORY.md > 180 lines. Consider running `/dream` when you see this warning.

**Related skills:**
- `/reflect` — Captures session learnings to CKS
- `/learn` — Novelty-weighted lesson capture
- `/gto` — Gap analysis for projects
