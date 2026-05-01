---
name: reason
version: 2.0.0
status: stable
category: meta
enforcement: advisory
workflow_steps:
  - step_classify: Classify query type, confidence, epistemic state, missing capabilities
  - step_route: Emit routing decision (local_only / single_challenger / parallel_challengers / human_review)
  - step_internal: Internal Reflexion pass (Generate → Critique → Improve) with frame chaining
  - step_external: Dispatch to external roles (verify/redteam/alternative) if needed
  - step_messy: Force unresolved tensions + ambiguities before synthesis (required for low-confidence)
  - step_dedupe: Cluster outputs, anti-majoritarian weighting, preserve minority reports
  - step_synthesize: Final synthesis with decision theory, bias check, second-order effects
triggers:
  - /reason
  - /reason_ppx
  - /reason_grok
  - /reason_openai
  - /think
suggest:
  - /genius
  - /s
---

# /reason — Unified Reasoning Engine (v2.0)

One command that replaces `/think`, `/reason_ppx`, `/reason_grok`, `/reason_openai`, and `/reason_openai_v3.0`.
Intelligently blends internal Reflexion depth with external multi-LLM breadth. Routes by epistemic state, not task type.

**Core principle:** You invoke this when you need the strongest possible analysis — whether that's a quick critique, a deep dive, or external verification.
The engine decides *how deep to go*, not you.

---

## Routing: Epistemic State (Not Task Type)

Most systems route on: coding task, architecture task, debugging task. That is shallow.

**Your trigger is:**
- "My confidence is low."
- "Something feels off."
- "This answer seems too neat."
- "I don't trust this conclusion."
- Or simply: any question needing analysis.

**Route by epistemic state:**

| State | Signal | Route |
|-------|--------|-------|
| Clear + confident | confidence ≥ 0.85, no gaps | `local_only` → return immediately |
| Specific gap | freshness, citations, adversarial review | `single_challenger` → one external model |
| Complex + uncertain | multiple gaps, high stakes | `parallel_challengers` → asymmetric roles |
| Policy/PII risk | sensitive data, compliance | `human_review` → local only after redaction |

---

## The Pipeline

### Stage 1: THINK Prepares the Case
- Restate the problem as you understand it
- Name the type: review / design / diagnose / optimize / tradeoff / explore
- Define what "strong" means for this specific question
- List assumptions being made
- Identify what would change your mind

### Stage 2: Deficiency Diagnosis
Before calling any models, diagnose what's actually wrong:

| Issue | Diagnosis |
|-------|-----------|
| Correctness? | answer may be wrong |
| Completeness? | missing considerations |
| Creativity? | options too narrow |
| Tradeoffs? | costs/benefits unclear |
| Hidden risk? | failure modes unidentified |
| Wrong framing? | solving wrong problem |

### Stage 3: Internal Reflexion (Generate → Critique → Improve)
- **Generate**: Synthesize strongest consensus from all available sources. Treat the requested mechanism as a capability target — if the named path is unavailable, generate alternatives across: native/direct, workaround, and architecture-level redesign. Mark each alternative as robust, brittle, version-dependent, or speculative.
- **Critique**: Cross-model analysis + evidence labeling + gap detection + solo-dev tradeoff callout.
- **Improve**: Refined final answer with frame chaining only when it meaningfully changes the outcome.

Also runs:
- **Decision Theory Pass**: Score each candidate on expected upside, downside risk, reversibility, time to feedback, energy cost, dependency load, compounding potential, robustness.
- **Bias Check**: Detect sunk cost, status quo bias, loss aversion, overconfidence, confirmation bias, novelty bias, analysis paralysis, emotional relief disguised as logic.
- **Second-Order Effects**: Ask — if this wins, what burden appears? If it fails, what cascades?

### Stage 4: External Dispatch (when routing decides)
Assign models to **cognitive roles**, not task categories. Any model can play any role.

| Role | What It Does | Typical Provider |
|------|--------------|-----------------|
| Reductionist | Simplify to essentials | (internal) |
| Verifier | Test claims for support/weakness | gemini |
| Red Team | Attack assumptions, find flaws | pi_m27 / minimax |
| Alternative | Propose materially different solution | codex |
| Historian | What similar cases teach | glm |
| Optimizer | Maximize objective function | (any) |
| Skeptic | Why this fails in reality | (any) |

**Sharp role differentiation beats same-prompt parallelism.** Don't ask all models the same question.

### Stage 5: Messy Phase (Required for low-confidence)
Before final synthesis, force all models to produce:
- Unresolved tensions
- Ambiguities
- Missing data
- Reasons all current options may fail
- What cannot yet be known

**Do not finalize before passing through productive mess.** Polished structure creates false confidence.

