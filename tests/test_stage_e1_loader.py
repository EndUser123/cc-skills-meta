"""Tests for stage_e1_loader (template loader / validator)."""
import json, sys
from pathlib import Path
from unittest.mock import MagicMock

STAGE_DIR = Path("P:/packages/.claude-marketplace/plugins/cc-skills-meta/skills/doc-compiler")
sys.path.insert(0, str(STAGE_DIR))

import stage_e1_loader as loader_mod


def make_plan(style: str = "deepwiki") -> dict:
    return {
        "presentation": {"style": style},
        "page_structure": {"sections": []},
        "template_version": "v2",
    }


def test_stage_e1_loads_valid_plan(tmp_path, monkeypatch):
    """Stage E1 passes when given a valid artifact-plan.json."""
    monkeypatch.chdir(tmp_path)
    plan = make_plan()
    (tmp_path / "artifact-plan.json").write_text(json.dumps(plan))

    monkeypatch.setattr(loader_mod, "BASE", tmp_path)
    monkeypatch.setattr(loader_mod, "OUT", tmp_path / "e1-output.json")
    monkeypatch.setattr(loader_mod, "TPL", STAGE_DIR / "templates")
    monkeypatch.setattr(loader_mod, "STYLES_DIR", STAGE_DIR / "templates" / "styles")

    exit_mock = MagicMock()
    monkeypatch.setattr(sys, "exit", exit_mock)
    monkeypatch.setattr(sys, "argv", ["stage_e1.py", "dummy"])

    loader_mod.main()

    e1 = json.loads((tmp_path / "e1-output.json").read_text())
    assert e1["status"] == "pass"
    assert e1["style_resolved"] == "deepwiki"


def test_stage_e1_resolves_deepwiki_style(tmp_path, monkeypatch):
    """Stage E1 resolves deepwiki style from plan."""
    monkeypatch.chdir(tmp_path)
    plan = make_plan("deepwiki")
    (tmp_path / "artifact-plan.json").write_text(json.dumps(plan))

    monkeypatch.setattr(loader_mod, "BASE", tmp_path)
    monkeypatch.setattr(loader_mod, "OUT", tmp_path / "e1-output.json")
    monkeypatch.setattr(loader_mod, "TPL", STAGE_DIR / "templates")
    monkeypatch.setattr(loader_mod, "STYLES_DIR", STAGE_DIR / "templates" / "styles")

    exit_mock = MagicMock()
    monkeypatch.setattr(sys, "exit", exit_mock)
    monkeypatch.setattr(sys, "argv", ["stage_e1.py", "dummy"])

    loader_mod.main()

    e1 = json.loads((tmp_path / "e1-output.json").read_text())
    assert e1["style_resolved"] == "deepwiki"


def test_stage_e1_resolves_product_style(tmp_path, monkeypatch):
    """Stage E1 resolves product style from plan."""
    monkeypatch.chdir(tmp_path)
    plan = make_plan("product")
    (tmp_path / "artifact-plan.json").write_text(json.dumps(plan))

    monkeypatch.setattr(loader_mod, "BASE", tmp_path)
    monkeypatch.setattr(loader_mod, "OUT", tmp_path / "e1-output.json")
    monkeypatch.setattr(loader_mod, "TPL", STAGE_DIR / "templates")
    monkeypatch.setattr(loader_mod, "STYLES_DIR", STAGE_DIR / "templates" / "styles")

    exit_mock = MagicMock()
    monkeypatch.setattr(sys, "exit", exit_mock)
    monkeypatch.setattr(sys, "argv", ["stage_e1.py", "dummy"])

    loader_mod.main()

    e1 = json.loads((tmp_path / "e1-output.json").read_text())
    assert e1["style_resolved"] == "product"


def test_stage_e1_resolves_minimal_style(tmp_path, monkeypatch):
    """Stage E1 resolves minimal style from plan."""
    monkeypatch.chdir(tmp_path)
    plan = make_plan("minimal")
    (tmp_path / "artifact-plan.json").write_text(json.dumps(plan))

    monkeypatch.setattr(loader_mod, "BASE", tmp_path)
    monkeypatch.setattr(loader_mod, "OUT", tmp_path / "e1-output.json")
    monkeypatch.setattr(loader_mod, "TPL", STAGE_DIR / "templates")
    monkeypatch.setattr(loader_mod, "STYLES_DIR", STAGE_DIR / "templates" / "styles")

    exit_mock = MagicMock()
    monkeypatch.setattr(sys, "exit", exit_mock)
    monkeypatch.setattr(sys, "argv", ["stage_e1.py", "dummy"])

    loader_mod.main()

    e1 = json.loads((tmp_path / "e1-output.json").read_text())
    assert e1["style_resolved"] == "minimal"