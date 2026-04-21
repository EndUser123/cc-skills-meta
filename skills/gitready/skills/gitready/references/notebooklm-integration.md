# NotebookLM Integration Reference

## Authentication

NotebookLM CLI authentication uses browser-based OAuth via Chrome DevTools Protocol.

**Profile location**: `C:/Users/brsth/.notebooklm-mcp-cli/profiles/default/`
**Credentials file**: `C:/Users/brsth/.notebooklm-mcp-cli/profiles/default/credentials.json`
**Auth method**: Browser-based OAuth (Chrome CDP), cookies + CSRF token extracted on login

**Login command**: `nlm login`
**Check auth**: `nlm login --check`
**Session lifetime**: ~20 minutes before re-authentication required

## Video Style Options

Valid `--style` values for `nlm video create`:
- `anime`
- `auto_select`
- `classic`
- `custom`
- `heritage`
- `kawaii`
- `paper_craft`
- `retro_print`
- `watercolor`
- `whiteboard`

**Note**: `documentary` style does NOT exist — use `whiteboard` for technical explainer videos.

## Slide Deck Format Options

`nlm slides create` uses `--format` not `--slide-format`:
- `detailed_deck` (default)
- `presenter_slides`

## Notebook Creation for Media Generation

Notebook ID: `05c29d13-2e07-4106-89f3-6e5d180870f7`
Notebook URL: https://notebooklm.google.com/notebook/05c29d13-2e07-4106-89f3-6e5d180870f7

## Artifact Status Reference

After generating artifacts, poll `nlm studio status <notebook_id>`:
- `completed` — ready to download
- `in_progress` — still generating (wait and poll again)
- `unknown` — generation failed or was abandoned

## Download Commands

```bash
# Infographic (already completed)
nlm download infographic <notebook_id> --id <artifact_id> --output <path>

# Video (may fail if status unknown)
nlm download video <notebook_id> --id <artifact_id> --output <path>

# Slide deck (in_progress at time of generation)
nlm download slide-deck <notebook_id> --id <artifact_id> --output <path>
```

## Error: "Could not add file source"

If `nlm source add --file` fails with "Could not add file source":
- Use `--text` with file content instead: `nlm source add <id> --text "$(cat file.py)" --title "file.py" --wait`
- This works for .py files, JSON, and text content
- Direct file upload seems to have issues with certain file types

## Video Generation Failed?

If video download fails with "Download failed for video":
- Check `nlm studio status <notebook_id>` — if status is `unknown`, the generation failed silently
- Re-generate with `--style whiteboard` (not documentary or other invalid styles)

## File Exclusion Patterns for Source Upload

Exclude from NotebookLM source uploads:
- Lock files: `package-lock.json`, `poetry.lock`, `requirements.lock`
- Test outputs: `htmlcov/`, `coverage.xml`, `.coverage*`
- Version control: `.git/`
- Cache/build: `__pycache__/`, `venv/`, `build/`, `dist/`
- Generated media: `assets/videos/`, `assets/infographics/`, `assets/slides/`
- Generic templates: `CONTRIBUTING.md`, `SECURITY.md`, `LICENSE`, `CHANGELOG.md`