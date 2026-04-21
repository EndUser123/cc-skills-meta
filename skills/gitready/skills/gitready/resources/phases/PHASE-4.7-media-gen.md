# PHASE 4.7: Media Generation (Auto-invoked) — NEW

**Objective**: Generate professional portfolio assets (banners, diagrams, videos) for GitHub showcase.

**When**: Automatically runs after PHASE 4.5 (Code Review) completes, before PHASE 5 (Portfolio Polish).

**What this does:**
- Generates visual assets for portfolio-quality packages
- Creates banner images for GitHub social preview
- Builds static overview images plus GitHub-safe Mermaid flowcharts
- Produces one concise technical explainer video focused on architecture, workflow, and outputs
- Creates a dedicated HTML video player page for GitHub Pages playback
- Verifies asset quality with vision API before acceptance

**Generated Assets:**

| Asset | Purpose | Tools (recommended first) | Time | Output Formats |
|-------|---------|---------------------------|------|---------------|
| **Banner** | GitHub social preview (1200×630) | OpenRouter (DALL-E 3), Midjourney, Stable Diffusion, PIL (manual) | ~30s | `assets/banners/{package}_banner.png` |
| **Architecture overview image** | Visual system overview | NotebookLM, DALL-E 3, Mermaid → PNG, PlantUML, Graphviz | ~2min | `assets/infographics/{package}_architecture.png` |
| **System overview flowchart** | GitHub-safe architecture view | Mermaid, PlantUML, Graphviz DOT, draw.io | ~1min | `docs/diagrams/system_overview.mmd` |
| **Workflow flowchart** | Phase-by-phase pipeline view | Mermaid, PlantUML, Graphviz DOT | ~1min | `docs/diagrams/workflow.mmd` |
| **Explainer video** | AI-narrated technical walkthrough | NotebookLM, Luma Dream Machine, Runway Gen-3, HeyGen | ~1-3min target | `assets/videos/{package}_explainer_pbs.mp4` |
| **Slide deck** | Interactive presentation | NotebookLM, Marp, Pandoc, PowerPoint | ~2min | `assets/slides/{package}_slides.pdf` |
| **Video player page** | Browser playback via GitHub Pages | Static HTML, GitHub default (no player) | ~30s | `docs/video.html` |

**Tool selection notes:**
- **NotebookLM**: Best for comprehensive assets (infographics + videos + slides) from source code analysis
- **OpenRouter/DALL-E 3**: Best for branded banner generation with text rendering
- **Mermaid**: Best for code-as-diagram flowcharts that render directly in GitHub
- **PIL (Python Imaging Library)**: Manual fallback for simple gradient/text banners
- **Marp**: Markdown-based slide deck alternative with GitHub rendering
- **PlantUML**: Alternative to Mermaid for UML-specific diagrams

**Auto-skip conditions:**
- No README images detected (`.gif`, `.png` in README)
- User explicitly opts out with `--skip media`

**Provider requirements:**
- **NotebookLM**: `uv tool install notebooklm-mcp-cli` (v0.4.4+) + `nlm login`
- **visual-explainer:generate-web-diagram**: Installed via `/universal-skills-manager` or ClawHub
- **OpenRouter**: `OPENROUTER_API_KEY` environment variable (for banner generation, optional)

**If providers missing:**
- Check provider status and display clear setup instructions
- Skip assets that require unavailable providers
- Continue with available assets only

**Execution flow:**
```
Provider detection → Review bundle generation → Video brief generation → Multi-source upload (brief + review bundle + source files) → Asset generation (NotebookLM + video page) → Quality verification → Notebook cleanup
```

**Asset generation via nlm CLI (v0.4.4+):**

```bash
# After uploading sources to notebook, generate artifacts:
NOTEBOOK_ID="<your-notebook-id>"

# Create architecture diagram (infographic)
nlm infographic create "$NOTEBOOK_ID" --orientation landscape --detail standard --style professional --confirm

# Create explainer video
# Prefer a concise technical walkthrough, not a broad marketing script.
nlm video create "$NOTEBOOK_ID" --format explainer --style documentary --confirm

# Create slide deck
nlm slides create "$NOTEBOOK_ID" --slide-format detailed_deck --confirm

# Poll for completion (background task recommended)
nlm studio status "$NOTEBOOK_ID"

# Download completed artifacts
nlm download infographic "$NOTEBOOK_ID" --id "$ARTIFACT_ID" --output assets/infographics/{package}_notebooklm.png
nlm download video "$NOTEBOOK_ID" --id "$ARTIFACT_ID" --output assets/videos/{package}_explainer.mp4
nlm download slide-deck "$NOTEBOOK_ID" --id "$ARTIFACT_ID" --output assets/slides/{package}_slides.pdf
```

