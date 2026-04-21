# PHASE 4: Validation Scripts

## Platform Compatibility Check

```bash
# Detect platform
PLATFORM="$(uname -s)"
case "$PLATFORM" in
  Linux*)     PLATFORM="linux" ;;
  Darwin*)    PLATFORM="macos" ;;
  MINGW*|MSYS*|CYGWIN*) PLATFORM="windows" ;;
  *)          PLATFORM="unknown" ;;
esac

# Check for deployment errors: Platform-specific docs referencing wrong scripts
if [ "$PLATFORM" = "windows" ]; then
  # Check Windows-specific documentation for .sh references in hook configs
  WINDOWS_DOCS=$(find {{TARGET_DIR}} -name "WINDOWS.md" -o -name "INSTALLATION.md" 2>/dev/null)

  if [ -n "$WINDOWS_DOCS" ]; then
    # Look for .sh files referenced in hook/command configurations
    SH_CONFIG_REFS=$(grep -n '"command".*\.sh' $WINDOWS_DOCS 2>/dev/null | grep -v "# " | grep -v "Unix\|Linux\|macOS\|Darwin")

    if [ -n "$SH_CONFIG_REFS" ]; then
      echo "ERROR: Windows documentation references .sh scripts in hook configurations:"
      echo "$SH_CONFIG_REFS"
      echo ""
      echo "Problem: Windows users cannot execute .sh scripts natively without WSL/Git Bash"
      echo "Solution: Change .sh to .bat in hook configuration examples"
    fi
  fi

  # Optional: Verify .bat/.ps1 alternatives exist for any .sh files in scripts/
  SH_SCRIPTS=$(find {{TARGET_DIR}} -name "*.sh" -path "*/scripts/*" 2>/dev/null)
  if [ -n "$SH_SCRIPTS" ]; then
    for sh_file in $SH_SCRIPTS; do
      bat_file="${sh_file%.sh}.bat"
      ps1_file="${sh_file%.sh}.ps1"
      if [ ! -f "$bat_file" ] && [ ! -f "$ps1_file" ]; then
        echo "WARNING: $sh_file has no .bat or .ps1 equivalent for Windows users"
      fi
    done
  fi
fi
```

## Symlink Test (for Claude skills)

```bash
test -L ~/.claude/skills/{{NAME}} && echo "Symlink: OK" || echo "Symlink: MISSING"
```

## Pytest Collect

```bash
pytest --collect-only {{TARGET_DIR}}/tests/
```

## Tree Diff

```bash
tree {{TARGET_DIR}} -a -L 3 > {{TARGET_DIR}}/post-pack-tree.txt
diff {{TARGET_DIR}}/pre-pack-tree.txt {{TARGET_DIR}}/post-pack-tree.txt
```

## Content Reasonableness Validation (v5.23)

```powershell
# Validate README.md has required template content
if (Test-Path "{{TARGET_DIR}}/README.md") {
    $readmeContent = Get-Content "{{TARGET_DIR}}/README.md" -Raw

    # For Claude plugins: must have Three Deployment Models section
    if ($PKG_TYPE -eq "claude-plugin" -or $PKG_TYPE -eq "brownfield-plugin") {
        if ($readmeContent -notmatch "Three Deployment Models") {
            Write-Host "README missing: 'Three Deployment Models' section (required for plugins)"
        }
        if ($readmeContent -notmatch "(?i)(junction|symlink).*dev.*mode") {
            Write-Host "README missing: junction/symlink dev mode instructions"
        }
        if ($readmeContent -notmatch "(?i)SKILLS.*Dev.*Deployment") {
            Write-Host "README missing: SKILLS dev deployment section"
        }
    }

    # Must have Quick Start section
    if ($readmeContent -notmatch "(?i)^#{1,3}\s*Quick Start") {
        Write-Host "README missing: 'Quick Start' section"
    }
    # Must have badges (at least one Shields.io badge)
    if ($readmeContent -notmatch "shields\.io") {
        Write-Host "README missing: badges (shields.io)"
    }
} else {
    Write-Host "README.md not found"
}

# Validate SKILL.md frontmatter (if skills/ directory exists)
$skillMd = "{{TARGET_DIR}}/skills/{{NAME}}/SKILL.md"
if (Test-Path $skillMd) {
    $frontmatter = Get-Content $skillMd -Raw
    $requiredFields = @("name:", "version:", "description:", "category:")
    foreach ($field in $requiredFields) {
        if ($frontmatter -notmatch "(?m)^$field") {
            Write-Host "SKILL.md missing frontmatter field: $field"
        }
    }
}

# Validate plugin.json (if .claude-plugin/ exists)
$pluginJson = "{{TARGET_DIR}}/.claude-plugin/plugin.json"
if (Test-Path $pluginJson) {
    try {
        $pluginData = Get-Content $pluginJson | ConvertFrom-Json
        if (-not $pluginData.name) {
            Write-Host "plugin.json missing: name field"
        }
        if (-not $pluginData.version) {
            Write-Host "plugin.json missing: version field"
        }
        if (-not $pluginData.description) {
            Write-Host "plugin.json missing: description field"
        }
    } catch {
        Write-Host "plugin.json is not valid JSON: $_"
    }
}

# Validate hooks.json structure (if hooks/ exists)
$hooksJson = "{{TARGET_DIR}}/hooks/hooks.json"
if (Test-Path $hooksJson) {
    try {
        $hooksData = Get-Content $hooksJson | ConvertFrom-Json
        $validEvents = @("PreToolUse", "PostToolUse", "PreCompact", "SessionStart",
                         "UserPromptSubmit", "ToolResponseReceived", "Stop")
        foreach ($prop in $hooksData.PSObject.Properties.Name) {
            if ($validEvents -notcontains $prop) {
                Write-Host "hooks.json contains unknown event: '$prop'"
            }
        }
    } catch {
        Write-Host "hooks.json is not valid JSON: $_"
    }
}
```
