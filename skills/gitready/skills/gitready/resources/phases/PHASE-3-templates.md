# PHASE 3: Generate Templates

**Objective**: Generate README.md, LICENSE, AGENTS.md, and configuration files based on package type.

**Templates auto-generated**:
- **Python libraries**: pip install instructions, Quick Start, development setup
- **Claude skills**: Manual installation via junctions/symlinks, no pyproject.toml
- **Claude Code plugins**: `/plugin` installation, local dev with junctions/symlinks
- **Brownfield plugins**: Migration notice, rollback instructions, updated usage examples

**All packages get AGENTS.md**:
- AI-maintainable documentation for Claude, Copilot, and other AI assistants
- Uses template from `resources/AGENTS.template.md`
- Documents plugin constraints, setup commands, and development workflows
- Critical for long-term maintainability by AI assistants

### README Structure Contract

**CRITICAL**: Keep the main `README.md` as the source of truth for package documentation. Use GitHub Pages only for browser playback of the explainer video unless the user explicitly asks for a separate docs site.

**Required top-level README order:**
1. Project title, badges, and one-paragraph overview
2. `Quick Start`
3. `See The Transformation` (before/after comparison table)
4. `Explainer Video`
5. `What {{package_name}} Does` (capabilities + pipeline overview)
6. `What Gets Created` (artifact tree — the outcome)
7. `Which Package Type Do You Need?` (decision helper, placed near artifacts)
8. `Development and Deployment`
9. `Additional Media Assets`
10. `Contributing`, `Changelog`, `License`, `Resources`
11. PHASE deep-dives (`PHASE 4.5`, `PHASE 6`, `PHASE 7`) — reference material at the end

**Rules:**
- Put the explainer video immediately after `Quick Start`
- Keep `What Gets Created` before `Which Package Type` so users see the outcome first, then learn which type they need
- Move PHASE sections to the end — they are reference material, not part of the primary user journey
- Keep architecture, workflow, and usage details on the main GitHub page
- Generate `docs/video.html` for GitHub Pages by default
- Do not generate extra Pages docs such as `docs/*architecture*.html` or `docs/*workflow*.html` unless the user explicitly asks for them
- Link the README poster image to the GitHub Pages player page and keep all other technical content in the repository README
- **Also generate `docs/README-preview.html`** — a styled HTML version of the README for local preview with GitHub-like CSS (light/dark theme support)

### README Template for Claude Code Plugins

**CRITICAL**: Include the "Three Deployment Models" section in every generated README.md to prevent confusion about installation methods.

