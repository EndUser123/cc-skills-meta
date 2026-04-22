# reason_openai — distilled

## reason_router.py

```python
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
classify_mode(prompt: str) -> tuple[Mode, float]
classify_depth(prompt: str) -> tuple[Depth, float]
get_context_signals() -> dict
score_deficiency(mode: Mode, context: dict) -> float
route(mode: Mode, depth: Depth, prompt: str) -> dict
run_local_only(router_output: dict, prompt: str) -> dict
run_targeted(router_output: dict, prompt: str) -> dict
run_tribunal(router_output: dict, prompt: str) -> dict
execute_router(router_output: dict, prompt: str) -> dict
synthesize(router_output: dict, execution_output: dict, prompt: str) -> dict
main()
```
