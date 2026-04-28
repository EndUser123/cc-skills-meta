---
name: reason_ppx
version: 1.0.0
status: stable
category: meta
enforcement: advisory
workflow_steps:
  - Assess query complexity
  - Classify task type
  - Build internal draft with claims — treat the requested mechanism as a capability target: if the named path is unavailable, generate alternatives across native/workaround/architecture-redesign. Mark each as robust, brittle, version-dependent, or speculative.
  - Dispatch to external roles (verify/redteam/alternative) if nontrivial
  - Reconcile contradictions
  - Finalize answer with evidence labels
triggers:
  - /reason_ppx
suggest: []
---

# /reason_ppx — Python-Backed Hybrid Reasoning Orchestrator

A self-contained Claude Code skill that combines internal THINK-style reasoning with targeted external LLM verification, red-teaming, and alternative generation via a Python orchestration kernel.

## Usage

```
/reason_ppx [query] [--options]
```

**Options:**
- `--no-external` — Pure internal reasoning (fastest)
- `--debug` — Full JSON state output
- `--context PATH` — Explicit file/directory context
- `--output [compact|verbose|json]` — Output format

**Mode Flags** (override routing toward specific reasoning behavior):
- `--mode review` — attack weak logic, hidden fragility, omitted costs, incentive blind spots
- `--mode design` — compare architectures: simplicity, failure containment, migration burden
- `--mode diagnose` — ranked hypotheses, smallest discriminating test
- `--mode optimize` — clarify objective first, ask whether redesign beats tuning
- `--mode decide` — regret minimization + optionality + expected value + downside containment
- `--mode explore` — challenge frame itself, what adjacent problem matters more
- `--mode off` — treat discomfort as signal, hidden mismatch, elegant-but-wrong
- `--mode execute` — produce momentum now, not just ideas

**Decision Flags** (when query is a decision):
- `--force-choice` — pick one option, state why it wins, state reversal trigger. No both-sidesing.
- `--kill` — explicit Keep/Delegate/Defer/Kill pruning. Aggressive reduction.
- `--invert` — analyze failure paths: how it fails, earliest warning sign, preventive move.
- `--ship` — add execution checklist: next 15min action, next 60min push, first milestone, blocker, kill criteria.

## Architecture

```
User Query
    │
    ▼
┌─────────────────────────────┐
│  Intake & Classification     │
│  (classifier.py)            │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  Context Building           │
│  (context_builder.py)       │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  Frame Selection            │
│  (frames.py)               │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  Internal Draft + Claims    │
│  (main.py: build_internal) │
└──────────────┬──────────────┘
               │
    ┌──────────┴──────────┐
    │  External needed?    │
    │  (policies.py)        │
    └──────────┬──────────┘
               │
    ┌──────────┴──────────┐
    │  YES                 │  NO
    ▼                      ▼
┌───────────────┐    ┌─────────────┐
│ Execute Roles │    │ Finalize    │
│ (providers.py)│    │ Answer      │
│ - verify      │    └─────────────┘
│ - redteam     │
│ - alternative │
└───────┬───────┘
        │
        ▼
┌───────────────────────────────┐
│  Reconciliation + Finalize    │
│  (synthesizer.py)             │
└───────────────┬───────────────┘
                │
                ▼
        Final Answer
        (evidence-labeled)
```

## External Roles

| Role | Provider | Purpose |
|------|----------|---------|
| verify | gemini | Test claims for support/weakness |
| redteam | pi_m27 | Attack for flaws, edge cases, risks |
| alternative | codex | Propose materially different solution |

## Reconciliation Enhancements (synthesizer.py)

The reconciliation layer applies three additional passes before finalizing:

### Decision Theory Pass
Score each candidate on:
- Expected upside, downside risk, reversibility
- Time to feedback, energy cost, dependency load
- Compounding potential, robustness if assumptions wrong

### Bias Check
Detect and flag:
- Sunk cost, status quo bias, loss aversion
- Overconfidence, confirmation bias, novelty bias
- Analysis paralysis, emotional relief disguised as logic

### Second-Order Effects
Ask:
- If this wins, what burden appears?
- If it fails, what cascades?
- What future optionality is destroyed or created?

## ADHD Compensation

The synthesizer also compensates for cognitive friction:
- If overwhelmed → reduce to what matters, what doesn't, next move
- If stuck comparing → choose top 2, kill the rest
- If perfection looping → B+ execution now over A+ theory later
- If scattered → re-anchor to objective
- If procrastinating → shrink first step until friction near zero

## Evidence Labels

Every claim is labeled:
- **VERIFIED** — Directly supported by sources
- **INFERRED** — Logical but not explicit
- **UNPROVEN** — Speculative or contradicted

## Key Files

| File | Purpose |
|------|---------|
| `py/main.py` | Entry point, orchestration loop |
| `py/classifier.py` | Task type classification |
| `py/frames.py` | Reasoning frame selection |
| `py/policies.py` | External dispatch decisions |
| `py/providers.py` | CLI invocation |
| `py/synthesizer.py` | Reconciliation + final answer |

## Backend Execution

```bash
python -m py.main --query "your question"
```

Or via skill invocation which delegates to the Python orchestrator.
