# PHASE 1.5: Detect Package Type (30s)

**Objective**: Determine if this is a Claude skill, Python library, Claude Code plugin, Claude Code plugin with MCP server, or hook-based package.

## Detection Script

```bash
# Check for SKILL.md (Claude skill marker)
if [ -f "{{TARGET_DIR}}/skill/SKILL.md" ] || [ -f "{{TARGET_DIR}}/SKILL.md" ]; then
    PACKAGE_TYPE="claude-skill"
    echo "Detected: Claude Skill"
# Check for .claude-plugin/ directory (Claude Code plugin with router integration)
elif [ -d "{{TARGET_DIR}}/.claude-plugin" ]; then
    PACKAGE_TYPE="claude-plugin"
    echo "Detected: Claude Code Plugin (with router integration)"

    # Check for MCP server
    if [ -f "{{TARGET_DIR}}/mcp_server.py" ] || [ -f "{{TARGET_DIR}}/mcp/server.py" ] || [ -d "{{TARGET_DIR}}/mcp" ]; then
        HAS_MCP_SERVER=true
        PACKAGE_TYPE="claude-plugin+mcp"
        echo "-> MCP Server: DETECTED"
    else
        HAS_MCP_SERVER=false
        echo "-> MCP Server: NOT FOUND"
    fi
# Check for hook/ directory (hook-based package)
elif [ -d "{{TARGET_DIR}}/hook" ]; then
    PACKAGE_TYPE="hook-package"
    echo "Detected: Hook Package"
# Check for Python library (src/ or pyproject.toml)
elif [ -d "{{TARGET_DIR}}/src" ] || [ -f "{{TARGET_DIR}}/pyproject.toml" ]; then
    PACKAGE_TYPE="python-library"
    echo "Detected: Python Library"

    # BROWNFIELD DETECTION: Auto-convert Python library to Claude Code plugin
    if [ -d "{{TARGET_DIR}}/src" ] && [ -f "{{TARGET_DIR}}/pyproject.toml" ]; then
        PACKAGE_TYPE="brownfield-plugin"
        echo "Detected: Python Library -> Converting to Claude Code Plugin"
        echo "Details: This will backup your current structure, migrate src/ to scripts/,"
        echo "remove pyproject.toml, and add plugin configuration files."
        echo "Rollback available via .backup/ directory."
    else
        PACKAGE_TYPE="python-library"
        echo "Detected: Python Library (legacy - no src/ directory)"
    fi
else
    PACKAGE_TYPE="claude-plugin"
    echo "Detected: Claude Code Plugin (default for new packages)"
fi
```

## Package Types

| Type | Trigger | Structure | Use Case | Recommendation |
|------|---------|-----------|----------|----------------|
| `claude-plugin` | `.claude-plugin/` exists OR empty/new directory | `.claude-plugin/` + `scripts/` + `hooks/` + README | **DEFAULT**: Packages with hooks/skills | Primary pattern |
| `claude-plugin+mcp` | `.claude-plugin/` + `mcp_server.py` or `mcp/` | `.claude-plugin/` + `scripts/` + `hooks/` + `.mcp.json` | Plugins with MCP server | For MCP integration |
| `brownfield-plugin` | Python library with `src/` + `pyproject.toml` | `src/` to `scripts/` conversion (automatic) | Convert existing Python lib to plugin | DEFAULT for Python libraries |
| `python-library` | Only `pyproject.toml` (no `src/`) OR explicitly opted out | `src/{{NAME}}/` + `tests/` + pyproject.toml | ADVANCED: Pure backend code (no hooks/skills) | Only when plugins inappropriate |
| `claude-skill` | `SKILL.md` exists | `skill/` only (no `src/`, no pyproject.toml) | Standalone Claude skills | For skill-only packages |
| `hook-package` | `hook/` directory exists | `hook/` + README | Legacy hook distribution | Use plugin pattern instead |