### Multi-Source Upload Strategy

**Why multiple sources matter:**
- Single README uploads produce generic assets lacking technical depth
- Review bundle provides architectural context and design intent
- Multiple source files provide NotebookLM with complete implementation details
- Better source material → More accurate, detailed, and professional assets
- Code examples, tests, and documentation improve asset quality significantly

**Hybrid approach (BEST): Review bundle + source files**

**Why this works better:**
- **Review bundle** = Executive summary with architecture, design intent, and component relationships
- **Source files** = Implementation details, concrete code examples, and actual behavior
- **Combined** = High-level understanding + low-level evidence = Best artifacts

**Source file identification:**

```bash
# Step 1: Generate review bundle (architectural context)
/review_bundle {{TARGET_DIR}}

# Step 2: Find all relevant source files (excludes cache, build artifacts, venv, templates)
cd {{TARGET_DIR}}

# CRITICAL: Upload actual IMPLEMENTATION FILES, not just documentation
# Core package structure MUST be included:
# - Python source files (*.py) - the actual implementation
# - Plugin metadata (.claude-plugin/plugin.json, hooks/hooks.json)
# - Core configuration files
# - Tests
# - Key documentation (README, skill docs)

# EXCLUDE template/legal files:
# - CONTRIBUTING.md, SECURITY.md, LICENSE - generic templates
# - CHANGELOG.md - version history only
# - *-tree.txt - diagnostic output files
# - Cache, build artifacts, venv

# Priority files (upload these AFTER review bundle):
find . -type f \( -name "*.py" -o -name "SKILL.md" -o -name "plugin.json" -o -name "hooks.json" \) \
  ! -path "./.git/*" ! -path "./__pycache__/*" ! -path "./venv/*" \
  ! -path "./.pytest_cache/*" ! -path "./.ruff_cache/*" | sort
```

**⚠️ CRITICAL: Upload implementation, NOT just templates!**

The most common mistake is uploading only documentation files (README, CHANGELOG, etc.) without the actual Python source code. NotebookLM needs both:
1. **Architectural context** (review bundle) → What is this system and why does it exist?
2. **Implementation details** (source files) → How does it actually work?

**Priority upload order:**
1. **Review bundle** (generated via `/review_bundle`) - Architectural overview
2. **Core implementation** - `core/*.py`, `*.py` (the actual code)
3. **Plugin configuration** - `.claude-plugin/plugin.json`, `hooks/hooks.json`
4. **Tests** - `tests/*.py`
5. **Skill documentation** - `SKILL.md` (if exists)
6. **Key README** - README.md (package overview)
7. **Templates/guides** - Only if they explain IMPLEMENTATION details

**EXCLUSION patterns:**

**⚠️ QUICK CHECKLIST - Always exclude these:**
- ❌ Lock files: `package-lock.json`, `poetry.lock`, `requirements.lock`, `yarn.lock`, `Cargo.lock`
- ❌ Test outputs: `htmlcov/`, `coverage.xml`, `.coverage*`, `.pytest_cache/`
- ❌ Version control: `.git/`, `.gitignore`, `.gitattributes`
- ❌ Cache/build: `__pycache__/`, `*.pyc`, `build/`, `dist/`, `venv/`, `.venv/`
- ❌ Generic templates: `CONTRIBUTING.md`, `SECURITY.md`, `LICENSE`, `CHANGELOG.md`
- ❌ State/diagnostics: `*-tree.txt`, `.claude/state/`, `*.pid`
- ❌ Generated media: `assets/videos/*.mp4`, `assets/infographics/*.png`, `assets/slides/*`

---

**Version control & caches:**
- `.git/`, `.gitignore`, `.gitattributes` - Version control metadata
- `__pycache__/`, `*.pyc` - Python bytecode
- `.pytest_cache/`, `.ruff_cache/`, `.benchmarks/` - Tool caches

**State & diagnostics:**
- `.claude/state/`, `*.pid`, `state*.json` - Claude Code state files
- `*-tree.txt`, `pre-pack-tree.txt`, `post-pack-tree.txt` - Diagnostic outputs

**Build & artifacts:**
- `build/`, `dist/`, `*.egg-info/` - Build artifacts
- `venv/`, `.venv/` - Virtual environments

