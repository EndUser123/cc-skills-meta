#!/usr/bin/env python3
"""
run_fidelity.py — Run FidelityTracker against a target skill.

Usage:
    python run_fidelity.py <skill_path> [eval_set_path]

Example:
    python run_fidelity.py P:/.claude/skills/gto
    python run_fidelity.py P:/.claude/skills/gto eval_sets/default.json
    python run_fidelity.py .  # run against self
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from fidelity_tracker import run as fidelity_tracker

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_fidelity.py <skill_path> [eval_set_path]")
        sys.exit(1)

    skill_path = sys.argv[1]
    eval_set_path = sys.argv[2] if len(sys.argv) > 2 else None

    score = fidelity_tracker(skill_path, eval_set_path)

    print(f"FidelityTracker — {skill_path}")
    print(f"  trigger_accuracy: {score.trigger_accuracy:.2%}")
    print(f"  outcome_accuracy:  {score.outcome_accuracy:.2%}")
    print(f"  degradation_delta: {score.degradation_delta:.2%}")
    print(f"  passed:             {score.passed}")
    details = score.details or {}
    print(f"  evals_passed:        {details.get('evals_passed', '?')}/{details.get('evals_total', '?')}")
    print(f"  eval_set:            {details.get('eval_set', '?')}")

    if not score.passed:
        print("  FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
