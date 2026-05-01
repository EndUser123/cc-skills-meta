# cc-skills-meta

Meta-cognitive and workflow skills for Claude Code — retrospectives, gap analysis, learning, self-improvement, and orchestration.

## Skills (3 Consolidated + 1 Runtime)

| Skill | Purpose |
|-------|---------|
| genius | `/genius` — Thought partner: challenges premises, surfaces cross-domain insights, maps problem first |
| reason | `/reason` — Unified reasoning engine (replaces `/think`, `/reason_ppx`, `/reason_grok`, `/reason_openai`, `/reason_openai_v3.0`). Routes by epistemic state: local_only → single_challenger → parallel_challengers |
| s | `/s` — Strategy engine: multi-persona brainstorming (Innovator/Pragmatist/Critic/Expert) with SCAMPER, Six Thinking Hats, First Principles |
| gto | `/gto` — Session-aware gap-to-opportunity analysis. Reads transcripts, detects uncompleted goals/deferred items, enriches via 5 LLM sub-agents, outputs structured RNS findings. Has its own hook lifecycle (PreToolUse, PostToolUse, Stop, SessionStart) and 282 tests. Not a prompt template — a runtime subsystem. Accessed via plugin (`cc-skills-meta:gto`) and project settings, not a junction. |

## Consolidation Notes

The original 52 skills were consolidated into 3:

- **`/genius`** — stays as-is. Unique "person in the room" tone + premise challenge. Nothing else does this.
- **`/reason`** — merges 5 skills into one. All were reasoning engines differing only in routing mechanism (confidence vs epistemic state vs Python backend). One command, auto-routing by epistemic state.
- **`/s`** — stays as-is. Unique multi-persona brainstorming with SCAMPER, Six Thinking Hats. Different use case (option generation vs reasoning).

### Old → New Mapping

| Old Skill | New Home | Status |
|-----------|----------|--------|
| `/think` | `/reason` (Quick depth tier) | Merged |
| `/reason_ppx` | `/reason` (Python backend) | Merged |
| `/reason_grok` | `/reason` (unified hybrid engine) | Merged |
| `/reason_openai` | `/reason` (6-stage pipeline) | Merged |
| `/reason_openai_v3.0` | `/reason` (elite decision modes) | Merged |

All old trigger names still work — they map to `/reason` via the `triggers` frontmatter.

## Artifacts Convention

All runtime artifacts write to:

```
.claude/.artifacts/{terminal_id}/{skill_name}/
```

| Artifact type | Destination |
|--------------|-------------|
| Runtime proof/evidence (artifact-proof.json, workflow-model.json) | `.claude/.artifacts/{terminal_id}/{skill_name}/` |
| Generated documentation (index.html) | Target skill's directory, alongside SKILL.md |
| Temporary/intermediate files | `.claude/.artifacts/{terminal_id}/{skill_name}/tmp/` |

**Rules:**
- `terminal_id` ensures concurrent sessions do not overwrite each other's artifacts
- Skills MUST NOT write state to their own directory or to the package root
- Generated documentation (index.html) is the exception — it belongs next to the skill it documents

## Scripts / Forked Tools

### skill-creator (subscription-first fork)

Fork of the `skill-creator` plugin with subscription-only API substitution.

**Location:** `scripts/skill_creator/`

**Why forked:** The original uses `anthropic.Anthropic()` for description improvement (separate API cost). This fork substitutes `claude -p` calls, routing through the Claude Code subscription.

**Key files:**
- `improve_description.py` — `claude_p()` substitution instead of `client.messages.create()`
- `sync_check.py` — auto-detects upstream plugin updates via SHA256[:12] hashes
- `run_loop.py` — full eval+improve loop calling `claude -p` throughout
- `run_eval.py` — trigger eval via `claude -p` (no API cost)

**Invocation:**
```bash
cd P:/packages/cc-skills-meta
python -m scripts.skill_creator.run_loop --eval-set <path> --skill-path <path> --model sonnet
python -m scripts.skill_creator.run_eval --eval-set <path> --skill-path <path>
```

**Version tracking:** On each run, `sync_check.py` compares hashes of tracked plugin scripts against `.fork_metadata.json`. If the plugin updates, it warns — run `python scripts/skill_creator/sync_check.py --check` to see what changed, then cherry-pick upstream changes.

**Tracked files (5):** `improve_description.py`, `run_loop.py`, `run_eval.py`, `utils.py`, `generate_report.py`

## Installation

Skills surfaced via junctions in .claude/skills/.

| Junction | Target |
|----------|--------|
| `.claude/skills/genius` | `packages/cc-skills-meta/skills/genius/` |
| `.claude/skills/reason` | `packages/cc-skills-meta/skills/reason/` |
| `.claude/skills/s` | `packages/cc-skills-utils/skills/s/` |
