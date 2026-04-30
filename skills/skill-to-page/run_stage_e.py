#!/usr/bin/env python3
"""Stage E runner: E1 → E2 → E3 → E4 with clear gates between each stage."""
import sys, subprocess
from pathlib import Path

BASE = Path("P:/packages/cc-skills-meta/skills/skill-to-page")

STAGES = [
    ("E1 (Template Loader)",   "stage_e1_loader.py"),
    ("E2 (Content Binder)",    "stage_e2_binder.py"),
    ("E3 (CSS/JS Assembler)",   "stage_e3_assembler.py"),
    ("E4 (HTML Writer)",        "stage_e4_writer.py"),
]

def run_stage(name, script):
    print(f"\n{'='*50}")
    print(f"Running {name}...")
    result = subprocess.run(
        ["uv", "run", "python", script],
        cwd=str(BASE),
        capture_output=True, text=True, encoding="utf-8", timeout=120
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"STDERR: {result.stderr[:500]}")
        print(f"FAILED: {name} — stopping pipeline")
        return False
    return True

for name, script in STAGES:
    ok = run_stage(name, script)
    if not ok:
        sys.exit(1)

print(f"\n{'='*50}")
print("Stage E pipeline COMPLETE — index.html assembled")
print("Next: run stage_f_validator.py, stage_g_validator.py, stage_h_validator.py")