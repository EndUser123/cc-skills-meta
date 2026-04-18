# CLI Options - Reflect Skill

## extract_signals.py Options

```bash
# Implicit pattern detection (enabled by default for production)
--implicit-patterns        Enable implicit learning pattern detection (default: enabled)
                           Detects retry patterns, tool discovery, pattern emergence
--no-implicit-patterns     Disable implicit pattern detection

# Semantic analysis
--semantic                Use AI-powered semantic analysis (default: enabled)
--no-semantic             Disable semantic analysis (regex-only, faster)
--model <model>           Model for semantic analysis (default: haiku)

# Other options
--skip-novelty            Skip CKS novelty detection (accumulation mode)
```

## Environment Variables

```bash
DISABLE_IMPLICIT_PATTERNS=1   Disable implicit pattern detection
SKIP_NOVELTY_CHECK=1          Skip CKS novelty detection (accumulation mode)
```

## Production Monitoring

When implicit pattern detection runs (default enabled), it provides:
- Pattern count: "Found N implicit pattern(s)"
- Pattern breakdown: "Pattern breakdown: retry_success: X, tool_discovery: Y, pattern_emergence: Z"
- Detailed learning: Each detected pattern includes:
  - Confidence level (MEDIUM: 0.6)
  - Learning type (retry_success, tool_discovery, pattern_emergence)
  - Implicit rule (actionable pattern learned)
  - Has implicit approval (user proceeded with follow-up task)
