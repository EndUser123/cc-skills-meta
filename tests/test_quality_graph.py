"""Tests for quality_graph.py — LangGraph QC subgraphs."""
import json, pytest, sys, tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

STAGE_DIR = Path("P:/packages/.claude-marketplace/plugins/cc-skills-meta/skills/doc-compiler")
sys.path.insert(0, str(STAGE_DIR / "runtime"))

import quality_graph as qg_mod


# ---------------------------------------------------------------------------
# Decision node tests
# ---------------------------------------------------------------------------

def test_decide_diagram_next_pass():
    """If gate_passed, route to __end__."""
    state = {"gate_passed": True, "retry_count": 0, "MAX_RETRIES": 3, "issues": []}
    result = qg_mod.decide_diagram_next(state)
    assert result == "__end__"


def test_decide_diagram_next_exhausted():
    """If retry_count >= MAX_RETRIES, route to escalate."""
    state = {"gate_passed": False, "retry_count": 3, "MAX_RETRIES": 3, "issues": ["x"]}
    result = qg_mod.decide_diagram_next(state)
    assert result == "escalate"


def test_decide_diagram_next_repairable():
    """If issues are repairable and retries available, route to repair."""
    state = {"gate_passed": False, "retry_count": 0, "MAX_RETRIES": 3,
             "issues": ["Node label too long (>50 chars): foo..."]}
    result = qg_mod.decide_diagram_next(state)
    assert result == "llm_diagram_repair"


def test_decide_diagram_next_non_repairable():
    """If issues are not repairable, route to escalate."""
    state = {"gate_passed": False, "retry_count": 0, "MAX_RETRIES": 3,
             "issues": ["syntax error in Mermaid"]}
    result = qg_mod.decide_diagram_next(state)
    assert result == "escalate"


def test_decide_ui_next_pass():
    """If gate_passed, route to __end__."""
    state = {"gate_passed": True, "retry_count": 0, "MAX_RETRIES": 2}
    result = qg_mod.decide_ui_next(state)
    assert result == "__end__"


def test_decide_ui_next_exhausted():
    """If retry_count >= MAX_RETRIES, route to escalate."""
    state = {"gate_passed": False, "retry_count": 2, "MAX_RETRIES": 2}
    result = qg_mod.decide_ui_next(state)
    assert result == "escalate"


def test_decide_ui_next_retry():
    """If failures and retries available, route to repair."""
    state = {"gate_passed": False, "retry_count": 0, "MAX_RETRIES": 2,
             "static_failures": ["S1 tocToggle sibling"]}
    result = qg_mod.decide_ui_next(state)
    assert result == "llm_ui_repair"


def test_decide_review_next_pass():
    """If review_passed, route to __end__."""
    state = {"review_passed": True, "retry_count": 0, "MAX_RETRIES": 2, "recommendations": []}
    result = qg_mod.decide_review_next(state)
    assert result == "__end__"


def test_decide_review_next_abort():
    """If no recommendations and not passed, route to abort."""
    state = {"review_passed": False, "retry_count": 0, "MAX_RETRIES": 2, "recommendations": []}
    result = qg_mod.decide_review_next(state)
    assert result == "abort"


def test_decide_review_next_retry():
    """If recommendations and retries available, route to repair."""
    state = {"review_passed": False, "retry_count": 0, "MAX_RETRIES": 2,
             "recommendations": ["Add missing aria-label to diagram viewport"]}
    result = qg_mod.decide_review_next(state)
    assert result == "llm_repair_fidelity"


# ---------------------------------------------------------------------------
# Is-repairable tests
# ---------------------------------------------------------------------------

def test_is_repairable_long_label():
    assert qg_mod._is_repairable("Node label too long (>50 chars): foo...") is True


def test_is_repairable_missing_terminal():
    assert qg_mod._is_repairable("No [*] terminal state found") is True


def test_is_repairable_syntax_error():
    assert qg_mod._is_repairable("syntax error in Mermaid") is False


