---
name: think
description: Adaptive reasoning gate for SDLC work - choose depth, chain frames, and verify before settling
version: "3.0.0"
status: stable
category: meta
enforcement: advisory
triggers:
  - /think
aliases:
  - /think
suggest:
  - /reason_openai
  - /genius
  - /truth
  - /decision-tree
  - /sequential-thinking
workflow_steps:
  - id: infer_subject
    description: "Infer the actual subject from prompt and conversation context"
  - id: choose_depth
    description: "Select reasoning depth appropriate to risk and uncertainty"
  - id: apply_frames
    description: "Chain reasoning frames as warranted"
  - id: verify
    description: "Verify claims before settling"
---

# /think

Use `/think` when a prompt needs better judgment, not more output.

## Core Goal

Pick the reasoning depth that best fits the risk, uncertainty, and blast radius of the problem, then return a distilled recommendation.

## Context Resolution

Treat `/think` as the reasoning mechanism, not the subject of the request.

- Infer the topic from the user's actual prompt and the surrounding conversation.
- Do not let the command name override the semantic subject the user is asking about.
- If the prompt mentions `/think` while discussing something else, analyze the something else.
- Ask a clarifying question only if multiple plausible subjects remain after using the conversation context.
- Prefer the user's intended object of analysis over any meta-reference to the tool itself.

## Reasoning Depth

If you invoke `/think`, use the full reasoning depth the problem warrants.

- Do not artificially cap analysis when the prompt is broad, ambiguous, high-stakes, or cross-cutting.
- Do not stop at the first adequate answer when a stronger critique, check, or frame chain would improve it.
- Stay concise only when the task is trivial, purely informational, or explicitly asks for a brief answer.

## Reasoning Loop

Borrow the useful part of `/sequential-thinking` without exposing the draft process to the user:

1. Generate a strong first answer.
2. Critique it for missing options, weak assumptions, contradictions, and overconfidence.
3. Refine it once using the critique.
4. Stop after one refinement unless a clearly better discriminating check exists.

Use this loop internally on broad, ambiguous, creative, or high-stakes prompts. Keep the final answer compact, but do not sacrifice option coverage.

## Open-Ended Prompt Pattern

When the prompt is open-ended, design work, or strategy-heavy, force three distinct branches before recommending:

1. Creative branch: the most novel or leverage-rich idea.
2. Skeptical branch: the strongest objection, failure mode, or premise challenge.
3. Pragmatic branch: the most boring option that would still work.

Then compare the branches and choose one. If a branch is only a wording variant, it does not count.

If the answer is still shaky after the first comparison, chain a second frame:

1. Decision matrix for tradeoffs.
2. Pre-mortem for failure modes.
3. Inversion for paths to failure.
4. Bayesian update for what the evidence actually changed.

Use the minimum chain that improves the answer. Do not add frames for style.

## Depth Ladder

Choose the depth that matches the problem, and escalate if the first pass still leaves meaningful uncertainty:

1. `/truth` if the question is about evidence, existence, behavior, implementation status, or "what actually happened."
2. Evidence-audit mode if you want the answer challenged, cross-checked, or auto-verified before it is trusted. This subsumes the old `/truth-av` behavior.
3. `/decision-tree` if the question is about options, lifecycle, state transitions, phases, or resource management. Use the SDLC branch, scoring axes, and matching branch template below.
4. `/sequential-thinking` if the question needs multiple hypotheses, root-cause analysis, or uncertainty reduction. Use investigation mode to state the primary hypothesis, test it, and keep only the minimum alternatives needed to falsify it.
5. `/think` if the prompt is straightforward enough that a concise recommendation is better than a framework dump.

If the prompt is broad, ambiguous, high-stakes, or cross-cutting, prefer deeper analysis over the first adequate tier.

The hook-level `tradeoff_decision` profile is only a lightweight precheck. Use the full `/decision-tree` mode when the decision needs the 5-dimensional scaffold.

## Evidence-Audit Mode

Use evidence-audit mode when the user wants verification, skepticism, or a direct assessment backed by proof.

- The hook stack may auto-route verification-heavy prompts here when they contain cues like verify, prove, validate, or fact-check.

