---
name: gto
description: "GTO v4.2 — Session-aware gap-to-opportunity analysis with RNS-compatible output"
version: "4.2.0"
triggers:
  - "/gto"
  - "gap analysis"
  - "find gaps"
  - "gap to opportunity"
category: analysis
enforcement: advisory
workflow_steps:
  - "Run deterministic analysis + session transcript analysis (orchestrator)"
  - "Optionally spawn enrichment agents for domain analysis, review, and normalization"
  - "Display findings in RNS domain-grouped format with Do ALL footer"
---

# GTO v4.2 — Session-Aware Gap-to-Opportunity Analysis

## Overview

GTO analyzes the current session's work — what was discussed, what was attempted, what remains incomplete — and produces RNS-compatible findings. It reads chat transcripts, handoff files, and session goals rather than doing heavy codebase scanning (that's /code, /test, /diagnose's job).

## Execution Directive

### Step 1: Run Session-Aware Analysis

```bash
cd "P:/packages/cc-skills-meta" && python -m skills.gto.orchestrator --terminal-id "$WT_SESSION" --session-id "$CLAUDE_SESSION_ID" --root .
```

This runs:
1. **Deterministic detectors** — .git presence, README existence
2. **Transcript resolution** — from identity.json (hook-captured, no scanning)
3. **File edit extraction** — Edit/Write tool calls from session transcript
4. **Session chain** — from session registry (terminal-scoped, no globbing)
5. **Session goal detection** — extracts stated goals from user messages
6. **Session outcome detection** — finds uncompleted goals, open questions, deferred items
7. **Completion filtering** — removes outcomes that were actually completed
8. **Carryover resolution** — marks findings as resolved if files were edited
9. **Agent handoff writing** — writes handoff files for enrichment agents
10. **Agent result reading** — merges any available agent enrichment results
11. **Merge, dedupe, route** — combine all sources, route to owning skills

Artifacts written to `.claude/.artifacts/{terminal_id}/gto/`.

### Step 1.5: Agent Enrichment (Optional)

Check if handoff files were written. If findings exist, spawn agents to enrich them:

```bash
test -f ".claude/.artifacts/{terminal_id}/gto/domain_analyzer_handoff.json" && echo "AGENTS_NEEDED" || echo "NO_AGENTS"
```

If `AGENTS_NEEDED`, spawn agents **sequentially** (each builds on the previous):

**Agent 1: Domain Analyzer** (subagent_type=general-purpose)
- Read: `.claude/.artifacts/{terminal_id}/gto/domain_analyzer_handoff.json`
- System prompt: from `skills/gto/agents/prompts.py` → `DOMAIN_ANALYZER_SYSTEM`
- Instructions: Analyze the findings and project context. Add domain-specific insights. Write findings as JSON array to `.claude/.artifacts/{terminal_id}/gto/domain_analyzer_result.json`

**Agent 2: Findings Reviewer** (subagent_type=general-purpose)
- Read: `.claude/.artifacts/{terminal_id}/gto/findings_reviewer_handoff.json`
- System prompt: from `skills/gto/agents/prompts.py` → `FINDINGS_REVIEWER_SYSTEM`
- Instructions: Review findings for accuracy, reject false positives, adjust severity. Write results to `.claude/.artifacts/{terminal_id}/gto/findings_reviewer_result.json`

**Agent 3: Action Normalizer** (subagent_type=general-purpose)
- Read: `.claude/.artifacts/{terminal_id}/gto/action_normalizer_handoff.json`
- System prompt: from `skills/gto/agents/prompts.py` → `ACTION_NORMALIZER_SYSTEM`
- Instructions: Normalize findings into canonical RNS action items. Write results to `.claude/.artifacts/{terminal_id}/gto/action_normalizer_result.json`

**Agent 4: Session Reviewer** (conditional — only if ambiguous outcomes exist)
- Read: `.claude/.artifacts/{terminal_id}/gto/session_reviewer_handoff.json`
- Instructions: Classify each outcome as `completed` or `open`, write to `session_reviewer_result.json`

**Agent 5: Gap Reviewer** (context-enriched structured review)
- Read: `.claude/.artifacts/{terminal_id}/gto/gap_reviewer_handoff.json`
- System prompt: from `skills/gto/agents/prompts.py` → `GAP_REVIEW_SYSTEM`
- Instructions: Produce a structured FACT/INFERENCE/UNKNOWN/RECOMMENDATION review plus any new gaps discovered. Write results to `.claude/.artifacts/{terminal_id}/gto/gap_reviewer_result.json`

After agents complete, re-run the orchestrator to merge results:

```bash
cd "P:/packages/cc-skills-meta" && python -m skills.gto.orchestrator --terminal-id "$WT_SESSION" --session-id "$CLAUDE_SESSION_ID" --root .
```

The second run reads agent result files and merges them into the final artifact.

### Step 1.6: Optional LLM Session Review

If the deterministic completion checker left ambiguous outcomes:

```bash
test -f ".claude/.artifacts/{terminal_id}/gto/session_reviewer_handoff.json" && echo "REVIEW_NEEDED" || echo "NO_REVIEW"
```

If `REVIEW_NEEDED`, this is handled as Agent 4 above.

### Step 2: Display Results

Read the artifact:
```bash
cat ".claude/.artifacts/{terminal_id}/gto/outputs/artifact.json"
```

Render the findings using the **RNS display format**. Read the canonical format spec before rendering:

```
Read file: skills/gto/__lib/machine_render.py
```

This module defines the domain map, emoji assignments, subletter numbering, and the full RNS pipe-delimited machine format. Use the same domain groupings and emoji when rendering the human-readable display.

