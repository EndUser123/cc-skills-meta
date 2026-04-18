# Recommended Next Steps (RNS) Format — GTO v4.0

GTO produces a **dynamic-domain, flat-numbered** next-steps format combining the best of pre-mortem's compact snapshot and RNS's effort/reversibility tracking.

## Output Format (Rendered — No Code Fences)

```
🧪 TESTS
  TEST-001 [~5min] [R:1.25] Fix missing test in test_file.py (file:45)
  TEST-002 [~10min] [R:1.5] Fix failing test_Auth (test_auth.py:23)
  [caused-by: TEST-001]

📄 DOCS
  DOC-001 [~15min] [R:1.0] Add docstring to function_x (src/utils.py:78)

🔧 QUALITY
  QUAL-001 [~30min] [R:1.75] Refactor session_manager.py (src/session_manager.py:12)
  [causes: QUAL-002]

🐙 GIT
  GIT-001 [~2min] [R:1.0] Commit 3 uncommitted changes in hooks/

📦 DEPS
  DEPS-001 [~5min] [R:1.5] Install missing httpx dependency

🎯 SESSION
  SESSION-001 [~10min] [R:1.0] Complete prior session commitment: add validation

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

0 — Do ALL Recommended Next Actions (7 items, ~67min total)
```

## Format Rules

| Aspect | Rule |
|--------|-------|
| **Domain grouping** | Dynamic — only domains with findings appear |
| **Section headers** | Emoji + domain name (e.g., 🧪 TESTS, 📄 DOCS) — rendered as text, no fences |
| **Item numbering** | Flat globally — TEST-001, DOC-001, not hierarchical 1.1, 1.2 |
| **Effort estimation** | [~5min], [~30min], [~2hr] per item |
| **Reversibility** | [R:1.0] to [R:2.0] per item, from Reversibility Scale |
| **Dependency annotations** | [causes: ID], [caused-by: ID], [blocks: ID] inline after item |
| **Priority sorting** | critical → high → medium → low within each domain |
| **Do All directive** | 0 — Do ALL Recommended Next Actions (N items, ~Xmin total) |

## Emoji-to-Domain Mapping

| Domain | Emoji |
|--------|-------|
| tests | 🧪 |
| docs | 📄 |
| code_quality / quality | 🔧 |
| git | 🐙 |
| dependencies / deps | 📦 |
| import | ⚡ |
| skill_coverage | 🎯 |
| correctness | ✅ |
| session | 🎯 |
| other | 📌 |

## Dynamic Domain Rules

- Only domains with at least one finding get a section
- Domains sorted by worst-severity item within (most severe first)
- Empty domains are silently omitted

## Reversibility Scale Reference

| Score | Level | Action |
|-------|-------|--------|
| 1.0-1.25 | Trivial | Fix immediately |
| 1.5 | Moderate | Fix with tests |
| 1.75 | Hard | Defer unless critical |
| 2.0 | Irreversible | Full deliberation required |

## Dependency Annotation Format

| Annotation | Meaning |
|------------|---------|
| [causes: ID] | This finding directly creates another finding |
| [caused-by: ID] | This finding is a consequence of another |
| [blocks: ID] | This finding prevents another from being addressed |

## Gap Type to Domain Mapping

| Gap Type | Domain | Emoji |
|----------|--------|-------|
| test_failure, missing_test | tests | 🧪 |
| missing_docs, outdated_docs | docs | 📄 |
| git_dirty, uncommitted_changes | git | 🐙 |
| import_error, missing_dependency | deps | 📦 |
| code_quality, tech_debt | quality | 🔧 |
| import_issue | import | ⚡ |
| skill_suggestion | skill_coverage | 🎯 |
| correctness_gap | correctness | ✅ |
| session_outcomes | session | 🎯 |
| other | other | 📌 |

## Reference Implementation

- `lib/next_steps_formatter.py` — `_format_gto_rsn_markdown()` function
- `lib/next_steps_formatter.py` — `GAP_TYPE_REVERSIBILITY` dict for reversibility scores
- `memory/reversibility_scale.md` — Reversibility Scale
