---
name: reason_ppx
version: 1.0.0
status: stable
category: meta
enforcement: advisory
workflow_steps:
  - Assess query complexity
  - Classify task type
  - Build internal draft with claims
  - Dispatch to external roles (verify/redteam/alternative) if nontrivial
  - Reconcile contradictions
  - Finalize answer with evidence labels
triggers:
  - /reason_ppx
suggest:
  - /think
  - /ai-pcli
  - /reason
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
