#!/usr/bin/env python
"""
Reason Router — classifies reasoning mode and depth, then executes.

Usage:
    python3 reason_router.py --prompt "your question or task"
"""

import argparse
import json
import os
import sys
from enum import Enum
from pathlib import Path


class Mode(Enum):
    REVIEW = "review"
    DESIGN = "design"
    DIAGNOSE = "diagnose"
    OPTIMIZE = "optimize"
    OFF = "off"


class Depth(Enum):
    LOCAL = 0
    TARGETED = 1
    TRIBUNAL = 2


MODE_KEYWORDS = {
    Mode.REVIEW: [
        "review", "critique", "assess", "evaluate", "check",
        "is this right", "does this work", "what do you think",
        "alternative", "better approach", "improvement",
    ],
    Mode.DESIGN: [
        "design", "architecture", "propose", "how should", "best way",
        "recommend", "spec", "plan", "approach", "alternative design",
    ],
    Mode.DIAGNOSE: [
        "diagnose", "debug", "why is", "why does", "root cause",
        "figure out", "investigate", "trace", "broken",
    ],
    Mode.OPTIMIZE: [
        "optimize", "performance", "faster", "efficient",
        "improve", "cleaner", "refactor",
    ],
    Mode.OFF: [
        "not sure", "unclear", "something off", "doesn't feel right",
        "uncertain", "what's the best", "which is better",
    ],
}


DEPTH_TRIGGERS = {
    Depth.LOCAL: [
        "quick", "shallow", "brief", "simple", "local only",
        "just ", "maybe", "shallow",
    ],
    Depth.TARGETED: [
        "targeted", "some", "balanced", "normal",
    ],
    Depth.TRIBUNAL: [
        "deep", "thorough", "comprehensive", "full",
        "all", "everything", "tribunal",
    ],
}


MODE_CONFIDENCE = {
    Mode.REVIEW: 0.85,
    Mode.DESIGN: 0.80,
    Mode.DIAGNOSE: 0.90,
    Mode.OPTIMIZE: 0.75,
    Mode.OFF: 0.60,
}


DEPTH_CONFIDENCE = {
    Depth.LOCAL: 0.70,
    Depth.TARGETED: 0.80,
    Depth.TRIBUNAL: 0.90,
}


def classify_mode(prompt: str) -> tuple[Mode, float]:
    prompt_lower = prompt.lower()
    scores = {}

    for mode, keywords in MODE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in prompt_lower)
        if score > 0:
            scores[mode] = score * MODE_CONFIDENCE[mode]

    if not scores:
        return Mode.REVIEW, MODE_CONFIDENCE[Mode.REVIEW]

    best = max(scores, key=scores.get)
    return best, scores[best]


def classify_depth(prompt: str) -> tuple[Depth, float]:
    prompt_lower = prompt.lower()
    scores = {}

    for depth, keywords in DEPTH_TRIGGERS.items():
        score = sum(1 for kw in keywords if kw in prompt_lower)
        if score > 0:
            scores[depth] = score * DEPTH_CONFIDENCE[depth]

    if not scores:
        return Depth.TARGETED, DEPTH_CONFIDENCE[Depth.TARGETED]

    best = max(scores, key=scores.get)
    return best, scores[best]


def get_context_signals() -> dict:
    signals = {}

    signals["has_git_changes"] = (
        os.system("git diff --quiet 2>nul") != 0
    )

    signals["file_count"] = 0
    try:
        result = os.popen("git ls-files 2>nul").read()
        signals["file_count"] = len(result.strip().split("\n"))
    except Exception:
        pass

    signals["recent_commits"] = 0
    try:
        result = os.popen(
            "git log --since='7 days ago' --oneline 2>nul"
        ).read()
        signals["recent_commits"] = len(result.strip().split("\n"))
    except Exception:
        pass

    return signals


def score_deficiency(mode: Mode, context: dict) -> float:
    score = 0.5

    if mode == Mode.REVIEW and context.get("has_git_changes"):
        score += 0.2

    if context.get("file_count", 0) > 20:
        score += 0.1

    if context.get("recent_commits", 0) > 5:
        score += 0.1

    return min(score, 1.0)


