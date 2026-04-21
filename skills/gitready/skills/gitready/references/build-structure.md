# PHASE 2: Build Structure (2min)

**Objective**: Create appropriate directory structure based on package type.

**DEFAULT**: Create Claude Code Plugins (`.claude-plugin/`, `scripts/`, `hooks/`) for packages with hooks/skills.
**MIGRATION**: Convert existing Python libraries to plugins via brownfield conversion.
**ADVANCED**: Create pure Python libraries only when plugin architecture isn't appropriate.

---

## For Claude Skills (`PACKAGE_TYPE=claude-skill`)

```
{{TARGET_DIR}}/
├── skill/                     # Single source of truth
│   ├── SKILL.md              # Skill definition
│   ├── resources/            # Templates, configs
│   ├── scripts/              # Hook scripts, utility scripts
│   ├── tests/                # Test suite (optional)
│   └── *.py                  # Python modules (if any)
├── README.md
├── LICENSE
└── .gitignore
```

**IMPORTANT**: Claude skills do NOT need `pyproject.toml`. Distributed via junctions from `skill/` to `~/.claude/skills/skill-name/`.

**Steps:**

1. **Create directory structure**:
```bash
mkdir -p {{TARGET_DIR}}/skill
```

2. **Generate README.md** (see PHASE 3 templates)
3. **Create LICENSE** (MIT by default)
4. **Create scripts/install-dev.bat** (Windows junction automation)

---

## For Claude Code Plugins (`PACKAGE_TYPE=claude-plugin`)

```
{{TARGET_DIR}}/
├── .claude-plugin/            # Plugin metadata
│   └── plugin.json            # Minimal manifest
├── commands/                  # OPTIONAL: Slash commands (.md files)
├── agents/                    # OPTIONAL: Subagents (.md files)
├── skills/                    # OPTIONAL: Auto-activating skills
│   └── skill-name/
│       └── SKILL.md
├── hooks/
│   └── hooks.json             # Hook configuration
├── scripts/                      # Python code
│   ├── __init__.py
│   ├── main.py
│   └── utils/
├── tests/
├── .gitignore
├── README.md
└── LICENSE
```

**IMPORTANT**: Claude Code plugins use auto-discovered components:
- `.claude-plugin/plugin.json` - Minimal manifest (name, description, author)
- Components at ROOT level - commands/, agents/, skills/, hooks/
- `scripts/` directory - Python code (NOT packages/hook/)
- NO pyproject.toml - Plugins are not pip packages
- CLAUDE_PLUGIN_ROOT - Use for all path references (portability)

**IMPORTANT**: Claude Code plugins do NOT use `.claude/skills/` layout. Skills MUST be at root level `skills/` directory. The `.claude/` directory is reserved for hooks, handoff state, and Claude Code internal files only. Never place skill definitions under `.claude/skills/` — this pattern is forbidden for plugins.

**Skills layout (correct):**
```
{{TARGET_DIR}}/
├── skills/                    # Skills at ROOT level (not under .claude/)
│   └── skill-name/
│       └── SKILL.md
├── .claude-plugin/
│   └── plugin.json
...
```

**Skills layout (WRONG — never do this):**
```
{{TARGET_DIR}}/
├── .claude/
│   └── skills/               # FORBIDDEN — skills under .claude/ not allowed
│       └── skill-name/
│           └── SKILL.md
```

**Steps:**

1. **Create directory structure**:
```bash
mkdir -p {{TARGET_DIR}}/.claude-plugin
mkdir -p {{TARGET_DIR}}/core
mkdir -p {{TARGET_DIR}}/hooks
mkdir -p {{TARGET_DIR}}/tests
# Optional: mkdir -p {{TARGET_DIR}}/commands agents skills scripts
```

2. **Create `.claude-plugin/plugin.json`**:
```json
{
  "name": "{{package_name}}",
  "description": "{{DESCRIPTION}}",
  "author": {
    "name": "{{AUTHOR_NAME}}",
    "email": "{{AUTHOR_EMAIL}}"
  }
}
```

3. **Create `hooks/hooks.json`** (if needed):
```json
{
  "{{HOOK_POINT}}": [{
    "matcher": ".*",
    "hooks": [{
      "type": "command",
      "command": "python CLAUDE_PLUGIN_ROOT/scripts/main.py"
    }]
  }]
}
```

4. **Create `scripts/__init__.py`**
5. **Create `.gitignore`** (Exclude .local.md files)
6. **Generate README.md** (see PHASE 3 templates)
7. **Create LICENSE** (MIT)

---

## For Python Libraries (`PACKAGE_TYPE=python-library`)

**Steps:**

1. **Create directory structure**:
```bash
mkdir -p {{TARGET_DIR}}/src/{{NAME}}
mkdir -p {{TARGET_DIR}}/tests
touch {{TARGET_DIR}}/src/{{NAME}}/__init__.py
touch {{TARGET_DIR}}/tests/__init__.py
```

2. **Generate README.md** (see PHASE 3 templates)
3. **Create LICENSE** (MIT)
4. **Create pyproject.toml** (full Python package)
5. **Create CONTRIBUTING.md**
6. **Create SECURITY.md**
