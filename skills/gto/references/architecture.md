# GTO v3 Architecture Reference

## Overview

GTO (Gap Technical Organizer) v3 is a three-layer gap analysis system:

1. **Layer 1: Python Deterministic** - Fast, deterministic gap detection
2. **Layer 2: Agents/AI Reasoning** - AI-powered gap discovery and analysis
3. **Layer 3: Claude Orchestrator** - User-facing skill coordination

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Layer 3: Claude Orchestrator              │
│                                                               │
│  /gto skill invocation → ViabilityGate → Detectors →        │
│  Subagents → ResultsBuilder → NextStepsFormatter → Output   │
│                                                               │
└──────────────────────────┬────────────────────────────────────┘
                               │
┌──────────────────────────▼────────────────────────────────────┐
│                    Layer 2: AI Subagents                     │
│                                                               │
│  GapFinderSubagent (line numbers)                             │
│  HealthCalculatorSubagent (health metrics)                     │
│  Future: ContextAnalyzer, PatternDetector                     │
│                                                               │
└──────────────────────────┬────────────────────────────────────┘
                               │
┌──────────────────────────▼────────────────────────────────────┐
│                 Layer 1: Python Deterministic                 │
│                                                               │
│  lib/viability_gate.py - Precondition checking               │
│  lib/chain_integrity_checker.py - Chain validation          │
│  lib/session_goal_detector.py - Goal detection               │
│  lib/unfinished_business_detector.py - Unfinished items      │
│  lib/code_marker_scanner.py - Code markers                   │
│  lib/test_presence_checker.py - Test coverage               │
│  lib/docs_presence_checker.py - Documentation               │
│  lib/dependency_checker.py - Dependencies                   │
│  lib/next_steps_formatter.py - Results formatting           │
│  lib/state_manager.py - Multi-terminal state                │
│  lib/results_builder.py - Consolidation & enrichment         │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

## Key Components

### ViabilityGate (P0)
- **Purpose**: Check preconditions before running expensive analysis
- **Location**: `lib/viability_gate.py`
- **Checks**:
  - Git repository exists
  - Working directory is clean (no uncommitted changes)
  - Git is available

### Detectors (P2)
All detectors follow a consistent pattern:
- Input: Project root path
- Output: Result dataclass with gaps list
- Methods: `check()` returns Result

**Detectors:**
1. **ChainIntegrityChecker** - Validates execution chain integrity
2. **SessionGoalDetector** - Detects session goal from conversation
3. **UnfinishedBusinessDetector** - Finds unfinished business from prior runs
4. **CodeMarkerScanner** - Scans for code markers (TODO, FIXME, etc.)
5. **TestPresenceChecker** - Checks for test coverage gaps
6. **DocsPresenceChecker** - Checks for documentation gaps
7. **DependencyChecker** - Checks dependency health

### Subagents (P2)
AI-powered analysis with line number precision:

1. **GapFinderSubagent**
   - Scans for gap markers with precise line numbers
   - Categorizes gaps by type (testing, docs, dependencies, code_quality)
   - Returns structured JSON for ResultsBuilder

2. **HealthCalculatorSubagent**
   - Calculates health metrics across 4 dimensions
   - Weighted scoring: test_coverage (30%), documentation (20%), dependencies (20%), code_quality (30%)
   - Returns HealthReport with overall score

### ResultsBuilder (P1)
- **Purpose**: Consolidate and enrich detector outputs
- **Features**:
  - Deduplication (MD5 signature-based)
  - Confidence scoring (0.0-1.0)
  - Effort estimation (minutes)
  - Theme detection (testing, docs, dependencies, etc.)
  - Recurrence tracking (cross-session)

### StateManager (P0)
- **Purpose**: Multi-terminal state isolation
- **Features**:
  - Terminal-scoped state directories (`.evidence/gto-state-{terminal_id}/`)
  - Atomic writes (temp-file + replace)
  - Schema versioning (current: 3.0.0)
  - Corruption recovery
  - History tracking (JSONL format)

### NextStepsFormatter (P1)
- **Purpose**: Format recommended next steps
- **Features**:
  - Grouping by category (tests, docs, git, dependencies, code_quality)
  - Sorting by priority (critical → high → medium → low)
  - Effort estimate display
  - Recurrence tracking

## Multi-Terminal Isolation

Each terminal gets isolated state:

```
P:\.claude\projects\PROJECT\.evidence\
├── gto-state-console-abc123\
│   └── state.json
├── gto-state-console-def456\
│   └── state.json
├── gto-history-console-abc123.jsonl
└── gto-history-console-def456.jsonl
```

**No shared mutable state** - each terminal writes to its own directory.

