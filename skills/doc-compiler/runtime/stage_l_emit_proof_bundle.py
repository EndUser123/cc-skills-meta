#!/usr/bin/env python3
"""Stage L: Emit Proof Bundle for doc-compiler.

Reads all validation artifacts and emits proof-bundle.json.
This is the final stage — it certifies that the pipeline completed successfully.
Emits: proof-bundle.json

Required prior stages: I (static validation), J (runtime validation), K (external critic)
must all pass before this stage can emit a valid bundle.
"""
import json, sys
from pathlib import Path
from datetime import datetime

BASE = Path("P:/packages/cc-skills-meta/skills/doc-compiler")

# All stage outputs this bundle aggregates
STAGE_OUTPUTS = {
    "stage_a": BASE / "source-model.json",
    "stage_b": BASE / "doc-model.json",
    "stage_c": BASE / "diagram-plan.json",
    "stage_d": BASE / "guides-loaded.json",
    "stage_e": BASE / "diagrams.json",
    "stage_f": BASE / "gate-result.json",
    "stage_g": BASE / "artifact-plan.json",
    "stage_h": BASE / "index.html",
    "stage_i": BASE / "static-validation.json",
    "stage_j": BASE / "runtime-validation.json",
    "stage_k": BASE / "validation-report.json",
    "stage_l": BASE / "proof-metadata.json",  # from stage I emit
}


def load_json(p: Path) -> dict:
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def check_stage(name: str, path: Path) -> dict:
    """Check a stage output and return its status."""
    if not path.exists():
        return {"name": name, "exists": False, "passed": False, "error": "file not found"}

    try:
        data = load_json(path)
        passed = data.get("passed", data.get("gate_passed", False))
        return {
            "name": name,
            "exists": True,
            "passed": passed,
            "size_bytes": path.stat().st_size,
            "key_data": data.get("summary", data.get("verification_matrix", {}))
        }
    except Exception as ex:
        return {"name": name, "exists": True, "passed": False, "error": str(ex)}


def main() -> None:
    print("Stage L: Aggregating proof bundle...")

    stage_statuses = []
    all_passed = True

    for stage_name, path in STAGE_OUTPUTS.items():
        status = check_stage(stage_name, path)
        stage_statuses.append(status)
        if not status["passed"]:
            all_passed = False

    # Load source model for metadata
    source_model = load_json(STAGE_OUTPUTS["stage_a"])

    # Check gate from stage F (diagram critic gate)
    gate_result = load_json(STAGE_OUTPUTS["stage_f"])
    gate_passed = gate_result.get("gate_passed", False)

    # Check static validation
    static_val = load_json(STAGE_OUTPUTS["stage_i"])
    static_passed = static_val.get("passed", False)

    # Check runtime validation
    runtime_val = load_json(STAGE_OUTPUTS["stage_j"])
    runtime_passed = runtime_val.get("runtime_verification", {}).get("all_passed", False)

    # Check external critic
    external_val = load_json(STAGE_OUTPUTS["stage_k"])
    external_passed = external_val.get("gate_passed", False)

    # Build proof bundle
    bundle = {
        "kind": "proof-bundle",
        "version": "1.0.0",
        "generated_at": datetime.now().isoformat(),
        "pipeline_completed": all_passed,
        "gate_passed": gate_passed and static_passed and runtime_passed and external_passed,
        "skill_name": source_model.get("name", "unknown"),
        "skill_version": source_model.get("version", "0.0.0"),
        "source_kind": source_model.get("kind", "unknown"),
        "source_path": source_model.get("source_path", ""),
        "stages": {},
        "validation_summary": {
            "diagram_gate": gate_passed,
            "static_validation": static_passed,
            "runtime_validation": runtime_passed,
            "external_critic": external_passed
        }
    }

    for status in stage_statuses:
        bundle["stages"][status["name"]] = status

    # Count diagrams
    diagrams_data = load_json(STAGE_OUTPUTS["stage_e"])
    diagram_count = len(diagrams_data.get("diagrams", []))

    bundle["artifacts"] = {
        "index_html": "index.html" if (BASE / "index.html").exists() else None,
        "diagrams_json": "diagrams.json" if diagrams_data else None,
        "mmd_files": [f"{d['diagram_id']}.mmd" for d in diagrams_data.get("diagrams", [])],
        "static_validation": "static-validation.json" if static_passed else None,
        "runtime_validation": "runtime-validation.json" if runtime_passed else None,
        "validation_report": "validation-report.json" if external_passed else None,
        "proof_metadata": "proof-metadata.json" if (BASE / "proof-metadata.json").exists() else None,
        "diagram_count": diagram_count
    }

    OUT = BASE / "proof-bundle.json"
    OUT.write_text(json.dumps(bundle, indent=2), encoding="utf-8")

    # Final gate
    final_passed = bundle["gate_passed"]
    print(f"\nStage L: {'PASS — PROOF BUNDLE CERTIFIED' if final_passed else 'FAIL — PIPELINE INCOMPLETE'}")
    print(f"  pipeline_completed={all_passed}")
    print(f"  gate_passed={final_passed}")
    print(f"  diagram_gate={gate_passed}")
    print(f"  static_validation={static_passed}")
    print(f"  runtime_validation={runtime_passed}")
    print(f"  external_critic={external_passed}")
    print(f"  diagrams={diagram_count}")
    for stage_name, path in STAGE_OUTPUTS.items():
        status = next((s for s in stage_statuses if s["name"] == stage_name), None)
        if status:
            icon = "✓" if status["passed"] else "✗"
            print(f"  {icon} {stage_name}")

    print(f"\nWritten: {OUT}")
    sys.exit(0 if final_passed else 1)


if __name__ == "__main__":
    main()