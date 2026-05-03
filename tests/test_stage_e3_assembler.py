"""Tests for stage_e3_assembler (CSS/JS style assembler)."""
import json, sys
from pathlib import Path
from unittest.mock import MagicMock

STAGE_DIR = Path("P:/packages/.claude-marketplace/plugins/cc-skills-meta/skills/doc-compiler")
sys.path.insert(0, str(STAGE_DIR))

import stage_e3_assembler as asm_mod


def make_e2(status="pass") -> dict:
    return {"stage": "E2", "status": status}


def make_plan(style="deepwiki", palette="tailwind-modern") -> dict:
    return {
        "presentation": {"style": style},
        "style": style,
        "ui_config": {"palette": palette},
    }


def test_stage_e3_assembles_css_with_deepwiki_style(tmp_path, monkeypatch):
    """Deepwiki style CSS is assembled from style overlay + shared layers."""
    monkeypatch.chdir(tmp_path)

    e2 = make_e2()
    (tmp_path / "e2-output.json").write_text(json.dumps(e2))

    plan = make_plan(style="deepwiki")
    (tmp_path / "artifact-plan.json").write_text(json.dumps(plan))

    monkeypatch.setattr(asm_mod, "E2_OUT", tmp_path / "e2-output.json")
    monkeypatch.setattr(asm_mod, "BASE", tmp_path)
    monkeypatch.setattr(asm_mod, "TPL", STAGE_DIR / "templates")
    monkeypatch.setattr(asm_mod, "STYLES_DIR", STAGE_DIR / "templates" / "styles")
    monkeypatch.setattr(asm_mod, "PALETTES_FILE", STAGE_DIR / "templates" / "mermaid-palettes.json")

    exit_mock = MagicMock()
    monkeypatch.setattr(sys, "exit", exit_mock)
    monkeypatch.setattr(sys, "argv", ["stage_e3.py", "dummy"])

    asm_mod.main()

    e3 = json.loads((tmp_path / "e3-output.json").read_text())
    assert e3["status"] == "pass"
    assert e3["style"] == "deepwiki"
    assert len(e3["css_parts"]) > 0


def test_stage_e3_assembles_css_with_product_style(tmp_path, monkeypatch):
    """Product style CSS is assembled correctly."""
    monkeypatch.chdir(tmp_path)

    e2 = make_e2()
    (tmp_path / "e2-output.json").write_text(json.dumps(e2))

    plan = make_plan(style="product")
    (tmp_path / "artifact-plan.json").write_text(json.dumps(plan))

    monkeypatch.setattr(asm_mod, "E2_OUT", tmp_path / "e2-output.json")
    monkeypatch.setattr(asm_mod, "BASE", tmp_path)
    monkeypatch.setattr(asm_mod, "TPL", STAGE_DIR / "templates")
    monkeypatch.setattr(asm_mod, "STYLES_DIR", STAGE_DIR / "templates" / "styles")
    monkeypatch.setattr(asm_mod, "PALETTES_FILE", STAGE_DIR / "templates" / "mermaid-palettes.json")

    exit_mock = MagicMock()
    monkeypatch.setattr(sys, "exit", exit_mock)
    monkeypatch.setattr(sys, "argv", ["stage_e3.py", "dummy"])

    asm_mod.main()

    e3 = json.loads((tmp_path / "e3-output.json").read_text())
    assert e3["status"] == "pass"
    assert e3["style"] == "product"


def test_stage_e3_assembles_css_with_minimal_style(tmp_path, monkeypatch):
    """Minimal style CSS is assembled correctly."""
    monkeypatch.chdir(tmp_path)

    e2 = make_e2()
    (tmp_path / "e2-output.json").write_text(json.dumps(e2))

    plan = make_plan(style="minimal")
    (tmp_path / "artifact-plan.json").write_text(json.dumps(plan))

    monkeypatch.setattr(asm_mod, "E2_OUT", tmp_path / "e2-output.json")
    monkeypatch.setattr(asm_mod, "BASE", tmp_path)
    monkeypatch.setattr(asm_mod, "TPL", STAGE_DIR / "templates")
    monkeypatch.setattr(asm_mod, "STYLES_DIR", STAGE_DIR / "templates" / "styles")
    monkeypatch.setattr(asm_mod, "PALETTES_FILE", STAGE_DIR / "templates" / "mermaid-palettes.json")

    exit_mock = MagicMock()
    monkeypatch.setattr(sys, "exit", exit_mock)
    monkeypatch.setattr(sys, "argv", ["stage_e3.py", "dummy"])

    asm_mod.main()

    e3 = json.loads((tmp_path / "e3-output.json").read_text())
    assert e3["status"] == "pass"
    assert e3["style"] == "minimal"


