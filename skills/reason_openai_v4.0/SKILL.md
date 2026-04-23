---
name: reason_openai_v4.0
description: Elite reasoning ecosystem — command + hooks + subagents + MCP + calibration.
enforcement: advisory
workflow_steps:
  - id: layer1_command
    description: "Use /reason_openai command with flags: mode, depth, force-choice, kill, invert, ship"
  - id: layer2_hooks
    description: "UserPromptSubmit preflight → Stop agent quality gate → Stop log → Stop pending queue → SessionStart reminder"
  - id: layer3_subagents
    description: "red_team attacks, implementation_realist critiques, decision_editor compresses, each with SubagentStop quality gate"
  - id: layer4_mcp
    description: "Connect GitHub, docs, browser for grounded reasoning with live data"
  - id: calibrate
    description: "Log every invocation to JSONL; pending queue for review; analyze with reason_openai_analyze.py; update CLAUDE.md"
allowed-tools: Bash(pwd:*), Bash(ls:*), Bash(find:*), Bash(git:*), Bash(cat:*), Bash(head:*), Bash(sed:*), Bash(test:*), Bash(grep:*)
---

# /reason_openai v4.0 — Ecosystem Reference

The command is one layer. The ecosystem is five.

## Layers

| # | Layer | Component | Purpose |
|---|-------|-----------|---------|
| 1 | Command | `/reason_openai` slash command | Flagship reasoning + decision |
| 2 | Hooks | `reason_openai_preflight.py` + `reason_openai_quality_gate.py` + `reason_openai_log.py` | Preflight context, output gate, usage logging |
| 3 | Subagents | `red_team.md`, `implementation_realist.md`, `decision_editor.md` | Adversarial split when warranted |
| 4 | MCP | GitHub, docs, browser | Grounded truth from live systems |
| 5 | Calibration | `reason_openai_analyze.py` + `reason_openai_analyze.md` | Personal feedback loop |

## Hooks (install to `~/.claude/settings.json`)

### `UserPromptSubmit` — preflight
Injects operating reminders when `/reason_openai` is invoked.

### `Stop` — agent quality gate + log + pending queue
1. `agent` (quality gate) — verifier agent checks decision-grade substance before allowing stop
2. `command` — `reason_openai_log.py` logs invocation to `~/.claude/logs/reason_openai_log.jsonl`
3. `command` — `reason_openai_pending_queue.py` writes to `reason_openai_pending.jsonl`

### `SubagentStop` — per-subagent quality gates
Verifies `red_team`, `implementation_realist`, and `decision_editor` outputs meet their contracts.

### `SessionStart` — reminder
`reason_openai_session_reminder.py` surfaces pending reviews at session start.

## Subagents

### `red_team`
Attack the answer. Hidden assumptions, failure modes, incentive misreads, elegant-but-wrong.

### `implementation_realist`
Practical execution critic. Migration risk, maintenance burden, integration realism.

### `decision_editor`
Compress and sharpen. Choose recommendation, reduce option sprawl, clarify next action.

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

## External intelligence policy
When hooks, subagents, MCP servers, repo context, or tools can materially improve truth, judgment, or execution quality, use them.
Prefer one verified insight over five plausible guesses.
Prefer grounded reasoning over elegant unsupported reasoning.

## MCP priorities
1. GitHub — PRs, issues, commit history
2. Docs/knowledge — fresh library/API docs
3. Browser/Playwright — validate flows, check behavior

## Installation

**Windows (symlink):**
```cmd
cmd //c mklink /J "C:\Users\brsth\.claude\plugins\reason_openai_v4.0" "P:\packages\cc-skills-meta\skills\reason_openai_v4.0"
```

**Then in Claude Code:** `/reload-plugins`

The plugin is self-contained — no manual hook registration or file copying required.

## Best test prompts
```
/reason_openai this migration plan feels too neat
/reason_openai --mode decide --force-choice postgres vs clickhouse for this workload
/reason_openai --mode execute --ship I have too many competing priorities this week
/reason_openai --mode review --depth board review this architecture for hidden failure modes
```

## Best flag combos
```
/reason_openai --mode decide --force-choice ...   # stuck decisions
/reason_openai --mode off --depth deep ...        # vague discomfort
/reason_openai --mode review --depth board ...    # high-stakes critique
/reason_openai --mode execute --ship ...          # thought → motion
/reason_openai --kill ...                         # aggressive pruning
/reason_openai --invert ...                      # failure path analysis
```