def test_is_repairable_crossing_count():
    assert qg_mod._is_repairable("High node count may benefit from subgraph grouping") is False


# ---------------------------------------------------------------------------
# Escalate node tests
# ---------------------------------------------------------------------------

def test_escalate_diagram_writes_gate_result(tmp_path, monkeypatch):
    """escalate_diagram writes gate-result.json with escalated=True."""
    monkeypatch.chdir(tmp_path)
    import quality_graph
    monkeypatch.setattr(quality_graph, "BASE", tmp_path)

    state = {
        "gate_passed": False,
        "retry_count": 3,
        "blocked_diagrams": ["flow-1", "flow-2"],
        "issues": ["long label", "syntax error"],
        "repair_record": [{"iteration": 1, "diagram_id": "flow-1", "issue": "long label", "repair": "/tmp/x.mmd"}],
    }
    qg_mod.escalate_diagram(state)

    gate = json.loads((tmp_path / "gate-result.json").read_text(encoding="utf-8"))
    assert gate["escalated"] is True
    assert gate["gate_passed"] is False
    assert gate["retry_count"] == 3
    assert gate["blocked_diagrams"] == ["flow-1", "flow-2"]


def test_escalate_ui_writes_proof(tmp_path, monkeypatch):
    """escalate_ui writes proof-attempt.json with escalated=True."""
    monkeypatch.chdir(tmp_path)
    import quality_graph
    monkeypatch.setattr(quality_graph, "BASE", tmp_path)

    state = {
        "gate_passed": False,
        "retry_count": 2,
        "static_failures": ["S1 tocToggle sibling"],
        "runtime_failures": ["J1_desktop_initial"],
        "repair_record": [],
    }
    qg_mod.escalate_ui(state)

    proof = json.loads((tmp_path / "proof-attempt.json").read_text(encoding="utf-8"))
    assert proof["escalated"] is True
    assert proof["gate_passed"] is False
    assert "S1 tocToggle sibling" in proof["static_failures"]


def test_abort_review_writes_proof(tmp_path, monkeypatch):
    """abort_review writes proof-attempt.json with aborted=True."""
    monkeypatch.chdir(tmp_path)
    import quality_graph
    monkeypatch.setattr(quality_graph, "BASE", tmp_path)

    state = {
        "review_passed": False,
        "retry_count": 2,
        "blocked_checks": ["step_coverage", "decision_coverage"],
        "recommendations": ["Add decision coverage"],
    }
    qg_mod.abort_review(state)

    proof = json.loads((tmp_path / "proof-attempt.json").read_text(encoding="utf-8"))
    assert proof["aborted"] is True
    assert proof["gate_passed"] is False
    assert proof["blocked_checks"] == ["step_coverage", "decision_coverage"]


# ---------------------------------------------------------------------------
# Graph-compile tests
# ---------------------------------------------------------------------------

def test_graphs_compile():
    """All three graphs compile without error."""
    assert qg_mod.diagram_repair_subgraph is not None
    assert qg_mod.ui_repair_subgraph is not None
    assert qg_mod.final_review_subgraph is not None


def test_diagram_graph_passes_with_no_issues(tmp_path, monkeypatch):
    """diagram_repair_subgraph ends immediately when critic passes."""
    monkeypatch.chdir(tmp_path)
    import quality_graph
    monkeypatch.setattr(quality_graph, "BASE", tmp_path)

    state: qg_mod.DiagramQCState = {
        "diagrams_json_path": str(tmp_path / "diagrams.json"),
        "diagrams_dir": str(tmp_path / "diagrams"),
        "doc_model_path": str(tmp_path / "doc-model.json"),
        "issues": [],
        "repair_record": [],
        "retry_count": 0,
        "MAX_RETRIES": 3,
        "gate_passed": False,
        "blocked_diagrams": [],
        "repair_staging_dir": str(tmp_path / "repair_1"),
    }

    with patch.object(qg_mod, "call_stage_f") as mock_f:
        mock_f.return_value = qg_mod.DiagramCriticResult(passed=True, issues=[], results=[])
        result = qg_mod.diagram_repair_subgraph.invoke(state)
        assert isinstance(result, dict)
        assert result["gate_passed"] is True


