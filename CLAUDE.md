# cc-skills-meta

Meta-cognitive and workflow skills for Claude Code — retrospectives, gap analysis, learning, self-improvement, and orchestration.

## Skills (52)

| Skill | Purpose |
|-------|---------|
| behave | /behave — LLM Behavioral Analysis |
| cco | CCO — Concurrent Agent Orchestrator |
| cks | /cks - Constitutional Knowledge System |
| cognitive-stack | Note: /cognitive-frameworks is deprecated - all cognitive frameworks are now |
| concept-mapper | Concept Mapper |
| constitutional-patterns | Constitutional Patterns Skill |
| constraints | /constraints — Show Project Constraints |
| csaf | /csaf - Cognitive Systems Architect Framework |
| csda | CSDA - Code Structure-Documentation Architecture |
| csf-nip-dev | Purpose |
| csf-nip-integration | CSF NIP Integration Skill |
| cwo | /cwo — CWO 16-Step Unified Orchestration |
| decision-tree | Decision Tree - SDLC Engine |
| dne | DUF-NSE - Past → Future Analysis |
| doc-to-skill | Documentation to Skill Converter |
| dream | Dream — Memory Consolidation |
| evidence-applicability | Purpose |
| evolve | /evolve - Modernization Mission Control |
| execution-clarity | Purpose |
| flow | Flow Orchestration Command |
| friction | /friction — Interaction & Workflow Friction Detector |
| garden | /garden – Knowledge Hygiene |
| gto | GTO v3.1 - Strategic Next-Step Advisor |
| learn | `/learn` - Intelligent Lesson Capture |
| library-first | /library-first - Existing Solutions First |
| lmc | /lmc - Lossless Maximal Compaction |
| mlc | /mlc - Minimal Lossy Compaction |
| ocpa | OCPA - Optimal Completion Path Analysis |
| orchestrator | Master Skill Orchestrator |
| pace | /pace – Cognitive Load & WIP Tracking |
| pds | /pds - Smart Engineering Orchestrator (XoT Enhanced) |
| prompt_refiner | Prompt Refiner v14.0 |
| ralph | Ralph Loop |
| recap | /recap — Terminal-Wide Session Catch-Up |
| reflect | Reflect - Self-Improving Skills |
| response-atomicity | Purpose |
| retro | RETRO — SELF-CONTRAST Orchestrator |
| rns | RNS — Recommended Next Steps from Arbitrary Output |
| sequential-thinking | Sequential Thinking with Self-Reflection |
| similarity | /similarity - Find Similar Skills |
| skeptic | Note: Cognitive frameworks (Cynefin, Hanlon's Razor, Inversion, Chesterton's ... |
| slc | /slc - Solo Dev Compliance |
| solo-dev-authority | Solo Dev Authority |
| standards | CSF NIP Standards |
| subagent-driven-development | Subagent-Driven Development |
| think | /think |
| top-problems | Top Problems Analyzer (/top-problems) |
| tot | Tree-of-Thoughts Reasoning |
| trace | /trace - Manual Trace-Through Verification |
| truth | /truth - Truth Constitution Command |
| usm | Universal Skills Manager |
| why | /why — Decision Archaeology |

## Artifacts Convention

All runtime artifacts write to:



Skills MUST NOT write state to their own directory or to the package root.

## Scripts / Forked Tools

### skill-creator (subscription-first fork)

Fork of the `skill-creator` plugin with subscription-only API substitution.

**Location:** `scripts/skill_creator/`

**Why forked:** The original uses `anthropic.Anthropic()` for description improvement (separate API cost). This fork substitutes `claude -p` calls, routing through the Claude Code subscription.

**Key files:**
- `improve_description.py` — `claude_p()` substitution instead of `client.messages.create()`
- `sync_check.py` — auto-detects upstream plugin updates via SHA256[:12] hashes
- `run_loop.py` — full eval+improve loop calling `claude -p` throughout
- `run_eval.py` — trigger eval via `claude -p` (no API cost)

**Invocation:**
```bash
cd P:/packages/cc-skills-meta
python -m scripts.skill_creator.run_loop --eval-set <path> --skill-path <path> --model sonnet
python -m scripts.skill_creator.run_eval --eval-set <path> --skill-path <path>
```

**Version tracking:** On each run, `sync_check.py` compares hashes of tracked plugin scripts against `.fork_metadata.json`. If the plugin updates, it warns — run `python scripts/skill_creator/sync_check.py --check` to see what changed, then cherry-pick upstream changes.

**Tracked files (5):** `improve_description.py`, `run_loop.py`, `run_eval.py`, `utils.py`, `generate_report.py`

## Installation

Skills surfaced via junctions in .claude/skills/.
