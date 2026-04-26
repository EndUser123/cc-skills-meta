# Claude Code Plugin Standards — Authoritative Reference

**Source**: plugin-dev:plugin-structure (official Claude Code plugin documentation)
**Version**: 5.26.0
**Last Updated**: 2026-04-24

## ⚠️ CRITICAL CORRECTIONS

**Previous errors in v5.6.0**:
- ❌ **WRONG**: Claimed `core/` is required for Python code
- ❌ **WRONG**: Validated against handoff/search-research (custom implementations)
- ✅ **CORRECT**: Use official plugin-dev:plugin-structure documentation

## Authoritative Directory Structure

```
plugin-name/
├── .claude-plugin/          # Plugin metadata (REQUIRED)
│   └── plugin.json          # Plugin manifest
├── commands/                 # Slash commands (.md files)
├── agents/                   # Subagent definitions (.md files)
├── skills/                   # Agent skills (subdirectories)
│   └── skill-name/
│       └── SKILL.md         # Required for each skill
├── hooks/
│   └── hooks.json           # Event handler configuration
├── .mcp.json                # MCP server definitions
└── scripts/                 # Helper scripts and utilities
```

**CRITICAL RULES**:
1. **`.claude-plugin/`** contains ONLY `plugin.json` (not other components)
2. **Component locations**: All components at ROOT level (NOT nested in `.claude-plugin/`)
3. **Python code**: In appropriate component dirs or `scripts/` (NO `core/` directory required)
4. **Auto-discovery**: Components auto-discovered from root-level directories

## Required Components

### ✅ ALWAYS Required

- **`.claude-plugin/plugin.json`** - Plugin manifest with at minimum `name` field

### ✅ Required If Used

- **`commands/`** - If plugin has slash commands
- **`agents/`** - If plugin has subagents
- **`skills/`** - If plugin has skills
- **`hooks/hooks.json`** - If plugin has hooks
- **`.mcp.json`** - If plugin has MCP servers

## Plugin Manifest (plugin.json)

### Minimal Required Format

```json
{
  "name": "plugin-name"
}
```

**Name requirements**:
- Use kebab-case format (lowercase with hyphens)
- Must be unique across installed plugins
- Example: `code-review-assistant`, `test-runner`, `api-docs`

### Recommended Full Format

```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "description": "Brief explanation of plugin purpose",
  "author": {
    "name": "Author Name",
    "email": "author@example.com",
    "url": "https://example.com"
  },
  "homepage": "https://docs.example.com",
  "repository": "https://github.com/user/plugin-name",
  "license": "MIT",
  "keywords": ["testing", "automation", "ci-cd"]
}
```

### Custom Paths (Optional)

```json
{
  "name": "plugin-name",
  "commands": "./custom-commands",
  "agents": ["./agents", "./specialized-agents"],
  "hooks": "./config/hooks.json",
  "mcpServers": "./.mcp.json"
}
```

**Path rules**:
- Must be relative to plugin root
- Must start with `./`
- Custom paths SUPPLEMENT defaults (not replace)

## Python Code Organization

### ❌ FORBIDDEN Structure

```
❌ WRONG: core/ directory (not in official spec)
plugin-name/
├── core/
│   ├── __init__.py
│   └── module.py
```

### ✅ CORRECT Structures

**Option 1: Scripts directory**
```
plugin-name/
├── .claude-plugin/
│   └── plugin.json
├── scripts/
│   ├── __init__.py
│   └── module.py
```

**Option 2: In component directories**
```
plugin-name/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   └── my-skill/
│       ├── SKILL.md
│       ├── handlers.py
│       └── utils.py
```

**Option 3: Hooks with embedded scripts**
```
plugin-name/
├── .claude-plugin/
│   └── plugin.json
├── hooks/
│   ├── hooks.json
│   └── scripts/
│       ├── validator.py
│       └── processor.py
```

## Required Files (Root)

- **`README.md`** - Portfolio-quality documentation
- **`LICENSE`** - License file (MIT recommended)

## Optional Files (Root)

- **`CHANGELOG.md`** - Version history
- **`AGENTS.md`** - AI-maintainable documentation
- **`CONTRIBUTING.md`** - Contribution guidelines
- **`.gitignore`** - Version control exclusions

## ❌ FORBIDDEN Files (Violate Plugin Standards)

### DELETE These Files

- **`pyproject.toml`** - Plugins don't use pip packaging
- **`setup.py`** - Plugins don't use pip packaging
- **`setup.cfg`** - Plugins don't use pip packaging
- **`core/` directory** - NOT in official plugin structure