- Treat claims as hypotheses until the relevant files, commands, or tests have been checked.
- Prefer actual evidence over confidence language.
- For advisory questions, answer directly with tradeoffs and sources instead of deferring back to the user.
- Cite the proof, not the vibe.
- If a claim depends on repo state, runtime behavior, or a missing file, verify it before stating it.

## Claim Status

When the answer includes ideas that are not yet verified, label them explicitly instead of blending them into the recommendation.

- `Verified`: supported by direct evidence, file inspection, command output, tests, or source material.
- `Inferred`: a reasonable conclusion drawn from verified evidence, but still a step removed from direct proof.
- `Unproven`: a hypothesis, guess, or idea that has not been validated yet.

If a material idea is unproven and there is a practical way to check it, call out the investigation step instead of presenting it as settled.

## Validation Response Shape

When the answer depends on ideas that are not fully verified, use this order:

1. Verified facts.
2. Inferred ideas.
3. Unproven ideas or hypotheses.
4. Next validation step.

Keep the list short, but do not merge these categories together. If a category is empty, omit it.

## Verification Handoff

When the answer depends on code, repo state, runtime behavior, or test results, do not settle the issue from reasoning alone if a concrete check is available.

Use a challenger to verify the smallest discriminating test:

1. `/codex` for code, repo behavior, implementation detail, debugging, refactors, and architecture.
2. `/ai-gemini` for broad framing, long-context critique, and creative alternatives.
3. `/ai-qwen` for model diversity or a fresh ranking when the branches are still close.

Ask the challenger to do four things:

1. State the current leading answer.
2. State the assumption that could break it.
3. Identify the smallest check, command, or file read that could falsify it.
4. Return a short ranked comparison, not a freeform brainstorm.

## Investigation Mode

Use investigation mode when the prompt is ambiguous, contradictory, a regression, a missing-behavior claim, a performance complaint, or a "what's wrong" diagnosis.

- State the most likely explanation first.
- Name only the minimum alternative explanations needed to test the primary one.
- Choose the smallest discriminating test or search path that could falsify the top hypothesis.
- Stay provisional until the test resolves the uncertainty.
- Do not turn uncertainty into a flat list of equally plausible theories.
- If the idea is not verified, suggest the most useful search, research, or broader discovery path before treating it as a recommendation.
- If `/search`, `/research`, or `/all` would materially improve confidence, use them or recommend them rather than guessing.

## Decision-Tree Mode

Use this when the problem has real options, state changes, timing, or lifecycle impact.

### Automatic Branch Selection

Pick the first matching branch in this order:

1. Incident / Bug / Regression if something is broken, flaky, intermittent, failing, or regressing.
2. Ops / Release Risk if the question is about deploy, rollback, hotfix, cutover, validation, or production safety.
3. Refactor / Migration if the work changes structure, moves APIs, extracts modules, or upgrades dependencies.
4. Architecture / Lifecycle if boundaries, ownership, state, timing, or persistence are the main concern.
5. Feature / Design if the question is primarily about building, choosing, or shaping a new capability.

If multiple branches match, keep the highest-risk operational branch and treat the others as secondary checks.

Apply the full 5-dimensional scaffold in order:

1. Name the decision and the concrete options.
2. Map the state transition for each option.
3. Analyze lifecycle impact: persistent, ephemeral, or mixed.
4. Check the phases that matter: before, during, after, or never.
5. Clarify the purpose and constraints, then recommend one path.

When the decision is SDLC-specific, narrow into the decision-tree branches:

- incident / bug / regression
- feature / design
- refactor / migration
- architecture / lifecycle
- ops / release risk

Score each option on blast radius, reversibility, compatibility risk, lifecycle impact, uncertainty, and effort before recommending.
Use the branch template that matches the problem. Do not force a generic template when the branch has a better one.
State the selected branch explicitly and explain the cue that selected it.

If evidence is also uncertain, verify the facts first, then apply the decision tree.

## Output Contract

Return:

1. The problem in one sentence.
2. The chosen depth tier.
3. The best recommendation.
4. The top tradeoffs or risks.
5. The evidence or verification step that would change the answer. In evidence-audit mode, include the verdict and proof for each material claim.
6. A rollback or reversibility note when relevant.