```markdown
## Installation

### Three Deployment Models

**IMPORTANT**: This package supports three different deployment modes. Choose the right one for your use case.

#### 1. SKILLS (Dev Deployment) ⭐ **Recommended for Development**

**For**: When you're actively developing this package and want instant feedback.

**Setup:**
\`\`\`powershell
# Windows (Junction - No admin required)
# For plugins with skills: Junction to the skills/ subdirectory

# IMPORTANT: Sanitize the junction name to remove problematic characters like @, ?, *, etc.
# These characters cause issues with slash command invocation on Windows.
$junctionName = "{{package_name}}" -replace '[@?*:<>|+]', ''
if ($junctionName -ne "{{package_name}}") {
    Write-Host "NOTE: Sanitized junction name from '{{package_name}}' to '$junctionName'"
}

New-Item -ItemType Junction -Path "P:\.claude\skills\$junctionName" -Target "P:\packages\{{package_name}}\skills\{{package_name}}"

# For standalone skills (skill/ directory): Junction to the skill/ subdirectory
# New-Item -ItemType Junction -Path "P:\.claude\skills\$junctionName" -Target "P:\packages\{{package_name}}\skill"

# macOS/Linux (Symlink)
ln -s /path/to/packages/{{package_name}}/skills/{{package_name}} ~/.claude/skills/$junctionName
\`\`\`

**Key points:**
- ✅ Edit in `P:/packages/{{package_name}}/`, changes work immediately
- ✅ No reinstallation required - skills auto-discover from `P:/.claude/skills/`
- ✅ Perfect for active development
- ✅ Junction to `skills/{{package_name}}/` for plugin skills, or `skill/` for standalone skills
- ⚠️  **CRITICAL**: The junction target must point to WHERE THE SKILL.md FILE ACTUALLY LIVES:
  - Plugin skills: `package-name/skills/skill-name/SKILL.md` → junction target: `skills/skill-name/`
  - Standalone skills: `package-name/skill/SKILL.md` → junction target: `skill/`

**Important Note on Skill Naming:**
- The junction NAME (`{{package_name}}`) should match the skill directory name in the package
- This ensures the skill URL (`/skill-name`) works correctly
- Example: If package has `skills/my-skill/SKILL.md`, create junction as `P:/.claude/skills/my-skill/`
- **CRITICAL**: Remove invalid characters (especially `@`, `?`, `*`, etc.) from the junction name before creation. These characters cause slash command invocation failures on Windows. Use the sanitization step shown above.
- The skill's **aliases** in the frontmatter determine what users type to invoke it

#### 2. HOOKS (Dev Deployment - Hook Files Only)

**For**: When this package has hook files (\`.py\` files in \`core/hooks/\`) you want to test.

**Setup:**
\`\`\`powershell
# Symlink individual hook files to P:/.claude/hooks/
cd P:/.claude/hooks

# Example: Symlink a specific hook file
cmd /c "mklink HookName.py P:/packages/{{package_name}}/core/hooks/HookName.py"
\`\`\`

**Key points:**
- ✅ Symlink individual \`.py\` hook files only (NOT the entire directory)
- ✅ Symlinks go in \`P:/.claude/hooks/\` (NOT \`~/.claude/plugins/\`)
- ✅ These are dev-only symlinks for working directly on source code
- ⚠️  After brownfield conversion, check for broken symlinks pointing to old \`src/\` paths

#### 3. PLUGINS (End User Deployment)

**For**: Distributing this package to other users via marketplace or GitHub.

**Setup:**
\`\`\`bash
# End users install via /plugin command
/plugin P:/packages/{{package_name}}

# Or from marketplace (when published)
/plugin install {{package_name}}
\`\`\`

**Key points:**
- ✅ Plugin copied to \`~/.claude/plugins/cache/\`
- ✅ Registered in \`~/.claude/plugins/installed_plugins.json\`
- ❌ **NOT for local development** - requires reinstall on every change
- ✅ Use for distributing finished packages to users

### Which Model Should You Use?

| Your Situation | Use This Model | Why |
|----------------|----------------|-----|
| Actively developing this package | **SKILLS** (junction) | Instant feedback, no reinstall |
| Testing hook file changes | **HOOKS** (symlinks) | Direct hook testing |
| Distributing to end users | **PLUGINS** (/plugin) | Proper distribution format |

### Common Mistakes to Avoid

- ❌ Don't use \`/plugin\` command for local development (requires reinstall on every change)
- ❌ Don't symlink entire directories to \`P:/.claude/hooks/\` (only symlink \`.py\` files)
- ❌ Don't confuse skills (\`P:/.claude/skills/\`) with plugins (\`~/.claude/plugins/\`)
- ❌ Don't forget to update symlinks after brownfield conversion - check for \`src/\` paths
\`\`\`
```

### Media Assets Section Template

**After media generation completes (PHASE 4.7), add this section to README.md after `Development and Deployment`:**

