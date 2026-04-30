# cc-skills-meta

Meta-cognitive and workflow skills for Claude Code — retrospectives, gap analysis, learning, self-improvement, and orchestration.

## Skills (52)

| Skill | Purpose |
|-------|---------|
| behave | /behave — LLM Behavioral Analysis |
| cco | CCO — Concurrent Agent Orchestrator |
| cks | /cks - Constitutional Knowledge System |
| cognitive-stack | Cognitive frameworks (Cynefin, Hanlon's Razor, Inversion, Chesterton's Fence) |
| concept-mapper | Concept Mapper |
| constitutional-patterns | Constitutional Patterns Skill |
| constraints | /constraints — Show Project Constraints |
| csaf | /csaf - Cognitive Systems Architect Framework |
| csda | CSDA - Code Structure-Documentation Architecture |
| csf-nip-dev | CSF NIP Development |
| csf-nip-integration | CSF NIP Integration Skill |
| cwo | /cwo — CWO 16-Step Unified Orchestration |
| decision-tree | Decision Tree - SDLC Engine |
| dne | DUF-NSE - Past to Future Analysis |
| doc-to-skill | Documentation to Skill Converter |
| dream | Dream — Memory Consolidation |
| evidence-applicability | Evidence applicability analysis |
| evolve | /evolve - Modernization Mission Control |
| execution-clarity | Execution clarity analysis |
| flow | Flow Orchestration Command |
| friction | /friction — Interaction and Workflow Friction Detector |
| garden | /garden — Knowledge Hygiene |
| gto | GTO v4.1 — Session-aware gap-to-opportunity analysis with RNS-compatible output |
| learn | /learn — Intelligent Lesson Capture |
| library-first | /library-first — Existing Solutions First |
| lmc | /lmc — Lossless Maximal Compaction |
| mlc | /mlc — Minimal Lossy Compaction |
| ocpa | OCPA - Optimal Completion Path Analysis |
| orchestrator | Master Skill Orchestrator |
| pace | /pace — Cognitive Load and WIP Tracking |
| pds | /pds — Smart Engineering Orchestrator (XoT Enhanced) |
| prompt_refiner | Prompt Refiner v14.0 |
| ralph | Ralph Loop |
| recap | /recap — Terminal-Wide Session Catch-Up |
| reflect | Reflect — Self-Improving Skills |
| response-atomicity | Response atomicity analysis |
| retro | RETRO — SELF-CONTRAST Orchestrator |
| rns | RNS — Recommended Next Steps from Arbitrary Output |
| sequential-thinking | Sequential Thinking with Self-Reflection |
| similarity | /similarity — Find Similar Skills |
| skeptic | Cognitive frameworks (Cynefin, Hanlon's Razor, Inversion, Chesterton's Fence) |
| slc | /slc — Solo Dev Compliance |
| solo-dev-authority | Solo Dev Authority |
| standards | CSF NIP Standards |
| subagent-driven-development | Subagent-Driven Development |
| think | /think |
| top-problems | Top Problems Analyzer (/top-problems) |
| tot | Tree-of-Thoughts Reasoning |
| trace | /trace — Manual Trace-Through Verification |
| truth | /truth — Truth Constitution Command |
| usm | Universal Skills Manager |
| why | /why — Decision Archaeology |

## Installation

Skills are surfaced via junctions in `.claude/skills/`.

```bash
# As a Claude Code plugin
/plugin install cc-skills-meta
```

## Artifacts Convention

All runtime artifacts write to:

```
.claude/.artifacts/{terminal_id}/{skill_name}/
```

Skills must not write state to their own directory or to the package root.