### Stage 6: Dedupe + Conflict Analysis
Cluster outputs into:
- Repeated points (higher weight as confirmation)
- Unique points (highest value — the one thing one model noticed)
- Contradictions
- Evidence-backed claims
- Speculative claims

**Anti-majoritarian rule:** Weight novelty and evidence, not vote count. A point found by one model that identifies a hidden failure mode outranks a point repeated by all five models that is shallow.

**Preserve minority reports explicitly.** The thing you most often need is the one thing one model noticed that everyone else missed.

### Stage 7: Final Synthesis
Final answer must include:
- Consensus findings
- High-value minority findings
- Unresolved disputes
- Best recommendation with why it wins
- Regret analysis: If wrong, what likely caused it? What did we trade away?
- Earliest warning sign we chose poorly
- Cheap pivot if mistaken
- What discriminating test would most reduce remaining uncertainty

---

## Mode Flags (override routing)

| Flag | Behavior |
|------|------------|
| `--mode review` | Attack weak logic, hidden fragility, omitted costs |
| `--mode design` | Compare architectures: simplicity, failure containment, migration burden |
| `--mode diagnose` | Ranked hypotheses, smallest discriminating test |
| `--mode optimize` | Clarify objective first, ask whether redesign beats tuning |
| `--mode decide` | Regret minimization + optionality + expected value |
| `--mode explore` | Challenge frame itself, what adjacent problem matters more |
| `--mode off` | Treat discomfort as signal, find hidden mismatch |
| `--mode execute` | Produce momentum now, not just ideas |

## Decision Flags (when query is a decision)

| Flag | Behavior |
|------|------------|
| `--force-choice` | Pick one option, state why it wins, state reversal trigger. No timid both-sidesing. |
| `--kill` | Explicit Keep/Delegate/Defer/Kill pruning. Aggressive reduction. |
| `--invert` | Analyze failure paths: how it fails, earliest warning sign, preventive move. |
| `--ship` | Add execution checklist: next 15min action, next 60min push, first milestone, blocker, kill criteria. |

## Depth Flags

| Flag | Behavior |
|------|------------|
| `--no-external` | Pure internal Reflexion (fastest) |
| `--debate-rounds N` | Force N rounds of external critique |
| `--framework [reflexion\|tot\|ooda\|feynman\|devil]` | Force a specific mental model |
| `--depth [auto\|deep\|board\|maximal]` | Override depth (default: auto) |
| `--brief` | Shorter output |
| `--full` | Full output with tradeoffs |

## External Provider Flags

| Flag | Behavior |
|------|------------|
| `--gemini-only` / `--pi-m27-only` / `--codex-only` | Restrict external models |
| `--local-only` | Skip external LLMs, use local agents only |
| `--context PATH` | Explicit files/directories (auto-detected otherwise) |
| `--output [compact\|verbose\|json]` | Output format |

---

## Quick (think replacement)

For trivial or purely informational queries:
1. Confirm the model is correct
2. Give the direct answer
3. Surface one thing you probably haven't considered

*This is what `/think` did — now it's the default fast path for `/reason`.*

---

## Standard (most prompts)

1. Map the problem first (if query is ambiguous)
2. Challenge the most critical premise
3. Give a strong recommendation
4. Surface one unexpected angle
5. State your thinnest confidence and what would change it

---

## Deep (ambiguous, high-stakes, cross-cutting)

1. Map with full model visibility
2. Challenge all major premises
3. Generate 3 genuinely different frames (not wording variants)
4. Give a clear recommendation with the strongest counterargument
5. Cross-domain synthesis for each frame
6. State the falsification condition explicitly

---

## Evidence Labels

Every material claim is labeled:
- **VERIFIED** — supported by file, command, test, or source
- **INFERRED** — logical from verified facts, one step removed
- **UNPROVEN** — hypothesis, analogy, or guess
- **MY BET** — when acting on thin evidence but have a strong opinion

---

## Output Contracts

### Compact (default)

```
RECOMMENDATION
• [Core answer with tradeoffs]

EVIDENCE LABELS
• Verified: ...
• Inferred: ...
• Unproven: ...

ROUTING
• route: single_challenger
• missing: freshness, citations
• confidence: 0.82

TRADEOFFS & SOLO-DEV NOTES
• ...

SOURCES / CITATIONS
• file:line or model:provider
```

### JSON (`--output json`)

```json
{
  "local_answer": "...",
  "confidence": 0.82,
  "task_type": "research",
  "missing_capabilities": ["freshness", "citations"],
  "data_class": "local_ok",
  "recommended_route": "single_challenger",
  "claims": [
    {"id": "C1", "text": "...", "status": "VERIFIED", "evidence": ["..."]},
    {"id": "C2", "text": "...", "status": "INFERRED", "evidence": []}
  ],
  "final_answer": "...",
  "confidence_summary": "...",
  "minority_report": "...",
  "regret_analysis": "...",
  "next_discriminating_test": "...",
  "sources": ["file:line", "gemini", "pi_m27"]
}
```

