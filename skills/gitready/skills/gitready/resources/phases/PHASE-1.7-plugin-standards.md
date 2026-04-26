# PHASE 1.7: Plugin Standards Validation

**Objective**: Validate existing files/folders against OFFICIAL Claude Code plugin standards and provide CRUD recommendations.

**When**: Automatically runs after PHASE 1.5 (Detect Package Type) completes, for ALL plugin package types.

**What this does**:
- Scans root directory for files/folders
- Compares against OFFICIAL plugin-dev:plugin-structure standards
- Identifies non-standard files that violate plugin conventions
- Provides CRUD recommendations (Create, Update, Delete)
- Offers auto-cleanup with confirmation
- **NO ARGUMENTS REQUIRED** - runs automatically

**Standards Source** (live, dynamic):
```
/plugin-dev:plugin-structure
```

Invoke the skill and capture its authoritative output, then diff against the target directory.

**⚠️ CRITICAL CORRECTION FROM v5.26.0**:
- ❌ **WRONG**: `core/` directory is NOT in official spec
- ✅ **CORRECT**: Python code in `scripts/` or component directories
- ✅ **CORRECT**: Components at ROOT level (not nested in `.claude-plugin/`)
- ✅ **CORRECT**: Dynamic invocation keeps validation in sync with official spec

**Required Directories**:
- **`.claude-plugin/`** - Plugin metadata (contains ONLY `plugin.json`)
- **Component dirs at ROOT** - `commands/`, `agents/`, `skills/`, `hooks/` (NOT nested in `.claude-plugin/`)

**Optional Directories** (created as needed):
- **`commands/`** - Slash commands (.md files)
- **`agents/`** - Subagent definitions (.md files)
- **`skills/`** - Agent skills (subdirectories with `SKILL.md`)
- **`hooks/`** - Hook configuration (`hooks.json`)
- **`scripts/`** - Helper scripts and utilities

**Required Files** (root):
- **`README.md`** - Portfolio documentation
- **`LICENSE`** - License file

**Optional Files** (root):
- **`CHANGELOG.md`** - Version history
- **`AGENTS.md`** - AI-maintainable documentation
- **`CONTRIBUTING.md`** - Contribution guidelines
- **`.gitignore`** - Version control exclusions

**FORBIDDEN Files** (violate plugin standards):
- **`pyproject.toml`** - Plugins don't use pip packaging
- **`setup.py`** - Plugins don't use pip packaging
- **`setup.cfg`** - Plugins don't use pip packaging
- **`core/`** directory - NOT in official plugin structure
- **`src/`** directory - Use appropriate component directories instead

### Detection Logic

```bash
# Scan root directory
cd {{TARGET_DIR}}
ROOT_ITEMS=$(find . -maxdepth 1 -type d ! -name ".*" ! -name "." | sort)
ROOT_FILES=$(find . -maxdepth 1 -type f ! -name ".*" | sort)

# Check for forbidden files
FORBIDDEN=""
if [ -f "pyproject.toml" ]; then
    FORBIDDEN="$FORBIDDEN\n❌ DELETE: pyproject.toml (plugins don't need pip packaging)"
fi
if [ -d "src" ]; then
    FORBIDDEN="$FORBIDDEN\n❌ DELETE/MIGRATE: src/ (use core/ for plugins)"
fi

# Check for non-standard files (artifact patterns)
TEMP_FILES=$(find . -maxdepth 1 -name "*SUMMARY*.md" -o -name "*REPORT*.md" -o -name "*CHECKLIST*.md" -o -name "*AUDIT*.md" -o -name "*TREE*.txt" -o -name "README_*.md" 2>/dev/null)
if [ -n "$TEMP_FILES" ]; then
    FORBIDDEN="$FORBIDDEN\n⚠️  MOVE TO docs/: Temporary documentation artifacts"
fi

# Check for test scripts in root
TEST_SCRIPTS=$(find . -maxdepth 1 -name "test_*.py" -o -name "verify_*.py" -o -name "analyze_*.py" -o -name "diagnose_*.py" 2>/dev/null)
if [ -n "$TEST_SCRIPTS" ]; then
    FORBIDDEN="$FORBIDDEN\n⚠️  MOVE TO tests/: Standalone test scripts"
fi

echo "$FORBIDDEN"
```

### CRUD Recommendations

