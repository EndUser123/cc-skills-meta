---
description: Elite reasoning ecosystem — command + hooks + subagents + MCP + calibration. Full 5-layer system with red_team, implementation_realist, decision_editor subagents.
allowed-tools: Bash(pwd:*), Bash(git:*), Bash(ls:*), Bash(find:*), Bash(cat:*), Bash(head:*), Bash(sed:*), Bash(test:*), Bash(grep:*)
---

`/reason_openai_v4` — Elite Reasoning Ecosystem

Loaded from: `P:/packages/cc-skills-meta/skills/reason_openai_v4.0/SKILL.md`

**This is a 5-layer ecosystem:**

| Layer | Component | Purpose |
|-------|-----------|---------|
| 1 | `/reason_openai_v4` command | Flagship reasoning + decision |
| 2 | Hooks (preflight/gate/log) | Preflight context, output gate, usage logging |
| 3 | Subagents (red_team, implementation_realist, decision_editor) | Adversarial split when warranted |
| 4 | MCP (GitHub, docs, browser) | Grounded truth from live systems |
| 5 | Calibration loop | Personal feedback loop |

**Usage:**
```
/reason_openai_v4 [query] [--flags]
```

**Best flag combinations:**
- `--mode decide --force-choice ...` — stuck decisions
- `--mode off --depth deep ...` — vague discomfort
- `--mode review --depth board ...` — high-stakes critique
- `--mode execute --ship ...` — thought → motion
- `--kill ...` — aggressive pruning
- `--invert ...` — failure path analysis

**Layer 3 subagents** (activated automatically on high-stakes queries):
- `red_team` — attack hidden assumptions, failure modes, incentive misreads
- `implementation_realist` — migration risk, maintenance burden, integration realism
- `decision_editor` — compress and sharpen, reduce option sprawl

**Calibration:** Every invocation is logged. After 20–50 uses, run the analyze loop and update CLAUDE.md.

Load the skill and execute `$ARGUMENTS`.