#!/usr/bin/env python3
"""reason_openai_router.py — mode/depth router for /reason_openai."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Sequence

class Mode(str, Enum):
    REVIEW = "review"
    DESIGN = "design"
    DIAGNOSE = "diagnose"
    OPTIMIZE = "optimize"
    OFF = "off"
    DECIDE = "decide"
    EXECUTE = "execute"

class Depth(int, Enum):
    LOCAL = 0
    TARGETED = 1
    TRIBUNAL = 2

@dataclass
class ContextSignals:
    prompt: str
    cwd: str
    in_git_repo: bool
    has_code_indicators: bool
    has_error_indicators: bool
    has_perf_indicators: bool
    has_existing_solution_indicators: bool
    has_design_indicators: bool
    has_dissatisfaction_indicators: bool
    has_vague_uncertainty_indicators: bool

@dataclass
class DeficiencyScores:
    framing: int = 0
    confidence: int = 0
    evidence: int = 0
    option_space: int = 0
    decision: int = 0
    implementation: int = 0

REVIEW_PATTERNS = [r"\breview\b", r"\bcritique\b", r"\bpoke holes\b", r"\bnot convinced\b", r"\bunhappy\b", r"\bchallenge\b"]
DESIGN_PATTERNS = [r"\bdesign\b", r"\barchitecture\b", r"\bapproach\b", r"\bsolution\b", r"\bbrainstorm\b", r"\boptions\b"]
DIAGNOSE_PATTERNS = [r"\bbug\b", r"\berror\b", r"\bfailing\b", r"\broot cause\b", r"\bwhy is\b", r"\bbroken\b"]
OPTIMIZE_PATTERNS = [r"\boptimi[sz]e\b", r"\bperformance\b", r"\blatency\b", r"\bcost\b", r"\bimprove\b"]
OFF_PATTERNS = [r"\bfeels off\b", r"\bsomething feels off\b", r"\bmissing something\b", r"\bvague\b", r"\buneasy\b"]
CODE_PATTERNS = [r"```", r"\bfunction\b", r"\bclass\b", r"\bmethod\b", r"\bmodule\b", r"\bpatch\b"]
ERROR_PATTERNS = [r"\berror\b", r"\bexception\b", r"\btraceback\b", r"\bfailed\b", r"\bcrash\b"]
PERF_PATTERNS = [r"\bslow\b", r"\blatency\b", r"\bthroughput\b", r"\bmemory\b", r"\bcpu\b"]
EXISTING_SOLUTION_PATTERNS = [r"\bthis answer\b", r"\bthis solution\b", r"\bthis patch\b", r"\bthis design\b"]

MODE_FLAG_PATTERNS = {
    Mode.REVIEW: r"--mode\s+review\b",
    Mode.DESIGN: r"--mode\s+design\b",
    Mode.DIAGNOSE: r"--mode\s+diagnose\b",
    Mode.OPTIMIZE: r"--mode\s+optimize\b",
    Mode.OFF: r"--mode\s+off\b",
    Mode.DECIDE: r"--mode\s+decide\b",
    Mode.EXECUTE: r"--mode\s+execute\b",
}

def contains_any(text: str, patterns: Sequence[str]) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)

def in_git_repo(cwd: str) -> bool:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"], cwd=cwd,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, check=False
        )
        return result.returncode == 0 and result.stdout.strip() == "true"
    except Exception:
        return False

def collect_context(prompt: str) -> ContextSignals:
    cwd = os.getcwd()
    return ContextSignals(
        prompt=prompt, cwd=cwd, in_git_repo=in_git_repo(cwd),
        has_code_indicators=contains_any(prompt, CODE_PATTERNS),
        has_error_indicators=contains_any(prompt, ERROR_PATTERNS),
        has_perf_indicators=contains_any(prompt, PERF_PATTERNS),
        has_existing_solution_indicators=contains_any(prompt, EXISTING_SOLUTION_PATTERNS),
        has_design_indicators=contains_any(prompt, DESIGN_PATTERNS),
        has_dissatisfaction_indicators=contains_any(prompt, REVIEW_PATTERNS),
        has_vague_uncertainty_indicators=contains_any(prompt, OFF_PATTERNS),
    )

def score_deficiencies(ctx: ContextSignals) -> DeficiencyScores:
    scores = DeficiencyScores()
    if ctx.has_vague_uncertainty_indicators:
        scores.framing += 2; scores.confidence += 2
    if ctx.has_dissatisfaction_indicators or ctx.has_existing_solution_indicators:
        scores.confidence += 3
    if ctx.has_error_indicators or ctx.has_code_indicators or ctx.has_perf_indicators:
        scores.evidence += 2; scores.implementation += 2
    if ctx.has_design_indicators:
        scores.option_space += 2; scores.decision += 1
    if contains_any(ctx.prompt, [r"\bwhich\b", r"\bchoose\b", r"\bbetter\b"]):
        scores.decision += 2
    return scores

def parse_mode_flags(prompt: str) -> Optional[Mode]:
    for mode, pattern in MODE_FLAG_PATTERNS.items():
        if re.search(pattern, prompt, re.IGNORECASE):
            return mode
    return None

def choose_mode(scores: DeficiencyScores, ctx: ContextSignals, forced: Optional[Mode] = None) -> Mode:
    if forced:
        return forced
    if ctx.has_vague_uncertainty_indicators and scores.framing >= 2:
        return Mode.OFF
    if ctx.has_error_indicators:
        return Mode.DIAGNOSE
    if ctx.has_perf_indicators:
        return Mode.OPTIMIZE
    if ctx.has_existing_solution_indicators or ctx.has_dissatisfaction_indicators:
        return Mode.REVIEW
    if ctx.has_design_indicators:
        return Mode.DESIGN
    ranked = {
        Mode.OFF: scores.framing + scores.confidence,
        Mode.REVIEW: scores.confidence + scores.implementation,
        Mode.DIAGNOSE: scores.evidence + scores.implementation,
        Mode.OPTIMIZE: scores.implementation + scores.decision,
        Mode.DESIGN: scores.option_space + scores.decision,
    }
    return max(ranked.items(), key=lambda x: x[1])[0]

def choose_depth(mode: Mode, scores: DeficiencyScores, ctx: ContextSignals) -> Depth:
    if mode == Mode.OFF and scores.confidence >= 3:
        return Depth.TARGETED
    if mode in {Mode.REVIEW, Mode.DESIGN} and (scores.confidence >= 3 or scores.option_space >= 2):
        return Depth.TARGETED
    if mode in {Mode.DIAGNOSE, Mode.OPTIMIZE} and (ctx.has_code_indicators or ctx.in_git_repo):
        return Depth.TARGETED
    if scores.confidence >= 3 and (scores.option_space >= 2 or scores.implementation >= 2):
        return Depth.TRIBUNAL
    return Depth.LOCAL

def route_explanation(mode: Mode, ctx: ContextSignals) -> str:
    reasons = []
    if ctx.has_existing_solution_indicators: reasons.append("existing solution detected")
    if ctx.has_dissatisfaction_indicators: reasons.append("dissatisfaction detected")
    if ctx.has_error_indicators: reasons.append("error symptoms present")
    if ctx.has_perf_indicators: reasons.append("performance cues present")
    if ctx.has_design_indicators: reasons.append("design cues present")
    if ctx.has_vague_uncertainty_indicators: reasons.append("vague uncertainty detected")
    reason_text = ", ".join(reasons) if reasons else "general reasoning requested"
    return f"Routed to {mode.value} because {reason_text}."

def build_local_reasoning_prompt(prompt: str, mode: Mode) -> str:
    guidance = {
        Mode.REVIEW: "Review the existing answer or solution. Surface hidden flaws, missed tradeoffs, and implementation risk.",
        Mode.DESIGN: "Expand the solution space, compare strong options, and recommend a path.",
        Mode.DIAGNOSE: "Generate hypotheses, identify the smallest discriminating check, and rank likely causes.",
        Mode.OPTIMIZE: "Clarify the objective function, identify true bottlenecks, and separate local tweaks from structural improvements.",
        Mode.OFF: "Do not answer directly. Identify what assumption may be wrong, what is missing, and what question should be asked instead.",
        Mode.DECIDE: "Force a clear recommendation. Name the best option, why it wins, its strongest challenge, and what would change the decision.",
        Mode.EXECUTE: "Move from thought to action. Identify the immediate next step and the concrete blockers to shipping.",
    }[mode]
    return (
        f"You are /reason_openai local controller.\n"
        f"Mode: {mode.value}\n"
        f"Goal: {guidance}\n\n"
        f"User prompt:\n{prompt}\n\n"
        "Return these exact sections:\n"
        "Route chosen:\n"
        "Best current conclusion:\n"
        "Why it wins:\n"
        "Strongest challenge:\n"
        "Biggest uncertainty:\n"
        "Best next action:\n"
        "Ignore:\n"
        "Minority warning:\n"
    )

def parse_sections(text: str) -> Dict[str, str]:
    labels = ["Route chosen:", "Best current conclusion:", "Why it wins:",
             "Strongest challenge:", "Biggest uncertainty:", "Best next action:", "Ignore:", "Minority warning:"]
    sections = {label[:-1]: "" for label in labels}
    current_key = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        matched = False
        for label in labels:
            if line.startswith(label):
                current_key = label[:-1]
                value = line[len(label):].strip()
                if value:
                    sections[current_key] = value
                matched = True
                break
        if not matched and current_key:
            sections[current_key] = (sections[current_key] + "\n" + line).strip()
    return sections

def format_result(sections: Dict[str, str], mode: Mode, why: str) -> str:
    parts = [
        f"Route chosen:\n{why}",
        f"Best current conclusion:\n{sections.get('Best current conclusion', 'No conclusion produced.')}",
        f"Why it wins:\n{sections.get('Why it wins', 'No reasoning produced.')}",
        f"Strongest challenge:\n{sections.get('Strongest challenge', 'No challenge produced.')}",
        f"Biggest uncertainty:\n{sections.get('Biggest uncertainty', 'No uncertainty produced.')}",
        f"Best next action:\n{sections.get('Best next action', 'No next action produced.')}",
    ]
    if sections.get("Ignore"):
        parts.append(f"Ignore:\n{sections['Ignore']}")
    if sections.get("Minority warning"):
        parts.append(f"Minority warning:\n{sections['Minority warning']}")
    return "\n\n".join(parts)

def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="/reason_openai router")
    parser.add_argument("--prompt", default="", help="Prompt to reason about")
    parser.add_argument("--mode", default="", help="Force mode: review, design, diagnose, optimize, off, decide, execute")
    parser.add_argument("--depth", default="", help="Force depth: local, targeted, tribunal")
    args = parser.parse_args(argv)

    prompt = args.prompt.strip()
    if not prompt:
        print("No prompt provided.")
        return 1

    forced_mode = None
    if args.mode:
        try:
            forced_mode = Mode(args.mode.lower())
        except ValueError:
            print(f"Unknown mode: {args.mode}")
            return 1

    forced_depth = None
    if args.depth:
        depth_map = {"local": Depth.LOCAL, "targeted": Depth.TARGETED, "tribunal": Depth.TRIBUNAL}
        forced_depth = depth_map.get(args.depth.lower())
        if forced_depth is None:
            print(f"Unknown depth: {args.depth}")
            return 1

    ctx = collect_context(prompt)
    scores = score_deficiencies(ctx)
    mode = choose_mode(scores, ctx, forced_mode)
    depth = forced_depth or choose_depth(mode, scores, ctx)
    why = route_explanation(mode, ctx)

    if depth == Depth.LOCAL:
        local_prompt = build_local_reasoning_prompt(prompt, mode)
        sys.stdout.write(local_prompt)
        return 0

    sys.stdout.write(
        f"Route chosen:\n{why}\n\n"
        f"Mode: {mode.value}\n"
        f"Depth: {depth.value}\n\n"
        f"For depth {depth.value}, invoke subagents:\n"
        f"- red_team (attack the conclusion)\n"
        f"- implementation_realist (pressure-test practicality)\n"
        f"- decision_editor (compress to final recommendation)\n\n"
        f"Local reasoning prompt:\n{build_local_reasoning_prompt(prompt, mode)}"
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
