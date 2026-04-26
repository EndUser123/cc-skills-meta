---
name: reason_openai
description: Elite reasoning ecosystem — command + hooks + subagents + existing tools + calibration.
enforcement: advisory
workflow_steps:
  - id: layer1_command
    description: "Use /reason_openai command with flags: mode, depth, force-choice, kill, invert, ship"
  - id: layer2_hooks
    description: "UserPromptSubmit preflight → Stop command quality gate → Stop log → Stop pending queue → SessionStart reminder"
  - id: layer3_subagents
    description: "red_team attacks, implementation_realist critiques, decision_editor compresses, each with SubagentStop quality gate"
  - id: layer4_tools
    description: "Use existing tools: GH CLI (github), /explore + /context7 + search-research (docs), browser-harness (browser)"
  - id: calibrate
    description: "Log every invocation to JSONL; pending queue for review; analyze with reason_openai_analyze.py; update CLAUDE.md"
allowed-tools: Bash(pwd:*), Bash(ls:*), Bash(find:*), Bash(git:*), Bash(cat:*), Bash(head:*), Bash(sed:*), Bash(test:*), Bash(grep:*)
---

# /reason_openai — Ecosystem Reference

The command is one layer. The ecosystem is five.

## Layers

| # | Layer | Component | Purpose |
|---|-------|-----------|---------|
| 1 | Command | `/reason_openai` slash command | Flagship reasoning + decision |
| 2 | Hooks | `reason_openai_preflight.py` + `reason_openai_quality_gate.py` + `reason_openai_log.py` | Preflight context, output gate, usage logging |
| 3 | Subagents | `red_team.md`, `implementation_realist.md`, `decision_editor.md` | Adversarial split when warranted |
| 4 | Tools | GH CLI, /explore, /context7, search-research, browser-harness | Existing tools provide grounded truth — no MCP servers needed |
| 5 | Calibration | `reason_openai_analyze.py` + `reason_openai_analyze.md` | Personal feedback loop |

## Hooks (install to `~/.claude/settings.json`)

### `UserPromptSubmit` — preflight
Injects operating reminders when `/reason_openai` is invoked.

### `Stop` — command quality gate + log + pending queue
1. `command` (quality gate) — `reason_openai_quality_gate.py` checks transcript for required sections before allowing stop
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

## External tools (Layer 4)
1. **GitHub** — GH CLI: PR context, issue history, commit diffs
2. **Docs/knowledge** — /explore + /context7 + search-research
3. **Browser** — browser-harness for live validation

## Execution

The `reason_openai_router.py` script handles mode detection and routing.

```bash
cd "P:/packages/cc-skills-meta/skills/reason_openai"
python3 reason_openai_router.py --prompt "$ARGUMENTS"
```

**Modes** (auto-detected or forced with `--mode`):
- `decide` — force a clear recommendation with justification
- `review` — critique existing answer, surface hidden flaws
- `off` — exploratory; diagnose what's wrong rather than answer
- `diagnose` — root-cause analysis
- `optimize` — performance, cost, latency improvements
- `design` — options and architecture creation
- `execute` — move from thought to action

**Depths** (auto-selected or forced with `--depth`):
- `local` — single-model reasoning, structured output prompt
- `targeted` — local + one subagent (red_team or implementation_realist)
- `tribunal` — local + all three subagents (red_team, implementation_realist, decision_editor)

**Standard output contract** (all modes):
```
Route chosen:
Best current conclusion:
Why it wins:
Strongest challenge:
Biggest uncertainty:
Best next action:
Ignore:
Minority warning:
```

### Subagent dispatch (targeted / tribunal depth)

When depth is `targeted` or `tribunal`, invoke subagents using the Agent() tool with the subagent definitions at:
- `P:/packages/cc-skills-meta/skills/reason_openai/agents/red_team.md`
- `P:/packages/cc-skills-meta/skills/reason_openai/agents/implementation_realist.md`
- `P:/packages/cc-skills-meta/skills/reason_openai/agents/decision_editor.md`

**Targeted depth** — invoke one subagent based on mode:
- `diagnose`, `optimize`, `review` → **red_team** (attack the hypothesis)
- `design`, `execute`, `decide` → **implementation_realist** (pressure-test practicality)

**Tribunal depth** — invoke all three in sequence:
1. **red_team** → find hidden flaws
2. **implementation_realist** → test execution realism
3. **decision_editor** → compress to final recommendation

**Subagent prompt composition**:
```
You are <subagent_name>. Read your definition at P:/packages/cc-skills-meta/skills/reason_openai/agents/<subagent_name>.md

User query: <original prompt>
Local reasoning: <output from local reasoning step>
Mode: <mode>

Follow your output contract exactly. Write findings to your response.
```

**Synthesis** — after subagents complete, synthesize all outputs into the standard contract format. The `decision_editor` output is the primary source; `red_team` and `implementation_realist` outputs inform and challenge the conclusion.

## Installation

**Windows (symlink):**
```cmd
cmd //c mklink /J "C:\Users\brsth\.claude\plugins\reason_openai" "P:\packages\cc-skills-meta\skills\reason_openai"
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