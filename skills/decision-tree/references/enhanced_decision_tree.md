# Enhanced Decision Tree Framework

**Purpose:** Prevent missing options by modeling decisions as state transitions with lifecycles, not static choices.

## The Problem with Simple Decision Trees

Traditional decision trees ask "which option?" and miss:
- **State transitions**: What happens AFTER this step?
- **Lifecycle assumptions**: Is this resource persistent or ephemeral?
- **Multi-phase operations**: Can this happen at different times?
- **Purpose questions**: WHY does this resource exist?

## Enhanced Framework: 5 Dimensions

### Dimension 1: State Transitions (NEW)

Model every option as a state machine transition:

```
FOR EACH decision option:
├─ Current state: ?
├─ Next state: ?
├─ Final state: ?
└─ Transition cost: ?

Example: "Combine transcripts"
├─ Option A: Combine before fetch
│  └─ State: (no transcripts) → (combine what?) → ERROR
├─ Option B: Combine after fetch
│  └─ State: (no transcripts) → (individual transcripts) → (combined) → (delete originals)
│  └─ This reveals the multi-phase process!
```

### Dimension 2: Lifecycle Questioning (NEW)

For every resource created, ask:

```
RESOURCE: [name]
├─ Creation: How?
├─ Purpose: WHY does it exist?
├─ Lifecycle:
│  ├─ Persistent: Long-term storage, ongoing queries
│  ├─ Ephemeral: Fetch → extract → delete
│  └─ Mixed: Persistent container, ephemeral contents
└─ Deletion: When/why does it get destroyed?
```

**Example application: NotebookLM notebooks**
- Original question: "How do we organize within the 300-source limit?"
- Enhanced question: "What is the notebook's lifecycle?"
  - If persistent: Complex organization needed
  - If ephemeral: Simple create → fetch → delete loop

### Dimension 3: Multi-Phase Decomposition (NEW)

Any operation that can be time-sliced needs phase modeling:

```
OPERATION: [name]
├─ Phase 1: Before [prerequisite] (impossible if no data)
├─ Phase 2: During [operation] (parallel processing)
├─ Phase 3: After [completion] (batch processing + cleanup)
└─ Phase 4: Never (don't do it at all)

Example: "Combine transcripts"
├─ Phase 1: Before fetch (impossible - no data yet)
├─ Phase 2: During fetch (parallel combining)
├─ Phase 3: After fetch (batch combining + cleanup) ✓
└─ Phase 4: Never (keep individual)

The original tree only considered Phase 1 and dismissed it.
It should have modeled all 4 phases explicitly.
```

### Dimension 4: Purpose-Based Resource Decomposition (NEW)

For compound systems, separate container lifecycles from content lifecycles:

```
SYSTEM: [name]
├─ Container: [outer resource] (persistent or ephemeral?)
├─ Content: [inner resources] (persistent or ephemeral?)
├─ Query: Capabilities (needed long-term or one-time?)
└─ Storage: Local vs External (where is source of truth?)

This reveals: "Persistent notebook, ephemeral video sources, persistent combined sources"
```

### Dimension 5: Original Option Comparison (UNCHANGED)

```
Q1. What are the options?
├─ Option A: [description]
│  ├─ PROS: [benefits]
│  └─ CONS: [drawbacks]
├─ Option B: [description]
│  ├─ PROS: [benefits]
│  └─ CONS: [drawbacks]
└─ VERDICT: [recommendation with reasoning]
```

## Enhanced Decision Tree Template

Combine all 5 dimensions for comprehensive analysis:

```markdown
# Decision: [title]

## Q1. What are the options? (original)
[Option A vs B vs C analysis]

## Q2. State Transitions (NEW)
FOR EACH option: current → next → final state

## Q3. Resource Lifecycles (NEW)
FOR EACH resource created: persistent / ephemeral / mixed

## Q4. Operation Phases (NEW)
FOR EACH operation: before / during / after / never

## Q5. Purpose Analysis (NEW)
FOR EACH resource: WHY does it exist? What is its ultimate goal?

## VERDICT
[Recommendation with explicit justification from all 5 dimensions]
```

## Case Study: NotebookLM Integration

### Original Tree (Missed Options)

```
Q3: Can we combine transcripts into single sources?
├─ Option A: Combine many transcripts into one text source
├─ CONS: Circular dependency: need transcripts to get transcripts
└─ VERDICT: ✗ WRONG DIRECTION

Result: Missed "fetch → combine → delete" workflow
```

### Enhanced Tree (Caught Options)

```
Q3: Can we combine transcripts into single sources?

Q2. State Transitions:
├─ Option A: Combine before fetch
│  └─ (no transcripts) → (combine what?) → ERROR ✗
├─ Option B: Combine after fetch
│  └─ (no transcripts) → (fetch individual) → (combine) → (delete originals) ✓

Q3. Resource Lifecycles:
├─ Video sources: Ephemeral (fetch → delete)
├─ Combined sources: Persistent (long-term query capability)
└─ Notebooks: Mixed (persistent container, ephemeral contents)

Q4. Operation Phases:
├─ Phase 1: Before fetch (impossible)
├─ Phase 2: During fetch (parallel combining - complex)
├─ Phase 3: After fetch (batch combining + cleanup) ✓
└─ Phase 4: Never (keep individual - wastes slots)

Q5. Purpose Analysis:
├─ Purpose: Reclaim 300-source slots while keeping transcripts accessible
├─ Method: Combine fetched transcripts, delete video sources
└─ Result: Can add more videos without hitting limit

VERDICT: ✓ Option B (fetch → combine → delete) is viable and optimal
```

## Implementation Guidelines

### When to Use Enhanced Framework

Use the 5-dimensional framework for:
- **Architecture decisions** (system design, component lifecycles)
- **Resource management** (storage, caching, cleanup strategies)
- **Multi-phase workflows** (operations with time dependencies)
- **Integration planning** (connecting systems with different lifecycles)

### When Simple Trees Suffice

Simple "Option A vs B" trees work for:
- **Binary choices** (flag on/off, single parameter)
- **Stateless operations** (no resource lifecycle concerns)
- **Well-understood patterns** (routine decisions with no novelty)

## Confidence Calibration

After applying the enhanced framework, rate your confidence:

| Confidence | Criteria |
|------------|----------|
| HIGH | All 5 dimensions analyzed, state transitions explicit, lifecycles defined |
| MEDIUM | 3-4 dimensions analyzed, some assumptions remain |
| LOW | <3 dimensions analyzed, significant gaps remain |

**Rule:** If confidence is MEDIUM or LOW, explicitly state which dimensions are missing before recommending.

## Anti-Patterns

| Anti-Pattern | Symptom | Fix |
|--------------|---------|-----|
| Static choice | Decisions presented as "A vs B" without state modeling | Add Q2 (state transitions) |
| Lifecycle blindness | Resource persistence assumed without questioning | Add Q3 (lifecycle analysis) |
| Phase fixation | Operation considered at only one point in time | Add Q4 (phase decomposition) |
| Purpose vacuum | Resources created without clear "why" | Add Q5 (purpose analysis) |

## References

- Origin: Identified gap in NotebookLM decision tree (2026-04-10)
- Related: `subagent-first/SKILL.md` (when to use subagents vs direct execution)
- Related: `orchestrator/decision_engine.py` (workflow branching logic)
