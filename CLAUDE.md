# cc-skills-meta

Meta-cognitive and workflow skills for Claude Code — retrospectives, gap analysis, learning, self-improvement, and orchestration.

## Skills (37)

| Skill | Purpose |
|-------|---------|
| cks | Constitutional Knowledge System |
| cognitive-stack | Cognitive architecture modes |
| constitutional-patterns | Pattern enforcement rules |
| constraints | Show active project constraints from CLAUDE.md |
| cwo | 16-step unified orchestration with CKS handoff |
| decision-tree | Decision tree analysis |
| dne | Do Not Execute safety gate |
| doc-to-skill | Convert documentation into Claude Skills |
| dream | Creative ideation |
| evidence-applicability | Evidence tier assessment |
| evolve | Skill evolution |
| execution-clarity | Execution protocols |
| friction | Interaction and workflow friction detection |
| gto | Gap-to-opportunity analysis with subagent dispatch |
| learn | Quality-controlled lesson storage |
| library-first | Check for existing solutions before generating new code |
| mlc | Meta-learning coordinator |
| orchestrator | Multi-agent orchestration |
| ralph | Task decomposition and iterative development loop |
| recap | Terminal-wide session catch-up |
| reflect | Session reflection and pre-mortem |
| response-atomicity | Response quality enforcement |
| retro | Self-contrast retrospective orchestrator |
| sequential-thinking | Structured reasoning |
| similarity | Find similar skills by semantic analysis |
| skeptic | Skeptical analysis of claims |
| skill-craft | Skill creation and management |
| solo-dev-authority | Constitutional constraints for solo developers |
| standards | Read and enforce CSF NIP standards |
| subagent-driven-development | Subagent task decomposition |
| think | Structured thinking modes |
| top-problems | Top problems aggregation |
| tot | Tree of thought exploration |
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
