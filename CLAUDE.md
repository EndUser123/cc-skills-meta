# cc-skills-meta

Meta-cognitive and workflow skills for Claude Code — retrospectives, gap analysis, learning, and self-improvement.

## Skills (20)

| Skill | Purpose |
|-------|---------|
| cks | Constitutional Knowledge System |
| decision-tree | Decision tree analysis |
| dne | Do Not Execute safety gate |
| dream | Creative ideation |
| evolve | Skill evolution |
| friction | Interaction and workflow friction detection |
| gto | Gap-to-opportunity analysis with subagent dispatch |
| learn | Quality-controlled lesson storage |
| mlc | Meta-learning coordinator |
| recap | Terminal-wide session catch-up |
| reflect | Session reflection and pre-mortem |
| retro | Self-contrast retrospective orchestrator |
| similarity | Find similar skills by semantic analysis |
| skill-craft | Skill creation and management |
| think | Structured thinking modes |
| top-problems | Top problems aggregation |
| trace | Decision trace reconstruction |
| truth | Truth validation |
| usm | Universal Skills Manager |
| why | Root-cause questioning |

## Artifacts Convention

All runtime artifacts write to:

```
P:/.claude/.artifacts/{terminal_id}/<skill-name>/
```

`terminal_id` from `CLAUDE_TERMINAL_ID` env var (falls back to `"default"`).

Skills MUST NOT write state to their own directory or to the package root. The `.gitignore` covers `.evidence/`, `.state/`, `.benchmarks/`, `__pycache__/`, `.claude/`.

## GTO Subagent Pattern

GTO dispatches parallel subagents (gap_finder, gto-logic, gto-quality, gto-code-critic) that write JSON to temp files, then merges results. Each subagent runs independently with its own output contract.

## Installation

Skills surfaced via junctions in `.claude/skills/`:

```powershell
New-Item -ItemType Junction -Path "P:/.claude/skills/<name>" -Target "P:/packages/cc-skills-meta/skills/<name>"
```

Command frontends live in `.claude/commands/<name>.md`.
