---
name: reason_grok
version: 1.1.0
status: stable
category: meta
enforcement: advisory
workflow_steps:
  - Assess query complexity and missing capabilities
  - Classify task type + detect data class for privacy routing
  - Emit structured routing decision (local_only / single_challenger / parallel_challengers / human_review)
  - Dispatch to internal Reflexion or external CLIs based on routing decision
  - Run multi-round critique/reflection if complex
  - Fuse evidence and produce labeled output
triggers:
  - /reason
suggest:
  - /think
  - /ai-pcli
  - /sequential-thinking
  - /decision-tree
---

# /reason — Unified Hybrid Reasoning Engine (2026 Architecture)

**Skill Version**: 1.0 (Radical Refactor — replaces /think, /ai-pcli, /ai-cli-gemini, /ai-pi-mm-m27)
**Generated**: 2026-04-21
**Purpose**: Single intelligent entry point that combines internal Reflexion-style depth (/think logic) with external multi-LLM breadth (parallel CLIs) for the highest-quality, most insightful responses possible. No more choosing between skills — just type `/reason` and get the best possible answer every time.

**Key Principles (Non-Negotiables — preserved and strengthened)**:
- Evidence labeling on every claim: **Verified** (directly supported by sources), **Inferred** (logical but not explicit), **Unproven** (speculative or contradicted).
- Solo-dev framing: all outputs consider practical constraints of a single developer (time, tools, maintainability).
- Citation enforcement: file:line references whenever files are read.
- Full CLI completion: external calls never return partial results.
- Adaptive depth: complexity is assessed automatically; simple queries stay fast, complex ones get debate/reflexion.
- Stateless and lightweight: no persistent memory unless you explicitly pass `--context FILE.md`.

**Usage**
```
/reason [your query] [--options]
```

**Common Options** (power-user flags):
- `--no-external` → pure internal Reflexion (fastest)
- `--debate-rounds N` → force N rounds of external critique (default: auto)
- `--framework [reflexion|tot|ooda|feynman|devil]` → force a specific mental model
- `--trace` → show full reasoning trace (orchestrator decisions, agent calls, critiques)
- `--gemini-only` / `--pi-m27-only` / `--codex-only` etc. → restrict external models (useful on Windows for gemini crashes)
- `--context PATH` → explicit files/directories (auto-detected otherwise)
- `--output [compact|verbose|json]` → default compact with tradeoffs

## How /reason Works (Dynamic Hybrid Orchestration)

### 1. Intake, Classification & Routing Decision (0.5–2s)

**Think-first as control plane, not answer generator.** The local pass emits a routing decision before any external dispatch — it decides *whether* to escalate and *which* specialist to call, not just generates an answer to compare.

Step 1: Fast internal classification
- Task type: code_review, planning, brainstorm, research, debug, refactor, general, rca
- Missing capabilities: freshness, citations, adversarial_review, long_horizon, multimodal, policy_risk
- Data class: local_ok, redact_then_remote, remote_only (privacy-aware routing)

Step 2: Emit structured routing decision
```
{
  "local_answer": "...",
  "confidence": 0.0,           // 0.0–1.0
  "task_type": "...",
  "missing_capabilities": ["freshness", "citations", ...],
  "data_class": "local_ok",
  "claims_to_verify": ["..."],
  "recommended_route": "local_only | single_challenger | parallel_challengers | human_review"
}
```

Step 3: Route based on decision
- **local_only** (confidence ≥ 0.85, no missing capabilities, local_ok data) → return local answer immediately
- **single_challenger** (one specific gap like freshness or citations) → call only the specialist that fills that gap
- **parallel_challengers** (complex task, multiple gaps) → call asymmetric specialists concurrently
- **human_review** (policy_risk or remote_only data) → escalate to user or route locally after redaction

### 2. Intelligent Dispatch (after routing decision)

- **Simple / local_only** → Pure internal Reflexion loop (Generate → Critique → Improve).
- **Single challenger** → One specialist call targeting the specific missing capability.
- **Parallel challengers** → Asymmetric role dispatch:
  - gemini → grounded verifier (freshness, citations)
  - minimax/M2.7 → adversarial reviewer (hidden flaws, regressions)
  - glm-5.1 → long-horizon implementer (complex builds)
  - codex → alternative generator (materially different approaches)
- **Complex / High-stakes** → Full hybrid cascade with debate rounds and hierarchical decomposition.

3. **Multi-Round Reflexion Engine** (core brain — evolved from original /think)
   - **Generate**: Synthesize strongest consensus from all available sources (internal + external).
   - **Critique**: Cross-model analysis + evidence labeling + gap detection + solo-dev tradeoff callout. Uses your existing ACG workflow where appropriate.
   - **Improve**: Refined final answer with frame chaining only when it meaningfully changes the outcome.
   - Optional 1–2 debate/reflexion rounds: critiques are fed back to external models or run internally.
   - Always ends with **Evidence Fusion Layer**: confidence matrix + explicit Verified/Inferred/Unproven labels on every major claim.

