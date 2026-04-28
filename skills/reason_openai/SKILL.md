---
name: reason_openai
description: Decision Quality Engine — cognitive amplification for moments when your thinking detects weakness.
version: "5.1.0"
status: stable
category: meta
enforcement: advisory
triggers:
  - /reason_openai
workflow_steps:
  - id: stage1_prepare
    description: "THINK prepares the case — restate problem, name type, define 'strong', list assumptions"
  - id: stage2_diagnose
    description: "Deficiency diagnosis — correctness, completeness, creativity, tradeoffs, risk, framing"
  - id: stage3_models
    description: "Role-based model assignment — cognitive roles, not brand names; sharp differentiation"
  - id: stage4_messy
    description: "Messy phase — unresolved tensions, ambiguities, what cannot be known (required)"
  - id: stage5_dedupe
    description: "Dedupe + conflict analysis — anti-majoritarian weighting, preserve minority reports"
  - id: stage6_synthesize
    description: "Final synthesis with regret analysis, warning signs, and discriminating test"
allowed-tools: Bash(pwd:*), Bash(ls:*), Bash(find:*), Bash(git:*), Bash(cat:*), Bash(head:*), Bash(sed:*), Bash(test:*), Bash(grep:*)
---

# /reason_openai — Decision Quality Engine

Triggered when your thinking detects weakness. Not a routing system. A cognitive amplification system.

**Core purpose:** You invoke this when something feels off, when an answer seems too neat, when confidence is low, when you're stuck, or when you need the strongest possible analysis.

**This is not a fast assistant.** This is your second brain for high-stakes moments.

---

## Core Insight: Route on Epistemic State, Not Task Type

Most systems route based on: coding task, architecture task, debugging task. That is shallow.

Your trigger is:
- "My confidence is low."
- "Something feels off."
- "This answer seems too neat."
- "I don't trust this conclusion."

**Route by epistemic state:**
- confusion high → exploration swarm
- answer feels brittle → adversarial review
- too many options → reduction engine
- high stakes + uncertainty → full tribunal
- intuition conflict → counterfactual mode

---

## The 6-Stage Pipeline

Each invocation runs through:

### Stage 1: THINK Prepares the Case
- Restate the problem as you understand it
- Name the type: review / design / diagnose / optimize / tradeoff / explore
- Define what "strong" means for this specific question
- List assumptions being made
- Identify what would change your mind

### Stage 2: Deficiency Diagnosis
Before calling any models, diagnose what's actually wrong:

Is the issue:
- **Correctness?** — answer may be wrong
- **Completeness?** — missing considerations
- **Creativity?** — options too narrow
- **Tradeoffs?** — costs/benefits unclear
- **Hidden risk?** — failure modes unidentified
- **Wrong framing?** — solving wrong problem

Route to the appropriate mode based on this diagnosis. This step prevents premature convergence.

### Stage 3: Model Assignment (Role-Based, Not Brand-Based)

Assign models to **cognitive roles**, not task categories. Any model can play any role. Rotate based on what the moment needs.

| Role | What It Does |
|------|--------------|
| Reductionist | Simplify to essentials |
| Adversary | Attack assumptions |
| Historian | What similar cases teach |
| Optimizer | Maximize objective function |
| Skeptic | Why this fails in reality |
| Inventor | Non-obvious alternatives |
| Integrator | Merge competing tensions |
| Constraint Lawyer | What was ignored |

**Sharp role differentiation beats same-prompt parallelism.** Don't ask all models the same question. Ask each model a role-specific question:

- Codex: "What breaks in implementation?"
- Gemini: "What architectural assumptions are weak?"
- GLM: "What practical issues or alternatives are missing?"
- Minimax: "Give fast adversarial challenges or unconventional options."

### Stage 4: Messy Phase (Required)

Before final synthesis, force all models to produce:
- Unresolved tensions
- Ambiguities
- Missing data
- Reasons all current options may fail
- What cannot yet be known

**Do not finalize before passing through productive mess.** Polished structure creates false confidence. This single step improves more than any model choice.

### Stage 5: Dedupe + Conflict Analysis

Cluster outputs into:
- Repeated points (higher weight as confirmation)
- Unique points (highest value — the one thing one model noticed)
- Contradictions
- Evidence-backed claims
- Speculative claims