\`\`\`markdown
## Explainer Video

[![Watch the demo with audio](assets/videos/{{package_name}}_video_poster.png)](https://{{github_username}}.github.io/{{package_name}}/docs/video.html)

> **[🎬 Watch the explainer in the browser](https://{{github_username}}.github.io/{{package_name}}/docs/video.html)**
> **[⬇️ Download the MP4 directly](https://github.com/{{github_username}}/{{package_name}}/releases/download/media/{{package_name}}_explainer_pbs.mp4)**
> *Browser playback requires GitHub Pages to be enabled for this repository.*

Quick overview of features and workflow.

## Additional Media Assets

### 📊 Architecture Flowchart

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

### 📑 Presentation Slides

[![Slide deck preview](assets/slides/{{package_name}}_slides_preview.png)](assets/slides/{{package_name}}_slides.pdf)

**[📄 View Slides (PDF)](assets/slides/{{package_name}}_slides.pdf)**
**[⬇️ Download PDF](assets/slides/{{package_name}}_slides.pdf)**

*Use the PDF for both viewing and download on GitHub.*

### Interactive Course

[**Learn how {{package_name}} works →**](https://{{github_username}}.github.io/{{package_name}}/docs/{{package_name}}_course.html)

*An interactive walkthrough of the architecture, components, and how everything fits together.*

---

**💡 Tip**: Use GitHub Pages for in-browser video playback. Keep the slide deck in PDF form for the cleanest GitHub viewing experience.
\`\`\`

**IMPORTANT**: This media layout uses GitHub-compatible markdown. Key points:
- **Images**: Use standard markdown \`![alt](path)\` syntax - renders inline
- **Videos**: Do not rely on HTML \`<video>\` tags in \`README.md\`
- **Recommended pattern**: Link a verified still frame such as \`assets/videos/{{package_name}}_video_poster.png\` in \`README.md\` to \`https://{{github_username}}.github.io/{{package_name}}/docs/video.html\`
- **Fallback**: Keep the release asset MP4 link for direct download/open
- **PDFs**: Use direct markdown links - opens in GitHub's built-in PDF viewer
- **Slide previews**: Export the first PDF page to \`assets/slides/{{package_name}}_slides_preview.png\` and link it to the PDF
- **Badges**: Use shields.io badges for visual appeal and clickability
- **GitHub Pages**: Enable Pages from \`main\` root so \`docs/video.html\` is publicly available
- **Pages scope**: Use GitHub Pages only for the video player by default; keep architecture and workflow documentation in \`README.md\`
- **Durations**: Never hardcode video runtimes. Measure the exported file first or omit the duration label entirely

**Runtime verification examples:**
```bash
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 assets/videos/{{package_name}}_explainer_pbs.mp4
```

**For brownfield conversions**: See \`references/brownfield-conversion.md\` for README update instructions (migration notice, rollback instructions, updated usage examples).

### HTML Preview Generation

**After generating README.md, also create an HTML preview file for local viewing:**

```bash
# Create docs directory if it doesn't exist
mkdir -p docs

