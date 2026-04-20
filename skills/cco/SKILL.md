---
name: cco
description: Concurrent agent orchestrator — decompose any task and delegate to parallel sub-agents. Handles both implementation tasks (code, files) and analysis/review tasks (multi-perspective, synthesis).
version: "1.0.0"
status: stable
category: development
triggers:
  - /cco
  - /agent-orchestrator
aliases:
  - /cco
  - /agent-orchestrator
activation_triggers:
  - orchestrate
  - multi-agent
  - parallel agents
  - multiple perspectives
  - cross-check
  - agent panel
  - get .* opinions
  - review with
  - analyze with
  - validate with
  - experts .* review

suggest:
  - /cwo
  - /workflow
  - /nse
---

# CCO — Concurrent Agent Orchestrator

## Purpose

Decompose any task — implementation or analysis — and delegate to parallel sub-agents for concurrent execution. You coordinate; agents execute. Never do the work yourself.

**Replaces `/agent-orchestrator`** (deprecated, same alias preserved).

## Prohibited Actions

- **NEVER execute work yourself** — delegate all file ops, analysis, and code changes to sub-agents
- **NEVER spawn agents sequentially** — launch all simultaneously in one response
- **NEVER accept sub-agent responses without tool usage verification** — 0 tool uses = failure
- **NEVER launch fewer than 2 agents** for analysis/review tasks — defeats multi-perspective purpose
- **NEVER invent plugin agent names** — use only names from `P:/.claude/docs/plugin-agents.md`
- **NEVER search without path scoping** — always specify exact paths, exclude venv/node_modules

## Workflow

1. **Capture context** — `pwd` + `git status` to anchor to launch directory
2. **Select agents** — choose from `P:/.claude/docs/plugin-agents.md`; never guess names
3. **Generate scoped prompts** — one optimized prompt per agent (see PROMPT TEMPLATE below)
4. **Launch in parallel** — all Task calls in a single response
5. **Validate results** — check every agent for 0 tool uses before synthesizing
6. **Synthesize** — aggregate findings, resolve conflicts, attribute sources

---

## Agent Selection

> Full registry with task-type mapping: **`P:/.claude/docs/plugin-agents.md`**

Quick reference for common tasks:

| Task | Agents |
|---|---|
| Code review | `feature-dev:code-reviewer`, `pr-review-toolkit:code-reviewer` |
| Simplification | `code-simplifier:code-simplifier`, `pr-review-toolkit:code-simplifier` |
| Architecture | `feature-dev:code-architect`, `feature-dev:code-explorer` |
| Silent failures | `pr-review-toolkit:silent-failure-hunter` |
| Type safety | `pr-review-toolkit:type-design-analyzer` |
| Root cause | `code-critic`, `rca-specialist` |
| Security | `adversarial-security` |

**When NOT to use multiple agents:** simple bug fix, single-file change, trivial refactor — direct action is faster.

---

## Prompt Template

Every agent gets a scoped prompt with these 4 elements:

```
You are the {AGENT_NAME} agent.

OBJECTIVE: {clear, specific goal — one thing}

OUTPUT_FORMAT: {expected structure — findings list, JSON, prose}

TOOLS: {which tools to use and when}

BOUNDARIES: {what NOT to do — prevents overlap with other agents}

PATH_SCOPE: Search ONLY in {specific_path}
EXCLUDE: .venv/, venv/, node_modules/, __pycache__/, .git/, dist/, build/

CONTEXT:
{only the snippet or description relevant to this agent's role}

YOUR FOCUS:
{the specific aspect this agent owns}
```

**Path scoping is mandatory.** Agents without it will search `.venv/Lib/site-packages/` (25 000+ lines of library code) instead of actual source.

| ❌ Wrong | ✅ Correct |
|---|---|
| "Find the 3 largest Python files" | "Find the 3 largest Python files in `P:\projects\yt-fts\src\`" |
| "Search for X in the codebase" | "Search for X in `P:\__csf\src\features\`" |

### Sequential workflows (CrewAI pattern)

When agents must build on each other's output:

```
Agent N receives:
  context=[agent_1_task, agent_2_task, ...]

PREVIOUS WORK:
{summary of what earlier agents found}

YOUR FOCUS:
{continue from where previous agents left off — do not repeat their work}
```

---

## ⚠️ Zero-Tool-Use Failure Gate (MANDATORY)

Before synthesizing, inspect every agent result:

```
FOR EACH agent result:
  IF tool_use_count == 0:
    → subagent_type was INVALID or unresolvable
    → DO NOT include in synthesis
    → LOG: "Agent '{subagent_type}' returned 0 tool uses — invalid type.
             Verify against P:/.claude/docs/plugin-agents.md"
    → STOP synthesis if >50% of agents failed
    → Report which types failed so the skill definition can be fixed
```

0 tool uses is a hard error, not a successful empty result. Silently including it fabricates consensus.

---

## Synthesis Pattern

```
1. VALIDATE  — zero-tool-use gate (above)
2. COLLECT   — gather valid agent outputs only
3. CLASSIFY  — agreements / conflicts / unique insights
4. RESOLVE   — address conflicts with rationale, weight by agent relevance
5. SYNTHESIZE — agreements first (confidence), conflicts (nuance), recommendation (actionable)
6. ATTRIBUTE — credit each agent by name
```

### Output format

```markdown
## Multi-Agent Analysis: {subject}

### Pre-Synthesis Validation
- {agent-type}: {N} tool uses ✓/✗

### Summary
{2–3 sentences}

### Agreements ✓
{points where all agents concurred}

### Conflicts ⚠️
{disagreements with resolution and rationale}

### Unique Insights 💡
{valuable points raised by only one agent}

### Recommendation
{clear, actionable next steps}

### Agent Contributions
- {agent}: {what they contributed}
```

---

## Scale by Complexity

| Complexity | Agents | Tool calls each | Example |
|---|---|---|---|
| Simple | 1 | 3–10 | Fact-finding, single file |
| Comparison | 2–3 | 10–15 | Review, architecture assessment |
| Complex | 4+ | divided | Multi-file cross-system analysis |

---

## Pre-Output Checklist

- [ ] Task tool called with 2+ different subagent types (for analysis tasks)
- [ ] Every agent received a distinct, scoped prompt
- [ ] All agent types verified against `P:/.claude/docs/plugin-agents.md`
- [ ] Zero-tool-use gate passed
- [ ] Synthesizing AGENT outputs, not own analysis
