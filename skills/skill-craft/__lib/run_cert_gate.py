#!/usr/bin/env python3
"""
run_cert_gate.py — Run CertificationGate against a target skill.

Usage:
    python run_cert_gate.py <skill_path>

Example:
    python run_cert_gate.py P:/.claude/skills/gto
    python run_cert_gate.py .  # run against self
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from certification_gate import check as certification_gate

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_cert_gate.py <skill_path>")
        sys.exit(1)

    skill_path = Path(sys.argv[1]).resolve()
    result = certification_gate(skill_path)

    print(f"CertificationGate — {skill_path}")
    print(f"  passed:  {result.passed}")
    if result.errors:
        print(f"  errors:")
        for e in result.errors:
            print(f"    - {e}")
    if result.warnings:
        print(f"  warnings:")
        for w in result.warnings:
            print(f"    - {w}")
    if result.passed:
        print("  OK")
    else:
        print("  FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
