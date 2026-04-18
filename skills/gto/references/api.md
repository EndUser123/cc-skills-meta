# GTO v3 API Reference

## Core Library (`__lib/`)

### Convenience Functions

```python
from gto.__lib import (
    # Viability
    check_viability,

    # Detectors
    check_chain_integrity,
    detect_session_goal,
    detect_unfinished_business,
    scan_code_markers,
    check_test_presence,
    check_docs_presence,
    check_dependencies,

    # Results
    build_initial_results,
    format_recommended_next_steps,

    # State
    get_state_manager,
)
```

### ViabilityGate

```python
from gto.__lib import ViabilityGate, check_viability

# Using class
gate = ViabilityGate(project_root=Path("path/to/project"))
result = gate.check()
if not result.is_viable:
    print(f"Viability failed: {result.failure_reason}")

# Using convenience function
result = check_viability(Path("path/to/project"))
```

### ChainIntegrityChecker

```python
from gto.__lib import ChainIntegrityChecker, check_chain_integrity

checker = ChainIntegrityChecker(project_root=Path("path/to/project"))
result = checker.check()
# result.issues: list[ChainIntegrityIssue]
# result.is_valid: bool
```

### SessionGoalDetector

```python
from gto.__lib import SessionGoalDetector, detect_session_goal

detector = SessionGoalDetector(transcript_path=Path("path/to/transcript.jsonl"))
result = detector.detect_goal()
# result.goal: str | None
# result.confidence: float (0.0 to 1.0)
```

### UnfinishedBusinessDetector

```python
from gto.__lib import UnfinishedBusinessDetector, detect_unfinished_business

detector = UnfinishedBusinessDetector(
    project_root=Path("path/to/project"),
    state_manager=StateManager()
)
result = detector.detect()
# result.items: list[UnfinishedItem]
```

### CodeMarkerScanner

```python
from gto.__lib import CodeMarkerScanner, scan_code_markers

scanner = CodeMarkerScanner(project_root=Path("path/to/project"))
result = scanner.scan()
# result.markers: list[CodeMarker]
```

### TestPresenceChecker

```python
from gto.__lib import TestPresenceChecker, check_test_presence

checker = TestPresenceChecker(project_root=Path("path/to/project"))
result = checker.check()
# result.gaps: list[TestGap]
# result.modules_checked: int
```

### DocsPresenceChecker

```python
from gto.__lib import DocsPresenceChecker, check_docs_presence

checker = DocsPresenceChecker(project_root=Path("path/to/project"))
result = checker.check()
# result.gaps: list[DocGap]
```

### DependencyChecker

```python
from gto.__lib import DependencyChecker, check_dependencies

checker = DependencyChecker(project_root=Path("path/to/project"))
result = checker.check()
# result.issues: list[DependencyIssue]
# result.packages_checked: int
```

### ResultsBuilder

```python
from gto.__lib import InitialResultsBuilder, build_initial_results, Gap

# Using class
builder = InitialResultsBuilder(project_root=Path("path/to/project"))
detector_results = {
    "viability_gate": viability_result,
    "chain_integrity": chain_result,
    # ... other detector results
}
results = builder.build(detector_results)

# Using convenience function
results = build_initial_results(detector_results, Path("path/to/project"))

# Access gaps
for gap in results.gaps:
    print(f"{gap.gap_id}: {gap.message} (confidence: {gap.confidence})")
```

### StateManager

```python
from gto.__lib import StateManager, StateFile, get_state_manager

# Using class
manager = StateManager(
    project_root=Path("path/to/project"),
    terminal_id="my-terminal"
)
state = manager.load()
state.gaps.append({"type": "test", "message": "Add tests"})
manager.save(state)

# Using convenience function
manager = get_state_manager(Path("path/to/project"), "my-terminal")

# History
manager.append_history({"run_summary": "GTO completed"})
history = manager.get_history(last_n=10)

# Recurrence tracking
gaps_with_recurrence = manager.update_gap_recurrence(gaps)
```

### NextStepsFormatter

```python
from gto.__lib import NextStepsFormatter, format_recommended_next_steps

# Using class
formatter = NextStepsFormatter()
formatted = formatter.format(gaps)

# Using convenience function
formatted = format_recommended_next_steps(gaps)

# Generate markdown
markdown = formatter.format_markdown(formatted)
print(markdown)
```

## Subagents (`subagents/`)

### GapFinderSubagent

```python
from gto.__lib import GapFinderSubagent, find_gaps

# Using class
finder = GapFinderSubagent(project_root=Path("path/to/project"))
result = finder.find_gaps()

# Using convenience function
result = find_gaps(Path("path/to/project"))

# Access findings
for gap in result.gaps:
    print(f"{gap.file_path}:{gap.line_number} - {gap.message}")
```

### HealthCalculatorSubagent

```python
from gto.__lib import HealthCalculatorSubagent, calculate_health

# Using class
calculator = HealthCalculatorSubagent(project_root=Path("path/to/project"))
report = calculator.calculate_health()

# Using convenience function
report = calculate_health(Path("path/to/project"))

# Access metrics
print(f"Overall score: {report.overall_score}")
print(f"Status: {report.status}")
for metric in report.metrics:
    print(f"{metric.name}: {metric.score} (weight: {metric.weight})")
```

## Data Classes

### Gap

```python
from gto.__lib import Gap

gap = Gap(
    gap_id="GAP-0001",
    type="missing_test",
    severity="high",
    message="No test file found",
    file_path="src/module.py",
    line_number=1,
    source="TestPresenceChecker",
    confidence=0.9,
    effort_estimate_minutes=15,
    theme="testing",
    recurrence_count=1,
    metadata={"key": "value"}
)
```

### ConsolidatedResults

```python
from gto.__lib import ConsolidatedResults

results = ConsolidatedResults(
    gaps=[gap1, gap2],
    total_gap_count=2,
    critical_count=0,
    high_count=1,
    medium_count=1,
    low_count=0,
    timestamp="2026-03-21T10:00:00",
    metadata={"key": "value"}
)
```

### StateFile

```python
from gto.__lib import StateFile

state = StateFile(
    version="3.0.0",
    terminal_id="my-terminal",
    timestamp="2026-03-21T10:00:00",
    session_id="session-123",
    gaps=[{"type": "test", "message": "gap"}],
    metadata={"key": "value"}
)
```

## Error Handling

All components use graceful degradation:

```python
# ViabilityGate
try:
    result = check_viability(project_root)
except Exception as e:
    print(f"Viability check failed: {e}")
    # Continue with degraded mode

# Detectors
result = checker.check()
# Returns empty result on failure, never raises

# Subagents
result = find_gaps(project_root)
# Returns empty result on failure, never raises
```

## Type Hints

All functions and classes use Python 3.12+ type hints:

```python
def check_viability(project_root: Path | None = None) -> ViabilityResult:
    ...

def build_initial_results(
    detector_results: dict[str, Any],
    project_root: Path | None = None,
) -> ConsolidatedResults:
    ...

class InitialResultsBuilder:
    def __init__(self, project_root: Path | None = None) -> None:
        ...

    def build(self, detector_results: dict[str, Any]) -> ConsolidatedResults:
        ...
```
