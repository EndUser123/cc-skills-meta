# Risk Assessment Reference

## Tier x Size x Kind Formula

Replaces subjective LxI scoring:

```
risk_score = (tier_weight x 0.5) + (size_weight x 0.3) + (kind_weight x 0.2)
```

**Implementation**: `scripts/risk_calculator.py`

## Components

### Tier (50% weight): How central is the code?

| Tier | Weight | Description |
|------|--------|-------------|
| CORE | 1.0 | Central architecture, critical paths |
| HIGH | 0.8 | Important subsystems |
| MEDIUM | 0.6 | Standard features |
| LOW | 0.4 | Peripheral features |
| UTILITY | 0.2 | Helper code, tools |

### Size (30% weight): How much code is changing?

| Size | Weight | Description |
|------|--------|-------------|
| LARGE | 1.0 | Multi-file, extensive changes |
| MEDIUM | 0.6 | Single file, moderate changes |
| SMALL | 0.3 | Function-level changes |
| TINY | 0.1 | Minor tweaks |

### Kind (20% weight): What type of change?

| Kind | Weight | Description |
|------|--------|-------------|
| REFACTOR | 1.0 | Restructuring existing code |
| FEATURE | 0.8 | Adding new functionality |
| BUGFIX | 0.6 | Fixing bugs |
| CONFIG | 0.3 | Configuration changes |
| DOCS | 0.1 | Documentation only |

## Risk Levels

| Level | Threshold |
|-------|-----------|
| CRITICAL | >= 0.8 |
| HIGH | >= 0.7 |
| MEDIUM | >= 0.5 |
| LOW | < 0.5 |

## Examples

- CORE + LARGE + REFACTOR = 1.0 (CRITICAL) - Major architectural refactoring
- UTILITY + TINY + DOCS = 0.15 (LOW) - Documentation update
- MEDIUM + MEDIUM + FEATURE = 0.64 (MEDIUM) - Standard feature addition
