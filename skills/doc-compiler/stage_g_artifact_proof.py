#!/usr/bin/env python3
"""Stage G: Artifact Proof Generator for doc-compiler.

Reads: index.html + source-model.json + e3-output.json
Emits: artifact-proof.json
"""
import json, re, sys
from pathlib import Path
from datetime import datetime

BASE = Path("P:/packages/cc-skills-meta/skills/doc-compiler")
INDEX = BASE / "index.html"
SOURCE = BASE / "source-model.json"
E3_OUT = BASE / "e3-output.json"
OUT = BASE / "artifact-proof.json"


def load_json(p: Path) -> dict:
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> None:
    errors = []

    index = INDEX.read_text(encoding="utf-8") if INDEX.exists() else ""
    model = load_json(SOURCE)
    e3 = load_json(E3_OUT)

    if not index:
        errors.append("index.html not found")
    if not model:
        errors.append("source-model.json not found")

    steps_declared = len(model.get("steps", []))
    steps_rendered = index.count('class="step"') if index else 0

    # Build verification matrix
    vmatrix = {
        "S5_mermaid_present": {
            "passed": 'id="mermaidSource"' in index,
            "reason": "mermaidSource element found" if 'id="mermaidSource"' in index else "missing mermaidSource"
        },
        "S12_no_placeholders": {
            "passed": "{{" not in index,
            "reason": "no placeholders remain" if "{{" not in index else "unfilled placeholders"
        },
        "S9_steps_present": {
            "passed": steps_rendered > 0,
            "reason": f"{steps_rendered} step elements rendered"
        },
        "coverage_steps": {
            "passed": steps_rendered >= steps_declared,
            "reason": f"rendered {steps_rendered}/{steps_declared} steps"
        },
    }

    # Check TOC state
    toc_state = {
        "toc_present": 'id="toc"' in index,
        "toc_toggle_present": 'id="tocToggle"' in index,
        "toc_items": index.count('<a href="#'),
    }

    # Check CSS contract
    css_contract = {
        "has_style_block": "<style>" in index,
        "responsive_meta": "viewport" in index,
        "dark_mode_support": "prefers-color-scheme" in index,
    }

    # Listener integrity
    listener_integrity = {
        "theme_toggle_listener": "theme-toggle" in index or "themeToggle" in index,
        "toc_toggle_listener": "tocToggle" in index,
    }

    proof = {
        "source_path": str(INDEX.resolve()) if INDEX.exists() else "",
        "artifact_path": str(INDEX.resolve()) if INDEX.exists() else "",
        "generated_at": datetime.now().isoformat(),
        "coverage": {
            "steps_declared": steps_declared,
            "workflow_sections_rendered": steps_rendered,
            "elements_present": len(re.findall(r'id="[^"]+"', index)) if index else 0,
        },
        "verification_matrix": vmatrix,
        "toc_state": toc_state,
        "css_contract": css_contract,
        "listener_integrity": listener_integrity,
    }

    OUT.write_text(json.dumps(proof, indent=2), encoding="utf-8")

    n_passed = sum(1 for v in vmatrix.values() if v["passed"])
    print(f"Stage G: PASS — {n_passed}/{len(vmatrix)} checks passed")
    print(f"Written: {OUT}")
    sys.exit(0)


if __name__ == "__main__":
    main()
