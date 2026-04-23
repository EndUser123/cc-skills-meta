---
description: Review the last reason_openai recommendation and record outcome calibration.
allowed-tools: Bash(tail:*), Bash(python:*)
---

# /reason_openai_review_last

Show the last `/reason_openai` log entry, then help assess:
- Did you act on it?
- Was it directionally correct?
- Outcome quality 1–5
- Biggest miss
- Time to action (minutes)
- Any review notes

First show the last entry:

```
!tail -1 ~/.claude/logs/reason_openai_log.jsonl 2>/dev/null || echo "No reason_openai logs found."
```

Then ask the user for the missing review fields and tell them the exact update command to run:

```
python ~/.claude/hooks/reason_openai_review_entry.py --id <id> --acted-on yes|no --correct yes|no --outcome-quality 1-5 --biggest-miss "..." --time-to-action N
```

If no logs exist, say so and suggest running `/reason_openai` first.
