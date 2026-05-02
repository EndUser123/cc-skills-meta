"""Epistemic validator for direct-answer and non-English detection.

Used by the plugin's StopHook_epistemic_contract.py subprocess hook.
Complements the hooks-level epistemic_validator.py (which handles
causal/comparative/fact-support rules via Stop.py in-process).
"""

import re
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class EpistemicIssue:
    type: str
    section: str
    bullet_index: int
    message: str


@dataclass
class EpistemicConfig:
    treat_missing_direct_answer_as: Literal["error", "warn", "ignore"] = "error"
    treat_non_english_output_as: Literal["error", "warn", "ignore"] = "error"
    session_language: str = "english"


# ---------------------------------------------------------------------------
# Direct-answer detection
# ---------------------------------------------------------------------------

_CONCRETE_QUESTION_RE = re.compile(
    r"^(?:Does|Is|Are|Can|Could|Should|Would|Will|Do|What|When|Where|Who|Why|How)\b",
    re.IGNORECASE,
)

_DIRECT_ANSWER_RE = re.compile(
    r"^(?:"
    r"(?:Direct\s+answer|Answer)\s*:"  # "Direct answer:" / "Answer:"
    r"|(?:The\s+answer\s+is)\s*:"       # "The answer is:"
    r"|Yes\b"                            # "Yes, ..."
    r"|No\b"                             # "No, ..."
    r"|Probably\s+(?:yes|no)\b"          # "Probably yes/no"
    r")",
    re.IGNORECASE | re.MULTILINE,
)


def is_concrete_question(text: str) -> bool:
    return bool(_CONCRETE_QUESTION_RE.match(text.strip()))


def has_direct_answer(text: str) -> bool:
    return bool(_DIRECT_ANSWER_RE.search(text))


def validate_missing_direct_answer(
    user_input: str,
    response: str,
    config: EpistemicConfig,
) -> EpistemicIssue | None:
    if config.treat_missing_direct_answer_as == "ignore":
        return None
    if not is_concrete_question(user_input):
        return None
    if has_direct_answer(response):
        return None
    return EpistemicIssue(
        type="missing_direct_answer",
        section="__GLOBAL__",
        bullet_index=-1,
        message="Direct answer missing. Concrete questions require a direct answer in the first sentence.",
    )


# ---------------------------------------------------------------------------
# Non-English detection
# ---------------------------------------------------------------------------

_CJK_RE = re.compile(
    r"[一-鿿぀-ゟ゠-ヿ가-힯]"
)
_CYRILLIC_RE = re.compile(r"[Ѐ-ӿ]")
_CODE_BLOCK_RE = re.compile(r"```[\s\S]*?```", re.MULTILINE)
_NON_WHITESPACE_RE = re.compile(r"\S")


def _strip_code_blocks(text: str) -> str:
    return _CODE_BLOCK_RE.sub("", text)


def is_substantially_non_english(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    prose = _strip_code_blocks(stripped)
    non_ws = _NON_WHITESPACE_RE.findall(prose)
    if not non_ws:
        return False
    cjk = len(_CJK_RE.findall(prose))
    cyrillic = len(_CYRILLIC_RE.findall(prose))
    non_latin = cjk + cyrillic
    ratio = non_latin / len(non_ws)
    return ratio > 0.3


def validate_non_english_output(
    response: str,
    config: EpistemicConfig,
) -> EpistemicIssue | None:
    if config.treat_non_english_output_as == "ignore":
        return None
    if config.session_language != "english":
        return None
    if not is_substantially_non_english(response):
        return None
    return EpistemicIssue(
        type="non_english_output",
        section="__GLOBAL__",
        bullet_index=-1,
        message="Response is substantially non-English. Default output language must be English.",
    )


# ---------------------------------------------------------------------------
# Repair path
# ---------------------------------------------------------------------------

_REPAIRABLE_TYPES = {"non_english_output", "missing_direct_answer"}


def is_repairable(issues: list[EpistemicIssue]) -> bool:
    if not issues:
        return False
    return all(i.type in _REPAIRABLE_TYPES for i in issues)


def build_repair_prompt(issues: list[EpistemicIssue]) -> str | None:
    if not is_repairable(issues):
        return None
    types = {i.type for i in issues}
    parts = ["REPAIR INSTRUCTIONS:"]
    if "non_english_output" in types:
        parts.append(
            "- Rewrite the entire response in English. "
            "Do not use non-English prose outside of quoted source material."
        )
    if "missing_direct_answer" in types:
        parts.append(
            "- Add a direct answer in the first sentence. "
            "Start with Yes/No/Probably or use 'Direct answer:' format."
        )
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_all_checks(
    user_input: str,
    response: str,
    config: EpistemicConfig,
) -> list[EpistemicIssue]:
    issues: list[EpistemicIssue] = []
    da = validate_missing_direct_answer(user_input, response, config)
    if da:
        issues.append(da)
    ne = validate_non_english_output(response, config)
    if ne:
        issues.append(ne)
    return issues