**DELETE** (violates plugin standards):
- `pyproject.toml`, `setup.py`, `setup.cfg` - Plugins don't use pip
- `src/` directory - Wrong structure, use `core/`
- `*.backup`, `*.old`, `*.bak` - Backup files
- `test_*.py`, `verify_*.py`, `analyze_*.py` - Temporary test scripts
- `*SUMMARY*.md`, `*REPORT*.md`, `*CHECKLIST*.md` - Temporary documentation
- `*TREE*.txt`, `README_NEW.md` - Diagnostic artifacts
- `.coverage`, `coverage.json` - Generated coverage files

**MOVE TO `docs/`** (historical context, not root clutter):
- `*_STRUCTURE.md`, `*_AUDIT*.md`, `*_VALIDATION*.md`
- `*_BREAKDOWN*.md`, `*_FIX*.md`, `*_DATA*.md`
- `*_IMPLEMENTATION*.md`, `*_PHASE*.md`

**MOVE TO `tests/`** (test suite organization):
- `test_*.py` (if useful tests)
- `verify_*.py` (if verification scripts)
- Review bundles, test fixtures

**KEEP IN ROOT** (standard plugin files):
- `README.md`, `LICENSE`, `CHANGELOG.md`
- `AGENTS.md`, `CONTRIBUTING.md`, `.gitignore`

### Auto-Cleanup Script

```bash
#!/bin/bash
# Auto-cleanup non-standard plugin files

# Create docs/ if needed
mkdir -p docs tests/fixtures

# Delete forbidden files
rm -f pyproject.toml setup.py setup.cfg
rm -f *.backup *.old *.bak
rm -f *SUMMARY*.md *REPORT*.md *CHECKLIST*.md *AUDIT*.md
rm -f *TREE*.txt README_NEW.md
rm -f test_*.py verify_*.py analyze_*.py diagnose_*.py
rm -f .coverage coverage.json

# Move documentation to docs/
mv *_STRUCTURE.md docs/ 2>/dev/null || true
mv *_AUDIT*.md docs/ 2>/dev/null || true
mv *_VALIDATION*.md docs/ 2>/dev/null || true
mv *_DATA*.md docs/ 2>/dev/null || true
mv *_IMPLEMENTATION*.md docs/ 2>/dev/null || true
mv *_PHASE*.md docs/ 2>/dev/null || true
mv review_bundle_*.md tests/fixtures/ 2>/dev/null || true

echo "✓ Cleanup complete"
echo "  Deleted: $(grep -c "DELETE" <<<$FORBIDDEN) forbidden files"
echo "  Moved: $(grep -c "MOVE" <<<$FORBIDDEN) files to appropriate directories"
```

### Output Format

**PLUGIN_STANDARDS_REPORT.md**:
```markdown
# Plugin Standards Validation Report

## Package Type: claude-plugin
## Compliance Score: 85/100

### ✅ Standards Compliant
- .claude-plugin/ exists
- core/ directory present
- hooks/ configuration present
- README.md with badges

### ❌ Standards Violations (5 items)
- **DELETE**: pyproject.toml (plugins don't need pip packaging)
- **MOVE TO docs/**: HANDOFF_QUALITY_CHECKLIST.md (7 files)
- **MOVE TO tests/**: test_handoff_save_direct.py (2 files)
- **DELETE**: pre-pack-tree.txt (diagnostic artifact)

### 🚀 Auto-Cleanup Available
Run this command to auto-fix all violations:
```bash
cd P:/packages/handoff && bash cleanup_plugin_standards.sh
```

### 📋 Manual Cleanup Required
None - all violations can be auto-fixed.
```

### hooks.json Validation (Auto-invoked when hooks/ exists)

**Objective**: Ensure `hooks/hooks.json` entries match actual hook Python files in the plugin.

**Why this matters**: hooks.json drifts from actual hook files over time. New hooks get added as `.py` files but never registered. Old hooks get removed but entries remain stale. During brownfield conversion, paths may still reference old `src/` locations.

#### Detection Logic

