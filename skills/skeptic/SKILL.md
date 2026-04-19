---
name: skeptic
description: AI output validation using cognitive frameworks and evidence checking
version: "1.0.0"
status: stable
category: validation
triggers:
  - /skeptic
  - "challenge this plan"
  - "verify AI output"
  - "is this hallucinated"
aliases:
  - /skeptic

suggest:
  - /guard
  - /analyze
  - /verify

# Note: Cognitive frameworks (Cynefin, Hanlon's Razor, Inversion, Chesterton's Fence,
# Devil's Advocate) are now applied automatically via cognitive_enhancers hook.
# No manual /cognitive-frameworks invocation needed.
---

# /skeptic – AI Output Validation

## Purpose

Act as a skeptical reviewer of AI-generated plans, diffs, and analyses, with emphasis on:
- Evidence.
- Coverage (tests, edge cases).
- Overreach and unintended changes.
- Hallucination risk.

## When to Use

- After receiving a large AI plan or diff.
- Before acting on AI-heavy recommendations or merging AI-generated changes.

## Inputs

- Required:
  - Target to inspect:
    - A plan file.
    - A diff.
    - The last tool output.
- Optional:
  - Risk tags:
    - e.g., "security-sensitive", "data-loss risk", "performance-critical".

## Dependencies

- Skills:
  - `/cognitive-frameworks` – Cynefin, inversion, Chesterton's fence, Devil's Advocate, etc.
- Data:
  - Git history / blame (for Chesterton's fence).
  - Relevant code and tests for the target area.

## High-Level Behavior

### 1. Context & Artifact Loading
Determine the artifact to critique (plan, diff, or narrative). Identify relevant code and tests (if needed).

### 2. Framework-Based Analysis
Use `/cognitive-frameworks` mental models:
- **Cynefin**: Characterize problem domain (Clear/Complicated/Complex/Chaotic)
- **Inversion**: "What could go wrong if we follow this?"
- **Chesterton's Fence**: Check whether the change removes or alters existing logic without understanding why it exists
- **Devil's Advocate**: Generate strongest objections and stakeholder impacts

### 3. AI-Specific Checks
- **Evidence**: Highlight claims without clear support (e.g., "this improves performance" with no measurement)
- **Coverage**: Identify missing tests, edge cases, or non-covered failure paths
- **Overreach**: Identify changes that go beyond request scope or touch unrelated modules
- **Hallucination**: Spot references to non-existent files, APIs, or patterns not present in the repo

### 4. Findings and Actions
Summarize findings with severity:
- High / Medium / Low

Propose concrete actions:
- Add tests for specific scenarios
- Run `/guard` for deeper risk analysis
- Narrow the change
- Discard or re-request the plan if hallucinations dominate

## Output Format

- "Skeptic report" including:
  - Brief context summary.
  - List of findings (each with severity, description, and rationale).
  - 2–3 actionable next steps.

## Notes

- Focus on *where to be careful*, not rewriting the entire plan.
- Can be chained with `/guard` and `/ship` for high-risk flows.