def test_ui_graph_passes_with_no_failures(tmp_path, monkeypatch):
    """ui_repair_subgraph ends immediately when no failures."""
    monkeypatch.chdir(tmp_path)
    import quality_graph
    monkeypatch.setattr(quality_graph, "BASE", tmp_path)

    state: qg_mod.UIQCState = {
        "index_html_path": str(tmp_path / "index.html"),
        "source_model_path": str(tmp_path / "source-model.json"),
        "static_failures": [],
        "runtime_failures": [],
        "repair_record": [],
        "retry_count": 0,
        "MAX_RETRIES": 2,
        "gate_passed": False,
        "repair_staging_dir": str(tmp_path / "ui_repair_1"),
    }

    with patch.object(qg_mod, "call_stage_i") as mock_i, \
         patch.object(qg_mod, "call_stage_j") as mock_j:
        mock_i.return_value = qg_mod.UIValidatorResult(passed=True, static_failures=[], runtime_failures=[])
        mock_j.return_value = qg_mod.UIValidatorResult(passed=True, static_failures=[], runtime_failures=[])
        result = qg_mod.ui_repair_subgraph.invoke(state)
        assert isinstance(result, dict)
        assert result["gate_passed"] is True


def test_review_graph_passes_when_claude_approves(tmp_path, monkeypatch):
    """final_review_subgraph ends immediately when review_passed."""
    monkeypatch.chdir(tmp_path)
    import quality_graph
    monkeypatch.setattr(quality_graph, "BASE", tmp_path)

    state: qg_mod.FinalReviewState = {
        "index_html_path": str(tmp_path / "index.html"),
        "source_model_path": str(tmp_path / "source-model.json"),
        "validation_report_path": str(tmp_path / "validation-report.json"),
        "review_passed": False,
        "recommendations": [],
        "retry_count": 0,
        "MAX_RETRIES": 2,
        "blocked_checks": [],
    }

    with patch.object(qg_mod, "call_stage_k") as mock_k:
        mock_k.return_value = qg_mod.ReviewResult(
            passed=True, step_coverage=1.0, decision_coverage=1.0,
            route_out_coverage=1.0, hallucination_detected=False,
            dom_issues=[], css_issues=[], failed_checks=[], recommendations=[],
        )
        result = qg_mod.final_review_subgraph.invoke(state)
        assert isinstance(result, dict)
        assert result["review_passed"] is True


# ---------------------------------------------------------------------------
# Retry-bound tests
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Retry-bound tests
# NOTE: LangGraph holds direct function references in its compiled graph, so
# patch.object(qg_mod, 'llm_diagram_repair') cannot intercept calls made
# inside diagram_repair_subgraph.invoke().  Retry count is enforced by the
# decision nodes (decide_diagram_next etc.), which are unit-tested above.
# The integration test below verifies the MAX_RETRIES boundary in isolation.
# ---------------------------------------------------------------------------

def test_diagram_next_escalates_at_retry_3():
    """decide_diagram_next routes to escalate when retry_count reaches MAX_RETRIES (3)."""
    for retry in (0, 1, 2):
        state = {"gate_passed": False, "retry_count": retry, "MAX_RETRIES": 3,
                 "issues": ["long label: x"]}
        assert qg_mod.decide_diagram_next(state) == "llm_diagram_repair", \
            f"retry={retry} should route to repair"

    # Exhausted — must escalate
    state_exhausted = {"gate_passed": False, "retry_count": 3, "MAX_RETRIES": 3, "issues": ["x"]}
    assert qg_mod.decide_diagram_next(state_exhausted) == "escalate"