```bash
cd {{TARGET_DIR}}

# Step 1: Extract hook file paths from hooks.json
if [ -f "hooks/hooks.json" ]; then
    REGISTERED_PATHS=$(python3 -c "
import json, sys
try:
    data = json.load(open('hooks/hooks.json'))
    paths = []
    for event_name, matchers in data.items():
        if isinstance(matchers, list):
            for matcher in matchers:
                hooks = matcher.get('hooks', []) if isinstance(matcher, dict) else []
                for hook in hooks:
                    cmd = hook.get('command', '')
                    # Extract the file path from commands like: python \"\$CLAUDE_PLUGIN_ROOT/scripts/hooks/X.py\"
                    import re
                    match = re.search(r'CLAUDE_PLUGIN_ROOT/(scripts/hooks/[^\s\"]+\.py)', cmd)
                    if match:
                        paths.append(match.group(1))
                    else:
                        # Bare path without CLAUDE_PLUGIN_ROOT
                        match2 = re.search(r'([\w/]+\.py)', cmd)
                        if match2 and 'hooks/' in match2.group(1):
                            paths.append(match2.group(1))
    for p in sorted(set(paths)):
        print(p)
except Exception as e:
    print(f'ERROR: {e}', file=sys.stderr)
    sys.exit(1)
")

    # Step 2: Find actual hook .py files (excluding __lib/ and __init__.py)
    ACTUAL_HOOKS=$(find scripts/hooks -maxdepth 1 -name "*.py" ! -name "__init__.py" ! -name "__lib*" 2>/dev/null | sort)

    # Step 3: Compare
    echo "=== hooks.json Validation ==="
    echo ""
    echo "Registered in hooks.json:"
    echo "$REGISTERED_PATHS" | while read path; do
        if [ -f "$path" ]; then
            echo "  ✓ $path"
        else
            echo "  ❌ STALE: $path (file does not exist)"
        fi
    done

    echo ""
    echo "Hook files not registered in hooks.json:"
    for actual in $ACTUAL_HOOKS; do
        basename=$(basename "$actual")
        if ! echo "$REGISTERED_PATHS" | grep -q "$basename"; then
            echo "  ⚠️  MISSING ENTRY: $actual"
        fi
    done

    # Step 4: Brownfield path check
    echo ""
    echo "Brownfield path validation:"
    if echo "$REGISTERED_PATHS" | grep -q "src/hooks/"; then
        echo "  ❌ STALE PATH: hooks.json references src/hooks/ (should be scripts/hooks/ after brownfield conversion)"
    else
        echo "  ✓ No stale src/ paths detected"
    fi
else
    echo "No hooks/hooks.json found — skipping hooks.json validation"
fi
```

#### What Gets Checked

| Check | What it catches | Severity |
|-------|-----------------|----------|
| Stale entry | hooks.json references `.py` file that doesn't exist | ❌ HIGH |
| Missing entry | `.py` hook file exists but isn't in hooks.json | ⚠️ MEDIUM |
| Brownfield path | hooks.json references `src/hooks/` instead of `scripts/hooks/` | ❌ HIGH |
| Empty hooks.json | hooks.json has event arrays but all are empty `[]` | ℹ️ INFO |

#### Auto-Fix for Missing Entries

When hook files are found that aren't registered in hooks.json, offer to add them:

```bash
# For each unregistered hook file, determine its event from the filename:
# PreCompact_*.py → "PreCompact" event
# SessionStart_*.py → "SessionStart" event
# UserPromptSubmit_*.py → "UserPromptSubmit" event
# PostToolUse_*.py → "PostToolUse" event
# PreToolUse_*.py → "PreToolUse" event

# Auto-generate the entry:
python3 -c "
import json, re, os

hooks_file = 'hooks/hooks.json'
data = json.load(open(hooks_file))

# Map filename prefix to event name
EVENT_MAP = {
    'PreCompact': 'PreCompact',
    'SessionStart': 'SessionStart',
    'UserPromptSubmit': 'UserPromptSubmit',
    'PostToolUse': 'PostToolUse',
    'PreToolUse': 'PreToolUse',
    'ToolResponseReceived': 'ToolResponseReceived',
    'Stop': 'Stop',
}

for hook_file in UNREGISTERED_FILES:
    basename = os.path.basename(hook_file)
    prefix = basename.split('_')[0]
    event = EVENT_MAP.get(prefix)
    if not event:
        print(f'Cannot determine event for {basename} — add manually')
        continue

    entry = {
        'matcher': '.*',
        'hooks': [{
            'type': 'command',
            'command': f'python \"\$CLAUDE_PLUGIN_ROOT/scripts/hooks/{basename}\"'
        }]
    }

    if event not in data:
        data[event] = []
    data[event].append(entry)
    print(f'Added {basename} to {event}')

with open(hooks_file, 'w') as f:
    json.dump(data, f, indent=2)
"
```

**Integration**: Runs automatically after package type detection, before structure building. Can be invoked standalone with `/gitready --check-standards`.
