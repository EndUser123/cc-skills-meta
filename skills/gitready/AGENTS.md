# AGENTS.md - gitready Plugin

**For AI coding assistants (Claude, Copilot, etc.) working on this codebase.**

---

## Role & Persona

You are a senior software architect specializing in the **Claude Code Plugin ecosystem**. Your goal is to help maintain and extend the `gitready` plugin while adhering to its strict **"Skill-Based Logic" philosophy**.

---

## Critical Plugin Constraints

### Structure Philosophy

**ALL logic must reside in specialized directories:**
- `core/` — Python code (no `src/` directory)
- `hooks/` — Hook configuration (hooks.json)
- `skills/` — Auto-activating skills (SKILL.md files)
- `commands/` — Slash commands (.md files)

**DO NOT create:**
- ❌ `src/` directory (Python libraries use `src/`, plugins do NOT)
- ❌ `pyproject.toml` (plugins are not pip packages)
- ❌ Standard Python package structure

### Hooks: No Stderr Policy

**CRITICAL**: Claude Code treats ALL stderr output from hooks as fatal errors.

**Hook rules:**
- NEVER write to stderr in hook scripts
- Redirect errors to stdout or log files
- Use `print()` for output (stdout only)
- Use `sys.exit(0)` for success (not return codes > 0)

**Why this matters**: If your hook writes anything to stderr, the user's Claude Code session will crash with "hook error."

### Portability: CLAUDE_PLUGIN_ROOT

**All internal scripts MUST use `${CLAUDE_PLUGIN_ROOT}` environment variable.**

**Wrong:**
```python
path = "P:/packages/gitready/core/main.py"  # Hardcoded path
```

**Right:**
```python
import os
from pathlib import Path

plugin_root = Path(os.environ.get('CLAUDE_PLUGIN_ROOT'))
path = plugin_root / "core" / "main.py"
```

**Why**: Plugins can be installed in different locations (marketplace, local development, GitHub). Hardcoded paths break portability.

---

## Setup & Dev Commands

### Testing

```bash
# Run test suite
pytest tests/test_main.py -v

# Run with coverage
pytest tests/ --cov=core --cov-report=term-mvv
```

### Version Synchronization

```bash
# Sync version across all artifacts
python core/sync.py
```

**What this does:**
- Reads version from `core/__init__.py` (source of truth)
- Updates `.claude-plugin/plugin.json`
- Updates `README.md` version references
- Validates all changes

**When to run:** After ANY version bump in `core/__init__.py`

### Plugin Validation

```bash
# Test plugin locally (requires Claude Code CLI)
claude --plugin-dir .

# Or with plugin command
/plugin P:/packages/gitready
```

---

## Common Workflows

### Adding a New Skill

1. Create `skills/<skill-name>/SKILL.md`
2. Follow Claude Code skill format (imperative language, verification steps)
3. Test by invoking the skill
4. Update README if skill is user-facing

### Updating Hooks

1. Edit `hooks/hooks.json`
2. Ensure matchers are **specific enough** to avoid trigger bloat
3. **CRITICAL**: Never write to stderr in hook commands
4. Test hook triggers

### Version Bumps

1. Update `core/__init__.py`: `__version__ = "5.6.0"`
2. Run `python core/sync.py` (updates everything else)
3. Commit changes

### NotebookLM Media Generation

```bash
# Update NotebookLM sources with latest code
nlm source add --file core/main.py \
               --file .claude-plugin/plugin.json \
               --file README.md \
               --file AGENTS.md \
               --file P:/.claude/skills/package/SKILL.md

# Regenerate explainer video
nlm video create --notebook "github-ready-docs" --output assets/explainer.mp4

# Regenerate presentation slides
nlm pdf create --notebook "github-ready-docs" --output assets/slides.pdf
```

---

## Verification Guidelines

Before finishing ANY task, you MUST:

### 1. Version Consistency

- [ ] `core/__init__.py` version matches `.claude-plugin/plugin.json`
- [ ] `README.md` version references match `core/__init__.py`
- [ ] Run `python core/sync.py` if versions are out of sync

