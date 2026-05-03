#!/usr/bin/env python3
"""doc-compiler Orchestrator

Runs all 12 stages of the doc-compiler pipeline in order.
Each stage reads its input artifacts and emits its output artifact.

Usage:
    python -m doc_compiler.runtime.orchestrator [--target <path>]

The target is a SKILL.md, plugin.json, README.md, or workflow YAML/JSON file.

Environment:
    DOCC_TARGET  — fallback target path if --target not provided
"""
import json, os, sys, subprocess
from pathlib import Path
from datetime import datetime

BASE = Path("P:/packages/cc-skills-meta/skills/doc-compiler")
RUNTIME = BASE / "runtime"

STAGES = [
    ("A", "stage_a_source_extractor"),
    ("B", "stage_b_doc_model_builder"),
    ("C", "stage_c_diagram_strategy_router"),
    ("D", "stage_d_guide_loader"),
    ("E", "stage_e_diagram_generator"),
    ("F", "stage_f_diagram_critic_gate"),
    ("G", "stage_g_artifact_plan_builder"),
    ("H", "stage_h_template_html_emitter"),
    ("I", "stage_i_static_validator"),
    ("J", "stage_j_runtime_validator"),
    ("K", "stage_k_external_critic"),
    ("L", "stage_l_emit_proof_bundle"),
]


def get_target() -> Path:
    """Resolve the target file path from CLI or environment."""
    if len(sys.argv) > 1 and sys.argv[1] == "--target":
        target = Path(sys.argv[2])
    elif len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        target = Path(sys.argv[1])
    else:
        target_path = os.environ.get("DOCC_TARGET", "")
        if not target_path:
            print("ERROR: Provide target path as CLI arg or set DOCC_TARGET", file=sys.stderr)
            print("Usage: python -m doc_compiler.runtime.orchestrator [--target] <path>", file=sys.stderr)
            sys.exit(1)
        target = Path(target_path)
    return target


def run_stage(stage_name: str, stage_module: str, target: Path) -> bool:
    """Run a single stage and return whether it passed."""
    stage_path = RUNTIME / f"{stage_module}.py"
    if not stage_path.exists():
        print(f"  ERROR: {stage_path} not found", file=sys.stderr)
        return False

    env = os.environ.copy()
    env["DOCC_TARGET"] = str(target.resolve())

    print(f"\n{'='*60}")
    print(f"Stage {stage_name}: {stage_module}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(
            [sys.executable, str(stage_path)],
            cwd=str(BASE),
            env=env,
            capture_output=False,
            text=True,
            timeout=300,
        )
        passed = result.returncode == 0
        status = "PASS" if passed else "FAIL"
        print(f"Stage {stage_name}: {status} (exit {result.returncode})")
        return passed
    except subprocess.TimeoutExpired:
        print(f"Stage {stage_name}: FAIL — timeout after 300s", file=sys.stderr)
        return False
    except Exception as ex:
        print(f"Stage {stage_name}: FAIL — {ex}", file=sys.stderr)
        return False


def main() -> None:
    print(f"doc-compiler orchestrator")
    print(f"Started: {datetime.now().isoformat()}")
    print(f"Base: {BASE}")

    target = get_target()
    print(f"Target: {target}")
    if not target.exists():
        print(f"ERROR: Target file does not exist: {target}", file=sys.stderr)
        sys.exit(1)

    # Verify runtime directory structure
    if not RUNTIME.exists():
        print(f"ERROR: Runtime directory not found: {RUNTIME}", file=sys.stderr)
        sys.exit(1)

    stage_results = {}
    failed = False

    for stage_name, stage_module in STAGES:
        passed = run_stage(stage_name, stage_module, target)
        stage_results[stage_name] = passed
        if not passed:
            failed = True
            print(f"\nStage {stage_name} FAILED — stopping pipeline.")
            break

    # Summary
    print(f"\n{'='*60}")
    print("PIPELINE SUMMARY")
    print(f"{'='*60}")
    for name, passed in stage_results.items():
        status = "PASS" if passed else "FAIL"
        icon = "✓" if passed else "✗"
        print(f"  {icon} Stage {name}: {status}")

    if failed:
        print("\nPipeline FAILED — some stages did not pass.")
        sys.exit(1)
    else:
        print("\nPipeline COMPLETED — all stages passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()