## Data Flow

```
User invokes /gto
    ↓
ViabilityGate check (P0)
    ↓
Run all detectors (P2)
    ├─ ChainIntegrityChecker
    ├─ SessionGoalDetector
    ├─ UnfinishedBusinessDetector
    ├─ CodeMarkerScanner
    ├─ TestPresenceChecker
    ├─ DocsPresenceChecker
    └─ DependencyChecker
    ↓
Invoke subagents (P2)
    ├─ GapFinderSubagent → gaps with line numbers
    └─ HealthCalculatorSubagent → health metrics
    ↓
ResultsBuilder consolidation (P1)
    ├─ Deduplicate gaps
    ├─ Apply confidence scoring
    ├─ Apply effort estimation
    └─ Apply theme detection
    ↓
NextStepsFormatter formatting (P1)
    ↓
JSON artifact output
```

## JSON Artifact Format

```json
{
  "gaps": [
    {
      "id": "GAP-0001-TEST",
      "type": "missing_test",
      "severity": "high",
      "message": "No test file found for module.py",
      "file_path": "src/module.py",
      "line_number": 1,
      "source": "TestPresenceChecker",
      "timestamp": "2026-03-21T10:00:00",
      "metadata": {},
      "confidence": 0.9,
      "effort_estimate_minutes": 15,
      "theme": "testing",
      "recurrence_count": 1
    }
  ],
  "total_gap_count": 5,
  "critical_count": 0,
  "high_count": 2,
  "medium_count": 2,
  "low_count": 1,
  "timestamp": "2026-03-21T10:00:00",
  "metadata": {
    "project_root": "P:\\project",
    "detector_count": 7,
    "raw_gap_count": 8,
    "deduplicated_count": 5,
    "duplicates_removed": 3
  }
}
```

## Health Score Calculation

Overall health = weighted sum of all metrics:

| Metric | Weight | Description |
|--------|--------|-------------|
| test_coverage | 0.3 | Ratio of test files to source files |
| documentation | 0.2 | Ratio of documented source files |
| dependencies | 0.2 | Dependency management health |
| code_quality | 0.3 | Inverse of TODO/HACK marker density |

**Status thresholds:**
- **Healthy**: score ≥ 0.8
- **Warning**: 0.5 ≤ score < 0.8
- **Critical**: score < 0.5

## Extension Points

### Adding New Detectors

1. Create new file in `lib/`: `my_detector.py`
2. Implement `check()` method returning Result dataclass
3. Add to `lib/__init__.py` exports
4. Add to ResultsBuilder consolidation methods

### Adding New Subagents

1. Create new file in `subagents/`: `my_subagent.py`
2. Implement analysis class with `find_*()` or `calculate_*()` method
3. Add to `subagents/__init__.py` exports
4. Call from main orchestrator

### Adding New Health Metrics

1. Add metric to `METRIC_WEIGHTS` in HealthCalculatorSubagent
2. Implement `_calculate_*()` method
3. Return HealthMetric with score (0.0-1.0) and weight

## Import Patterns

GTO uses `sys.path` manipulation to import from its internal `hooks/__lib` directory. This pattern differs from CSF-level imports (documented in ADR-20260322-syspath-manipulation.md).

### Internal Import Pattern

GTO modules that need shared utilities from `hooks/__lib` use relative path resolution:

```python
# hooks/gto_verify_wrapper.py pattern
from pathlib import Path

def _find_hooks_dir(start: Path) -> Path:
    """Find the hooks directory by walking up from start path."""
    current = start
    while current != current.parent:
        if (current / "hooks").exists():
            return current / "hooks"
        current = current.parent
    raise FileNotFoundError("hooks directory not found")

# Then insert to sys.path
_HOOKS_DIR = _find_hooks_dir(Path(__file__))
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))
```

### Why This Pattern

- **Internal isolation**: GTO's `hooks/__lib` contains GTO-specific utilities, not CSF shared code
- **Relative resolution**: Uses `_find_hooks_dir()` to locate the hooks directory relative to the module
- **No package dependency**: Avoids requiring GTO to be installed as a package

### Files Using This Pattern

| File | Purpose |
|------|---------|
| `hooks/gto_verify_wrapper.py` | Verification wrapper for GTO hooks |
| `evals/gto_assertions.py` | Binary assertions script |
| `gto_orchestrator.py` | Main orchestrator |

### Contrast with CSF-level Imports

CSF-level imports (documented in ADR-20260322) use:
- Editable package installation: `pip install -e`
- Standard `import` statements
- No path manipulation

GTO internal imports use:
- `sys.path.insert()` with relative path resolution
- Internal `hooks/__lib` directory
- No package installation required