def route(mode: Mode, depth: Depth, prompt: str) -> dict:
    context = get_context_signals()
    deficiency = score_deficiency(mode, context)

    result = {
        "mode": mode.value,
        "mode_confidence": MODE_CONFIDENCE[mode],
        "depth": depth.value,
        "depth_label": depth.name,
        "deficiency_score": deficiency,
        "context_signals": context,
        "prompt": prompt,
        "route": _route_name(mode, depth),
        "specialists": _specialists_for(mode, depth),
    }

    return result


def _route_name(mode: Mode, depth: Depth) -> str:
    return f"{mode.value}-{depth.name.lower()}"


def _specialists_for(mode: Mode, depth: Depth) -> list[str]:
    base = {
        Mode.REVIEW: ["logic", "quality"],
        Mode.DESIGN: ["architecture", "security"],
        Mode.DIAGNOSE: ["debug", "trace"],
        Mode.OPTIMIZE: ["performance", "security"],
        Mode.OFF: ["debate", "challenger"],
    }

    specialists = base.get(mode, ["general"])

    if depth == Depth.TARGETED:
        return specialists[:1]

    if depth == Depth.TRIBUNAL:
        return specialists + ["adversarial"]

    return ["general"]


def run_local_only(router_output: dict, prompt: str) -> dict:
    return {
        "route": "local",
        "mode": router_output["mode"],
        "depth": router_output["depth"],
        "conclusion": f"[LOCAL] {prompt}",
        "challenge": "No external perspective run in local-only mode.",
        "uncertainty": "Local reasoning only — may miss alternatives.",
        "next_action": "Consider running targeted or tribunal for better coverage.",
    }


def run_targeted(router_output: dict, prompt: str) -> dict:
    specialists = router_output.get("specialists", [])
    primary = specialists[0] if specialists else "general"

    return {
        "route": "targeted",
        "mode": router_output["mode"],
        "depth": router_output["depth"],
        "specialist": primary,
        "conclusion": f"[TARGETED:{primary}] {prompt}",
        "challenge": f"Limited to {primary} specialist view.",
        "uncertainty": "Only one perspective — may miss nuanced issues.",
        "next_action": "Consider tribunal for multi-perspective analysis.",
    }


def run_tribunal(router_output: dict, prompt: str) -> dict:
    specialists = router_output.get("specialists", [])

    return {
        "route": "tribunal",
        "mode": router_output["mode"],
        "depth": router_output["depth"],
        "specialists": specialists,
        "conclusion": f"[TRIBUNAL] {prompt}",
        "challenge": "Multiple perspectives in parallel — consensus required.",
        "uncertainty": "Time-intensive; may be overkill for simple questions.",
        "next_action": "Synthesize findings from all specialists.",
    }


def execute_router(router_output: dict, prompt: str) -> dict:
    depth = Depth(router_output["depth"])

    if depth == Depth.LOCAL:
        return run_local_only(router_output, prompt)
    elif depth == Depth.TARGETED:
        return run_targeted(router_output, prompt)
    else:
        return run_tribunal(router_output, prompt)


def synthesize(
    router_output: dict, execution_output: dict, prompt: str
) -> dict:
    return {
        "route_chosen": router_output["route"],
        "best_current_conclusion": execution_output["conclusion"],
        "strongest_challenge": execution_output["challenge"],
        "biggest_uncertainty": execution_output["uncertainty"],
        "best_next_action": execution_output["next_action"],
        "mode": router_output["mode"],
        "depth": router_output["depth_label"],
        "deficiency_score": router_output["deficiency_score"],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Reason Router — classify and execute reasoning"
    )
    parser.add_argument(
        "--prompt", "-p", required=True, help="User prompt to route"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output raw JSON"
    )

    args = parser.parse_args()

    mode, mode_c = classify_mode(args.prompt)
    depth, depth_c = classify_depth(args.prompt)

    router_output = route(mode, depth, args.prompt)
    execution_output = execute_router(router_output, args.prompt)
    result = synthesize(router_output, execution_output, args.prompt)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Route: {result['route_chosen']}")
        print(f"Mode: {result['mode']} | Depth: {result['depth']}")
        print(f"Deficiency: {result['deficiency_score']:.2f}")
        print()
        print(f"Conclusion: {result['best_current_conclusion']}")
        print(f"Challenge: {result['strongest_challenge']}")
        print(f"Uncertainty: {result['biggest_uncertainty']}")
        print(f"Next Action: {result['best_next_action']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