# Generate HTML preview with warm palette (codebase-to-course design system)
cat > docs/README-preview.html << 'HTMLEOF'
<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{package_name}} - README Preview</title>
    <!-- Google Fonts: Bricolage Grotesque (display), DM Sans (body), JetBrains Mono (code) -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,600;12..96,700;12..96,800&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        /* === WARM COLOR PALETTE (codebase-to-course design system) === */
        /* Light theme: warm off-white like aged paper */
        :root, [data-theme="light"] {
            --bg-color: #FAF7F2;
            --bg-warm: #F5F0E8;
            --bg-code: #1E1E2E;
            --text-color: #2C2A28;
            --text-muted: #6B6560;
            --text-light: #9E9790;
            --link-color: #0969da;
            --border-color: #E5DFD6;
            --heading-color: #111;
            --inline-code-bg: #EEEBE5;
            --blockquote-border: #E5DFD6;
            --blockquote-bg: #F5F0E8;
            --toggle-bg: #F5F0E8;
            --toggle-fg: #655e56;
            --accent: #D94F30;
            --accent-hover: #C4432A;
            --surface: #FFFFFF;
            --surface-warm: #FDF9F3;
            /* Catppuccin Mocha syntax colors (dark code blocks) */
            --code-keyword: #CBA6F7;
            --code-string: #A6E3A1;
            --code-function: #89B4FA;
            --code-comment: #6C7086;
            --code-number: #FAB387;
            --code-property: #F9E2AF;
            --code-operator: #94E2D5;
        }
        /* Dark theme */
        [data-theme="dark"] {
            --bg-color: #0d1117;
            --bg-warm: #161b22;
            --bg-code: #1E1E2E;
            --text-color: #c9d1d9;
            --text-muted: #8b949e;
            --text-light: #6e7681;
            --link-color: #58a6ff;
            --border-color: #30363d;
            --heading-color: #f0f6fc;
            --inline-code-bg: #2d333b;
            --blockquote-border: #3b434b;
            --blockquote-bg: #161b22;
            --toggle-bg: #30363d;
            --toggle-fg: #c9d1d9;
            --accent: #D94F30;
            --accent-hover: #C4432A;
            --surface: #161b22;
            --surface-warm: #1C2128;
        }
        /* === BASE STYLES === */
        body {
            font-family: 'DM Sans', -apple-system, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
            padding-top: calc(40px + 50px);
            color: var(--text-color);
            line-height: 1.6;
            background: var(--bg-color);
            transition: background 0.3s ease, color 0.3s ease;
        }
        /* === ACCESSIBILITY: Skip to content === */
        .skip-link {
            position: absolute;
            top: -100%;
            left: 0;
            background: var(--accent);
            color: white;
            padding: 8px 16px;
            z-index: 9999;
            transition: top 0.2s;
        }
        .skip-link:focus { top: 0; }
        /* === THEME TOGGLE === */
        .theme-toggle {
            position: fixed;
            top: 20px;
            right: 20px;
            width: 44px;
            height: 44px;
            border-radius: 50%;
            border: 1px solid var(--border-color);
            background: var(--toggle-bg);
            color: var(--toggle-fg);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            transition: border-color 0.2s ease, color 0.2s ease, background 0.2s ease;
            z-index: 1000;
        }
        .theme-toggle:hover, .theme-toggle:focus-visible {
            border-color: var(--accent);
            color: var(--accent);
            outline: none;
        }
        /* === TYPOGRAPHY === */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Bricolage Grotesque', Georgia, serif;
            color: var(--heading-color);
            line-height: 1.2;
        }
        h1 { font-size: 2.25rem; font-weight: 700; border-bottom: 1px solid var(--border-color); padding-bottom: 0.3em; }
        h2 { font-size: 1.5rem; font-weight: 600; border-bottom: 1px solid var(--border-color); padding-bottom: 0.3em; margin-top: 2rem; }
        h3 { font-size: 1.25rem; font-weight: 600; }
        h4 { font-size: 1rem; font-weight: 600; color: var(--text-muted); }
        p { color: var(--text-color); margin-bottom: 1rem; }
        /* === CODE (text wraps, no horizontal scroll) === */
        code {
            background: var(--inline-code-bg);
            border-radius: 4px;
            padding: 0.2em 0.4em;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.875em;
            white-space: pre-wrap;
            word-break: break-word;
        }
        pre {
            background: var(--bg-code);
            border-radius: 8px;
            padding: 16px;
            overflow-x: hidden;
            white-space: pre-wrap;
            word-break: break-word;
        }
        pre code { background: none; padding: 0; font-size: 0.875em; white-space: pre-wrap; word-break: break-word; }
        /* Catppuccin syntax highlighting (dark code blocks only) */
        .code-keyword { color: var(--code-keyword); }
        .code-string { color: var(--code-string); }
        .code-function { color: var(--code-function); }
        .code-comment { color: var(--code-comment); }
        .code-number { color: var(--code-number); }
        .code-property { color: var(--code-property); }
        .code-operator { color: var(--code-operator); }
        /* === LINKS === */
        a { color: var(--link-color); text-decoration: none; }
        a:hover { text-decoration: underline; }
        a:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
        /* === TABLES === */
        table { border-collapse: collapse; width: 100%; margin: 1em 0; }
        th, td { border: 1px solid var(--border-color); padding: 8px 12px; text-align: left; color: var(--text-color); }
        th { background: var(--bg-warm); font-weight: 600; }
        /* === QUOTES === */
        blockquote { border-left: 4px solid var(--accent); margin: 1em 0; padding: 0.5em 1em; color: var(--text-muted); background: var(--blockquote-bg); border-radius: 0 4px 4px 0; }
        /* === HEADER === */
        .header-section {
            background: linear-gradient(135deg, var(--accent) 0%, #C4432A 100%);
            color: white;
            padding: 2em;
            border-radius: 12px;
            margin-bottom: 2em;
            transition: background 0.3s ease;
        }
        .header-section h1 { color: white; border: none; font-size: 2.5rem; }
        .header-section p { color: rgba(255,255,255,0.9); font-size: 1.1rem; }
        /* === BADGES === */
        .badge { display: inline-block; background: var(--inline-code-bg); border: 1px solid var(--border-color); border-radius: 6px; padding: 3px 8px; font-size: 0.75em; margin: 2px; font-family: 'JetBrains Mono', monospace; }
        hr { border: none; border-top: 1px solid var(--border-color); margin: 2em 0; }
        /* === CODE HILITE (for pre-existing content) === */
        .codehilite { background: var(--bg-code); padding: 16px; border-radius: 8px; overflow-x: hidden; white-space: pre-wrap; word-break: break-word; }
        /* === ANIMATE IN (scroll-triggered reveal) === */
        .animate-in {
            opacity: 0;
            transform: translateY(16px);
            transition: opacity 0.5s cubic-bezier(0.16, 1, 0.3, 1), transform 0.5s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .animate-in.visible {
            opacity: 1;
            transform: translateY(0);
        }
        /* === PREFERS REDUCED MOTION === */
        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after {
                animation-duration: 0.01ms !important;
                transition-duration: 0.01ms !important;
            }
        }
        /* === SCROLLBAR STYLING === */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: var(--border-color); border-radius: 3px; }
    </style>
