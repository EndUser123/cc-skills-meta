# Quality Pipeline Reference

## Quality Skills (9 total)

**Testing (3 skills):**
- `/t` - Context-aware adaptive testing with risk scoring and code flow tracing
- `/qa` - Quality assurance certification
- `/tdd` - Test-driven development workflow

**Validation (2 skills):**
- `/comply` - Standards and constitutional validation
- `/validate_spec` - Specification validation

**Analysis (3 skills):**
- `/debug` - Systematic debugging (4-phase)
- `/rca` - Root cause analysis
- `/nse` - Next step engine

**Optimization (2 skills):**
- `/refactor` - Multi-file refactoring
- `/q` - Code quality monitoring

## Quality Workflows

Predefined quality workflow templates:

| Workflow Type | Skills | Use Case |
|--------------|--------|----------|
| **standard** | `/t` -> `/comply` -> `/qa` | Regular quality checks |
| **deep** | `/t` -> `/analyze` -> `/comply` -> `/debug` -> `/qa` | Comprehensive review |
| **regression** | `/t` -> `/rca` -> `/debug` -> `/fix` | Regression investigation |
| **optimization** | `/t` -> `/q` -> `/refactor` -> `/comply` -> `/qa` | Code improvement |
| **spec_validation** | `/validate_spec` -> `/comply` -> `/t` | Spec compliance |
| **quick_check** | `/t` -> `/comply` | Fast validation |

## Quality Stage Transitions

Valid quality pipeline transitions:

```
test -> validate -> comply -> qa -> (refactor | nse)
                      |
                    opts -> refactor

debug <-> rca -> nse -> (test | comply)
```

## Quality Metrics Tracking

- Execution counts per quality skill
- Pass/fail rates (when metrics provided)
- Coverage suggestions
- Issues found and resolved
- Aggregate statistics (min, max, avg)

## Quality Pipeline Behavior

### Automatic Quality Detection

When invoking a quality skill, the orchestrator:

1. **Detects quality skill** - Checks if skill is in quality categories
2. **Validates transitions** - Ensures quality pipeline stage is valid
3. **Enriches suggestions** - Adds quality-specific next steps
4. **Tracks metrics** - Records category and pipeline info

### Quality Transition Validation

The orchestrator blocks invalid quality transitions:

```
VALID:   /t -> /comply -> /qa
INVALID: /qa -> /t  (wrong order)
INVALID: /comply -> /debug  (stage mismatch)
```

### Integration with Suggest Fields

Quality pipeline works alongside suggest fields:
- Suggest fields provide general workflow guidance
- Quality pipeline provides quality-specific validation
- Both are checked during skill invocation