**Lock files (machine-generated dependency pinning):**
  - `package-lock.json` - npm/yarn lock files
  - `poetry.lock` - Poetry lock files
  - `requirements.lock`, `Pipfile.lock` - pip lock files
  - `yarn.lock`, `Cargo.lock`, `go.sum` - Other package manager locks

**IDE & temp files:**
- `.vscode/`, `.idea/`, `*.swp`, `*.swo` - IDE configuration
- `*.tmp`, `*.bak`, `*.backup`, `*.old` - Temporary/backup files

**Generic templates (NOT package-specific):**
- `CONTRIBUTING.md`, `SECURITY.md`, `LICENSE` - Generic legal/templates
- `CHANGELOG.md` - Version history only (doesn't explain implementation)

**Generated outputs (OUTPUTS, not inputs):**
- `assets/videos/*.mp4`, `assets/infographics/*.png` - Media OUTPUTS
- `assets/slides/*` - Presentation OUTPUTS
- **Test outputs (machine-generated test artifacts):**
  - `htmlcov/`, `coverage.xml`, `.coverage*`, `.coverage.*` - Coverage reports
  - `.pytest_cache/` - Pytest cache
  - `test-results/`, `junit.xml` - Test result files
  - `.hypothesis/`, `.mypy_cache/` - Tool caches

**Binary artifacts:**
- `*.so`, `*.pyd`, `*.dll`, `*.exe` - Compiled binaries
- `*.zip`, `*.tar.gz`, `*.rar` - Compressed archives

**Upload process:**

```bash
# === STEP 1: Generate review bundle (architectural context) ===
echo "Generating review bundle for architectural context..."
Skill(skill="review_bundle", args="{{TARGET_DIR}}")

# Find the generated review bundle
REVIEW_BUNDLE=$(ls -t P:/__csf/.staging/review_bundle_*.md 2>/dev/null | head -1)
if [ -z "$REVIEW_BUNDLE" ]; then
  echo "⚠️  Warning: Review bundle not found, continuing without it"
else
  echo "✓ Review bundle generated: $REVIEW_BUNDLE"
fi

# === STEP 2: Create NotebookLM notebook with clear temporary naming ===
TEMP_NOTEBOOK_NAME="TEMP: {{package_name}} Media Generation [$(date +%Y%m%d_%H%M%S)]"
nlm notebook create "$TEMP_NOTEBOOK_NAME"
NOTEBOOK_ID=$(nlm notebook list | grep "$TEMP_NOTEBOOK_NAME" | head -1 | awk '{print $1}')

if [ -z "$NOTEBOOK_ID" ]; then
  echo "❌ Error: Failed to create notebook"
  exit 1
fi

echo "✓ Notebook created: $NOTEBOOK_ID"

# === STEP 3: Upload review bundle FIRST (architectural overview) ===
if [ -n "$REVIEW_BUNDLE" ] && [ -f "$REVIEW_BUNDLE" ]; then
  echo "Uploading review bundle..."
  timeout 60 nlm source add "$NOTEBOOK_ID" --file "$REVIEW_BUNDLE" --wait
  echo "✓ Review bundle uploaded"
fi

# === STEP 3.5: Upload a narration brief to control tone and length ===
cat > /tmp/video_brief.md <<'EOF'
# Video Brief

Create a concise technical explainer video for engineers evaluating this package.

Requirements:
- Tone: technical, calm, direct, low-hype
- Audience: developers, maintainers, technical reviewers
- Length target: 60 to 120 seconds
- Focus on:
  1. what the package does
  2. how the workflow operates
  3. what files and outputs it creates
  4. why the result is useful in practice
- Prefer concrete nouns and file paths over abstract claims
- Avoid marketing language, rhetorical questions, and dramatic setup
- Avoid extended "before/after pain" storytelling
- Avoid filler such as "imagine", "revolutionary", "seamless", "game-changing"
- End with a brief technical summary, not a call-to-action
EOF

timeout 60 nlm source add "$NOTEBOOK_ID" --file /tmp/video_brief.md --wait
echo "✓ Video brief uploaded"

# === STEP 4: Upload source files (implementation details) ===
# CRITICAL: Upload IMPLEMENTATION files FIRST, not just documentation!
# Priority: *.py > plugin.json > hooks.json > SKILL.md > README.md
#
# EXCLUDE (see QUICK CHECKLIST above):
# - Lock files: package-lock.json, poetry.lock, requirements.lock
# - Test outputs: htmlcov/, coverage.xml, .coverage*
# - Version control: .git/
# - Cache/build: __pycache__/, venv/, build/, dist/
# - Generic templates: CONTRIBUTING.md, SECURITY.md, LICENSE
# - State/diagnostics: *-tree.txt
# - Generated media: assets/videos/, assets/infographics/, assets/slides/

echo "Uploading source files..."
find . -type f \( -name "*.py" -o -name "*.json" -o -name "SKILL.md" -o -name "README.md" \) \
  ! -path "./.git/*" \
  ! -path "./__pycache__/*" \
  ! -path "./venv/*" \
  ! -path "./.venv/*" \
  ! -path "./.pytest_cache/*" \
  ! -path "./.ruff_cache/*" \
  ! -path "./.benchmarks/*" \
  ! -path "./build/*" \
  ! -path "./dist/*" \
  ! -path "./.eggs/*" \
  ! -path "./htmlcov/*" \
  ! -path "./assets/videos/*" \
  ! -path "./assets/infographics/*" \
  ! -path "./assets/slides/*" \
  ! -name "package-lock.json" \
  ! -name "poetry.lock" \
  ! -name "requirements.lock" \
  ! -name "yarn.lock" \
  ! -name "Cargo.lock" \
  ! -name "*.egg-info/*" \
  ! -name "*-tree.txt" \
  ! -name ".coverage*" \
  ! -name "coverage.xml" \
  ! -name "junit.xml" | head -30 | \
  while read file; do
    echo "Uploading: $file"
    timeout 60 nlm source add "$NOTEBOOK_ID" --text "$(cat "$file")" --title "$(basename "$file")" --wait
  done

# === STEP 5: Upload key documentation (if not already included) ===
if [ -f "README.md" ]; then
  timeout 60 nlm source add "$NOTEBOOK_ID" --file README.md --wait 2>/dev/null || true
fi

# === STEP 6: Verify all sources uploaded ===
echo ""
echo "=== Sources uploaded to notebook $NOTEBOOK_ID ==="
nlm source list "$NOTEBOOK_ID"
echo ""

# === STEP 7: NOW generate assets (only after ALL uploads complete) ===
echo "Starting asset generation..."
```


### Video Compliance Verification & Regeneration (Option B Pipeline)

**Objective**: Verify generated videos comply with technical writing standards and regenerate non-compliant videos using Option B (Script → TTS → ffmpeg).

**When**: Automatically runs after video download (NotebookLM generation completes).

**Why this matters**: NotebookLM videos often contain casual language ("cool", "awesome", "super") even with technical briefs. Option B provides full control over compliance with faster iteration than regenerating via NotebookLM.

**Compliance standards**:
- **Absolutely forbidden**: "cool", "awesome", "super", "amazing", "ultra", "mega", "neat", "nifty", "handy", "sweet", "sick", "dope", "fire"
- **Marketing hype**: "game-changing", "revolutionary", "seamless", "transformative"
- **Anti-patterns**: "imagine", "picture this", "envision"

**Verification workflow with faster-whisper**:

```bash
# Step 1: Install faster-whisper if not available
pip install faster-whisper

# Step 2: Transcribe and verify video compliance
python << 'VERIFY_EOF'
from faster_whisper import WhisperModel
import json
import re

FORBIDDEN_PATTERNS = [
    r'\bsuper\b', r'\bcool\b', r'\bawesome\b', r'\bamazing\b',
    r'\bultra\b', r'\bmega\b', r'\bneat\b', r'\bnifty\b',
    r'\bhandy\b', r'\bsweet\b', r'\bsick\b', r'\bdope\b',
    r'\bfire\b', r'\bgame.?changing\b', r'\brevolutionary\b',
    r'\bseamless\b', r'\btransformative\b', r'\bimagine\b',
    r'\bpicture this\b', r'\benvision\b'
]

def check_compliance(text):
    violations = []
    text_lower = text.lower()
    for pattern in FORBIDDEN_PATTERNS:
        matches = re.finditer(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            violations.append({
                'word': match.group(),
                'position': match.start(),
                'context': text[max(0, match.start()-30):min(len(text), match.end()+30)]
            })
    return violations

# Transcribe
model = WhisperModel("base", device="cpu", compute_type="int8")
segments, info = model.transcribe("assets/videos/{package}_explainer.mp4", beam_size=5)

# Check violations
all_violations = []
for segment in segments:
    violations = check_compliance(segment.text.strip())
    for v in violations:
        all_violations.append({**v, 'time': f"{segment.start:.1f}-{segment.end:.1f}s"})

# Save transcript with violations
with open('assets/videos/{package}_transcript.json', 'w') as f:
    json.dump({'violations': all_violations, 'count': len(all_violations)}, f)

# Report
if all_violations:
    print(f"❌ FAILED: {len(all_violations)} violations found")
    exit(1)
else:
    print("✅ PASSED: No forbidden words")
    exit(0)
VERIFY_EOF
```

**Option B regeneration pipeline** (if violations found):

```bash
# Step 1: Generate compliant script (no forbidden words)
cat > assets/scripts/{package}_compliant_script.txt << 'SCRIPT_EOF'
[Write technical script without forbidden words]
SCRIPT_EOF

# Step 2: Install free TTS (edge-tts)
pip install edge-tts

# Step 3: Generate compliant audio
edge-tts --file assets/scripts/{package}_compliant_script.txt \
  --write-media assets/audio/{package}_compliant_audio.mp3

# Step 4: Replace audio track using ffmpeg
ffmpeg -i assets/videos/{package}_explainer.mp4 \
  -i assets/audio/{package}_compliant_audio.mp3 \
  -c:v copy -map 0:v:0 -map 1:a:0 -shortest \
  assets/videos/{package}_compliant.mp4 -y

# Step 5: Re-verify compliance
# Run faster-whisper verification again on compliant video
```

**Decision factors**:
- **Speed**: Option B (2-3 minutes) vs NotebookLM regeneration (5-10 minutes + uncertain)
- **Control**: Full script control vs AI generation variability
- **Cost**: Free (edge-tts) vs NotebookLM credits
- **Iteration**: Script changes are instant vs re-uploading sources to NotebookLM

**Duration**: ~3-5 minutes for full verification + regeneration (if needed)

**Output**:
- `assets/videos/{package}_transcript.json` - Transcript with violation markers
- `assets/videos/{package}_compliant.mp4` - Compliant video (0 violations)
- Verification report with violation count and locations

**Integration**: Runs automatically after video download, before notebook cleanup



**Notebook cleanup after asset generation:**

```bash
# ⚠️  SAFETY: This cleanup is OPTIONAL and MANUAL
# Review the matched notebook ID before running to ensure it's the correct one

# After generating all assets, you can clean up the temporary notebook
# Step 1: List all notebooks to see what exists
echo "Current notebooks:"
nlm notebook list

# Step 2: Find the temporary notebook by name pattern
NOTEBOOK_ID=$(nlm notebook list | grep "TEMP: {{package_name}} Media Generation" | head -1 | awk '{print $1}')

# Step 3: Show what would be deleted (SAFETY CHECK)
if [ -n "$NOTEBOOK_ID" ]; then
  echo "Found temporary notebook: $NOTEBOOK_ID"
  echo "This will ONLY delete notebooks matching: 'TEMP: {{package_name}} Media Generation'"
  read -p "Delete this temporary notebook? (y/N): " CONFIRM

  # Step 4: Delete only with explicit confirmation
  if [ "$CONFIRM" = "y" ] || [ "$CONFIRM" = "Y" ]; then
    if nlm notebook delete --id "$NOTEBOOK_ID" 2>/dev/null; then
      echo "✓ Deleted temporary notebook: $NOTEBOOK_ID"
    else
      echo "✗ Failed to delete notebook (may have been deleted already)"
      exit 1
    fi
  else
    echo "✗ Cleanup cancelled - notebook kept"
  fi
else
  echo "✓ No temporary notebooks found matching pattern"
fi
```

**Safety features**:
- **Confirmation prompt**: Requires explicit `y` before deletion
- **Pattern matching**: Only deletes notebooks with exact pattern match
- **Error handling**: Detects and reports deletion failures
- **Dry-run mode**: Shows what will be deleted before asking for confirmation

**⚠️ WARNING: Deletion is permanent**

**Before running cleanup**, verify:
1. **The notebook ID matches**: Check that `NOTEBOOK_ID` is the temporary notebook you just created
2. **No similar notebook names**: Ensure you don't have real notebooks with similar names
3. **Backup important data**: NotebookLM doesn't have undelete - export important notebooks first

**Risks mitigated by this approach**:
- ❌ **Overly broad grep pattern**: Fixed by exact pattern match + confirmation prompt
- ❌ **Silent failures**: Fixed by explicit error handling and exit codes
- ❌ **Wrong notebook deletion**: Fixed by dry-run mode + user confirmation
- ❌ **User confusion**: Fixed by clear "TEMP:" prefix + safety warnings

**Why use clearly named temp notebooks:**
- **Easy identification**: "TEMP: {package} Media Generation [timestamp]" makes it obvious these are temporary
- **Prevents clutter**: Don't leave generic "My Notebook" entries in your NotebookLM library
- **Safe cleanup**: Clear naming pattern ensures you only delete temp notebooks, not real ones
- **Debugging**: Timestamp helps identify which notebook belongs to which /package run

**Usage example - Typical cleanup session:**

```bash
# After running /package, you have a temporary notebook
# Let's clean it up

$ nlm notebook list
Notebooks:
abc123  TEMP: mylib Media Generation [20260310_131419]
def456  My Project Research
ghi789  Package Documentation

# Run the cleanup command
$ NOTEBOOK_ID=$(nlm notebook list | grep "TEMP: mylib Media Generation" | head -1 | awk '{print $1}')
$ echo "Current notebooks:"
$ nlm notebook list
Notebooks:
abc123  TEMP: mylib Media Generation [20260310_131419]
def456  My Project Research
ghi789  Package Documentation

$ echo "Found temporary notebook: abc123"
Found temporary notebook: abc123

$ echo "This will ONLY delete notebooks matching: 'TEMP: mylib Media Generation'"
This will ONLY delete notebooks matching: 'TEMP: mylib Media Generation'

$ read -p "Delete this temporary notebook? (y/N): " CONFIRM
Delete this temporary notebook? (y/N): y

$ if nlm notebook delete --id "abc123" 2>/dev/null; then
>   echo "✓ Deleted temporary notebook: abc123"
> else
>   echo "✗ Failed to delete notebook (may have been deleted already)"
>   exit 1
> fi
✓ Deleted temporary notebook: abc123

$ nlm notebook list
Notebooks:
def456  My Project Research
ghi789  Package Documentation
```

**Troubleshooting - Common cleanup issues:**

**Issue 1: "NOTEBOOK_ID is empty"**
- **Cause**: No notebooks match the pattern (already deleted or never created)
- **Solution**: This is expected - no cleanup needed
- **Verify**: Run `nlm notebook list` to see current notebooks

**Issue 2: "Pattern doesn't match"**
- **Cause**: Package name in grep pattern doesn't match actual notebook name
- **Solution**: Use broader pattern or manually select notebook ID from list
- **Example**: `grep "TEMP: mylib"` instead of `grep "TEMP: mylib Media Generation"`

**Issue 3: "Multiple notebooks match"**
- **Cause**: Multiple /package runs created temp notebooks
- **Solution**: Review list and decide which to delete, or delete all that match
- **Safe approach**: Run cleanup multiple times, confirm each deletion individually

**Issue 4: "Permission denied" or "Deletion fails"**
- **Cause**: NotebookLM authentication issue or network problem
- **Solution**:
  1. Check `nlm` CLI is authenticated: `nlm auth status`
  2. Re-authenticate if needed: `nlm login`
  3. Verify network connectivity
  4. Try manual deletion via NotebookLM web interface

**Quality comparison:**

| Approach | Source Material | Asset Quality | Time |
|----------|----------------|---------------|------|
| **Single README** | 1 file | Generic, shallow | Fast (~30s upload) |
| **Multi-source** | 10-50 files | Accurate, detailed, professional | Medium (~2min upload) |
| **Review bundle only** | 1 comprehensive file | Good architecture, missing implementation details | Fast (~30s upload) |
| **Review bundle + source files** | 1 architecture doc + 10-50 files | **Best quality** - context + implementation | Medium (~2min total) |

**Recommended strategy:**
1. **Default**: Review bundle + source files (production assets)
   - Review bundle provides architectural overview and design intent
   - Source files provide implementation details and concrete examples
   - Best of both worlds: high-level understanding + low-level evidence
2. **Fast iteration**: Review bundle only for testing /package workflow
3. **Fallback**: Multi-source without review bundle if review_bundle skill unavailable
3. **Fallback**: Single README if sources unavailable (degraded quality)

**Recommended video structure:**
```
CONTEXT (10-15s): Name the package and its purpose in one sentence.
WORKFLOW (25-40s): Show how it detects type, generates structure, and validates outputs.
ARTIFACTS (20-30s): Call out the key outputs: docs, flowchart, video, slides.
SUMMARY (10-15s): Close with the practical result for a developer using the package.
```

**Avoid this anti-pattern:**
- long "problem/pain/agitate" intros
- generic business narration
- theatrical transitions
- repeating the same feature list in multiple ways
- durations over 2 minutes unless the user explicitly wants a deep dive

**Why the old approach was annoying:**
- PBS tends to produce sales-demo narration rather than technical explanation
- fixed long sections bias NotebookLM toward overlong scripts
- `auto_select` style makes tone unpredictable
- the result often sounds generic even when the source material is technical

**Quality verification:**

### Banner Validation (`validate_banner.py`)

After banner generation, automatically validate quality using `scripts/validate_banner.py`:

**Basic checks (always run):**
- File exists and readable
- Dimensions: 1200×630 (GitHub social preview standard)
- File size: 10KB - 500KB (reasonable range)
- Image not corrupted

**Vision analysis (requires `Z_AI_API_KEY`):**
- Text readability (contrast ratio ≥ 4.5:1)
- Package name visibility
- Professionalism assessment
- Visual appeal rating (1-10 scale)
- Specific issues + recommendations

**Usage:**
```bash
# Basic validation only
python scripts/validate_banner.py assets/banners/{package}_banner.png

# With Z.ai Vision API (requires Z_AI_API_KEY env var)
python scripts/validate_banner.py assets/banners/{package}_banner.png

# Exit with error if validation fails
python scripts/validate_banner.py assets/banners/{package}_banner.png --fail-on-issues
```

**Quality criteria:**
- **Excellent** (8-10): Ready for portfolio use
- **Good** (6-7): Acceptable, minor improvements possible
- **Needs improvement** (<6): Should regenerate before publishing

**Other asset verification:**
- Check assets contain package name
- Verify relevance to package purpose
- Validate formats (diagram, video, slides)
- Reject generic/wrong-format assets and retry

**Duration**: 5-10 minutes (depending on selected assets)

**Output**: Professional visual assets in `assets/` directory
- `assets/banners/{package}_banner.png`
- `assets/infographics/{package}_architecture.png`
- `assets/videos/{package}_explainer_pbs.mp4`
- `assets/slides/{package}_slides.pdf` (view and download as PDF)

**Rationale**: Media generation after code review ensures we're creating assets for quality code. Portfolio polish (PHASE 5) then references these visual assets in README.md.

---

## System Overview Diagrams (GitHub-First Mermaid)

**Objective**: Generate editable Mermaid architecture flowcharts that render cleanly on GitHub.

**When**: Runs automatically after NotebookLM media generation.

**What this does:**
- Creates plain Mermaid flowcharts for the README and optional supporting docs
- Generates a high-level system overview and workflow diagram
- Outputs source diagrams to `docs/diagrams/` for easy editing and git tracking
- Embeds the GitHub-safe overview directly in `README.md`

**GitHub compatibility rules (mandatory):**
- Target **GitHub's Mermaid renderer**, not Mermaid Live's broader feature set
- Prefer `graph TB` or `flowchart TB` system-overview diagrams for anything embedded in `README.md`
- Keep labels short and structural: phases, systems, outputs, decisions
- Do **not** use Mermaid C4 blocks (`C4Context`, `C4Container`, `C4Component`) in GitHub-facing README sections
- Do **not** emit `UpdateLayoutConfig(...)`, `include:`, or malformed init closers like `%%%`
- If technical C4 diagrams are still useful, keep them as optional secondary docs and verify they are not the primary README artifact

**Diagram types generated:**

| Diagram | Purpose | Output File | Style |
|---------|---------|-------------|-------|
| **System Overview** | High-level architecture and outputs | `docs/diagrams/system_overview.mmd` | Mermaid flowchart |
| **Workflow** | Phase-by-phase pipeline view | `docs/diagrams/workflow.mmd` | Mermaid flowchart |

**Why this style:**
- **Editable**: Text-based → easy to update alongside code
- **Version-controllable**: Track changes in git like code
- **Renderable**: GitHub renders basic Mermaid flowcharts more consistently than C4
- **Readable**: Better portfolio presentation for recruiters and repo visitors
- **Portable**: Same structure works in README, docs pages, and HTML wrappers

**Execution flow:**
```bash
# 1. Create diagrams directory
mkdir -p docs/diagrams

# 2. Generate GitHub-safe Mermaid flowcharts
# Prefer system_overview.mmd and workflow.mmd

# 3. Copy GitHub-compatible overview into README.md
```mermaid
graph TB
    Input[User: /{{package_name}}] --> Detect[Detect Package Type]
    Detect --> Type{Package Type?}
    Type -->|Plugin| Plugin[Plugin Structure]
    Type -->|Skill| Skill[Skill Structure]
    Type -->|Library| Library[Library Structure]
    Plugin --> Polish[Portfolio Polish]
    Skill --> Polish
    Library --> Polish
    Polish --> Docs[Documentation]
    Polish --> Media[Media Assets]
    Docs --> Output[GitHub-Ready Package]
    Media --> Output
```
```

**Duration**: ~1 minute (both flowcharts)

**Auto-skip conditions:**
- Mermaid diagrams already exist in `docs/diagrams/`
- User explicitly opts out with `--skip mermaid`

**Provider requirements:**
- **mermaid-diagrams skill**: Installed via `/universal-skills-manager` or ClawHub
- No API keys required (pure Mermaid syntax generation)

**Quality verification:**
- Check the README diagram is a plain Mermaid flowchart, not C4
- Verify relationships show the major phases, decisions, and outputs
- Validate Mermaid syntax renders correctly
- Scan `README.md` and `docs/diagrams/*.mmd` for banned patterns before finishing:
  - `C4Context`
  - `C4Container`
  - `C4Component`
  - `System_Bnd`
  - `Container_Bnd`
  - `Component_Bnd`
  - `UpdateLayoutConfig`
  - `include:`
  - `%%%`

**Comparison: Mermaid vs NotebookLM diagrams**

| Aspect | Mermaid Diagrams | NotebookLM Diagrams |
|--------|-----------------|---------------------|
| **Format** | Text (`.mmd` files) | Images (`.png`) |
| **Version control** | ✅ Git-diff friendly | ❌ Binary changes |
| **Editability** | ✅ Text editor | ❌ Regenerate only |
| **Renderers** | GitHub, VS Code, Mermaid Live | Image viewers |
| **Best for** | Technical documentation, architecture specs | Social preview, quick visuals |
| **Location** | `docs/diagrams/` | `assets/infographics/` |
| **Automation** | Auto-generated in /package | Auto-generated in /package |

**Both are generated automatically** by `/package` - each serves a different purpose.

---

## GitHub Pages Video Player

**Objective**: Generate a single-purpose HTML page for browser playback of the explainer video.

**When**: Runs after the explainer video is generated.

**What this does:**
- Creates `docs/video.html` as a lightweight HTML5 player page
- Keeps GitHub Pages focused on playback only
- Leaves architecture and workflow explanation on the main GitHub repository page

**Generated asset:**

| Asset | Purpose | Format | Output |
|-------|---------|--------|--------|
| **Video player page** | Browser playback for the README video link | HTML | `docs/video.html` |

**Integration with README.md:**

```markdown
[![Watch the demo with audio](assets/videos/{{package_name}}_video_poster.png)](https://{{github_username}}.github.io/{{package_name}}/docs/video.html)
```

**Rules:**
- Do not create extra GitHub Pages docs for architecture or workflow unless the user explicitly asks for a separate docs site
- Keep GitHub as the source of truth for technical documentation
- Use GitHub Pages only to solve the inline video playback limitation

---

## Code Flow Diagrams (On-Demand)

**For function-level visualization**, use `/code-flow-visualizer` separately:

```bash
# Visualize a specific function
/code-flow-visualizer path/to/file.py function_name

# Auto-detect main functions
/code-flow-visualizer path/to/file.py
```

**When to use:**
- Documenting complex algorithm logic
- Explaining code flow in pull requests
- Creating onboarding diagrams for new contributors
- Analyzing unfamiliar codebases

**Output:** Mermaid flowchart showing conditional branches, loops, and data flow

**Note:** Not automatically invoked by `/package` - use on-demand for specific files.

---

## GitHub Slide Deck Integration

**PDF Usage:**

| Format | Best For | GitHub Integration |
|--------|----------|-------------------|
| **PDF** | Primary viewing format on GitHub | `[View Slides (PDF)](assets/slides/{package}_slides.pdf)` |

**Recommended approach:**
1. Keep the published slide deck in `assets/slides/` as PDF
2. Make the PDF the first and most prominent slide link in `README.md`
3. Use a slide preview image that links directly to the PDF
4. Prefer this README pattern:
   `View Slides (PDF)`, then `Download PDF`

---