</head>
<body>
<a class="skip-link" href="#content">Skip to content</a>
<button class="theme-toggle" onclick="toggleTheme()" aria-label="Toggle light/dark mode" title="Toggle theme">
    <span id="theme-icon">&#9788;</span>
</button>
<script>
function toggleTheme() {
    const html = document.documentElement;
    const icon = document.getElementById('theme-icon');
    const current = html.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    icon.innerHTML = next === 'dark' ? '&#9790;' : '&#9788;';
    localStorage.setItem('theme', next);
}
(function() {
    // Respect system preference if no saved theme
    const saved = localStorage.getItem('theme');
    if (!saved) {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
        document.getElementById('theme-icon').innerHTML = prefersDark ? '&#9790;' : '&#9788;';
    } else {
        document.documentElement.setAttribute('data-theme', saved);
        document.getElementById('theme-icon').innerHTML = saved === 'dark' ? '&#9790;' : '&#9788;';
    }
    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        if (!localStorage.getItem('theme')) {
            document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light');
            document.getElementById('theme-icon').innerHTML = e.matches ? '&#9790;' : '&#9788;';
        }
    });
})();
</script>
<div id="content">
<!-- README CONTENT WILL BE INSERTED HERE BY THE SKILL -->
</div>
</body>
</html>
HTMLEOF
```

**HTML preview features:**
- **Warm palette** — off-white background (#FAF7F2), vermillion accent (#D94F30)
- **Google Fonts** — Bricolage Grotesque (headings), DM Sans (body), JetBrains Mono (code)
- **Day-night toggle** — clickable sun/moon button, persists preference in localStorage, respects system preference
- **Accessibility** — skip-to-content link, focus-visible styles, prefers-reduced-motion support
- **Scroll-triggered animations** — `.animate-in` class for reveal effects
- **Text-wrapping code** — no horizontal scrollbars, `white-space: pre-wrap`
- **Catppuccin syntax highlighting** — purple/green/blue color scheme for dark code blocks
- **Responsive scrollbar** — subtle 6px scrollbar styling

**Output file:** `docs/README-preview.html`

**Note:** The HTML preview is for local development viewing. The canonical documentation remains `README.md` which GitHub renders automatically.
