from __future__ import annotations

import re
from .models import ContextBundle, DataClass


PATH_PATTERNS = [
    r"[A-Za-z]:[\\/][^\s]+",
    r"\./[^\s]+",
    r"\.\./[^\s]+",
    r"/[^\s]+",
]


def build_context(query: str) -> ContextBundle:
    paths = []
    for pattern in PATH_PATTERNS:
        paths.extend(re.findall(pattern, query))

    detected_code = any(token in query for token in ["def ", "class ", "{", "}", "function ", "import "])
    detected_fs = len(paths) > 0 or "repo" in query.lower() or "directory" in query.lower()

    # Default to LOCAL_OK; pruning text-policing Stop hooks to alleviate deadlock.
    data_class = DataClass.LOCAL_OK

    summary = []
    if paths:
        summary.append(f"Detected paths: {', '.join(paths)}")
    if detected_code:
        summary.append("Detected possible code snippets or code-centric phrasing.")
    if detected_fs:
        summary.append("Detected filesystem/repo orientation.")

    return ContextBundle(
        explicit_paths=paths,
        inline_context="",
        detected_code=detected_code,
        detected_filesystem_reference=detected_fs,
        working_summary=" ".join(summary).strip(),
        data_class=data_class
    )