---

## Persistent Weakness Profile (auto-compensation)

**Your known tendencies:**
- Overvalues elegance over operational reality
- Underweights maintenance cost
- Optimizes too early before options are explored
- Trusts architecture over implementation evidence
- Too many options causes paralysis
- Prefers reversible decisions (sometimes to a fault)

**How the orchestrator compensates:**

| Your Tendency | Orchestrator Response |
|---------------|---------------------|
| Overvalues elegance | Force realist critic + ops cost challenge |
| Underweights maintenance | Add implementation realist pass first |
| Optimizes too early | Force exploration phase before reduction |
| Trusts architecture | Add code-path evidence requirement |
| Options paralysis | Kill mode: aggressive pruning to top 2 |
| Prefers reversible | Challenge: what does irreversibility buy us? |

---

## Information Gain as Objective

Don't ask "what answer is best?" Ask "what next step most reduces uncertainty?"

Great orchestration often concludes: **"Stop thinking. Run this discriminating test."** That is intelligence.

---

## Time-Separated Reasoning (optional)

Instead of one swarm, run two passes:

**Pass 1:** Fast instinctive responses
**Pass 2:** After first synthesis, re-ask without showing previous outputs
**Pass 3:** Critique differences between Pass 1 and Pass 2

Fresh generations often catch what first-pass consensus missed. This mimics "sleeping on it."

---

## Counterfactual Mode

Ask models:
- If the opposite were true, how would we know?
- If this project fails in 6 months, what caused it?
- If a competitor solved this better, what did they do differently?
- If constraints disappeared, what would we redesign?

This surfaces hidden assumptions faster than ordinary review.

---

## Privacy-Aware Routing

Before any external call, detect data class from query content:

| Data Class | Policy | Example |
|------------|--------|---------|
| `local_ok` | external calls permitted | general questions, code, architecture |
| `redact_then_remote` | extract claims only, then optionally escalate | policy, compliance, legal text |
| `remote_only` | external ok without restriction | public data only |

Sensitive keywords trigger local-only routing: secret, api_key, password, token, credential, pii, personal, confidential, contract, ssn, credit card.
Policy keywords trigger redaction-first: policy, compliance, gdpr, hipaa, regulate, security.

---

## Failure Resilience

- Gemini Windows crash → auto-drop + compensate with remaining models + deeper internal critique
- Conceptual query ambiguity → forces BRAINSTORM + Reflexion
- Extensionless directories → smart context extraction + evidence-audit fallback
- Rate limits / empty outputs → retry logic + partial compensation + clear [EMPTY] / [RATE_LIMIT] flags
- Task classifier ties → overridden by complexity assessment
- Privacy-sensitive content → routes to local_only automatically
- Slow providers → quorum with soft deadline stops waiting once min_success is met
- Prompt injection in retrieved docs → untrusted outputs isolated from model inputs

---

## What /reason Is NOT

- Not a fast assistant for trivial questions (use `/genius` for thought partnership)
- Not a multi-LLM router (routing is a byproduct, not the goal)
- Not a committee (committees average — this prices disagreement)
- Not a brainstorming engine (use `/s` for multi-persona option generation)

## What /reason IS

A Decision Quality Engine for moments of uncertainty. Optimizes for:
- Clarity
- Option quality
- Uncertainty reduction
- Minority insight preservation
- Decisions robust to error

---

## Supported Mental Models (auto-selected or forced)

| Model | When |
|-------|------|
| Reflexion (default) | Generate → Critique → Improve |
| Tree of Thoughts (ToT) | Parallel branching frames + pruning |
| ReAct | Reason + Act (calls external CLIs as tools) |
| OODA Loop | Observe → Orient → Decide → Act |
| Feynman Technique | "Explain like I'm a junior dev" |
| Devil's Advocate + Pre-Mortem | Adversarial review |

Use `--framework` to override.

---

## Best Test Prompts

```
/reason this solution feels too neat
/reason I'm stuck between three approaches
/reason --mode decide --force-choice postgres vs clickhouse
/reason --mode diagnose what bottleneck is causing this latency
/reason this architecture — what am I not considering
/reason --no-external quick factual question
```

---

## Migration

This skill replaces:
- `/think` (now the Quick depth tier)
- `/reason_ppx` (Python backend merged in)
- `/reason_grok` (unified hybrid engine — now the base)
- `/reason_openai` (6-stage pipeline — now the full pipeline)
- `/reason_openai_v3.0` (elite decision command — now mode flags)

**All old trigger names still work** — they map to `/reason` via the `triggers` frontmatter.