### ⚠️ MOVE TO `docs/` (Historical Context)

- **`*_STRUCTURE.md`** - Architecture documentation
- **`*_AUDIT*.md`** - Audit reports
- **`*_VALIDATION*.md`** - Validation reports
- **`*_DATA*.md`** - Data model documentation
- **`*_IMPLEMENTATION*.md`** - Implementation notes
- **`*_PHASE*.md`** - Phase summaries
- **`*_BREAKDOWN*.md`** - Breakdown documents
- **`*_FIX*.md`** - Fix documentation

### ⚠️ MOVE TO `tests/` (Test Suite)

- **`test_*.py`** - Test scripts (if useful)
- **`verify_*.py`** - Verification scripts
- **`analyze_*.py`** - Analysis scripts
- **`diagnose_*.py`** - Diagnostic scripts

### ❌ DELETE (Temporary Artifacts)

- **`*SUMMARY*.md`** - Summary documents
- **`*REPORT*.md`** - Report documents
- **`*CHECKLIST*.md`** - Checklist documents
- **`*TREE*.txt`** - Diagnostic tree output
- **`README_NEW.md`** - Draft README files
- **`*.backup`** - Backup files
- **`*.old`** - Old files
- **`*.bak`** - Backup files
- **`.coverage`** - Generated coverage
- **`coverage.json`** - Generated coverage reports

## CLAUDE_PLUGIN_ROOT Environment Variable

**Correct variable**: `${CLAUDE_PLUGIN_ROOT}` (not `$CLAUDE_PLUGIN_ROOT`)

**Usage in hooks**:
```json
{
  "PreToolUse": [{
    "hooks": [{
      "type": "command",
      "command": "bash ${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh"
    }]
  }]
}
```

**Usage in MCP servers**:
```json
{
  "mcpServers": {
    "server-name": {
      "command": "node",
      "args": ["${CLAUDE_PLUGIN_ROOT}/servers/server.js"]
    }
  }
}
```

**Never use**:
- Hardcoded absolute paths
- Relative paths without `${CLAUDE_PLUGIN_ROOT}`
- Home directory shortcuts (`~/plugins/...`)

## File Naming Conventions

### Component Files

- **Commands**: kebab-case `.md` files → `code-review.md` → `/code-review`
- **Agents**: kebab-case `.md` files → `test-generator.md`
- **Skills**: kebab-case directories → `api-testing/`
- **Scripts**: kebab-case with extensions → `validate-input.sh`

## Deployment Models

### 1. SKILLS (Dev Deployment) ⭐

**Setup**:
```powershell
# Windows (Junction)
New-Item -ItemType Junction -Path "P:\.claude\skills\plugin-name" -Target "P:\packages\plugin-name\skills\plugin-name"

# macOS/Linux (Symlink)
ln -s /path/to/packages/plugin-name/skills/plugin-name ~/.claude/skills/plugin-name
```

### 2. HOOKS (Dev Deployment)

**Setup**:
```powershell
cd P:/.claude/hooks
cmd /c "mklink HookName.py P:/packages/plugin-name/scripts/HookName.py"
```

### 3. PLUGINS (End User Deployment)

**Setup**:
```bash
/plugin P:/packages/plugin-name
```

## Validation Checklist

### ✅ Standards Compliant

- [ ] `.claude-plugin/` directory exists
- [ ] `.claude-plugin/plugin.json` exists with `name` field
- [ ] Component directories at ROOT level (not nested in `.claude-plugin/`)
- [ ] NO `core/` directory (not in official spec)
- [ ] NO `pyproject.toml` (plugins use different packaging)
- [ ] README.md exists with badges
- [ ] LICENSE file exists

### ⚠️ Common Violations

- [ ] `core/` directory → MOVE code to `scripts/` or component dirs
- [ ] `pyproject.toml` present → DELETE
- [ ] Components nested in `.claude-plugin/` → Move to root
- [ ] Temporary docs in root → MOVE to `docs/`

## Compliance Scoring

### Score Calculation

**100-90** (Excellent): All required elements present, no violations
**89-70** (Good): Required elements present, minor violations
**69-50** (Fair): Missing some required elements
**Below 50** (Poor): Major structure violations

## References

- **Primary Source**: plugin-dev:plugin-structure (official Claude Code plugin documentation)
- **Supporting Skills**: plugin-dev:plugin-settings, plugin-dev:create-plugin
- **Production Examples**: Plugins following official structure

---

**NOTE**: This is the authoritative reference based on official Claude Code plugin documentation from plugin-dev:plugin-structure. All plugin validation MUST use these standards.