**Anti-majoritarian rule:** Weight novelty and evidence, not vote count. A point found by one model that identifies a hidden failure mode outranks a point repeated by all five models that is shallow.

**Preserve minority reports explicitly.** The thing you most often need is the one thing one model noticed that everyone else missed.

### Stage 6: Final Synthesis

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

## Mode-Specific Pipelines

### Explore Mode (stuck / no good options / need alternatives)
Run full swarm. Output 10-20 distinct approaches, surprising reframes, top 3 worth testing.

### Critique Mode (solution exists, needs stronger review)
Targeted adversarial pass. Output: strongest objections, hidden risks, verdict.

### Decide Mode (options exist, need recommendation)
Multi-model with decision-editor. Output: top 2-3 options, why weaker ones lose, recommended path.

### Diagnose Mode (root cause / bottleneck / performance)
Hypothesis tree + ranked possibilities + discriminating test.

### Optimize Mode (objective unclear or options mediocre)
Define objective function first. Then test against it ruthlessly.

---

## Escalation Tiers

### Low (confidence is low but stakes are normal)
THINK + one model + synthesis

### Medium (answer feels brittle or options are close)
THINK + two models (complementary roles) + synthesis

### High (high stakes + real uncertainty)
THINK + full swarm + messy phase + dedupe + critic + synthesis

### Critical (irreversible decision / prior answer disappointed you)
THINK → Codex + Gemini + GLM + Messy Phase → Critic → Full Synthesis

---

## Persistent Weakness Profile

Track reasoning tendencies to personalize and compensate:

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

This memory lives in your `MEMORY.md` and updates after each calibration cycle.

---

## Confidence Token System (Optional Deep Mode)

For hard decisions, have each model allocate confidence tokens across hypotheses:

```
Hypothesis A = 55
Hypothesis B = 20
Hypothesis C = 15
Hypothesis D = 10
```

Then ask critics to challenge overpriced hypotheses. This reveals confidence structure better than textual summaries.

---

## Time-Separated Reasoning (Optional)

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

## Information Gain as Objective

Don't ask "what answer is best?" Ask "what next step most reduces uncertainty?"

Great orchestration often concludes: **"Stop thinking. Run this discriminating test."** That is intelligence.

---

## Output Contract

Every output must include:

```
WHAT WAS WRONG WITH THE PRIOR ANSWER
[What deficiency triggered this invocation]

THINK PREPARATION
Problem restated (in your own words, not the user's phrasing):
Assumptions:
What would change my mind:

DEFICIENCY DIAGNOSIS
Type:
Why this matters:

MODEL CONTRIBUTIONS
[Role-specific findings, not model names]

MESSY PHASE
[Unresolved tensions, ambiguities, what cannot be known]

DEDUPE + CONFLICT
[What repeated, what unique, what contradicts]

MINORITY REPORT
[Low-consensus high-value finding — preserve explicitly]

RECOMMENDATION
Best call:
Why it wins:
Why it might be wrong:
What we traded away:

REGRET ANALYSIS
If wrong, what likely caused it:
Earliest warning sign:
Cheap pivot if mistaken:

NEXT DISCRIMINATING TEST
[What would most reduce remaining uncertainty]
```

---

## Evidence Labels

See `/genius`'s **Evidence Labels** section for the canonical definition.

---

## What This Skill Is NOT

- Not a fast assistant for trivial questions
- Not a multi-LLM router (routing is a byproduct, not the goal)
- Not a committee (committees average — this prices disagreement)

**Capability-target discipline:** When you ask for a specific mechanism (e.g., "use MCP", "use A2A"), treat that as the *means*, not the *goal*. See `/think`'s **Capability Target Principle** for the full evaluation ladder.

Never reply with "no, you can't do that" when a capability-preserving alternative exists.

## What This Skill IS

A Decision Quality Engine for moments of uncertainty. Optimizes for:
- clarity
- option quality
- uncertainty reduction
- minority insight preservation
- decisions robust to error

---

## Best Test Prompts

```
/reason_openai this solution feels too neat
/reason_openai I'm stuck between three approaches
/reason_openai --mode decide --force-choice postgres vs clickhouse
/reason_openai --mode diagnose what bottleneck is causing this latency
/reason_openai this architecture — what am I not considering
```