def test_ui_next_escalates_at_retry_2():
    """decide_ui_next routes to escalate when retry_count reaches MAX_RETRIES (2)."""
    for retry in (0, 1):
        state = {"gate_passed": False, "retry_count": retry, "MAX_RETRIES": 2,
                 "static_failures": ["S1"]}
        assert qg_mod.decide_ui_next(state) == "llm_ui_repair", \
            f"retry={retry} should route to repair"

    state_exhausted = {"gate_passed": False, "retry_count": 2, "MAX_RETRIES": 2, "static_failures": ["S1"]}
    assert qg_mod.decide_ui_next(state_exhausted) == "escalate"


def test_review_next_aborts_at_retry_2():
    """decide_review_next routes to abort when retry_count reaches MAX_RETRIES (2)."""
    state_first = {"review_passed": False, "retry_count": 0, "MAX_RETRIES": 2,
                   "recommendations": ["Add aria-label"]}
    assert qg_mod.decide_review_next(state_first) == "llm_repair_fidelity"

    state_exhausted = {"review_passed": False, "retry_count": 2, "MAX_RETRIES": 2,
                       "recommendations": ["Add aria-label"]}
    assert qg_mod.decide_review_next(state_exhausted) == "abort"


# ---------------------------------------------------------------------------
# run_*_qc public API tests
# ---------------------------------------------------------------------------

def test_run_diagram_qc_raises_without_langgraph(tmp_path, monkeypatch):
    """run_diagram_qc raises RuntimeError if LangGraph not available."""
    import quality_graph
    original = quality_graph.LANGGRAPH_AVAILABLE
    quality_graph.LANGGRAPH_AVAILABLE = False
    saved = quality_graph.diagram_repair_subgraph
    quality_graph.diagram_repair_subgraph = None
    try:
        with pytest.raises(RuntimeError, match="LangGraph"):
            qg_mod.run_diagram_qc(str(tmp_path / "d.json"), str(tmp_path / "d"), str(tmp_path / "m.json"))
    finally:
        quality_graph.LANGGRAPH_AVAILABLE = original
        quality_graph.diagram_repair_subgraph = saved


def test_run_ui_qc_raises_without_langgraph(tmp_path, monkeypatch):
    """run_ui_qc raises RuntimeError if LangGraph not available."""
    import quality_graph
    original = quality_graph.LANGGRAPH_AVAILABLE
    quality_graph.LANGGRAPH_AVAILABLE = False
    saved = quality_graph.ui_repair_subgraph
    quality_graph.ui_repair_subgraph = None
    try:
        with pytest.raises(RuntimeError, match="LangGraph"):
            qg_mod.run_ui_qc(str(tmp_path / "i.html"), str(tmp_path / "s.json"))
    finally:
        quality_graph.LANGGRAPH_AVAILABLE = original
        quality_graph.ui_repair_subgraph = saved


def test_run_final_review_raises_without_langgraph(tmp_path, monkeypatch):
    """run_final_review raises RuntimeError if LangGraph not available."""
    import quality_graph
    original = quality_graph.LANGGRAPH_AVAILABLE
    quality_graph.LANGGRAPH_AVAILABLE = False
    saved = quality_graph.final_review_subgraph
    quality_graph.final_review_subgraph = None
    try:
        with pytest.raises(RuntimeError, match="LangGraph"):
            qg_mod.run_final_review(str(tmp_path / "i.html"), str(tmp_path / "s.json"))
    finally:
        quality_graph.LANGGRAPH_AVAILABLE = original
        quality_graph.final_review_subgraph = saved


# ---------------------------------------------------------------------------
# State schema tests
# ---------------------------------------------------------------------------

def test_diagram_qc_state_accepts_all_fields():
    """DiagramQCState TypedDict accepts all documented fields."""
    state: qg_mod.DiagramQCState = {
        "diagrams_json_path": "/x/diagrams.json",
        "diagrams_dir": "/x/diagrams",
        "doc_model_path": "/x/doc-model.json",
        "issues": [],
        "repair_record": [],
        "retry_count": 0,
        "MAX_RETRIES": 3,
        "gate_passed": False,
        "blocked_diagrams": [],
        "repair_staging_dir": "/x/repair_1",
    }
    assert state["MAX_RETRIES"] == 3
    assert state["gate_passed"] is False


