from __future__ import annotations

import json
import re
import shutil
import subprocess
from typing import Sequence


def run_command(cmd: Sequence[str], timeout: int = 180) -> tuple[bool, str, str]:
    # Resolve command name to actual path on Windows (handles .CMD/.PS1 shim files)
    cmd_list = list(cmd)
    resolved = shutil.which(cmd_list[0])
    if resolved:
        cmd_list = [resolved] + cmd_list[1:]

    try:
        proc = subprocess.run(
            cmd_list,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )
        return proc.returncode == 0, proc.stdout.strip(), proc.stderr.strip()
    except subprocess.TimeoutExpired as e:
        return False, "", f"TIMEOUT: {e}"
    except FileNotFoundError:
        return False, "", f"NOT_FOUND: {cmd_list[0]}"
    except Exception as e:
        return False, "", f"EXCEPTION: {e}"


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def normalize_query(query: str) -> str:
    """Normalize query for consistent ledger keys."""
    return query.strip().lower()


def json_pretty(obj) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False, default=str)
