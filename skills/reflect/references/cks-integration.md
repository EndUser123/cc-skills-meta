# CKS Schema Integration - Reflect Skill

**Implementation**: `scripts/cks_schema_mapper.py`

## Finding Types

/reflect findings are automatically classified into 5 types for CKS (Constitutional Knowledge System) storage:

| Finding Type | Description | Example Categories |
|--------------|-------------|-------------------|
| **PATTERN** | Repeated patterns, anti-patterns | forgotten, edge case, inconsistency, mismatch |
| **REFACTOR** | Code quality improvements | code quality, complex, duplicate, naming |
| **DEBT** | Technical debt indicators | violation, smell, missing, outdated |
| **DOC** | Documentation needs | documentation, unclear, README |
| **OPT** | Optimization opportunities | optimization, performance, caching |

## CKS Metadata Schema

When findings are stored to CKS, they include structured metadata:

```yaml
finding:
  text: "Consider using caching for expensive operations"
  category: "optimization"
  score: 8

  # CKS Schema Metadata (auto-added)
  finding_type: "OPT"              # One of: PATTERN, REFACTOR, DEBT, DOC, OPT
  severity_weight: 0.6             # 0.0-1.0 based on score + category
  category_confidence: "HIGH"       # HIGH, MEDIUM, LOW based on classification certainty
```

## Output Format

Findings are stored in CKS with the following structure:

```json
{
  "text": "User correction or pattern detected",
  "category": "correction|pattern|premortem|...",
  "score": 7,
  "timestamp": "2026-03-03T12:00:00Z",
  "session_id": "...",
  "metadata": {
    "finding_type": "PATTERN|REFACTOR|DEBT|DOC|OPT",
    "severity_weight": 0.7,
    "category_confidence": "HIGH|MEDIUM|LOW",
    "source_skill": "reflect"
  }
}
```

## Category Mapping

**PATTERN** (HIGH confidence for):
- forgotten, forgot, missed
- edge case, edge case, boundary
- inconsistency, inconsistent, mismatch
- anti-pattern, smell

**REFACTOR** (HIGH confidence for):
- code quality, clean code
- complex, complexity, simplify
- duplicate, duplication, DRY
- naming, rename, refactor

**DEBT** (HIGH confidence for):
- violation, violates
- smell, technical debt
- missing, lacks, needs
- outdated, deprecated, legacy

**DOC** (HIGH confidence for):
- documentation, docs, README
- unclear, confusing, ambiguous
- comment, annotate

**OPT** (HIGH confidence for):
- optimization, optimize
- performance, slow, latency
- caching, cache, memoization

## CKS Auto-Save Status

**Status**: Infrastructure present, integrates with reflect.py main workflow.

**What's implemented**:
- `scripts/cks_auto_save.py` - Auto-save module with graceful failure
- `scripts/cks_schema_mapper.py` - Finding type classification
- `store_lessons_to_cks()` in reflect.py - Stores approved changes to CKS
- Graceful fallback (CKS unavailable doesn't block reflection)

**Workflow**:
1. Run `/reflect` (generates analysis output)
2. User approves changes
3. Changes applied + stored to CKS automatically
4. Lessons available via `/learn` or CKS queries
