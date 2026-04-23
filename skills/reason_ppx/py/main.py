from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import asdict

from .classifier import classify_task
from .config import OrchestratorConfig
from .context_builder import build_context
from .frames import select_frames
from .models import Claim, ClaimStatus, ReasoningState, Severity, ClassificationResult, Finding, ExternalResult
from .policies import build_external_queries, should_run_second_round, should_use_external
from .adapters import execute_external_queries
from .synthesizer import finalize_answer, reconcile
from .utils import json_pretty, normalize_query


LEDGER_PATH = os.path.join(".claude", "state", "reason_ppx_ledger.json")


def load_ledger(config: OrchestratorConfig) -> dict:
    if not os.path.exists(LEDGER_PATH):
        return {}
    try:
        with open(LEDGER_PATH, "r") as f:
            data = json.load(f)
            # Check TTL (Widened to 24h as per config)
            now = time.time()
            valid_data = {}
            for k, v in data.items():
                ts = v.get("_timestamp", 0)
                if now - ts < config.evidence_store_ttl_hours * 3600:
                    valid_data[k] = v
            return valid_data
    except Exception:
        return {}


def save_ledger(query: str, state: ReasoningState):
    os.makedirs(os.path.dirname(LEDGER_PATH), exist_ok=True)
    norm_query = normalize_query(query)
    try:
        data = {}
        if os.path.exists(LEDGER_PATH):
            with open(LEDGER_PATH, "r") as f:
                data = json.load(f)
        
        state_dict = asdict(state)
        state_dict["_timestamp"] = time.time()
        data[norm_query] = state_dict
        
        with open(LEDGER_PATH, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def build_internal_draft(state: ReasoningState) -> ReasoningState:
    task = state.task.task_type.value if state.task else "general"
    state.internal_draft = (
        f"Task type: {task}\n"
        f"Primary frame: {state.primary_frame}\n"
        f"Challenger frame: {state.challenger_frame}\n\n"
        f"Best current answer:\n"
        f"- Start from the most likely correct path.\n"
        f"- Explicitly separate facts, inferences, and open questions.\n"
        f"- Prefer a recommendation that survives critique over one that only sounds clever.\n"
    )

    state.claims = [
        Claim(
            id="C1",
            text="The best final answer should be synthesized by the orchestrator, not delegated verbatim to one external model.",
            status=ClaimStatus.VERIFIED,
            impact=Severity.HIGH,
            evidence=["Architectural principle enforced by orchestrator design."]
        ),
        Claim(
            id="C2",
            text="Targeted external roles produce better results than giving all external models the same broad prompt.",
            status=ClaimStatus.INFERRED,
            impact=Severity.HIGH,
            evidence=[]
        ),
        Claim(
            id="C3",
            text="A second external round is only useful when contradictions materially affect the recommendation.",
            status=ClaimStatus.INFERRED,
            impact=Severity.MEDIUM,
            evidence=[]
        ),
    ]

    state.assumptions = [
        "External CLIs are installed and callable in the current environment.",
        "The user prefers stronger reasoning over minimal latency."
    ]
    state.unknowns = [
        "Which claim in the draft would fail first under real repo/file evidence?"
    ]
    return state


def orchestrate(
    query: str,
    debug: bool = False,
    no_external: bool = False,
    mode: str = "auto",
    force_choice: bool = False,
    kill: bool = False,
    invert: bool = False,
    ship: bool = False,
    output: str = "compact",
) -> ReasoningState:
    # Build config with CLI overrides
    config = OrchestratorConfig(
        override_no_external=no_external,
        override_mode=mode,
        override_force_choice=force_choice,
        override_kill=kill,
        override_invert=invert,
        override_ship=ship,
        override_output=output,
    )
    norm_query = normalize_query(query)

    # Check ledger for cross-turn data
    ledger = load_ledger(config)
    cached_entry = ledger.get(norm_query)

    if cached_entry:
        # Reconstruct state from ledger to avoid Amnesia Loop
        state = ReasoningState(query=query)
        state.execution_notes.append(f"ledger_hit=true")

        # Basic fields
        for field in ["final_answer", "confidence_summary", "primary_frame", "challenger_frame",
                      "internal_draft", "strategy_shift", "assumptions", "unknowns", "contradictions"]:
            if field in cached_entry:
                setattr(state, field, cached_entry[field])

        # Nested objects
        if cached_entry.get("task"):
            state.task = ClassificationResult(**cached_entry["task"])

        if cached_entry.get("claims"):
            state.claims = [Claim(**c) for c in cached_entry["claims"]]

        if cached_entry.get("external_results"):
            # Deep reconstruction for external results and findings
            results = []
            for r in cached_entry["external_results"]:
                normalized = []
                for f in r.get("normalized", []):
                    normalized.append(Finding(**f))
                r_copy = dict(r)
                r_copy["normalized"] = normalized
                results.append(ExternalResult(**r_copy))
            state.external_results = results

        # Re-apply CLI flags even on ledger hit
        state.force_choice = force_choice
        state.kill = kill
        state.invert = invert
        state.ship = ship

        if state.final_answer:
            if debug:
                print(json_pretty(asdict(state)))
            else:
                print(finalize_answer(state, output_format=output))
            return state

    state = ReasoningState(query=query)
    state.task = classify_task(query)
    state.context = build_context(query)
    # Pass mode override to frame selection
    state.primary_frame, state.challenger_frame = select_frames(state.task.task_type, override_mode=mode)
    state = build_internal_draft(state)

    # Store decision flags in state for synthesizer
    state.force_choice = force_choice
    state.kill = kill
    state.invert = invert
    state.ship = ship

    # Emit routing decision for observability
    state.execution_notes.append(
        f"route=external" if should_use_external(state, config) else "route=local_only"
    )
    state.execution_notes.append(
        f"missing_capabilities={state.task.missing_capabilities}"
    )
    state.execution_notes.append(
        f"data_class={state.context.data_class.value}"
    )

    round_number = 1
    if should_use_external(state, config):
        state.external_queries = build_external_queries(state, config)
        state.external_results = execute_external_queries(state.external_queries, config)
        state = reconcile(state)

        while should_run_second_round(state, config, round_number):
            round_number += 1
            next_queries = build_external_queries(state, config)
            more_results = execute_external_queries(next_queries, config)
            state.external_results.extend(more_results)
            state = reconcile(state)
            if round_number >= config.max_external_rounds:
                break

    state.final_answer = finalize_answer(state, output_format=output)
    state.confidence_summary = (
        f"Task={state.task.task_type.value}; "
        f"classification_confidence={state.task.confidence:.2f}; "
        f"contradictions={len(state.contradictions)}; "
        f"missing_capabilities={[c.value for c in state.task.missing_capabilities]}"
    )

    # Save to ledger for cross-turn provenance
    save_ledger(query, state)

    if debug:
        print(json_pretty(asdict(state)))
    else:
        print(state.final_answer)

    return state


def main():
    parser = argparse.ArgumentParser(description="THINK Orchestrator")
    parser.add_argument("--query", required=True, help="User query")
    parser.add_argument("--debug", action="store_true", help="Print full state as JSON")
    parser.add_argument("--no-external", action="store_true", help="Skip external calls, local reasoning only")
    parser.add_argument("--mode", default="auto", help="Reasoning mode: auto, review, design, diagnose, optimize, decide, explore, off, execute")
    parser.add_argument("--force-choice", action="store_true", help="Pick one option, no both-sidesing")
    parser.add_argument("--kill", action="store_true", help="Prune aggressively")
    parser.add_argument("--invert", action="store_true", help="Analyze failure paths")
    parser.add_argument("--ship", action="store_true", help="Add execution checklist")
    parser.add_argument("--output", default="compact", help="Output format: compact, verbose, json")
    args = parser.parse_args()
    orchestrate(
        args.query,
        debug=args.debug,
        no_external=args.no_external,
        mode=args.mode,
        force_choice=args.force_choice,
        kill=args.kill,
        invert=args.invert,
        ship=args.ship,
        output=args.output,
    )


if __name__ == "__main__":
    main()
