# Systematic Modernization Flow

A 4-phase process to transform legacy/working code into high-standard production systems.

## ⚡ EXECUTION DIRECTIVE

**Apply these phases in order. Do not skip the AUDIT phase.**

---

## STEP 0: TRIAGE (Pre-Routing)

**Objective:** Assess modernization scope and select execution path.

1. **Parse Modernization Request:**

   - Single file vs. module vs. entire codebase?
   - Known debt (TODO/FIXME) vs. systemic patterns?
   - Breaking changes acceptable?

2. **Explore Context:**

   ```bash
   /complexity <target> --threshold 10
   ```

   - Get a quick debt map before committing to full audit.

3. **Select Path:**
   | Scope | Path | Skip To |
   |-------|------|---------|
   | Single file, low complexity | FAST | Phase 3 (EXECUTE) |
   | Module, moderate debt | STANDARD | Phase 1 (AUDIT) |
   | Codebase-wide, high debt | CAREFUL | Phase 2 (STRATEGY) with `/llm-debate` |

**Exit Criteria:** Path selected, scope defined.

---

## Phase 1: AUDIT (Measure Debt & Baseline)

**Objective:** Map the technical debt landscape and establish performance baselines.

1.  **Run Complexity Scan:**
    ```bash
    /complexity <target> --threshold 10
    ```
2.  **Run Quality & Dependency Scan:**
    ```bash
    /analyze <target> --focus quality --focus library
    ```
    _Identify anemic models, circular imports, and outdated API patterns._
3.  **Establish Performance Baseline:**

    ```bash
    /profile <target> --baseline
    ```

    _Record resource usage/timing for the working but "smelly" code._

4.  **Self-Admitted Technical Debt (SATD) Scan:**
    ```bash
    rg -n "TODO|FIXME|HACK|XXX|DESIGN SMELL" <target> --type py
    ```
    _Classify findings into a prioritized debt backlog._

---

## Phase 2: STRATEGY (Design Abstraction)

**Objective:** Decide on the "Standard of Excellence" before editing.

0.  **Opportunity Brainstorm (Optional but Recommended):**

    ```bash
    /brainstorm "modernization paths for <target>"
    ```

    _Generates 15+ diverse refactoring approaches before strategic commitment._

1.  **Architectural Check:**
    ```bash
    /design "Should we modernize <component> using <pattern>?"
    ```
2.  **Multi-Agent Strategy Debate (High-Stakes):**

    ```bash
    /llm-debate "Validate: <proposed_pattern>" --agents architecture_reviewer performance_optimizer security_expert --mode concurrent
    ```

    _Use for decisions with >2 hour implementation time._

3.  **Verify Solo-Dev Feasibility:**
    Ensure the design minimizes maintenance burden and dependencies.

4.  **Incremental Tasking:**
    ```bash
    /plan "<refactor_goal>" --challenge
    ```
    _Breaks the evolution into 2-5 minute "Safe-Point" chunks, gated by `/checkpoint`._

---

## Phase 3: EXECUTE (Transform & Purge)

**Objective:** Apply synergies and eliminate "Ghost Code."

-1. **Predictive Regression Check (Future):**
_TODO: Query `P:/logs/test_failure_ledger.json` to predict if this refactor is likely to regress known failure modes. Requires `/verify` history logging._

0.  **TDD Gate (Optional):**

    ```bash
    /tdd on
    ```

    _Enforces test-first for structural changes. Disable with `/tdd off`._

1.  **Multi-File Synergy:**
    `bash
/refactor <files/dir>
`
    1b. **Deep Semantic Analysis (High-CC Files):**
    `bash
/aid refactor <high_cc_file>
`
    _Use for files with CC > 15 that need SOLID violation analysis._

2.  **Dead-Code Purge (MANDATORY post-refactor):**
    ```bash
    /analyze <target> --focus dead-code
    ```
    _Prune functions and modules orphaned by the refactor._
3.  **Safety:**
    Use `/checkpoint` before and after structural transitions.

---

## Phase 4: HARDEN (Certify & Seal)

**Objective:** Verify gains and update the project's "Collective Memory."

1.  **Performance Certification:**
    ```bash
    /profile <target> --compare
    ```
    _Ensure modern patterns (like Async) didn't regress performance._

1b. **Log Complexity Delta:**
After `/profile --compare`, note the before/after CC scores. Append to `P:/logs/debt_ledger.json`:
`json
    {"date": "<ISO_DATE>", "target": "<file>", "cc_before": N, "cc_after": M, "delta": N-M}
    `

2.  **Systematic Validation:**
    ```bash
    /verify --tier 1,2,3
    ```
3.  **Knowledge Sync (The Seal):**

    ```bash
    /learn
    ```

    _Finalize the evolution by updating the CKS and Project Constitution (`CLAUDE.md`)._

4.  **Auto-Generate Architecture Decision Record (ADR):**
    After `/learn`, draft an ADR to `P:/__csf/adr/` documenting:
    - **Context:** What was the old pattern?
    - **Decision:** What is the new standard?
    - **Consequences:** What are the trade-offs?

---

## Evolution Guardrails

- **Zero-Regression Rule:** If performance regresses or tests fail, roll back.
- **Standards Pivot:** Never evolve into a pattern that violates `code-python-2025`.
- **Knowledge Debt:** An evolution isn't complete until `/learn` updates the CKS.
