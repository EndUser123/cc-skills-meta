# Meta-Patterns - Reflect Skill

## Self-Verification (Step 3.8 Applied to Self)

**Principle**: "Require empirical evidence before declaring risks mitigated" applies to AI suggestions too.

**Check**: `check_self_verification()` detects when AI suggests improvements without first verifying the gap exists.

**Example violation**:
```
AI: "We should add integration tests for this feature."
# Without first checking: "What integration tests already exist?"
```

**Correct approach**:
```
AI: "Let me check what tests exist first..."
[runs Glob/Grep to find existing tests]
AI: "I found unit tests but no integration tests for skill invocation. Adding those would fill a real gap."
```

**Meta-note**: Suggestions about verification systems themselves receive HIGH severity, since the verification principle should apply most strongly to verification-related suggestions.