The display must follow the `/rns` output format:
- Domain-grouped sections with emoji headers: `{num} {emoji} {DOMAIN} ({count})`
- Domain-numbered items: `{num}{letter} [{action}/{priority}] Description @ file:line`
- Sort within domain: recover > prevent > realize, then CRITICAL > HIGH > MEDIUM > LOW
- Footer: `0 — Do ALL Recommended Next Actions (N items)`
- No markdown fences around the RNS output

### Step 2.5: Forward-Looking Opportunity Analysis

After rendering the deterministic findings, produce a structured gap-to-opportunity review. This is now partially automated via **Agent 5 (Gap Reviewer)** which receives pre-populated detector evidence and produces a FACT/INFERENCE/UNKNOWN/RECOMMENDATION review plus any new findings.

**If Agent 5 ran successfully** (check `gap_reviewer_result.json`), incorporate its review into the display. The review appears as a structured section after the RNS findings.

**If Agent 5 did not run** (first pass, no agent results yet), perform the analysis manually based on these signals:

| Signal | What to notice |
|--------|----------------|
| **Incomplete work** | Features half-implemented, functions with TODO bodies, tests commented out, branches unmerged |
| **Dependency chains** | A was completed but B depends on A and wasn't started — B is the natural next step |
| **Deferred decisions** | "We'll deal with that later", "skip for now", "not in scope" — these are future work queued by the user |
| **Work trajectory** | The pattern of what was done implies what comes next (wired agents → test them; created module → document it) |
| **Avoidance signals** | Something mentioned once then skirted around — usually the hard or uncertain parts that will surface again |
| **Recurring themes** | Same concern raised across multiple turns or sessions — high-confidence prediction it will come up again |

For each predicted next action, render it as a `realize` action item in the RNS output with:
- **Specific description**: not "add tests" but "write integration tests for agent handoff/result round-trip in domain_analyzer.py"
- **Confidence indicator**: HIGH (dependency chain, explicitly deferred), MEDIUM (trajectory pattern), LOW (speculative)
- **Evidence**: cite the transcript turn or finding that supports the prediction

Display order:
1. **Signals observed** — list each signal detected in the transcript with the specific evidence (turn number, finding ID, file reference)
2. **Predicted opportunities** — the actions that follow from those signals, rendered as RNS `realize` items
3. Evidence precedes prediction, not the reverse — the reader should see the reasoning before the recommendation

Rules:
- Do NOT surface predictions that duplicate existing findings (those already appear as gaps)
- Prefer 3-5 high-specificity predictions over 10 generic ones
- If the session was exploratory with no clear trajectory, say so rather than forcing predictions
- Frame predictions as opportunities the user can act on, not obligations

## Session Data Sources

GTO reads from session-scoped sources (not global git state):

| Source | Purpose |
|--------|---------|
| `identity.json` | Hook-captured session_id, transcript_path, cwd |
| `session_registry.jsonl` | Terminal-scoped session chain history |
| `~/.claude/projects/*.jsonl` | Chat transcripts (tool call extraction, goal/outcome detection) |
| `.claude/.artifacts/{terminal_id}/gto/carryover.json` | Persisted findings across runs |
| `.claude/.artifacts/{terminal_id}/gto/*_handoff.json` | Agent input files |
| `.claude/.artifacts/{terminal_id}/gto/*_result.json` | Agent output files |

## Agent System Prompts

Agent prompts are defined in `skills/gto/agents/prompts.py`:

| Agent | Prompt Constant | Purpose |
|-------|----------------|---------|
| Domain Analyzer | `DOMAIN_ANALYZER_SYSTEM` | Enrich findings with domain-specific health assessments |
| Findings Reviewer | `FINDINGS_REVIEWER_SYSTEM` | Validate severity, reject false positives, dedupe |
| Action Normalizer | `ACTION_NORMALIZER_SYSTEM` | Normalize into canonical RNS action items |
| Session Reviewer | (in session_reviewer.py) | Classify ambiguous session outcomes |
| Gap Reviewer | `GAP_REVIEW_SYSTEM` | Structured FACT/INFERENCE/UNKNOWN/RECOMMENDATION review with context injection |

## Gap-to-Skill Routing

Findings are automatically routed to owning skills:

| Gap Type | Routes To |
|----------|-----------|
| missingdocs | /docs |
| techdebt | /code |
| runtime_error, bug | /diagnose |
| security | /security |
| perf | /perf |
| invalidrepo | /git |
| session_* | Review and act |

## Artifact Location

All artifacts are terminal-scoped:
```
.claude/.artifacts/{terminal_id}/gto/
├── state/run_state.json
├── outputs/artifact.json
├── logs/failures.jsonl
├── carryover.json
├── domain_analyzer_handoff.json
├── domain_analyzer_result.json
├── findings_reviewer_handoff.json
├── findings_reviewer_result.json
├── action_normalizer_handoff.json
├── action_normalizer_result.json
├── session_reviewer_handoff.json
└── session_reviewer_result.json
```

## Verification

The stop hook verifies completion by checking:
1. State phase == "completed"
2. Artifact file exists with valid JSON
3. Machine output has RNS|D| and RNS|Z| markers
4. All expected artifacts are present

## Critical Rules

- Do NOT parse prose output for completion detection
- Use state-driven verification only
- Terminal-scoped artifacts prevent cross-terminal conflicts
- Session findings come from transcript analysis, not codebase scanning
- Heavy codebase analysis should be routed to /code, /test, /diagnose — not done by GTO
- Agents are optional enrichment — the orchestrator works without them
- Agent results are merged on the next orchestrator run, not inline
