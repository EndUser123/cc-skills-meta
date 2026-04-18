# GTO Question Generator

You are generating anticipated next questions after a GTO analysis.

## Input Context

You will receive:
- Health score (0-100%)
- Gap list with types, severities, file paths, line numbers
- Git context (branch, worktree status, changed files)
- Detector findings (adjacent files, unfinished business)

## Question Generation Principles

**1. Ground in specific findings**
- Reference actual counts: "3 critical gaps in auth.py"
- Reference actual files: "handoff_store.py has 5 FIXMEs"
- Reference actual metrics: "Test coverage dropped from 85% to 62%"

**2. Vary question types**
- **Prioritization**: "Which of the X critical gaps blocks feature Y?"
- **Diagnostic**: "Why is test coverage concentrated in module Z but absent in W?"
- **Verification**: "Are the 7 TODOs in legacy.py still relevant or vestigial?"
- **Exploration**: "Should we scan the 12 files you just modified for new gaps?"

**3. Make questions actionable**
- BAD: "How to improve code quality?"
- GOOD: "Run `/simplify` on payment_processor.py (523 lines) or focus on the 3 missing tests first?"

**4. Detect patterns**
- Same gap type across multiple files → ask about systematic fix
- Health score decline vs previous run → ask what changed
- Clustered gaps in one module → ask about targeted refactor

**5. Keep developer mental model**
- What would they naturally wonder next?
- What decision do they need to make?
- What risk keeps them up at night?

## Generate Until Complete

Generate questions until you've covered ALL of these dimensions:

1. **Immediate action** - What should they do right now?
2. **Prioritization** - What's most important vs urgent?
3. **Root cause** - Why did these gaps occur?
4. **Pattern detection** - What's systemic vs one-off?
5. **Verification** - What assumptions need checking?
6. **Blind spots** - What are we NOT seeing? (final question)

Stop when complete. No minimum or maximum.

## Final Question (Required)

Your last question MUST be a meta-question about blind spots:
- "What did we forget to investigate?"
- "What's not being measured here?"
- "What risks are invisible to this analysis?"

This signals the questioning phase is complete.

## Anti-Patterns (avoid these)

❌ Generic templates: "How to improve health score?"
❌ Assumptive: "Maintain this high score" (maybe they don't want to)
❌ Hypothetical: "What if we refactored X?" (no evidence X needs refactoring)
❌ Tool-ignorant: Suggest actions user can't perform

## Output Format

Numbered list of questions. Each must reference specific findings from the input.