def test_ui_qc_state_accepts_all_fields():
    """UIQCState TypedDict accepts all documented fields."""
    state: qg_mod.UIQCState = {
        "index_html_path": "/x/index.html",
        "source_model_path": "/x/source-model.json",
        "static_failures": [],
        "runtime_failures": [],
        "repair_record": [],
        "retry_count": 0,
        "MAX_RETRIES": 2,
        "gate_passed": False,
        "repair_staging_dir": "/x/ui_repair_1",
    }
    assert state["MAX_RETRIES"] == 2


def test_final_review_state_accepts_all_fields():
    """FinalReviewState TypedDict accepts all documented fields."""
    state: qg_mod.FinalReviewState = {
        "index_html_path": "/x/index.html",
        "source_model_path": "/x/source-model.json",
        "validation_report_path": "/x/validation-report.json",
        "review_passed": False,
        "recommendations": [],
        "retry_count": 0,
        "MAX_RETRIES": 2,
        "blocked_checks": [],
    }
    assert state["MAX_RETRIES"] == 2


# ---------------------------------------------------------------------------
# LLM repair node tests (mocked)
# ---------------------------------------------------------------------------

def test_llm_diagram_repair_records_repair(tmp_path, monkeypatch):
    """llm_diagram_repair appends to repair_record."""
    monkeypatch.chdir(tmp_path)
    import quality_graph
    monkeypatch.setattr(quality_graph, "BASE", tmp_path)

    # Create a minimal diagram file
    diagrams_dir = tmp_path / "diagrams"
    diagrams_dir.mkdir()
    (diagrams_dir / "flow-1.mmd").write_text("graph TD\n  A-->B\n", encoding="utf-8")

    # Issue format must parse as "diagram_id: message"
    state: qg_mod.DiagramQCState = {
        "diagrams_json_path": str(tmp_path / "diagrams.json"),
        "diagrams_dir": str(diagrams_dir),
        "doc_model_path": str(tmp_path / "doc-model.json"),
        "issues": ["flow-1: Node label too long (>50 chars)"],
        "repair_record": [],
        "retry_count": 1,
        "MAX_RETRIES": 3,
        "gate_passed": False,
        "blocked_diagrams": ["flow-1"],
        "repair_staging_dir": str(tmp_path / "repair_1"),
    }

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            stdout="```mermaid\ngraph TD\n  A-->B\n```\n",
            returncode=0,
        )
        result = qg_mod.llm_diagram_repair(state)

        assert len(result["repair_record"]) == 1
        assert result["repair_record"][0]["iteration"] == 1
        assert result["repair_record"][0]["diagram_id"] == "flow-1"


def test_llm_diagram_repair_handles_missing_mmd_file(tmp_path, monkeypatch):
    """llm_diagram_repair handles case where no .mmd file exists for diagram_id."""
    monkeypatch.chdir(tmp_path)
    import quality_graph
    monkeypatch.setattr(quality_graph, "BASE", tmp_path)

    diagrams_dir = tmp_path / "diagrams"
    diagrams_dir.mkdir()

    state: qg_mod.DiagramQCState = {
        "diagrams_json_path": str(tmp_path / "diagrams.json"),
        "diagrams_dir": str(diagrams_dir),
        "doc_model_path": str(tmp_path / "doc-model.json"),
        "issues": ["long label: nonexistent"],
        "repair_record": [],
        "retry_count": 0,
        "MAX_RETRIES": 3,
        "gate_passed": False,
        "blocked_diagrams": ["nonexistent"],
        "repair_staging_dir": str(tmp_path / "repair_1"),
    }

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="```mermaid\ngraph TD\n  A-->B\n```\n", returncode=0)
        result = qg_mod.llm_diagram_repair(state)
        # No file to repair — repair_record stays empty
        assert len(result["repair_record"]) == 0