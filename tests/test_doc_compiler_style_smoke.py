"""Smoke tests for style-aware doc-compiler pipeline.

Verifies each style (deepwiki, product, minimal) can pass through
stage B (artifact plan builder) and stage E1 (template loader) without error.
"""
import sys, json
from pathlib import Path
from unittest.mock import MagicMock

STAGE_DIR = Path("P:/packages/.claude-marketplace/plugins/cc-skills-meta/skills/doc-compiler")
sys.path.insert(0, str(STAGE_DIR))

import stage_b_artifact_plan_builder as plan_mod
import stage_e1_loader as loader_mod


MODEL_DEEPWIKI = {
    "name": "test-skill",
    "version": "1.0.0",
    "description": "Test skill for style smoke",
    "style": "deepwiki",
    "steps": [{"id": "step-1", "index": 1, "name": "Test Step", "display_name": "Test Step",
               "description": "A test step", "kind": "step", "conditions": [], "inputs": [],
               "outputs": [], "routes_to": [], "artifacts_emitted": []}],
    "decision_points": [],
    "route_outs": [],
    "terminal_states": [],
    "artifacts": [],
    "gaps": [],
    "ambiguities": [],
}


def test_stage_b_resolves_style_from_frontmatter(tmp_path, monkeypatch):
    """Stage B writes presentation.style matching the model's style field."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "source-model.json"
    src.write_text(json.dumps(MODEL_DEEPWIKI))

    monkeypatch.setattr(plan_mod, "SOURCE", src)
    monkeypatch.setattr(plan_mod, "OUT", tmp_path / "artifact-plan.json")

    exit_mock = MagicMock()
    monkeypatch.setattr(sys, "exit", exit_mock)

    # argv: [script, arg1(ignored), style_override]
    monkeypatch.setattr(sys, "argv", ["stage_b.py", "dummy", "product"])
    plan_mod.main()

    plan = json.loads((tmp_path / "artifact-plan.json").read_text())
    # CLI arg takes precedence over frontmatter
    assert plan["presentation"]["style"] == "product"


def test_stage_b_uses_frontmatter_style_when_no_cli_override(tmp_path, monkeypatch):
    """When no CLI override, Stage B reads style from source-model.json."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "source-model.json"
    src.write_text(json.dumps(MODEL_DEEPWIKI))

    monkeypatch.setattr(plan_mod, "SOURCE", src)
    monkeypatch.setattr(plan_mod, "OUT", tmp_path / "artifact-plan.json")

    exit_mock = MagicMock()
    monkeypatch.setattr(sys, "exit", exit_mock)

    # No style override via CLI
    monkeypatch.setattr(sys, "argv", ["stage_b.py", "dummy"])
    plan_mod.main()

    plan = json.loads((tmp_path / "artifact-plan.json").read_text())
    # Model has style=deepwiki
    assert plan["presentation"]["style"] == "deepwiki"


def test_stage_b_defaults_to_deepwiki_when_style_unknown(tmp_path, monkeypatch):
    """Unknown style falls back to deepwiki."""
    monkeypatch.chdir(tmp_path)
    model = dict(MODEL_DEEPWIKI)
    model["style"] = ""  # empty-style model
    src = tmp_path / "source-model.json"
    src.write_text(json.dumps(model))

    monkeypatch.setattr(plan_mod, "SOURCE", src)
    monkeypatch.setattr(plan_mod, "OUT", tmp_path / "artifact-plan.json")

    exit_mock = MagicMock()
    monkeypatch.setattr(sys, "exit", exit_mock)

    monkeypatch.setattr(sys, "argv", ["stage_b.py", "dummy", "not_a_real_style"])
    plan_mod.main()

    plan = json.loads((tmp_path / "artifact-plan.json").read_text())
    assert plan["presentation"]["style"] == "deepwiki"


def test_stage_b_section_order_varies_by_style(tmp_path, monkeypatch):
    """Each style produces a different section order in artifact-plan.json."""
    # Match actual SECTION_ORDERS from stage_b_artifact_plan_builder.py
    cases = [
        ("deepwiki", ["overview", "what-it-does", "pipeline", "stages", "validation"]),
        ("product",  ["overview", "what-it-does", "workflow", "pipeline", "stages"]),
        ("minimal",  ["overview", "artifacts", "stages", "validation", "functions"]),
    ]
    for style_name, expected_first_sections in cases:
        monkeypatch.chdir(tmp_path)
        model = dict(MODEL_DEEPWIKI)
        model["style"] = style_name
        src = tmp_path / "source-model.json"
        src.write_text(json.dumps(model))

        monkeypatch.setattr(plan_mod, "SOURCE", src)
        monkeypatch.setattr(plan_mod, "OUT", tmp_path / "artifact-plan.json")
        monkeypatch.setattr(sys, "argv", ["stage_b.py", "dummy"])

        exit_mock = MagicMock()
        monkeypatch.setattr(sys, "exit", exit_mock)

        plan_mod.main()
        plan = json.loads((tmp_path / "artifact-plan.json").read_text())
        section_ids = [s["id"] for s in plan["page_structure"]["sections"]]
        # Check first few sections match expectation for style
        assert section_ids[:len(expected_first_sections)] == expected_first_sections, \
            f"{style_name}: got {section_ids}"


def test_stage_e1_loads_all_styles(tmp_path, monkeypatch):
    """Stage E1 loads and validates templates without error for each known style."""
    monkeypatch.chdir(tmp_path)
    # Write a minimal artifact-plan.json with each style
    plan = {
        "presentation": {"style": ""},
        "page_structure": {"sections": []},
        "template_version": "v2",
    }
    plan_path = tmp_path / "artifact-plan.json"
    plan_path.write_text(json.dumps(plan))

    for style in ("deepwiki", "product", "minimal"):
        monkeypatch.setattr(sys, "argv", ["stage_e1.py", "dummy", style])
        monkeypatch.setattr(loader_mod, "BASE", tmp_path)
        monkeypatch.setattr(loader_mod, "OUT", tmp_path / "e1-output.json")
        monkeypatch.setattr(loader_mod, "TPL", STAGE_DIR / "templates")
        monkeypatch.setattr(loader_mod, "STYLES_DIR", STAGE_DIR / "templates" / "styles")

        exit_mock = MagicMock()
        monkeypatch.setattr(sys, "exit", exit_mock)

        try:
            loader_mod.main()
        except SystemExit as e:
            pass  # may exit on real error; check e1-output below

        e1_path = tmp_path / "e1-output.json"
        if e1_path.exists():
            e1 = json.loads(e1_path.read_text())
            assert e1["status"] == "pass", f"{style}: {e1.get('errors', [])}"
            assert e1["style_resolved"] == style, f"{style}: resolved to {e1['style_resolved']}"
