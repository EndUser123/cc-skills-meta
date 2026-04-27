---
name: gto
description: "GTO v4.0 — Strategic gap-to-opportunity analysis with RNS-compatible output"
version: "4.0.0"
triggers:
  - "/gto"
  - "gap analysis"
  - "find gaps"
  - "gap to opportunity"
category: analysis
enforcement: advisory
workflow_steps:
  - "Run deterministic analysis (orchestrator --skip-agents)"
  - "Dispatch domain analyzer agent via Agent tool"
  - "Run full orchestrator to merge results"
  - "Display findings in RNS domain-grouped format with Do ALL footer"
---

# GTO v4.0 — Gap-to-Opportunity Analysis

## Overview

GTO runs gap analysis on the current codebase, producing RNS-compatible machine output and displaying findings in RNS domain-grouped format. It uses deterministic detectors first, then optionally dispatches subagents for deeper analysis.

## Execution Directive

When invoked, run the orchestrator and dispatch agent subanalyses:

### Step 1: Run Deterministic Analysis

```bash
cd "P:/packages/cc-skills-meta" && python -m skills.gto.orchestrator --mode full --skip-agents --terminal-id "$WT_SESSION" --session-id "$CLAUDE_SESSION_ID" --root .
```

This writes artifacts to `.claude/.artifacts/{terminal_id}/gto/`.

### Step 2: Dispatch Domain Analyzer Agent (if mode != quick)

Spawn a subagent to perform deeper domain analysis:

```
Agent(subagent_type="general-purpose",
  description="GTO domain analysis",
  prompt="You are a domain-specific code gap analyzer. Read the handoff file at .claude/.artifacts/{terminal_id}/gto/inputs/agent_handoff.json for your target and configuration. Analyze the codebase for gaps in quality, tests, docs, security, and performance. Write your findings as a JSON array to .claude/.artifacts/{terminal_id}/gto/inputs/domain_analyzer_result.json. Each finding must have: id, title, description, domain, gap_type, severity, action, priority, file (or null), line (or null), effort, unverified (boolean), evidence (array of {kind, value}). Maximum 15 findings.")
```

### Step 3: Run Full Orchestrator (merging agent results)

```bash
cd "P:/packages/cc-skills-meta" && python -m skills.gto.orchestrator --mode full --terminal-id "$WT_SESSION" --session-id "$CLAUDE_SESSION_ID" --root .
```

### Step 4: Display Results

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

## Modes

| Mode | Description |
|------|-------------|
| `full` | Deterministic + agent analysis (default) |
| `quick` | Deterministic detectors only, no agents |
| `agent-only` | Only agent analysis, skip deterministic |

## Agent Dispatch Pattern

GTO uses Claude Code's Agent tool for subagent dispatch. Handoff is file-based:

1. Orchestrator writes handoff JSON to `inputs/agent_handoff.json`
2. Agent reads handoff, performs analysis, writes results to `inputs/domain_analyzer_result.json`
3. Orchestrator re-runs, picks up agent results, merges with deterministic findings

## Output Format

GTO produces RNS-compatible machine output:

```
RNS|D|1|🔧|QUALITY
RNS|A|1a|quality|E:~5min|recover/medium|description|file_ref|owner=/code|done=0|caused_by=|blocks=|unverified=0
RNS|Z|0|NONE
```

This is compatible with `/rns` for cross-session action tracking.

## Artifact Location

All artifacts are terminal-scoped:
```
.claude/.artifacts/{terminal_id}/gto/
├── state/run_state.json
├── inputs/agent_handoff.json
├── inputs/domain_analyzer_result.json
├── outputs/artifact.json
├── logs/failures.jsonl
└── carryover.json
```

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
| staledeps | /deps |

## Verification

The stop hook verifies completion by checking:
1. State phase == "completed"
2. Artifact file exists with valid JSON
3. Machine output has RNS|D| and RNS|Z| markers
4. All expected artifacts are present

## Critical Rules

- Do NOT parse prose output for completion detection
- Use state-driven verification only
- Agent handoff is file-based, not API-based
- Terminal-scoped artifacts prevent cross-terminal conflicts
- Deterministic findings always take precedence over agent findings on merge
