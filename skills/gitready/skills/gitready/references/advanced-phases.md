# Advanced Phases: Code Review, GitHub Publication, Finalization, Quality Scanning

## PHASE 4.5: Code Review & Meta-Review (Auto-invoked)

**When**: Automatically runs after PHASE 4 (Validate) completes, before PHASE 5 (Portfolio Polish).

**What this does:**
1. **Code Review Plugin**: Comprehensive code review with confidence-based scoring
   - Checks for security, performance, and maintainability issues
   - Confidence threshold (80+) for filtering findings
   - Generates summary report with actionable recommendations

2. **Meta-Review System**: Cross-file analysis for architectural issues
   - Path traversal vulnerability detection (taint propagation)
   - Import graph analysis (circular dependencies, layering violations)
   - Documentation consistency validation
   - AnalysisUnit-based manifest-driven review

**Execution:**
```python
# Code review (existing)
Skill(skill="code-review:code-review", args="{{TARGET_DIR}}")

# Meta-review (NEW - T-007 integration)
from lib.meta_review.prepare_context import prepare_agent_context
from lib.analysis_unit import create_analysis_unit

unit_id = create_analysis_unit(Path("{{TARGET_DIR}}"))
context = prepare_agent_context(unit_id, perspective="security", max_tokens=8000)

# Run meta-review analyzers
from lib.analysis_unit.analyzers.path_traversal import PathTraversalAnalyzer
from lib.analysis_unit.analyzers.import_graph import ImportGraphAnalyzer
from lib.analysis_unit.analyzers.doc_consistency import DocConsistencyAnalyzer

pt_findings = PathTraversalAnalyzer().analyze(manifest)["findings"]
ig_findings = ImportGraphAnalyzer().analyze(manifest)["findings"]
dc_findings = DocConsistencyAnalyzer(manifest).analyze()

# Combine findings
meta_review_summary = {
    "path_traversal": pt_findings,
    "import_graph": ig_findings,
    "doc_consistency": dc_findings,
    "total_findings": len(pt_findings) + len(ig_findings) + len(dc_findings)
}
```

**Integration notes:**
- Run AFTER structure validation passes
- Run BEFORE portfolio polish (prevents polishing bad code)
- Meta-review is optional (controlled by META_REVIEW_ENABLED env var, default: true)
- If critical findings (HIGH severity): fix before proceeding to PHASE 5
- If advisory findings (MEDIUM/LOW severity): document, proceed to PHASE 5
- If no findings: proceed to PHASE 5

**Duration**: 1-3 minutes (combined)

---

## PHASE 4.6: Quality Scanning (Optional, during validation)

**Trigger**: User explicitly requests quality scan via `--scan-quality` flag.

**What this does:**

1. **Security Scanning**: Runs `bandit` for Python security issues, `safety` for known vulnerable dependencies
2. **Dependency Auditing**: Runs `pip-audit` for vulnerability scanning, checks for outdated packages
3. **Badge Validation**: Verifies all badge URLs in README.md are reachable
4. **Quality Metrics**: Counts Python/test files, calculates test ratio, reports total lines of code

**Script**: `../../scripts/scan_package_quality.py`

**Options:**
- `--skip-security` - Skip security scanning (bandit, safety)
- `--skip-audit` - Skip dependency auditing (pip-audit)
- `--skip-badges` - Skip badge validation
- `--skip-quality` - Skip code quality metrics
- `--save-report` - Save scan results to .quality-report.json
- `--fail-on-issues` - Exit with error code if issues are found

---

## PHASE 6: GitHub Publication (Optional)

**Trigger**: User explicitly requests via `--publish` flag.

**What this does:**

1. **Monorepo Extraction** (if package is in a monorepo):
   - Uses `../../scripts/extract_from_monorepo.py` to create clean git history
   - Two methods: subtree split (preserves history) or fresh init (clean slate)

2. **GitHub Repository Creation**:
   - Uses `../../scripts/create_github_repo.py` to create repository via GitHub CLI (gh)
   - Sets repository to public, adds remote and pushes code

**Prerequisites**: GitHub CLI (`gh`) installed and authenticated.

**Usage:**
```bash
/gitready my-package --publish

# Or manually
cd P:/packages/my-package
python ../../scripts/extract_from_monorepo.py . my-package
python ../../scripts/create_github_repo.py my-package . "My awesome package"
```

---

## PHASE 7: Repository Finalization (Optional)

**Trigger**: User explicitly requests via `--finalize` flag.

**What this does:**

1. **GitHub Pages Enablement**: Automatically enables GitHub Pages for documentation
2. **Initial Release Creation**: Creates v0.1.0 or v1.0.0 release via `gh release create`
3. **Repository Topics/Tags**: Adds relevant topics (python, claude-code, plugin, mcp, etc.)
4. **CODEOWNERS File**: Generates CODEOWNERS file from git config or provided username
5. **SECURITY.md File**: Generates security policy template

**Script**: `../../scripts/finalize_github_repo.py`

**Options:**
- `--package-type` - Type of package (plugin, skill, mcp, library, tool)
- `--release-version` - Version for initial release (default: 0.1.0)
- `--username` - GitHub username for CODEOWNERS
- `--skip-pages` - Skip GitHub Pages enablement
- `--skip-release` - Skip initial release creation
- `--skip-topics` - Skip adding repository topics
- `--skip-codeowners` - Skip CODEOWNERS file generation
- `--skip-security` - Skip SECURITY.md generation
