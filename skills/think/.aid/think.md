# /think — distilled (SKILL.md only)

## Core Loop
1. Strong first answer
2. Critique: missing options, weak assumptions, contradictions, overconfidence
3. One refinement
4. Stop — unless a discriminating check remains

## Open-Ended: 3 Branches First
1. **Creative** — most novel/leverage-rich idea
2. **Skeptical** — strongest objection, failure mode, premise challenge
3. **Pragmatic** — boring option that still works
→ Compare, then choose. Re-rank if challenger surfaces better alternative.

## Frame Chain (pick minimum; don't chain for style)
- Decision matrix → Pre-mortem → Inversion (option selection)
- Tree search → Causal graph → Bayesian update (uncertain systems)
- First principles → Systems thinking → Pragmatic (design)
- Challenger debate → Root-cause → Verification handoff (risky claims)

| Situation | Frame |
|---|---|
| Comparing options | Decision matrix |
| Unknown branches | Tree search |
| Dependencies/side effects | Causal graph |
| Risk/rollback/failure | Pre-mortem |
| Adversarial pressure | Challenger debate |
| Breaking to fundamentals | First principles |
| Flipping for failure | Inversion |
| Belief update from evidence | Bayesian update |
| Feedback loops/emergence | Systems thinking |
| Simple vs complex vs chaotic | Cynefin |
| Causes and counterfactuals | Causal trace |
| Primary defect/bottleneck | Root-cause analysis |

## Depth Ladder
1. `/truth` — evidence, existence, behavior, "what actually happened"
2. Evidence-audit — challenge/cross-check before trusting
3. `/decision-tree` — options, lifecycle, state transitions, phases, SDLC
4. `/sequential-thinking` — multiple hypotheses, RCA, uncertainty reduction
5. `/think` — concise recommendation when framework dump is overkill

## Evidence-Audit Mode
- Verify repo state before stating claims
- Prefer actual evidence over confidence language
- Label: **Verified** | **Inferred** | **Unproven**
- Validation order: verified → inferred → unproven → next check

## Decision-Tree Mode (5 dimensions)
1. Name decision + concrete options
2. Map state transition per option
3. Lifecycle impact: persistent/ephemeral/mixed
4. Phases: before/during/after/never
5. Purpose + constraints → recommend

Branch selection order:
1. Incident/Bug/Regression — broken, flaky, intermittent, failing, regressing
2. Ops/Release Risk — deploy, rollback, hotfix, cutover, validation
3. Refactor/Migration — structure changes, API moves, dependency upgrades
4. Architecture/Lifecycle — boundaries, ownership, state, timing, persistence
5. Feature/Design — building/choosing/shaping new capability

Score: blast radius, reversibility, compatibility risk, lifecycle impact, uncertainty, effort

## External Challenger (SDLC_MULTI_LLM=1 → /ai-cli)
Prefer: `/codex` (code/repo), `/ai-gemini` (broad framing), `/ai-qwen` (fresh ranking)

4-element challenger prompt:
1. State leading answer
2. State main assumption
3. Break it / propose stronger alternative
4. Short ranked comparison — not freeform

## Output Contract
1. Problem in one sentence
2. Chosen depth tier
3. Best recommendation
4. Top tradeoffs/risks
5. Evidence/verification step that would change answer
6. Rollback/reversibility note when relevant

## Open-Ended Structure
1. Best answer
2. Strongest alternative + why it loses
3. One premise/assumption worth challenging
4. What evidence/constraint would change recommendation

## Operating Rules
- Do NOT print internal scaffold
- Do NOT cap depth on ambiguous/risky/cross-cutting prompts
- Do NOT skip challenging the first answer
- Be decisive when evidence is sufficient
- Prefer verification over speculation when a concrete check exists
- For creative prompts: include ≥1 non-obvious + ≥1 premise-challenging option
- If another option is materially stronger, re-rank before answering
- If challenger would improve answer, recommend proactively
- `/truth-av` deprecated — behavior now in `/think` evidence-audit mode