def test_stage_e3_style_overlay_is_used_not_shared(tmp_path, monkeypatch):
    """Style-specific CSS (deepwiki.css) is loaded via read_optional, not shared path."""
    monkeypatch.chdir(tmp_path)

    e2 = make_e2()
    (tmp_path / "e2-output.json").write_text(json.dumps(e2))

    plan = make_plan(style="deepwiki")
    (tmp_path / "artifact-plan.json").write_text(json.dumps(plan))

    monkeypatch.setattr(asm_mod, "E2_OUT", tmp_path / "e2-output.json")
    monkeypatch.setattr(asm_mod, "BASE", tmp_path)
    monkeypatch.setattr(asm_mod, "TPL", STAGE_DIR / "templates")
    monkeypatch.setattr(asm_mod, "STYLES_DIR", STAGE_DIR / "templates" / "styles")
    monkeypatch.setattr(asm_mod, "PALETTES_FILE", STAGE_DIR / "templates" / "mermaid-palettes.json")

    exit_mock = MagicMock()
    monkeypatch.setattr(sys, "exit", exit_mock)
    monkeypatch.setattr(sys, "argv", ["stage_e3.py", "dummy"])

    asm_mod.main()

    e3 = json.loads((tmp_path / "e3-output.json").read_text())
    # css_parts should include the style-specific override
    assert "style/deepwiki.css" in e3["css_parts"], \
        f"Expected style overlay in css_parts, got: {e3['css_parts']}"


def test_stage_e3_rejects_failed_e2(tmp_path, monkeypatch):
    """Stage E3 exits early if E2 status is not pass."""
    monkeypatch.chdir(tmp_path)

    e2 = make_e2(status="fail")
    (tmp_path / "e2-output.json").write_text(json.dumps(e2))

    plan = make_plan()
    (tmp_path / "artifact-plan.json").write_text(json.dumps(plan))

    monkeypatch.setattr(asm_mod, "E2_OUT", tmp_path / "e2-output.json")
    monkeypatch.setattr(asm_mod, "BASE", tmp_path)
    monkeypatch.setattr(asm_mod, "TPL", STAGE_DIR / "templates")
    monkeypatch.setattr(asm_mod, "STYLES_DIR", STAGE_DIR / "templates" / "styles")
    monkeypatch.setattr(asm_mod, "PALETTES_FILE", STAGE_DIR / "templates" / "mermaid-palettes.json")

    exit_mock = MagicMock()
    monkeypatch.setattr(sys, "exit", exit_mock)
    monkeypatch.setattr(sys, "argv", ["stage_e3.py", "dummy"])

    asm_mod.main()

    # sys.exit(1) was called to halt on failed E2
    assert len(exit_mock.call_args_list) == 1
    assert exit_mock.call_args_list[0][0][0] == 1, \
        f"Expected sys.exit(1), got {exit_mock.call_args_list}"


def test_stage_e3_inlines_palette(tmp_path, monkeypatch):
    """Selected palette is inlined into the JS block."""
    monkeypatch.chdir(tmp_path)

    e2 = make_e2()
    (tmp_path / "e2-output.json").write_text(json.dumps(e2))

    plan = make_plan(style="deepwiki", palette="nord")
    (tmp_path / "artifact-plan.json").write_text(json.dumps(plan))

    monkeypatch.setattr(asm_mod, "E2_OUT", tmp_path / "e2-output.json")
    monkeypatch.setattr(asm_mod, "BASE", tmp_path)
    monkeypatch.setattr(asm_mod, "TPL", STAGE_DIR / "templates")
    monkeypatch.setattr(asm_mod, "STYLES_DIR", STAGE_DIR / "templates" / "styles")
    monkeypatch.setattr(asm_mod, "PALETTES_FILE", STAGE_DIR / "templates" / "mermaid-palettes.json")

    exit_mock = MagicMock()
    monkeypatch.setattr(sys, "exit", exit_mock)
    monkeypatch.setattr(sys, "argv", ["stage_e3.py", "dummy"])

    asm_mod.main()

    e3 = json.loads((tmp_path / "e3-output.json").read_text())
    assert e3["status"] == "pass"
    assert e3["palette_inlined"] == "nord"

    js_block = (tmp_path / "e3_js_block.js").read_text(encoding="utf-8")
    assert "const PALETTES" in js_block


def test_stage_e3_css_size_is_nonzero(tmp_path, monkeypatch):
    """CSS block is assembled and has non-zero size."""
    monkeypatch.chdir(tmp_path)

    e2 = make_e2()
    (tmp_path / "e2-output.json").write_text(json.dumps(e2))

    plan = make_plan()
    (tmp_path / "artifact-plan.json").write_text(json.dumps(plan))

    monkeypatch.setattr(asm_mod, "E2_OUT", tmp_path / "e2-output.json")
    monkeypatch.setattr(asm_mod, "BASE", tmp_path)
    monkeypatch.setattr(asm_mod, "TPL", STAGE_DIR / "templates")
    monkeypatch.setattr(asm_mod, "STYLES_DIR", STAGE_DIR / "templates" / "styles")
    monkeypatch.setattr(asm_mod, "PALETTES_FILE", STAGE_DIR / "templates" / "mermaid-palettes.json")

    exit_mock = MagicMock()
    monkeypatch.setattr(sys, "exit", exit_mock)
    monkeypatch.setattr(sys, "argv", ["stage_e3.py", "dummy"])

    asm_mod.main()

    e3 = json.loads((tmp_path / "e3-output.json").read_text())
    assert e3["css_size"] > 0, "CSS block should have non-zero size"
    assert e3["js_size"] > 0, "JS block should have non-zero size"