### 2. Diagram Validity

- [ ] No GitHub-incompatible Mermaid patterns: `System_Bnd`, `Container_Bnd`, `Component_Bnd`, `UpdateLayoutConfig`, `include:`, or `%%%`
- [ ] `README.md` uses a GitHub-safe Mermaid flowchart for the primary architecture view, not Mermaid C4 blocks
- [ ] Test Mermaid diagrams render with `mmdc` if it is installed

### 3. README Links

- [ ] All NotebookLM asset links are valid (check files exist)
- [ ] Interactive HTML diagram links work (`docs/*.html`)
- [ ] No broken image links

### 4. Hook Compliance

- [ ] Hook commands do NOT write to stderr
- [ ] All paths use `${CLAUDE_PLUGIN_ROOT}`
- [ ] Hook matchers are specific (not overly broad `. *` patterns)

### 5. Code Quality

- [ ] `ruff check` passes (no linting errors)
- [ ] `pytest tests/` passes (all tests green)
- [ ] Type hints included on all public functions

---

## Architecture Overview

### "Skill-Based Logic" Philosophy

**Core principle**: The plugin metadata is minimal. Actual package creation logic lives in the `/package` skill.

**Why this design:**
- Plugins provide metadata and trigger configuration
- Skills contain the workflow logic
- Separation of concerns (discovery vs. execution)

### Component Structure

```
gitready/
├── .claude-plugin/          # Plugin metadata
│   └── plugin.json          # Name, description, author
├── core/                    # Python code (NOT src/)
│   ├── __init__.py          # Version definition
│   ├── main.py              # Version retrieval API
│   └── sync.py              # Version synchronization
├── hooks/                   # Hook configuration
│   └── hooks.json           # Trigger patterns
├── skills/                  # Optional auto-activating skills
├── commands/                # Optional slash commands
├── tests/                   # Test suite
├── docs/                    # Documentation & diagrams
│   └── diagrams/           # C4 architecture diagrams
└── assets/                  # Generated media assets
    ├── infographics/
    ├── videos/
    └── slides/
```

---

## Non-Negotiable Design Principles

1. **Plugin structure is mandatory** — `.claude-plugin/`, `core/`, `hooks/` directories required
2. **Semantic versioning required** — Version must be MAJOR.MINOR.PATCH format
3. **No stderr in hooks** — Claude Code treats stderr as fatal errors
4. **CLAUDE_PLUGIN_ROOT usage** — All paths must use this env var for portability
5. **Three deployment models** — SKILLS (junction), HOOKS (symlinks), PLUGINS (/plugin command)

---

## Known Issues & Gotchas

### Issue: Version Mismatch

**Symptom**: README.md says v5.5.5, but `core/__init__.py` says v5.5.0

**Fix**: Run `python core/sync.py` to synchronize versions

**Prevention**: Always update `core/__init__.py` first, then run sync script

### Issue: Author Fields are Placeholders

**Symptom**: plugin.json contains "Your Name" and "your.email@example.com"

**Fix**: Manually edit `.claude-plugin/plugin.json` with real author info

**Note**: This is a one-time setup step, not automated

### Issue: Hooks Write to Stderr

**Symptom**: Claude Code session crashes with "hook error"

**Fix**: Remove ALL stderr writes from hook commands:
- Change `print("error", file=sys.stderr)` → `print("error")` (stdout)
- Change `sys.stderr.write()` → `sys.stdout.write()`
- Use `logging` with stream configuration if needed

### Issue: Hardcoded Paths Break Portability

**Symptom**: Plugin works on your machine but fails for others

**Fix**: Replace hardcoded paths with `${CLAUDE_PLUGIN_ROOT}`:
```python
import os
plugin_root = Path(os.environ.get('CLAUDE_PLUGIN_ROOT', '.'))
config_path = plugin_root / ".claude-plugin" / "plugin.json"
```

---

## Testing Strategy

### Unit Tests (tests/test_main.py)

- `test_get_version()` — Verify version retrieval works
- `test_version_format()` — Validate semantic versioning format

