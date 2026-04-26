from __future__ import annotations

from ..models import Finding

# Domain definitions matching RNS render.py DOMAIN_MAP
DOMAIN_MAP: dict[str, tuple[str, str]] = {
    "quality": ("🔧", "QUALITY"),
    "tests": ("🧪", "TESTS"),
    "docs": ("📄", "DOCS"),
    "security": ("🔒", "SECURITY"),
    "performance": ("⚡", "PERFORMANCE"),
    "git": ("🐙", "GIT"),
    "deps": ("📦", "DEPS"),
    "other": ("📌", "OTHER"),
}


def _subletter(idx: int) -> str:
    """Return Excel-style column label for 1-based index: 1→a, 26→z, 27→aa."""
    result: list[str] = []
    n = idx - 1
    while True:
        n, rem = divmod(n, 26)
        result.append(chr(ord("a") + rem))
        if n == 0:
            break
    return "".join(reversed(result))


def _get_domain_def(domain: str) -> tuple[str, str]:
    return DOMAIN_MAP.get(domain, ("📌", domain.upper()))


def render_machine_format(findings: list[Finding]) -> str:
    """Render findings in RNS-compatible machine-parseable pipe-delimited format.

    Format matches RNS render.py render_machine_format():
        RNS|D|{num}|{emoji}|{label}
        RNS|A|{num}{sub}|{domain}|E:{effort}|{action}/{priority}|{desc}|{file_ref}|owner={owner}|done={done}|caused_by={caused_by}|blocks={blocks}|unverified={unverified}
        RNS|Z|0|NONE

    This is the authoritative machine output contract for GTO artifacts.
    """
    lines: list[str] = ["<!-- format: machine -->"]

    # Group findings by domain
    groups: dict[str, list[Finding]] = {}
    for f in findings:
        groups.setdefault(f.domain, []).append(f)

    domain_num = 0
    for domain_key, domain_findings in groups.items():
        domain_num += 1
        emoji, label = _get_domain_def(domain_key)
        lines.append(f"RNS|D|{domain_num}|{emoji}|{label}")

        for idx, f in enumerate(domain_findings, start=1):
            sub = _subletter(idx)
            effort = f.effort or "?"
            desc = f.description.replace("|", "\\|")
            file_ref = f.file or ""
            if f.line:
                file_ref = f"{file_ref}:{f.line}" if file_ref else str(f.line)
            owner = f.owner_skill or ""
            done = "1" if f.status == "resolved" else "0"
            caused_by = ""
            blocks = ""
            unverified = "1" if f.unverified else "0"
            lines.append(
                f"RNS|A|{domain_num}{sub}|{f.domain}|"
                f"E:{effort}|{f.action}/{f.priority}|"
                f"{desc}|{file_ref}|owner={owner}|done={done}|"
                f"caused_by={caused_by}|blocks={blocks}|unverified={unverified}"
            )

    lines.append("RNS|Z|0|NONE")
    return "\n".join(lines)
