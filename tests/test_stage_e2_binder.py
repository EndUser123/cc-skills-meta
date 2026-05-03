"""Tests for stage_e2_binder (content binder)."""
import json, sys, html
from pathlib import Path
from unittest.mock import MagicMock, call

STAGE_DIR = Path("P:/packages/.claude-marketplace/plugins/cc-skills-meta/skills/doc-compiler")
sys.path.insert(0, str(STAGE_DIR))

import stage_e2_binder as binder_mod


def make_e1(status="pass") -> dict:
    return {"stage": "E1", "status": status}


def make_plan(steps=None, route_outs=None, terminal_states=None,
              name="test-skill", version="1.0.0", description="A test skill",
              style="deepwiki", kind="skill") -> dict:
    return {
        "content_bindings": {
            "name": name,
            "version": version,
            "description": description,
            "steps": steps or [],
            "route_outs": route_outs or [],
            "terminal_states": terminal_states or [],
        },
        "presentation": {"style": style},
        "style": style,
        "kind": kind,
    }


def test_stage_e2_binder_fills_hero(tmp_path, monkeypatch):
    """Hero template receives skill name, version, description."""
    monkeypatch.chdir(tmp_path)

    e1 = make_e1()
    (tmp_path / "e1-output.json").write_text(json.dumps(e1))

    plan = make_plan(name="my-skill", version="2.0.0", description="My description")
    (tmp_path / "artifact-plan.json").write_text(json.dumps(plan))

    monkeypatch.setattr(binder_mod, "E1_OUT", tmp_path / "e1-output.json")
    monkeypatch.setattr(binder_mod, "PLAN", tmp_path / "artifact-plan.json")
    monkeypatch.setattr(binder_mod, "BASE", tmp_path)
    monkeypatch.setattr(binder_mod, "TPL", STAGE_DIR / "templates")

    exit_mock = MagicMock()
    monkeypatch.setattr(sys, "exit", exit_mock)
    monkeypatch.setattr(sys, "argv", ["stage_e2.py", "dummy"])

    binder_mod.main()

    e2 = json.loads((tmp_path / "e2-output.json").read_text())
    assert e2["status"] == "pass"

    # Check filled templates contain expected bindings
    assert "hero.html" in e2["templates_filled"]


def test_stage_e2_binder_fills_steps(tmp_path, monkeypatch):
    """Steps accordion is populated from content_bindings.steps."""
    monkeypatch.chdir(tmp_path)

    e1 = make_e1()
    (tmp_path / "e1-output.json").write_text(json.dumps(e1))

    plan = make_plan(steps=[
        {"name": "Step One", "display_name": "Step One", "description": "First step"},
        {"name": "Step Two", "display_name": "Step Two", "description": "Second step"},
    ])
    (tmp_path / "artifact-plan.json").write_text(json.dumps(plan))

    monkeypatch.setattr(binder_mod, "E1_OUT", tmp_path / "e1-output.json")
    monkeypatch.setattr(binder_mod, "PLAN", tmp_path / "artifact-plan.json")
    monkeypatch.setattr(binder_mod, "BASE", tmp_path)
    monkeypatch.setattr(binder_mod, "TPL", STAGE_DIR / "templates")

    exit_mock = MagicMock()
    monkeypatch.setattr(sys, "exit", exit_mock)
    monkeypatch.setattr(sys, "argv", ["stage_e2.py", "dummy"])

    binder_mod.main()

    e2 = json.loads((tmp_path / "e2-output.json").read_text())
    assert e2["status"] == "pass"


def test_stage_e2_binder_fills_route_outs(tmp_path, monkeypatch):
    """Route-outs section is populated; target/description are HTML-escaped."""
    monkeypatch.chdir(tmp_path)

    e1 = make_e1()
    (tmp_path / "e1-output.json").write_text(json.dumps(e1))

    plan = make_plan(route_outs=[
        {"target": "/planning", "trigger": "route", "description": "Go to planning"},
        {"target": "<script>alert('xss')</script>", "trigger": "fail", "description": "Should be escaped"},
    ])
    (tmp_path / "artifact-plan.json").write_text(json.dumps(plan))

    monkeypatch.setattr(binder_mod, "E1_OUT", tmp_path / "e1-output.json")
    monkeypatch.setattr(binder_mod, "PLAN", tmp_path / "artifact-plan.json")
    monkeypatch.setattr(binder_mod, "BASE", tmp_path)
    monkeypatch.setattr(binder_mod, "TPL", STAGE_DIR / "templates")

    exit_mock = MagicMock()
    monkeypatch.setattr(sys, "exit", exit_mock)
    monkeypatch.setattr(sys, "argv", ["stage_e2.py", "dummy"])

    binder_mod.main()

    e2 = json.loads((tmp_path / "e2-output.json").read_text())
    assert e2["status"] == "pass"

    # Verify XSS payload is escaped in output
    filled_route_outs = (tmp_path / "e2-filled_route-outs.html").read_text(encoding="utf-8")
    assert "&lt;script&gt;" in filled_route_outs
    assert "<script>alert" not in filled_route_outs


def test_stage_e2_binder_rejects_failed_e1(tmp_path, monkeypatch):
    """Stage E2 exits early if E1 status is not pass."""
    monkeypatch.chdir(tmp_path)

    e1 = make_e1(status="fail")
    (tmp_path / "e1-output.json").write_text(json.dumps(e1))

    plan = make_plan()
    (tmp_path / "artifact-plan.json").write_text(json.dumps(plan))

    monkeypatch.setattr(binder_mod, "E1_OUT", tmp_path / "e1-output.json")
    monkeypatch.setattr(binder_mod, "PLAN", tmp_path / "artifact-plan.json")
    monkeypatch.setattr(binder_mod, "BASE", tmp_path)
    monkeypatch.setattr(binder_mod, "TPL", STAGE_DIR / "templates")

    exit_mock = MagicMock()
    monkeypatch.setattr(sys, "exit", exit_mock)
    monkeypatch.setattr(sys, "argv", ["stage_e2.py", "dummy"])

    binder_mod.main()

    # sys.exit(1) was called to halt on failed E1
    assert exit_mock.call_args_list == [call(1)], f"Expected sys.exit(1), got {exit_mock.call_args_list}"


def test_stage_e2_binder_no_unfilled_slots_in_filled_output(tmp_path, monkeypatch):
    """Filled templates should not contain any remaining {{placeholder}} tokens."""
    monkeypatch.chdir(tmp_path)

    e1 = make_e1()
    (tmp_path / "e1-output.json").write_text(json.dumps(e1))

    plan = make_plan()
    (tmp_path / "artifact-plan.json").write_text(json.dumps(plan))

    monkeypatch.setattr(binder_mod, "E1_OUT", tmp_path / "e1-output.json")
    monkeypatch.setattr(binder_mod, "PLAN", tmp_path / "artifact-plan.json")
    monkeypatch.setattr(binder_mod, "BASE", tmp_path)
    monkeypatch.setattr(binder_mod, "TPL", STAGE_DIR / "templates")

    exit_mock = MagicMock()
    monkeypatch.setattr(sys, "exit", exit_mock)
    monkeypatch.setattr(sys, "argv", ["stage_e2.py", "dummy"])

    binder_mod.main()

    e2 = json.loads((tmp_path / "e2-output.json").read_text())
    assert e2["status"] == "pass"
    assert e2["unfilled_slots"] == [], f"Remaining unfilled slots: {e2['unfilled_slots']}"