## Standard Response Shape

For open-ended or strategy-heavy prompts, use this structure:

1. Restate the real capability target in one sentence.
2. Evaluate the direct path.
3. Best answer.
4. Strongest alternative and why it loses.
5. One premise or assumption worth challenging.
6. What evidence or constraint would change the recommendation.

For requests with a named mechanism: start by confirming the capability target, then evaluate the direct path before presenting alternatives. See **Capability Target Principle** for the full evaluation ladder.

Rerun the branch comparison internally before finalizing the answer. Do not wait for user pushback to reassess whether another branch is stronger.

## External Challenger Policy

If the internal critique still leaves meaningful uncertainty, the task is high-stakes, or the tradeoff surface is large, suggest an external challenger agent before finalizing the answer.

Use this escalation when:

1. Two or more branches are still close after internal reranking.
2. A wrong answer would be costly, hard to roll back, or sticky.
3. The problem is creative, strategic, or architecture-heavy enough that a second viewpoint is likely to surface a better option.

Prefer the challenger by domain:

1. `/codex` for code, repo behavior, implementation detail, debugging, refactors, and architecture.
2. `/ai-gemini` for broad framing, long-context critique, and creative alternatives.
3. `/ai-qwen` for a different second opinion when you want model diversity or a fresh ranking.

When proposing a challenger, ask a focused attack question:

1. State the current leading answer.
2. State the main assumption it depends on.
3. Ask the challenger to break it, propose a stronger alternative, or identify a falsifying condition.
4. Ask for a short ranked comparison, not a freeform brainstorm.

## External Challenger Dispatch

When the escalation criteria in the External Challenger Policy are met AND `SDLC_MULTI_LLM` is set to `"1"`, dispatch an external challenger via `/ai-cli`:

```bash
python -c "import os; print(os.environ.get('SDLC_MULTI_LLM', '0'))"
```

If `"1"`, run:

```bash
python "P:/packages/cc-skills-ai-cli/skills/ai-cli/ai_cli.py" "<CHALLENGER_PROMPT>" --context "<relevant_file_if_any>" --<provider>-only --output-format json --no-critic --timeout 120
```

Where:
- `<CHALLENGER_PROMPT>` follows the 4-element structure: (1) state leading answer, (2) state main assumption, (3) ask challenger to break it or propose stronger alternative, (4) ask for short ranked comparison.
- Provider selection:
  - `--codex-only` for code, repo behavior, implementation detail
  - `--gemini-only` for broad framing, long-context critique, creative alternatives
  - `--qwen-only` for model diversity or fresh ranking

After receiving the external challenger response, incorporate it into the Output Contract item 5 ("evidence or verification step that would change the answer"). If the challenger surfaced a stronger alternative, re-rank before finalizing.

**Fallback:** If the external dispatch fails, note in the output: "External challenger unavailable; internal review only."

## Reasoning Frames

Pick the frame that matches the shape of the problem instead of using one generic pattern for everything:

| Situation | Frame |
| --- | --- |
| Comparing options with tradeoffs | Decision matrix |
| Exploring unknown branches | Tree search |
| Understanding dependencies or side effects | Causal graph |
| Managing risk, rollback, or failure modes | Pre-mortem |
| Need adversarial pressure-testing | Challenger debate |
| Breaking a problem into fundamentals | First principles |
| Flipping a plan to look for failure | Inversion |
| Updating a belief from evidence | Bayesian update |
| Looking for feedback loops or emergence | Systems thinking |
| Sorting simple vs complex vs chaotic | Cynefin |
| Examining causes and counterfactuals | Causal trace |
| Isolating the primary defect or bottleneck | Root-cause analysis |

If more than one frame fits, combine the minimum number needed to improve the answer. Do not add frames just for style.

For creative prompts, first branch, then recombine the strongest pieces after pruning weak ones.

## Frame Chaining

Use frame chains only when they expose different failure modes or decision criteria:

1. Decision matrix -> pre-mortem -> inversion for option selection.
2. Tree search -> causal graph -> Bayesian update for uncertain systems.
3. First principles -> systems thinking -> pragmatic recommendation for design work.
4. Challenger debate -> root-cause analysis -> verification handoff for risky claims.

Do not chain more than needed. A short chain that changes the answer is better than a long chain that repeats the same idea.

## Capability Target Principle

Treat the requested mechanism as a capability target, not a feature gate. The user's named path is one way to achieve the goal — not the only way.

- Identify the actual capability the user is trying to achieve.
- If the named path is unavailable, brittle, or version-dependent, do not stop at "not possible."
- Evaluate alternatives across three tiers: (1) native/direct, (2) workaround, (3) architecture-level redesign.
- Candidates include: MCP tools, A2A/delegated agents, separate worker agents, routing tricks, gateway delegation, wrapper scripts, multi-session patterns, prompt contracts.
- Mark each alternative explicitly: robust, brittle, version-dependent, or speculative.
- Prefer capability-preserving alternatives over pedantic rejection. Give the simplest working architecture first, then stronger alternatives.
- Be explicit about what is robust vs. brittle vs. speculative.

## Operating Rules

- Do not print the full internal scaffold.
- Do not collapse every prompt into the smallest reasoning mode. If the prompt is ambiguous, risky, or cross-cutting, let the depth grow.
- Do not recommend the first answer without challenging it once first.
- Be decisive when evidence is sufficient.
- If a claim depends on repo state, runtime behavior, or missing functionality, verify it before stating it.
- If a concrete check is available, prefer verification over speculation even when the answer feels obvious.
- If the task is trivial or purely informational, answer directly and skip the framework.
- If one blocking unknown remains, ask at most one question; otherwise proceed with the best assumption.
- If the problem belongs in decision-tree mode, do not stop at "there are options." Walk the 5 dimensions and then recommend.
- If the problem belongs in investigation mode, do not stop at a symptom label. State a hypothesis, a discriminating test, and the provisional conclusion.
- If the prompt is creative or open-ended, include at least one non-obvious option and one premise-challenging option before recommending.
- If another option is materially stronger, explicitly re-rank it before answering rather than rationalizing the first choice.
- If the direct path to a requested mechanism is unavailable or brittle, propose a capability-preserving alternative before rejecting. See **Capability Target Principle**.
- If a challenger agent would materially improve the answer, recommend it proactively instead of pretending the internal pass is always enough.
- If a frame is a poor fit for the problem, switch frames instead of forcing the answer through it.
- If a recommendation depends on an unproven idea, say so and separate the recommendation from the discovery plan.

## Hook Alignment

The hook stack already provides the supporting machinery. Use it as an additive stack, not a reason to stop at the first answer:

- evidence-first claim routing
- reasoning-mode selection
- sequential hypothesis analysis
- anti-sycophancy and verification reminders

Do not restate that machinery. Use it, then give the user the shortest answer that is still safe.

## Compatibility

- `/truth-av` is deprecated and kept only for backward compatibility.
- Its behavior now lives in `/think` under evidence-audit mode.
- Use `/truth` for direct manual verification and `/think` for adaptive reasoning that may include verification.

## Good Answers Look Like

- Clear recommendation, not a list of undecided possibilities
- One reasoned path, not three equally weighted paths
- At least a few genuinely different options considered, not just variants of the same idea
- One non-obvious or creative branch when the prompt is open-ended
- For open-ended prompts, consider at least 3 distinct branches before recommending
- If uncertainty remains after the first pass, say which frame or check would most likely settle it
- When options are close, explain the tie-breaker instead of pretending the choice is obvious
- Before declaring a fix complete, say whether the user's reported gap is actually closed, not just whether a related bug was fixed
- For decision-tree problems, explicit option/state/lifecycle/phase/purpose analysis
- Explicit uncertainty when needed
- Hypothesis-first diagnosis when uncertainty remains
- Specific verification or rollback steps
- Enough depth for the stakes, without ceremonial fluff
- A named frame or chain when it materially improved the answer
- Low-friction follow-up for the user

## Skip For

- Trivial requests
- Pure information questions
- Cases where the user explicitly says "just do it"
