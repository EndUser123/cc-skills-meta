# Completion Report Templates

## Phase Execution Tracker (MANDATORY)

Before writing the completion report, track which phases actually ran during this session:

```
# Phase execution tracking — prevents false completion claims
#
# As each phase EXECUTES (not checks, not skips, not "already exists"), add:
#   PHASES_EXECUTED+=("PHASE 1: Diagnose")
#   PHASES_EXECUTED+=("PHASE 1.5: Detect type")
#   PHASES_EXECUTED+=("PHASE 2: Build")
#   PHASES_EXECUTED+=("PHASE 3: Templates")
#   PHASES_EXECUTED+=("PHASE 4: Validate")
#   PHASES_EXECUTED+=("PHASE 4.5: Code Review")
#   PHASES_EXECUTED+=("PHASE 4.7: Media")
#   PHASES_EXECUTED+=("PHASE 4.8: Course")
#   PHASES_EXECUTED+=("PHASE 5: Polish")
#   PHASES_EXECUTED+=("PHASE 8: Cleanup")
#
# CRITICAL: Only claim COMPLETE for phases that were actually EXECUTED this session.
# File existence alone is NOT execution evidence.
```

## TRUTH Claim Rule (PREVENT FALSE completion claims)

**The completion report MUST distinguish three categories:**

1. **EXECUTED**: Phase was run during this session. Show evidence of what was generated.
2. **PRE-EXISTING**: File existed before this session. Show when it was last modified.
3. **SKIPPED**: Phase was not run (not applicable or `--skip` flag).

```bash
# WRONG (causes false completion claims):
#   "Architecture diagram: COMPLETE" — found Mermaid in README but PHASE 5 was never run
#   "Media assets: GENERATED" — docs/video.html exists from a prior session
#   "Tests: PASSING" — test directory exists but no pytest was run this session

# RIGHT (evidence-backed claims):
#   "PHASE 5 Polish: EXECUTED — generated badges, CHANGELOG"
#   "PHASE 4.7 Media: SKIPPED (not applicable for skill-only plugin)"
#   "Architecture diagram: PRE-EXISTING (Mermaid block in README, not modified this session)"
```

## What to Verify

```bash
# 1. Check if GitHub remote exists
git remote -v | grep github.com

# 2. Check if repo is public (requires gh CLI)
gh repo view --json name,owner,isPublic,url

# 3. Verify portfolio polish completeness
checklist=(
  "README.md with badges"
  "CHANGELOG.md"
  "CONTRIBUTING.md"
  "AGENTS.md"
  "LICENSE file"
  "tests/ directory exists"
  "pytest tests pass"
  "pyproject.toml or setup.py"
  "Media assets generated (if applicable)"
)
```

## Output Format

**MUST show one of these statuses, with truth-claim evidence for each item:**

### STATUS: PUBLIC ON GITHUB
```
Package is LIVE and PUBLIC on GitHub!

https://github.com/EndUser123/package-name

Phase Execution Evidence:
PHASE 1 Diagnose: EXECUTED -> detected {type}
PHASE 1.5 Detect: EXECUTED -> classified as {classification}
PHASE 2 Build: EXECUTED -> created {files}
PHASE 3 Templates: EXECUTED -> generated {artifacts}
PHASE 4 Validate: EXECUTED -> {results}
PHASE 5 Polish: EXECUTED -> generated badges, CHANGELOG
PHASE 4.7 Media: SKIPPED (not applicable for {reason})

Ready for: recruiters, portfolio, public use
```

### STATUS: READY FOR GITHUB (NOT YET PUBLIC)
```
Package is POLISHED and ready for GitHub!

Phase Execution Evidence:
PHASE 1 Diagnose: EXECUTED -> {evidence}
PHASE 5 Polish: EXECUTED -> {what was generated this session}
PHASE 4.7 Media: SKIPPED (not applicable for {reason})
PHASE 4.8 Course: SKIPPED (not applicable for {reason})

Next steps:
1. Create GitHub repo: gh repo create package-name --public --source=. --push
2. Or manually: git remote add origin https://github.com/USER/REPO.git && git push -u origin main

After pushing: https://github.com/YOUR_USERNAME/package-name
```

### STATUS: LOCAL ONLY (NEEDS POLISH)
```
Package exists locally

Phases executed this session:
PHASE 1 Diagnose: EXECUTED -> {evidence}
PHASE 5 Polish: NOT EXECUTED (files may exist from prior session)
PHASE 4.7 Media: NOT EXECUTED

Not yet ready for GitHub:
- [ ] Execute portfolio polish (PHASE 5) — run: /gitready <package-path>
- [ ] Generate media assets (PHASE 4.7) — if applicable
- [ ] Ensure all tests pass
- [ ] Review Recruiter Readiness Report

Run: /gitready <package-path>
```
