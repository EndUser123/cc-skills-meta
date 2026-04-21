"""Regression checks for GitHub-compatible Mermaid output."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
README_PATH = REPO_ROOT / "README.md"
DIAGRAM_DIR = REPO_ROOT / "docs" / "diagrams"

FORBIDDEN_PATTERNS = (
    "System_Bnd(",
    "Container_Bnd(",
    "Component_Bnd(",
    "UpdateLayoutConfig(",
    "include:",
    "}%%%",
)

README_FORBIDDEN_PATTERNS = FORBIDDEN_PATTERNS + (
    "C4Context",
    "C4Container",
    "C4Component",
)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_readme_mermaid_uses_github_compatible_subset():
    content = _read_text(README_PATH)
    for pattern in README_FORBIDDEN_PATTERNS:
        assert pattern not in content, f"README contains forbidden Mermaid pattern: {pattern}"


def test_diagram_sources_use_github_compatible_subset():
    for path in sorted(DIAGRAM_DIR.glob("*.mmd")):
        content = _read_text(path)
        for pattern in FORBIDDEN_PATTERNS:
            assert pattern not in content, f"{path.name} contains forbidden Mermaid pattern: {pattern}"


def test_mermaid_init_directives_use_standard_closing_marker():
    for path in [README_PATH, *sorted(DIAGRAM_DIR.glob("*.mmd"))]:
        content = _read_text(path)
        assert "%%%" not in content, f"{path.name} contains malformed Mermaid init closing marker"