### Manual Verification

After any code changes:

```bash
# 1. Check version sync
python core/sync.py

# 2. Run linter
ruff check core/

# 3. Run tests
pytest tests/ -v

# 4. Verify plugin structure
ls -la .claude-plugin/ core/ hooks/
```

---

## Integration Points

### NotebookLM Integration

**Purpose**: Generate media assets (videos, diagrams, slides) for portfolio presentation

**Workflow:**
1. Upload source files: `nlm source add --file <path>`
2. Generate assets: `nlm video create`, `nlm pdf create`
3. Download artifacts: `nlm download`

**Key sources to upload:**
- `core/__init__.py` — Version definition
- `core/main.py` — Core logic
- `.claude-plugin/plugin.json` — Plugin metadata
- `README.md` — User documentation
- `AGENTS.md` — This file (AI agent instructions)
- `P:/.claude/skills/package/SKILL.md` — Skill logic (IMPORTANT)

**Note**: The SKILL.md file was previously NOT uploaded to NotebookLM (oversight). Include it for better context in generated media.

### /package Skill

**Location**: `P:/.claude/skills/package/SKILL.md`

**Relationship**: This plugin provides metadata for the `/package` skill

**Contract:**
- Plugin provides version, hooks, and structure
- `/package` skill contains workflow logic
- Skill uses plugin metadata during package creation

---

## Troubleshooting

### "Hook error" in Claude Code

**Cause**: Hook wrote to stderr

**Diagnosis**:
```bash
# Check hook script for stderr writes
grep -r "stderr" hooks/
grep -r "sys.stderr" core/
```

**Fix**: Replace all stderr writes with stdout

### Version mismatch after sync

**Cause**: Multiple version patterns in README not updated

**Diagnosis**:
```bash
grep -r "5\.[0-9]\.[0-9]" README.md
```

**Fix**: Run `python core/sync.py` again, or manually update remaining references

### Plugin not discovered by Claude Code

**Cause**: `.claude-plugin/plugin.json` is malformed or missing required fields

**Diagnosis**:
```bash
# Validate plugin.json syntax
python -m json.tool .claude-plugin/plugin.json
```

**Fix**: Ensure plugin.json has required fields: `name`, `description`, `author`

---

## Advanced Topics

### Adding MCP Server Integration

**When**: Plugin needs Model Context Protocol server

**Structure:**
- Add `.mcp.json` configuration file (NOT `mcp/` directory)
- Define server command and args in `.mcp.json`
- Update README with MCP usage instructions

**Example .mcp.json:**
```json
{
  "gitready": {
    "command": "python",
    "args": ["-m", "core.mcp.server"]
  }
}
```

### Creating Subagent Commands

**When**: Plugin needs AI-powered commands

**Structure:**
- Add `agents/` directory
- Create agent definitions (`.md` files)
- Define tool permissions in agent files

**Note**: Subagents are advanced — only create if simple skills/commands are insufficient

---

## Contributing Guidelines

### Pull Requests

Before submitting PR:

1. **Run version sync**: `python core/sync.py`
2. **Run tests**: `pytest tests/ -v`
3. **Run linter**: `ruff check core/`
4. **Update documentation**: README.md, AGENTS.md if needed
5. **Verify hooks**: Ensure no stderr writes

### Code Style

- Follow PEP 8 for Python code
- Use type hints on all public functions
- Add docstrings to modules and public functions
- Maximum line length: 100 characters (enforced by ruff)

### Testing

- Write tests for new functionality
- Maintain >80% test coverage
- Use descriptive test names (test_<function>_<scenario>)

---

## Resources

- **Plugin Development**: `P:/.claude/skills/plugin-development`
- **Hook Development**: `P:/.claude/skills/hook-development`
- **MCP Integration**: `P:/.claude/skills/mcp-integration`
- **Claude Code Docs**: https://docs.anthropic.com

---

**Last Updated**: 2026-03-11
**Plugin Version**: 5.5.5
**Maintained By**: Your Name <your.email@example.com>
