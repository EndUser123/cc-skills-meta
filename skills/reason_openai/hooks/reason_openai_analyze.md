# reason_openai_analyze.md

Calibration guide for the `reason_openai_analyze.py` script.

## What it does

Reads `~/.claude/logs/reason_openai_log.jsonl` and prints:
- mode / depth distribution
- field completeness (% present, avg length)
- quality heuristics (missing sections, weak recommendations)
- top repeated misses

## Running it

```bash
python P:/packages/cc-skills-meta/skills/reason_openai/hooks/reason_openai_analyze.py
```

Or ask naturally: *"what patterns am I repeating in /reason_openai?"*

## Reading the output

### Mode/depth distribution

If one mode dominates (>80%), you may be over-indexing. Example:
- `decide` at 70% → confirm you're not avoiding genuine exploration
- `review` at 10% → confirm you're not skipping adversarial challenge

### Field completeness

Each field has a completeness score. Flag any field below 60%:

| Field | Threshold | Common cause |
|-------|-----------|--------------|
| Best current conclusion | 60% | Hedging instead of committing |
| Why it wins | 60% | Vague justification, no evidence |
| Strongest challenge | 60% | Avoiding the real objection |
| Best next action | 60% | Option sprawl, no clear first step |
| Ignore | 50% | Low — may indicate false balance |

### Quality heuristics

The script flags:
- Sections present but <20 chars (stubbed headings)
- "why it wins" missing evidence links
- "next action" missing an owner or time boundary

### Top repeated misses

If the same section is missing across >30% of entries, the **skill body** needs fixing — not your workflow. Check SKILL.md's enforcement and prompt instructions.

## When to update CLAUDE.md

After running analysis on 20–50 invocations, update CLAUDE.md when you see:

1. **Consistent mode mismatch** — you're invoking `review` when `decide` would have been better. Add a note to CLAUDE.md under your reasoning patterns.

2. **Repeated section weakness** — a specific field (e.g., "Why it wins") consistently lacks grounding. Add a reminder to your reasoning prompt or frontmatter enforcement.

3. **Depth calibration drift** — tribunal runs always win over targeted, or vice versa. Adjust the default depth in the skill body.

4. **Subagent failure patterns** — if `red_team` outputs frequently miss "Failure modes", the subagent definition needs updating, not your usage.

## Calibration loop

```
log (every invocation)
  ↓
analyze (after 20–50 uses)
  ↓
update CLAUDE.md with observed patterns
  ↓
update command/hooks/subagents as needed
```

Do not update CLAUDE.md on every run — wait for a pattern to appear at least 3 times.

## Output file reference

The script prints to stdout. Redirect to file for tracking:
```bash
python .../reason_openai_analyze.py > ~/.claude/logs/reason_openai_analysis.txt
```