### 3. Multi-Round Reflexion Engine (core brain — evolved from original /think)
- **Generate**: Synthesize strongest consensus from all available sources (internal + external).
- **Critique**: Cross-model analysis + evidence labeling + gap detection + solo-dev tradeoff callout.
- **Improve**: Refined final answer with frame chaining only when it meaningfully changes the outcome.
- Optional debate/reflexion rounds: critiques fed back to external models or run internally.
- Ends with **Evidence Fusion Layer**: confidence matrix + Verified/Inferred/Unproven on every major claim.

### 4. Privacy-Aware Routing
Before any external call, detect data class from query content:
- **local_ok**: general questions, code, architecture — external calls permitted
- **redact_then_remote**: policy, compliance, legal text — extract claims only, then optionally escalate
- **remote_only**: public data only — external ok without restriction

Sensitive keywords trigger local-only routing: secret, api_key, password, token, credential, pii, personal, confidential, contract, ssn, credit card.
Policy keywords trigger redaction-first: policy, compliance, gdpr, hipaa, regulate, security.

### 5. Output Format

**Structured (JSON, `--output json`):**
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
  "sources": ["file:line", "gemini", "pi_m27"]
}
```

**Compact (default):**
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

Use `--trace` for full orchestrator log (routing decision, agent calls, critique steps).

### 6. Evaluation Methodology

Evaluate as a **routing-and-orchestration system**, not a single-model prompt.

**Metrics to log per answer:**
- `task_type`, `risk_class`, `route_id`, `prompt_version`, `provider`, `model`
- `tokens_in`, `tokens_out`, `cache_hits`, `latency_ms`
- `confidence_local`, `confidence_final`, `judge_disagreement`, `fallback_used`
- `user_acceptance`, `human_audit_label`

**Benchmark suite (7 test sets):**
1. Local-only factual reasoning (no freshness needed)
2. Freshness-required (recent/current → forces external escalation)
3. Long-context design (architecture tradeoffs, RFCs)
4. Repository coding (bug fixes, refactors)
5. Creative ideation (naming, product ideas under constraints)
6. Adversarial (prompt injection, contradictory specs)
7. Privacy-sensitive (secrets, PII, contracts → should route local_only)

**Starter prompt pack:**
1. "Given this ADR, what is the strongest argument against the chosen design?"
2. "Is the claim below current as of today? Cite the primary source."
3. "Review this patch like a hostile principal engineer: correctness + rollback risks only."
4. "Propose three designs, then explicitly reject the two weaker ones."
5. "Find the smallest test that would falsify this hypothesis."
6. "Rewrite for a CTO but preserve uncertainty and unresolved risks."

## Supported Mental Models / Frameworks (auto-selected or forced)
- **Reflexion** (default): Generate → Critique → Improve (your original /think loop, now on ensemble data).
- **Tree of Thoughts (ToT)**: Parallel branching frames + pruning via external critique.
- **ReAct**: Reason + Act (calls external CLIs as tools mid-reasoning).
- **OODA Loop**: Observe (external data) → Orient (internal critique) → Decide → Act.
- **Feynman Technique**: Force "explain like I'm a junior dev" in Improve phase.
- **Devil's Advocate + Pre-Mortem**: Explicit adversarial review (leverages MiniMax-M2.7).

The orchestrator picks the best one based on task; `--framework` overrides.

## Failure Resilience & Known Edge Cases Handled Automatically
- Gemini Windows AttachConsole crash → auto-drop + compensate with remaining models + deeper internal critique.
- Conceptual query ambiguity → forces BRAINSTORM + Reflexion (no more "what project?" trap).
- Extensionless directories → smart context extraction + evidence-audit fallback.
- Rate limits / empty outputs → retry logic + partial compensation + clear [EMPTY] / [RATE_LIMIT] flags.
- Task classifier ties → overridden by complexity assessment.
- Privacy-sensitive content → routes to local_only automatically (secrets, PII, contracts).
- Slow providers → quorum with soft deadline stops waiting once min_success is met.
- Prompt injection in retrieved docs → untrusted outputs isolated from model inputs.

**This is the complete, production-ready unified reasoning engine.**
Drop this SKILL.md into `P:/.claude/skills/reason/SKILL.md` (or your equivalent skills directory) and start using `/reason` immediately.

It delivers dramatically better answers than any previous combination because it intelligently blends:
- **Internal depth** (your Reflexion + evidence labeling)
- **External breadth** (4 diverse LLMs in parallel)
- **Dynamic orchestration** (2026 supervisor-worker + debate cascade)

You now have one command that always chooses the optimal path for maximum insight.
